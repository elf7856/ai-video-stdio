import { useState, useEffect, useRef } from 'react';
import type { Shot, GeneratedVideo } from '../api/types';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

interface UseVideoPlaybackProps {
    orderedShots: ShotWithVideo[];
}

export const useVideoPlayback = ({ orderedShots }: UseVideoPlaybackProps) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const animationFrameRef = useRef<number | null>(null);
    const wasPlayingRef = useRef<boolean>(false);
    const orderedShotsRef = useRef<ShotWithVideo[]>([]);
    const currentShotIndexRef = useRef<number>(0);

    const [currentShotIndex, setCurrentShotIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [globalTime, setGlobalTime] = useState(0);
    const [totalDuration, setTotalDuration] = useState(0);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);

    // Sync refs with state
    useEffect(() => {
        orderedShotsRef.current = orderedShots;
    }, [orderedShots]);

    useEffect(() => {
        currentShotIndexRef.current = currentShotIndex;
    }, [currentShotIndex]);

    // Recalculate total duration when shots change
    useEffect(() => {
        const total = orderedShots.reduce((sum, s) => sum + s.duration, 0);
        setTotalDuration(total);
    }, [orderedShots]);

    // Smooth progress update using requestAnimationFrame
    useEffect(() => {
        if (!isPlaying) return;

        const updateProgress = () => {
            if (videoRef.current && orderedShotsRef.current.length > 0) {
                const shotLocalTime = videoRef.current.currentTime;
                const prevDuration = orderedShotsRef.current
                    .slice(0, currentShotIndexRef.current)
                    .reduce((acc, s) => acc + s.duration, 0);
                const newGlobalTime = prevDuration + shotLocalTime;
                setGlobalTime(newGlobalTime);
            }
            animationFrameRef.current = requestAnimationFrame(updateProgress);
        };

        animationFrameRef.current = requestAnimationFrame(updateProgress);

        return () => {
            if (animationFrameRef.current) {
                cancelAnimationFrame(animationFrameRef.current);
            }
        };
    }, [isPlaying]);

    // Handle shot switching - auto-play if was playing
    useEffect(() => {
        if (!videoRef.current) return;

        const video = videoRef.current;

        const handleLoadedMetadata = () => {
            video.currentTime = 0;

            // Auto-play if was playing before shot switch
            if (wasPlayingRef.current) {
                video.play().then(() => {
                    setIsPlaying(true);
                }).catch(err => {
                    console.error('Auto-play failed:', err);
                    setIsPlaying(false);
                    wasPlayingRef.current = false;
                });
            }
        };

        video.addEventListener('loadedmetadata', handleLoadedMetadata);

        return () => {
            video.removeEventListener('loadedmetadata', handleLoadedMetadata);
        };
    }, [currentShotIndex]);

    // Playback handlers
    const handlePlayPause = () => {
        if (videoRef.current) {
            if (isPlaying) {
                videoRef.current.pause();
                wasPlayingRef.current = false;
            } else {
                videoRef.current.play();
                wasPlayingRef.current = true;
            }
            setIsPlaying(!isPlaying);
        }
    };

    const handleTimeUpdate = () => {
        if (videoRef.current && orderedShots.length > 0) {
            const shotLocalTime = videoRef.current.currentTime;
            const currentShot = orderedShots[currentShotIndex];

            // Check if we need to switch to next shot
            if (currentShot && shotLocalTime >= currentShot.duration - 0.05) {
                if (currentShotIndex < orderedShots.length - 1) {
                    wasPlayingRef.current = isPlaying;
                    setCurrentShotIndex(prev => prev + 1);
                } else {
                    setIsPlaying(false);
                    wasPlayingRef.current = false;
                }
            }
        }
    };

    const handleSeek = (_: Event, value: number | number[]) => {
        const seekTime = value as number;
        setGlobalTime(seekTime);

        let acc = 0;
        for (let i = 0; i < orderedShots.length; i++) {
            const shot = orderedShots[i];
            if (seekTime >= acc && seekTime <= acc + shot.duration + 0.01) {
                const localTime = seekTime - acc;

                if (currentShotIndex !== i) {
                    // Switching to a different shot - store the target time
                    // The video will seek after the shot source changes
                    setCurrentShotIndex(i);
                    // Use setTimeout to update currentTime after React state update
                    setTimeout(() => {
                        if (videoRef.current) {
                            videoRef.current.currentTime = localTime;
                        }
                    }, 50);
                } else {
                    // Same shot - directly update currentTime
                    if (videoRef.current) {
                        videoRef.current.currentTime = localTime;
                    }
                }
                return;
            }
            acc += shot.duration;
        }
    };

    const handleVolumeChange = (_: Event, value: number | number[]) => {
        const newVolume = value as number;
        setVolume(newVolume);
        if (videoRef.current) {
            videoRef.current.volume = newVolume;
        }
        setIsMuted(newVolume === 0);
    };

    const toggleMute = () => {
        if (videoRef.current) {
            videoRef.current.muted = !isMuted;
            setIsMuted(!isMuted);
        }
    };

    return {
        videoRef,
        currentShotIndex,
        setCurrentShotIndex,
        isPlaying,
        setIsPlaying,
        globalTime,
        setGlobalTime,
        totalDuration,
        volume,
        isMuted,
        handlePlayPause,
        handleTimeUpdate,
        handleSeek,
        handleVolumeChange,
        toggleMute,
    };
};
