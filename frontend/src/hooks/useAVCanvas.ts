/**
 * useAVCanvas - AVCanvas 封装 Hook
 *
 * 基于 @webav/av-canvas 实现专业的视频编辑播放器
 */

import { useRef, useEffect, useState, useCallback } from 'react';
import { AVCanvas } from '@webav/av-canvas';
import { MP4Clip, VisibleSprite } from '@webav/av-cliper';
import type { Shot, GeneratedVideo } from '../api/types';
import { getFullUrl } from '../utils/url';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

interface UseAVCanvasProps {
    orderedShots: ShotWithVideo[];
    containerRef: React.RefObject<HTMLDivElement>;
}

export const useAVCanvas = ({ orderedShots, containerRef }: UseAVCanvasProps) => {
    const avCanvasRef = useRef<AVCanvas | null>(null);
    const spritesRef = useRef<VisibleSprite[]>([]);
    const ignoreNextTimeUpdate = useRef(false);
    const targetSeekTime = useRef<number | null>(null);
    const previousShotsRef = useRef<ShotWithVideo[]>([]);

    // 状态
    const [isReady, setIsReady] = useState(false);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0); // 秒
    const [totalDuration, setTotalDuration] = useState(0); // 秒
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [currentShotIndex, setCurrentShotIndex] = useState(0);

    // 初始化 AVCanvas
    useEffect(() => {
        if (!containerRef.current || orderedShots.length === 0) return;

        // 检查是否需要完全重新初始化
        const needsReinit =
            previousShotsRef.current.length === 0 || // 首次初始化
            previousShotsRef.current.length !== orderedShots.length ||
            previousShotsRef.current.some((shot, i) => {
                const prevVideoPath = shot.videoData?.videoPath || shot.videoPath || '';
                const currVideoPath = orderedShots[i]?.videoData?.videoPath || orderedShots[i]?.videoPath || '';
                return prevVideoPath !== currVideoPath;
            });

        // 如果只是 duration 改变，只更新 sprite 时间
        if (!needsReinit && avCanvasRef.current && spritesRef.current.length > 0) {
            console.log('[useAVCanvas] ✅ Only updating sprite times (duration changed)');

            let accTime = 0;
            for (let i = 0; i < orderedShots.length; i++) {
                const shot = orderedShots[i];
                const sprite = spritesRef.current[i];
                if (sprite) {
                    sprite.time = {
                        offset: accTime * 1e6,
                        duration: shot.duration * 1e6
                    };
                    accTime += shot.duration;
                }
            }

            // 更新总时长
            const total = orderedShots.reduce((sum, shot) => sum + shot.duration, 0);
            setTotalDuration(total);

            // 保存当前 shots 引用
            previousShotsRef.current = orderedShots;

            // 不需要重新初始化，直接返回，不执行下面的代码
            return;
        }

        console.log('[useAVCanvas] ❌ Full reinitialization required');

        // 需要重新初始化，先手动销毁旧的
        if (avCanvasRef.current) {
            console.log('[useAVCanvas] Manually destroying old AVCanvas');
            avCanvasRef.current.destroy();
            avCanvasRef.current = null;
            spritesRef.current = [];
        }

        const initAVCanvas = async () => {
            try {
                console.log('[useAVCanvas] Initializing with', orderedShots.length, 'shots');

                // 创建 AVCanvas 实例
                const avCanvas = new AVCanvas(containerRef.current!, {
                    width: 1280,
                    height: 720,
                    bgColor: '#000000'
                });

                // 监听时间更新事件
                const unsubscribeTimeUpdate = avCanvas.on('timeupdate', (time: number) => {
                    const timeInSeconds = time / 1e6;

                    // 如果我们正在 seek，并且需要忽略这次更新
                    if (ignoreNextTimeUpdate.current && targetSeekTime.current !== null) {
                        // 检查时间是否接近目标时间（误差在 0.1 秒内）
                        const timeDiff = Math.abs(timeInSeconds - targetSeekTime.current);
                        if (timeDiff > 0.1) {
                            // 时间差太大，忽略这次更新
                            console.log('[useAVCanvas] Ignoring timeupdate:', timeInSeconds, 'target:', targetSeekTime.current);
                            return;
                        } else {
                            // 时间接近目标，接受这次更新并重置标志
                            ignoreNextTimeUpdate.current = false;
                            targetSeekTime.current = null;
                        }
                    }

                    setCurrentTime(timeInSeconds);

                    // 更新当前镜头索引
                    let acc = 0;
                    for (let i = 0; i < orderedShots.length; i++) {
                        acc += orderedShots[i].duration;
                        if (timeInSeconds < acc) {
                            setCurrentShotIndex(i);
                            break;
                        }
                    }
                });

                // 监听播放状态事件
                const unsubscribePlaying = avCanvas.on('playing', () => {
                    setIsPlaying(true);
                });

                const unsubscribePaused = avCanvas.on('paused', () => {
                    setIsPlaying(false);
                });

                // 加载所有视频片段
                const sprites: VisibleSprite[] = [];
                let accTime = 0;

                for (let i = 0; i < orderedShots.length; i++) {
                    const shot = orderedShots[i];
                    const videoPath = shot.videoData?.videoPath || shot.videoPath || '';

                    // 只处理有视频的shots，跳过只有图片的
                    if (!videoPath) {
                        console.log('[useAVCanvas] Shot', i, 'has no video path, skipping');
                        continue;
                    }

                    const fullUrl = getFullUrl(videoPath);
                    console.log('[useAVCanvas] Loading shot', i, ':', fullUrl);

                    try {
                        // 获取视频流
                        const response = await fetch(fullUrl);
                        if (!response.ok) {
                            throw new Error(`Failed to fetch: ${response.statusText}`);
                        }

                        // 创建 MP4Clip
                        const clip = new MP4Clip(response.body!);

                        // 创建 VisibleSprite
                        const sprite = new VisibleSprite(clip);

                        // 设置时间范围（微秒）
                        sprite.time = {
                            offset: accTime * 1e6,
                            duration: shot.duration * 1e6
                        };

                        // 添加到画布
                        await avCanvas.addSprite(sprite);
                        sprites.push(sprite);

                        accTime += shot.duration;
                        console.log('[useAVCanvas] Shot', i, 'loaded, accumulated time:', accTime);
                    } catch (err) {
                        console.error('[useAVCanvas] Failed to load shot', i, ':', err);
                        throw err;
                    }
                }

                // 保存引用
                avCanvasRef.current = avCanvas;
                spritesRef.current = sprites;

                // 设置总时长
                const total = orderedShots.reduce((sum, shot) => sum + shot.duration, 0);
                setTotalDuration(total);

                setIsReady(true);
                setError(null);

                console.log('[useAVCanvas] Initialized successfully, total duration:', total);

                // 保存当前 shots 引用
                previousShotsRef.current = orderedShots;

                // 返回清理函数
                return () => {
                    unsubscribeTimeUpdate();
                    unsubscribePlaying();
                    unsubscribePaused();
                };
            } catch (err: any) {
                console.error('[useAVCanvas] Initialization error:', err);
                setError(err.message || 'Failed to initialize player');
                setIsReady(false);
            }
        };

        let cleanup: (() => void) | undefined;
        initAVCanvas().then(fn => { cleanup = fn; });

        // 清理函数：只在组件卸载时执行
        return () => {
            console.log('[useAVCanvas] Component unmounting, cleaning up');
            if (cleanup) cleanup();
            if (avCanvasRef.current) {
                avCanvasRef.current.destroy();
                avCanvasRef.current = null;
            }
            spritesRef.current = [];
        };
    }, [orderedShots, containerRef]);

    // 播放/暂停
    const handlePlayPause = useCallback(() => {
        if (!avCanvasRef.current || !isReady) return;

        try {
            if (isPlaying) {
                avCanvasRef.current.pause();
                setIsPlaying(false);
                console.log('[useAVCanvas] Paused at', currentTime);
            } else {
                avCanvasRef.current.play({ start: currentTime * 1e6 });
                setIsPlaying(true);
                console.log('[useAVCanvas] Playing from', currentTime);
            }
        } catch (err) {
            console.error('[useAVCanvas] Play/Pause error:', err);
            setError('Failed to play/pause');
        }
    }, [isPlaying, isReady, currentTime]);

    // Seek
    const handleSeek = useCallback(async (time: number, shouldResume?: boolean) => {
        if (!avCanvasRef.current || !isReady) return;

        try {
            console.log('[useAVCanvas] Seeking to', time);

            // 记录当前播放状态
            const wasPlaying = shouldResume !== undefined ? shouldResume : isPlaying;

            // 设置标志和目标时间
            ignoreNextTimeUpdate.current = true;
            targetSeekTime.current = time;

            // 暂停播放
            avCanvasRef.current.pause();
            setIsPlaying(false);

            // 跳转到指定时间（使用 previewFrame）
            await avCanvasRef.current.previewFrame(time * 1e6);

            // 更新当前镜头索引
            let acc = 0;
            for (let i = 0; i < orderedShots.length; i++) {
                acc += orderedShots[i].duration;
                if (time < acc) {
                    setCurrentShotIndex(i);
                    break;
                }
            }

            // 立即更新时间状态
            setCurrentTime(time);

            // 如果之前在播放，继续播放
            if (wasPlaying) {
                // 不使用 play({ start })，直接从当前位置播放
                setTimeout(() => {
                    if (avCanvasRef.current) {
                        // 再次确认位置
                        avCanvasRef.current.previewFrame(time * 1e6).then(() => {
                            if (avCanvasRef.current) {
                                // 从当前位置开始播放（不指定 start）
                                avCanvasRef.current.play();
                                setIsPlaying(true);
                            }
                        });
                    }
                }, 100); // 增加延迟
            } else {
                // 如果不需要播放，立即重置标志
                setTimeout(() => {
                    ignoreNextTimeUpdate.current = false;
                    targetSeekTime.current = null;
                }, 100);
            }

            console.log('[useAVCanvas] Seeked to', time, 'wasPlaying:', wasPlaying);
        } catch (err) {
            console.error('[useAVCanvas] Seek error:', err);
            setError('Failed to seek');
            // 出错时重置标志
            ignoreNextTimeUpdate.current = false;
            targetSeekTime.current = null;
        }
    }, [isReady, isPlaying, orderedShots]);

    // 音量控制
    const handleVolumeChange = useCallback((newVolume: number) => {
        setVolume(newVolume);
        setIsMuted(newVolume === 0);

        // AVCanvas 的音量控制
        // TODO: 需要查看 AVCanvas 是否有音量 API
        console.log('[useAVCanvas] Volume changed to', newVolume);
    }, []);

    // 静音切换
    const toggleMute = useCallback(() => {
        const newMuted = !isMuted;
        setIsMuted(newMuted);

        // TODO: 实现静音功能
        console.log('[useAVCanvas] Muted:', newMuted);
    }, [isMuted]);

    // 预览指定时间的帧（用于拖动进度条）
    const previewFrame = useCallback(async (time: number) => {
        if (!avCanvasRef.current || !isReady) return;

        try {
            await avCanvasRef.current.previewFrame(time * 1e6);

            // 更新当前镜头索引
            let acc = 0;
            for (let i = 0; i < orderedShots.length; i++) {
                acc += orderedShots[i].duration;
                if (time < acc) {
                    setCurrentShotIndex(i);
                    break;
                }
            }
        } catch (err) {
            console.error('[useAVCanvas] Preview frame error:', err);
        }
    }, [isReady, orderedShots]);

    return {
        // 状态
        isReady,
        isPlaying,
        currentTime,
        totalDuration,
        currentShotIndex,
        volume,
        isMuted,
        error,

        // 控制方法
        handlePlayPause,
        handleSeek,
        handleVolumeChange,
        toggleMute,
        previewFrame,

        // 引擎实例（用于高级操作）
        avCanvas: avCanvasRef.current
    };
};
