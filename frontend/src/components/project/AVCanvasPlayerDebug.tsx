/**
 * 简化版 AVCanvasPlayer - 用于调试
 * 暂时使用原生 video 元素替代 AVCanvas
 */

import React, { useRef, useState, useEffect } from 'react';
import { Box, Typography, IconButton, Slider, Stack, Chip, alpha, useTheme } from '@mui/material';
import { PlayArrow as PlayIcon, Pause as PauseIcon, VolumeUp as VolumeIcon, VolumeOff as MuteIcon } from '@mui/icons-material';
import type { Shot, GeneratedVideo } from '../../api/types';
import { getFullUrl } from '../../utils/url';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

interface AVCanvasPlayerProps {
    orderedShots: ShotWithVideo[];
    onTimeUpdate?: (time: number) => void;
    onShotChange?: (index: number) => void;
    onPlayStateChange?: (isPlaying: boolean) => void;
    externalSeekTime?: number | null;
}

const formatTime = (seconds: number): string => {
    return `${seconds.toFixed(2)}s`;
};

export const AVCanvasPlayerDebug: React.FC<AVCanvasPlayerProps> = ({
    orderedShots,
    onTimeUpdate,
    onShotChange,
    onPlayStateChange,
    externalSeekTime
}) => {
    const theme = useTheme();
    const videoRef = useRef<HTMLVideoElement>(null);

    const [currentShotIndex, setCurrentShotIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [totalDuration, setTotalDuration] = useState(0);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);

    // 计算总时长
    useEffect(() => {
        const total = orderedShots.reduce((sum, shot) => sum + shot.duration, 0);
        setTotalDuration(total);
    }, [orderedShots]);

    // 当前镜头
    const currentShot = orderedShots[currentShotIndex];
    const videoPath = currentShot?.videoData?.videoPath || currentShot?.videoPath;

    // 视频时间更新
    const handleTimeUpdate = () => {
        if (!videoRef.current) return;

        const localTime = videoRef.current.currentTime;

        // 计算全局时间
        const offsetTime = orderedShots.slice(0, currentShotIndex).reduce((sum, s) => sum + s.duration, 0);
        const globalTime = offsetTime + localTime;

        setCurrentTime(globalTime);
        onTimeUpdate?.(globalTime);

        // 检查是否需要切换到下一个镜头
        if (localTime >= currentShot.duration && currentShotIndex < orderedShots.length - 1) {
            setCurrentShotIndex(currentShotIndex + 1);
        }
    };

    // 播放/暂停
    const handlePlayPause = () => {
        if (!videoRef.current) return;

        if (isPlaying) {
            videoRef.current.pause();
            setIsPlaying(false);
        } else {
            videoRef.current.play();
            setIsPlaying(true);
        }
    };

    // 音量控制
    const handleVolumeChange = (value: number) => {
        setVolume(value);
        if (videoRef.current) {
            videoRef.current.volume = value;
        }
    };

    const toggleMute = () => {
        setIsMuted(!isMuted);
        if (videoRef.current) {
            videoRef.current.muted = !isMuted;
        }
    };

    // 通知父组件
    useEffect(() => {
        onShotChange?.(currentShotIndex);
    }, [currentShotIndex, onShotChange]);

    useEffect(() => {
        onPlayStateChange?.(isPlaying);
    }, [isPlaying, onPlayStateChange]);

    // 外部seek
    useEffect(() => {
        if (externalSeekTime === null || externalSeekTime === undefined) return;

        // 找到对应的镜头
        let acc = 0;
        let targetShotIndex = 0;
        let localTime = 0;

        for (let i = 0; i < orderedShots.length; i++) {
            if (externalSeekTime < acc + orderedShots[i].duration) {
                targetShotIndex = i;
                localTime = externalSeekTime - acc;
                break;
            }
            acc += orderedShots[i].duration;
        }

        setCurrentShotIndex(targetShotIndex);

        setTimeout(() => {
            if (videoRef.current) {
                videoRef.current.currentTime = localTime;
            }
        }, 100);
    }, [externalSeekTime, orderedShots]);

    return (
        <Box sx={{
            flex: 1,
            bgcolor: '#050505',
            display: 'flex',
            flexDirection: 'column',
            position: 'relative'
        }}>
            {/* 视频容器 */}
            <Box sx={{
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
                overflow: 'hidden',
                bgcolor: '#000'
            }}>
                {videoPath ? (
                    <video
                        ref={videoRef}
                        src={getFullUrl(videoPath)}
                        onTimeUpdate={handleTimeUpdate}
                        onEnded={() => {
                            if (currentShotIndex < orderedShots.length - 1) {
                                setCurrentShotIndex(currentShotIndex + 1);
                            } else {
                                setIsPlaying(false);
                            }
                        }}
                        style={{
                            maxWidth: '100%',
                            maxHeight: '100%',
                            objectFit: 'contain'
                        }}
                    />
                ) : (
                    <Typography color="white">No video available</Typography>
                )}

                {/* 镜头信息 */}
                <Chip
                    label={`镜头 ${currentShotIndex + 1} / ${orderedShots.length}`}
                    size="small"
                    sx={{
                        position: 'absolute',
                        top: 16,
                        left: 16,
                        bgcolor: alpha(theme.palette.background.paper, 0.8),
                        backdropFilter: 'blur(10px)',
                        fontWeight: 600,
                        zIndex: 10
                    }}
                />

                {/* 调试标识 */}
                <Chip
                    label="DEBUG MODE"
                    size="small"
                    color="warning"
                    sx={{
                        position: 'absolute',
                        top: 16,
                        right: 16,
                        bgcolor: alpha(theme.palette.warning.main, 0.8),
                        backdropFilter: 'blur(10px)',
                        fontWeight: 600,
                        zIndex: 10
                    }}
                />
            </Box>

            {/* 控制栏 */}
            <Box sx={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                bgcolor: alpha('#000', 0.8),
                backdropFilter: 'blur(10px)',
                px: 3,
                py: 1.5,
                zIndex: 100
            }}>
                <Stack direction="row" alignItems="center" spacing={2}>
                    {/* 播放/暂停 */}
                    <IconButton
                        onClick={handlePlayPause}
                        sx={{
                            bgcolor: alpha('#FF4081', 0.1),
                            '&:hover': { bgcolor: alpha('#FF4081', 0.2) }
                        }}
                    >
                        {isPlaying ? <PauseIcon /> : <PlayIcon />}
                    </IconButton>

                    {/* 时间显示 */}
                    <Typography
                        variant="body2"
                        sx={{
                            minWidth: 180,
                            color: 'white',
                            fontFamily: 'monospace',
                            fontSize: '0.95rem',
                            fontWeight: 500
                        }}
                    >
                        {formatTime(currentTime)} / {formatTime(totalDuration)}
                    </Typography>

                    <Box sx={{ flex: 1 }} />

                    {/* 音量控制 */}
                    <IconButton onClick={toggleMute} size="small" sx={{ color: 'white' }}>
                        {isMuted ? <MuteIcon /> : <VolumeIcon />}
                    </IconButton>

                    <Slider
                        value={isMuted ? 0 : volume}
                        min={0}
                        max={1}
                        step={0.01}
                        onChange={(_, value) => handleVolumeChange(value as number)}
                        sx={{
                            width: 100,
                            '& .MuiSlider-thumb': {
                                width: 12,
                                height: 12
                            },
                            '& .MuiSlider-track': {
                                height: 3
                            },
                            '& .MuiSlider-rail': {
                                height: 3
                            }
                        }}
                    />
                </Stack>
            </Box>
        </Box>
    );
};
