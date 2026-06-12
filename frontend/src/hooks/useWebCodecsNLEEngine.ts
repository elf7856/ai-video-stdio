/**
 * useWebCodecsNLEEngine - 使用完整 WebCodecs NLE 引擎的 React Hook
 *
 * 特点：
 * - 帧级精确 seek
 * - 真正的无缝切换
 * - 专业后期编辑能力
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { createWebCodecsNLEEngine, WebCodecsNLEEngine } from '../engine/webcodecs-full';
import type { VideoSegment } from '../engine/webcodecs/types';
import { getFullUrl } from '../utils/url';
import type { Shot, GeneratedVideo } from '../api/types';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

interface UseWebCodecsNLEEngineProps {
    orderedShots: ShotWithVideo[];
    canvasRef: React.RefObject<HTMLCanvasElement>;
}

export const useWebCodecsNLEEngine = ({ orderedShots, canvasRef }: UseWebCodecsNLEEngineProps) => {
    // NLE 引擎实例
    const engineRef = useRef<WebCodecsNLEEngine | null>(null);

    // 播放状态
    const [isReady, setIsReady] = useState(false);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [totalDuration, setTotalDuration] = useState(0);
    const [currentSegmentIndex, setCurrentSegmentIndex] = useState(0);
    const [volume, setVolumeState] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [error, setError] = useState<string | null>(null);

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
            console.error('[useWebCodecsNLEEngine] Canvas ref is null');
            return;
        }

        if (orderedShots.length === 0) {
            console.warn('[useWebCodecsNLEEngine] No shots to load');
            return;
        }

        // 检查 WebCodecs 支持
        if (typeof VideoDecoder === 'undefined') {
            setError('WebCodecs is not supported in this browser. Please use Chrome 94+, Edge 94+, or Safari 17+');
            return;
        }

        // 创建引擎
        const engine = createWebCodecsNLEEngine({
            canvas: canvasRef.current,
            urlHelper: getFullUrl
        });

        // 转换数据并加载时间轴
        const segments = convertShotsToSegments(orderedShots);

        engine.loadTimeline(segments)
            .then(() => {
                console.log('[useWebCodecsNLEEngine] Timeline loaded successfully');

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
                console.error('[useWebCodecsNLEEngine] Failed to load timeline:', err);
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
            console.warn('[useWebCodecsNLEEngine] Engine not ready');
            return;
        }

        try {
            await engineRef.current.togglePlayPause();
        } catch (err) {
            console.error('[useWebCodecsNLEEngine] Play/Pause failed:', err);
            setError('Failed to play/pause');
        }
    }, []);

    // 跳转
    const handleSeek = useCallback(async (_event: unknown, value: number | number[]) => {
        if (!engineRef.current) return;

        const seekTime = value as number;

        try {
            await engineRef.current.seek(seekTime);
        } catch (err) {
            console.error('[useWebCodecsNLEEngine] Seek failed:', err);
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
