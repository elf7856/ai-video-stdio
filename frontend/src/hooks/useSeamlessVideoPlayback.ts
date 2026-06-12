import { useState, useEffect, useRef, useCallback } from 'react';
import type { Shot, GeneratedVideo } from '../api/types';
import { getFullUrl } from '../utils/url';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

interface UseSeamlessVideoPlaybackProps {
    orderedShots: ShotWithVideo[];
}

/**
 * 无缝视频播放 Hook - 使用双缓冲技术实现流畅的镜头切换
 *
 * 技术原理：
 * 1. 双缓冲：维护两个 video 元素（primary 和 secondary）
 * 2. 预加载：播放当前镜头时，预加载下一个镜头
 * 3. 无缝切换：切换时直接显示已加载的 video，无需等待
 */
export const useSeamlessVideoPlayback = ({ orderedShots }: UseSeamlessVideoPlaybackProps) => {
    // 双缓冲：两个 video 元素
    const primaryVideoRef = useRef<HTMLVideoElement>(null);
    const secondaryVideoRef = useRef<HTMLVideoElement>(null);

    // 当前使用哪个 video 元素（true = primary, false = secondary）
    const [usePrimary, setUsePrimary] = useState(true);

    // 当前活跃的 video ref
    const activeVideoRef = usePrimary ? primaryVideoRef : secondaryVideoRef;
    const animationFrameRef = useRef<number | null>(null);
    const orderedShotsRef = useRef<ShotWithVideo[]>([]);
    const currentShotIndexRef = useRef<number>(0);
    const lastUpdateTimeRef = useRef<number>(0);
    const isPreloadingRef = useRef<boolean>(false);
    const isPlayingRef = useRef<boolean>(false); // 添加 ref 来跟踪播放状态
    const usePrimaryRef = useRef<boolean>(true); // 添加 ref 来跟踪使用哪个 video
    const isSwitchingRef = useRef<boolean>(false); // 防止重复切换

    const [currentShotIndex, setCurrentShotIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [globalTime, setGlobalTime] = useState(0);
    const [totalDuration, setTotalDuration] = useState(0);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Sync refs
    useEffect(() => {
        orderedShotsRef.current = orderedShots;
    }, [orderedShots]);

    useEffect(() => {
        currentShotIndexRef.current = currentShotIndex;
    }, [currentShotIndex]);

    // 同步 isPlaying 到 ref
    useEffect(() => {
        isPlayingRef.current = isPlaying;
    }, [isPlaying]);

    // 同步 usePrimary 到 ref
    useEffect(() => {
        usePrimaryRef.current = usePrimary;
    }, [usePrimary]);

    // Calculate total duration
    useEffect(() => {
        const total = orderedShots.reduce((sum, s) => sum + s.duration, 0);
        setTotalDuration(total);
    }, [orderedShots]);

    // 预加载下一个镜头
    const preloadNextShot = useCallback((nextIndex: number) => {
        if (nextIndex >= orderedShots.length || isPreloadingRef.current) return;

        const nextShot = orderedShots[nextIndex];
        if (!nextShot?.videoData?.videoPath) return;

        isPreloadingRef.current = true;
        // 获取当前非活跃的 video 元素
        const currentInactiveVideo = usePrimary ? secondaryVideoRef.current : primaryVideoRef.current;

        if (currentInactiveVideo) {
            const videoUrl = getFullUrl(nextShot.videoData.videoPath);

            currentInactiveVideo.src = videoUrl;
            currentInactiveVideo.currentTime = 0;
            currentInactiveVideo.volume = volume;
            currentInactiveVideo.muted = isMuted;
            currentInactiveVideo.crossOrigin = "anonymous";

            // 预加载但不播放
            currentInactiveVideo.load();

            currentInactiveVideo.addEventListener('loadeddata', () => {
                isPreloadingRef.current = false;
            }, { once: true });

            currentInactiveVideo.addEventListener('error', (e) => {
                console.error(`Failed to preload shot ${nextIndex + 1}:`, e);
                isPreloadingRef.current = false;
            }, { once: true });
        }
    }, [orderedShots, volume, isMuted, usePrimary]);

    // 加载并播放指定镜头
    const loadAndPlayShot = useCallback((shotIndex: number, autoPlay: boolean = false) => {
        if (shotIndex < 0 || shotIndex >= orderedShots.length) return;

        const shot = orderedShots[shotIndex];
        if (!shot?.videoData?.videoPath) {
            setError(`Shot ${shotIndex + 1} has no video`);
            return;
        }

        // 获取当前活跃的 video 元素
        const currentActiveVideo = usePrimary ? primaryVideoRef.current : secondaryVideoRef.current;
        if (!currentActiveVideo) return;

        const videoUrl = getFullUrl(shot.videoData.videoPath);

        currentActiveVideo.src = videoUrl;
        currentActiveVideo.currentTime = 0;
        currentActiveVideo.volume = volume;
        currentActiveVideo.muted = isMuted;
        currentActiveVideo.crossOrigin = "anonymous";

        const handleLoadedData = () => {
            setError(null);
            if (autoPlay) {
                currentActiveVideo.play().then(() => {
                    setIsPlaying(true);
                    isPlayingRef.current = true;
                }).catch(err => {
                    console.error('Auto-play failed:', err);
                    setIsPlaying(false);
                    isPlayingRef.current = false;
                });
            }

            // 预加载下一个镜头
            if (shotIndex + 1 < orderedShots.length) {
                setTimeout(() => {
                    preloadNextShot(shotIndex + 1);
                }, 100);
            }
        };

        const handleError = (e: Event) => {
            console.error(`Failed to load shot ${shotIndex + 1}:`, e);
            setError(`Failed to load shot ${shotIndex + 1}`);
            setIsPlaying(false);
            isPlayingRef.current = false;
        };

        currentActiveVideo.addEventListener('loadeddata', handleLoadedData, { once: true });
        currentActiveVideo.addEventListener('error', handleError, { once: true });

        currentActiveVideo.load();
    }, [orderedShots, volume, isMuted, usePrimary, preloadNextShot]);

    // 无缝切换到下一个镜头
    const switchToNextShot = useCallback(() => {
        // 防止重复调用
        if (isSwitchingRef.current) {
            console.log('[DEBUG] Already switching, skipping');
            return;
        }

        const nextIndex = currentShotIndexRef.current + 1;
        const currentUsePrimary = usePrimaryRef.current;

        console.log('[DEBUG switchToNextShot] Called with currentIndex:', currentShotIndexRef.current, 'nextIndex:', nextIndex, 'usePrimary:', currentUsePrimary);

        if (nextIndex >= orderedShotsRef.current.length) {
            // 播放完毕
            setIsPlaying(false);
            isPlayingRef.current = false;
            const currentActiveVideo = currentUsePrimary ? primaryVideoRef.current : secondaryVideoRef.current;
            if (currentActiveVideo) {
                currentActiveVideo.pause();
            }
            return;
        }

        isSwitchingRef.current = true;

        // 检查下一个镜头是否已预加载
        const currentActiveVideo = currentUsePrimary ? primaryVideoRef.current : secondaryVideoRef.current;
        const currentInactiveVideo = currentUsePrimary ? secondaryVideoRef.current : primaryVideoRef.current;
        const nextShot = orderedShotsRef.current[nextIndex];

        if (currentInactiveVideo && nextShot?.videoData?.videoPath) {
            const actualUrl = currentInactiveVideo.src;

            // 如果已预加载正确的视频
            if (actualUrl.includes(nextShot.videoData.videoPath) && currentInactiveVideo.readyState >= 2) {
                // 暂停当前视频
                if (currentActiveVideo) {
                    console.log('[DEBUG switchToNextShot] Pausing current active video');
                    currentActiveVideo.pause();
                }

                // 重置新视频到开头
                currentInactiveVideo.currentTime = 0;

                // 播放新视频
                currentInactiveVideo.play().then(() => {
                    console.log('[DEBUG] Successfully switched to next shot, video playing');

                    // 同步更新所有状态（ref 和 state）
                    const newUsePrimary = !currentUsePrimary;
                    usePrimaryRef.current = newUsePrimary;
                    currentShotIndexRef.current = nextIndex;
                    isPlayingRef.current = true;

                    // 立即更新所有 state，保持 ref 和 state 同步
                    setUsePrimary(newUsePrimary);
                    setCurrentShotIndex(nextIndex);
                    setIsPlaying(true);

                    console.log('[DEBUG] All states updated - usePrimary:', newUsePrimary, 'shotIndex:', nextIndex);

                    // 解除切换锁
                    isSwitchingRef.current = false;

                    // 预加载下下个镜头
                    if (nextIndex + 1 < orderedShotsRef.current.length) {
                        setTimeout(() => {
                            preloadNextShot(nextIndex + 1);
                        }, 300);
                    }
                }).catch(err => {
                    console.error('Failed to play preloaded video:', err);
                    setIsPlaying(false);
                    isPlayingRef.current = false;
                    isSwitchingRef.current = false;
                });

                return;
            }
        }

        // 如果没有预加载，回退到传统加载方式
        if (currentActiveVideo) {
            currentActiveVideo.pause();
        }

        setCurrentShotIndex(nextIndex);

        setTimeout(() => {
            loadAndPlayShot(nextIndex, true);
            isSwitchingRef.current = false;
        }, 50);

    }, [preloadNextShot, loadAndPlayShot]); // 只依赖不会频繁变化的函数

    // 初始化：加载第一个镜头
    useEffect(() => {
        if (orderedShots.length > 0 && currentShotIndex === 0) {
            loadAndPlayShot(0, false);
        }

        // 添加事件监听来调试
        const primary = primaryVideoRef.current;
        const secondary = secondaryVideoRef.current;

        const handlePause = (e: Event) => {
            const video = e.target as HTMLVideoElement;
            const isPrimary = video === primary;
            console.log(`[DEBUG] Video ${isPrimary ? 'PRIMARY' : 'SECONDARY'} paused! currentTime:`, video.currentTime);
            console.trace('Pause stack trace');
        };

        const handlePlay = (e: Event) => {
            const video = e.target as HTMLVideoElement;
            const isPrimary = video === primary;
            console.log(`[DEBUG] Video ${isPrimary ? 'PRIMARY' : 'SECONDARY'} playing! currentTime:`, video.currentTime);
        };

        if (primary) {
            primary.addEventListener('pause', handlePause);
            primary.addEventListener('play', handlePlay);
        }
        if (secondary) {
            secondary.addEventListener('pause', handlePause);
            secondary.addEventListener('play', handlePlay);
        }

        return () => {
            if (primary) {
                primary.removeEventListener('pause', handlePause);
                primary.removeEventListener('play', handlePlay);
            }
            if (secondary) {
                secondary.removeEventListener('pause', handlePause);
                secondary.removeEventListener('play', handlePlay);
            }
        };
    }, [orderedShots.length]);

    // 注意：不需要监听 currentShotIndex 变化来重新加载视频
    // 因为 switchToNextShot 已经处理了自动切换的逻辑
    // 手动跳转由 handleSeek 直接处理

    // 进度更新循环 - 使用单一的 useEffect，不依赖频繁变化的状态
    useEffect(() => {
        let frameCount = 0;

        const updateProgress = (timestamp: number) => {
            // 检查是否正在播放
            if (!isPlayingRef.current) {
                animationFrameRef.current = requestAnimationFrame(updateProgress);
                return;
            }

            // 获取当前活跃的 video 元素 - 使用 ref 而不是依赖 state
            const currentActiveVideo = usePrimaryRef.current ? primaryVideoRef.current : secondaryVideoRef.current;

            if (currentActiveVideo && orderedShotsRef.current.length > 0) {
                // 节流：30fps
                if (timestamp - lastUpdateTimeRef.current < 33) {
                    animationFrameRef.current = requestAnimationFrame(updateProgress);
                    return;
                }
                lastUpdateTimeRef.current = timestamp;

                const shotLocalTime = currentActiveVideo.currentTime;
                const currentShot = orderedShotsRef.current[currentShotIndexRef.current];

                // 每30帧打印一次调试信息
                frameCount++;
                if (frameCount % 30 === 0) {
                    console.log('[DEBUG Progress]', {
                        shotIndex: currentShotIndexRef.current,
                        usePrimary: usePrimaryRef.current,
                        isPlaying: isPlayingRef.current,
                        videoPaused: currentActiveVideo.paused,
                        currentTime: shotLocalTime.toFixed(3),
                        duration: currentActiveVideo.duration.toFixed(3)
                    });
                }

                // 计算全局时间
                let prevDuration = 0;
                for (let i = 0; i < currentShotIndexRef.current; i++) {
                    prevDuration += orderedShotsRef.current[i].duration;
                }
                const newGlobalTime = prevDuration + shotLocalTime;
                setGlobalTime(newGlobalTime);

                // 检查是否需要切换镜头
                if (currentShot) {
                    const shotDuration = currentShot.duration;
                    const actualVideoDuration = currentActiveVideo.duration;
                    const effectiveDuration = Math.min(shotDuration, actualVideoDuration);

                    // 提前 0.05 秒切换，减少卡顿感
                    if (!isNaN(effectiveDuration) && shotLocalTime >= effectiveDuration - 0.05) {
                        switchToNextShot();
                    }
                }
            }
            animationFrameRef.current = requestAnimationFrame(updateProgress);
        };

        animationFrameRef.current = requestAnimationFrame(updateProgress);

        return () => {
            if (animationFrameRef.current) {
                cancelAnimationFrame(animationFrameRef.current);
            }
        };
    }, [switchToNextShot]);

    // 播放/暂停
    const handlePlayPause = useCallback(() => {
        const currentActiveVideo = usePrimary ? primaryVideoRef.current : secondaryVideoRef.current;
        if (!currentActiveVideo) return;

        if (isPlaying) {
            currentActiveVideo.pause();
            setIsPlaying(false);
            isPlayingRef.current = false;
        } else {
            currentActiveVideo.play().then(() => {
                setIsPlaying(true);
                isPlayingRef.current = true;
            }).catch(err => {
                console.error('Play failed:', err);
                setError('Failed to play video');
            });
        }
    }, [isPlaying, usePrimary]);

    // 跳转
    const handleSeek = useCallback((_: Event, value: number | number[]) => {
        const seekTime = value as number;

        // 立即更新全局时间，不要等待进度循环
        setGlobalTime(seekTime);

        let acc = 0;
        for (let i = 0; i < orderedShots.length; i++) {
            const shot = orderedShots[i];
            const shotDuration = shot.duration;

            if (seekTime >= acc && seekTime <= acc + shotDuration + 0.01) {
                const localTime = seekTime - acc;

                if (currentShotIndex !== i) {
                    // 切换到不同镜头
                    setCurrentShotIndex(i);
                    setTimeout(() => {
                        const currentActiveVideo = usePrimaryRef.current ? primaryVideoRef.current : secondaryVideoRef.current;
                        if (currentActiveVideo) {
                            currentActiveVideo.currentTime = localTime;
                        }
                    }, 50);
                } else {
                    // 同一镜头内跳转
                    const currentActiveVideo = usePrimaryRef.current ? primaryVideoRef.current : secondaryVideoRef.current;
                    if (currentActiveVideo) {
                        currentActiveVideo.currentTime = localTime;
                    }
                }
                return;
            }
            acc += shotDuration;
        }
    }, [orderedShots, currentShotIndex]);

    // 音量控制
    const handleVolumeChange = useCallback((_: Event, value: number | number[]) => {
        const newVolume = value as number;
        setVolume(newVolume);

        if (primaryVideoRef.current) {
            primaryVideoRef.current.volume = newVolume;
        }
        if (secondaryVideoRef.current) {
            secondaryVideoRef.current.volume = newVolume;
        }

        setIsMuted(newVolume === 0);
    }, []);

    const toggleMute = useCallback(() => {
        const newMuted = !isMuted;
        setIsMuted(newMuted);

        if (primaryVideoRef.current) {
            primaryVideoRef.current.muted = newMuted;
        }
        if (secondaryVideoRef.current) {
            secondaryVideoRef.current.muted = newMuted;
        }
    }, [isMuted]);

    return {
        primaryVideoRef,
        secondaryVideoRef,
        activeVideoRef,
        usePrimary,
        currentShotIndex,
        setCurrentShotIndex,
        isPlaying,
        setIsPlaying,
        globalTime,
        setGlobalTime,
        totalDuration,
        volume,
        isMuted,
        error,
        handlePlayPause,
        handleSeek,
        handleVolumeChange,
        toggleMute,
    };
};
