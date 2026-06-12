/**
 * useCanvasNLEEngine - 使用 Canvas NLE 引擎的 React Hook
 *
 * 这个 Hook 封装了 Canvas 基础的 NLE 引擎
 * 特点：
 * - 使用 Canvas 渲染，实现真正的无缝切换
 * - 利用 requestVideoFrameCallback 提取帧
 * - 双 video 预加载
 * - 完全消除切换闪烁
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { createCanvasNLEEngine, CanvasNLEEngine } from '../engine/webcodecs';
import type { VideoSegment } from '../engine/webcodecs';
import { getFullUrl } from '../utils/url';
import type { Shot, GeneratedVideo } from '../api/types';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

interface UseCanvasNLEEngineProps {
    orderedShots: ShotWithVideo[];
    canvasRef: React.RefObject<HTMLCanvasElement>;
}

export const useCanvasNLEEngine = ({ orderedShots, canvasRef }: UseCanvasNLEEngineProps) => {
    // NLE 引擎实例
    const engineRef = useRef<CanvasNLEEngine | null>(null);

    // 播放状态
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [totalDuration, setTotalDuration] = useState(0);
    const [currentSegmentIndex, setCurrentSegmentIndex] = useState(0);
    const [volume, setVolumeState] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isReady, setIsReady] = useState(false);

    // 转换 Shot 数据为 VideoSegment
    const convertShotsToSegments = useCallback((shots: ShotWithVideo[]): VideoSegment[] => {
        let accTime = 0;
        return shots.map((shot, index) => {
            const segment: VideoSegment = {
                id: `shot-${shot.sequence ?? index}`,
                url: shot.videoData?.videoPath || '',
                startTime: accTime,
                duration: shot.duration || 5
            };
            accTime += shot.duration || 5;
            return segment;
        });
    }, []);

    // 初始化引擎
    useEffect(() => {
        if (!canvasRef.current) {
            console.error('[useCanvasNLEEngine] Canvas ref is null');
            return;
        }

        if (orderedShots.length === 0) {
            console.warn('[useCanvasNLEEngine] No shots to load');
            return;
        }

        // 创建引擎
        const engine = createCanvasNLEEngine({
            canvas: canvasRef.current,
            urlHelper: getFullUrl
        });

        // 转换数据并加载时间轴
        const segments = convertShotsToSegments(orderedShots);

        engine.loadTimeline(segments)
            .then(() => {
                console.log('[useCanvasNLEEngine] Timeline loaded successfully');

                // 更新状态
                const state = engine.getState();
                setTotalDuration(state.duration);
                setCurrentTime(state.currentTime);
                setCurrentSegmentIndex(state.currentSegmentIndex);
                setError(null);
                setIsReady(true);

                // 注册事件监听器
                engine.on('ready', () => {
                    setIsReady(true);
                });

                engine.on('play', () => {
                    setIsPlaying(true);
                });

                engine.on('pause', () => {
                    setIsPlaying(false);
                });

                engine.on('timeupdate', (event) => {
                    setCurrentTime(event.data.time);
                });

                engine.on('segmentchange', (event) => {
                    setCurrentSegmentIndex(event.data.index);
                });

                engine.on('ended', () => {
                    setIsPlaying(false);
                });

                engine.on('error', (event) => {
                    setError(event.data?.message || 'Playback error');
                });

                engineRef.current = engine;
            })
            .catch(err => {
                console.error('[useCanvasNLEEngine] Failed to load timeline:', err);
                setError(err.message);
            });

        // 清理函数
        return () => {
            if (engineRef.current) {
                engineRef.current.dispose();
                engineRef.current = null;
            }
        };
    }, [orderedShots, canvasRef, convertShotsToSegments]);

    // 播放/暂停
    const handlePlayPause = useCallback(async () => {
        if (!engineRef.current) {
            console.warn('[useCanvasNLEEngine] Engine not ready');
            return;
        }

        try {
            await engineRef.current.togglePlayPause();
        } catch (err) {
            console.error('[useCanvasNLEEngine] Play/Pause failed:', err);
            setError('Failed to play/pause');
        }
    }, []);

    // 跳转
    const handleSeek = useCallback(async (_event: unknown, value: number | number[]) => {
        if (!engineRef.current) return;

        const seekTime = value as number;

        try {
            await engineRef.current.seek(seekTime);
            setCurrentTime(seekTime);
        } catch (err) {
            console.error('[useCanvasNLEEngine] Seek failed:', err);
            setError('Failed to seek');
        }
    }, []);

    // 音量控制
    const handleVolumeChange = useCallback((_: Event, value: number | number[]) => {
        if (!engineRef.current) return;

        const newVolume = value as number;
        engineRef.current.setVolume(newVolume);
        setVolumeState(newVolume);
        setIsMuted(newVolume === 0);
    }, []);

    // 静音切换
    const toggleMute = useCallback(() => {
        if (!engineRef.current) return;

        const newMuted = !isMuted;
        engineRef.current.setMuted(newMuted);
        setIsMuted(newMuted);
    }, [isMuted]);

    return {
        // 播放状态
        isReady,
        isPlaying,
        currentTime,
        totalDuration,
        currentSegmentIndex,

        // 音频状态
        volume,
        isMuted,

        // 错误状态
        error,

        // 控制方法
        handlePlayPause,
        handleSeek,
        handleVolumeChange,
        toggleMute,

        // 引擎实例（用于高级操作）
        engine: engineRef.current
    };
};
