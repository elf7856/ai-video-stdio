/**
 * useNLEEngine - 使用 NLE 引擎的 React Hook
 *
 * 这个 Hook 封装了 NLE 引擎，使其可以在 React 组件中使用
 * 职责：
 * - 初始化引擎
 * - 同步引擎状态到 React state
 * - 提供播放控制接口
 * - 清理资源
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { createNLEEngine, NLEEngine } from '../engine';
import type { VideoClipData } from '../engine';
import { getFullUrl } from '../utils/url';
import type { Shot, GeneratedVideo } from '../api/types';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

interface UseNLEEngineProps {
    orderedShots: ShotWithVideo[];
}

export const useNLEEngine = ({ orderedShots }: UseNLEEngineProps) => {
    // Video 元素引用
    const primaryVideoRef = useRef<HTMLVideoElement>(null);
    const secondaryVideoRef = useRef<HTMLVideoElement>(null);

    // NLE 引擎实例
    const engineRef = useRef<NLEEngine | null>(null);

    // 播放状态
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [totalDuration, setTotalDuration] = useState(0);
    const [currentClipIndex, setCurrentClipIndex] = useState(0);
    const [volume, setVolumeState] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // 缓冲状态（用于 UI 显示）
    const [usePrimary, setUsePrimary] = useState(true);

    // 转换 Shot 数据为 VideoClipData
    const convertShotsToClips = useCallback((shots: ShotWithVideo[]): VideoClipData[] => {
        let accTime = 0;
        return shots.map((shot, index) => {
            const clip: VideoClipData = {
                id: `shot-${shot.sequence ?? index}`,
                videoPath: shot.videoData?.videoPath || '',
                duration: shot.duration,
                startTime: accTime,
                endTime: accTime + shot.duration
            };
            accTime += shot.duration;
            return clip;
        });
    }, []);

    // 初始化引擎
    useEffect(() => {
        if (!primaryVideoRef.current || !secondaryVideoRef.current) {
            return;
        }

        if (orderedShots.length === 0) {
            return;
        }

        // 创建引擎
        const engine = createNLEEngine({
            primaryVideoElement: primaryVideoRef.current,
            secondaryVideoElement: secondaryVideoRef.current,
            urlHelper: getFullUrl
        });

        // 转换数据并加载时间轴
        const clips = convertShotsToClips(orderedShots);

        engine.loadTimeline(clips)
            .then(() => {
                console.log('[useNLEEngine] Timeline loaded successfully');

                // 更新状态
                const state = engine.getState();
                setTotalDuration(engine.getDuration());
                setCurrentTime(state.currentTime);
                setCurrentClipIndex(state.currentClipIndex);
                setError(null);

                // 注册事件监听器
                engine.on('play', () => {
                    setIsPlaying(true);
                });

                engine.on('pause', () => {
                    setIsPlaying(false);
                });

                engine.on('timeupdate', (event) => {
                    setCurrentTime(event.data.time);
                });

                engine.on('clipchange', (event) => {
                    setCurrentClipIndex(event.data.clipIndex);

                    // 更新缓冲状态以触发 UI 更新
                    const bufferState = engine.getBufferState();
                    setUsePrimary(bufferState.activePrimary);
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
                console.error('[useNLEEngine] Failed to load timeline:', err);
                setError(err.message);
            });

        // 清理函数
        return () => {
            if (engineRef.current) {
                engineRef.current.dispose();
                engineRef.current = null;
            }
        };
    }, [orderedShots, convertShotsToClips]);

    // 播放/暂停
    const handlePlayPause = useCallback(async () => {
        if (!engineRef.current) return;

        try {
            await engineRef.current.togglePlayPause();
        } catch (err) {
            console.error('[useNLEEngine] Play/Pause failed:', err);
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
            console.error('[useNLEEngine] Seek failed:', err);
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
        // Video 元素引用
        primaryVideoRef,
        secondaryVideoRef,

        // 缓冲状态
        usePrimary,

        // 播放状态
        isPlaying,
        currentTime,
        totalDuration,
        currentClipIndex,

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
