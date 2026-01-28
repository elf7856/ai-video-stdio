/**
 * AVCanvasPlayer - 基于 AVCanvas 的专业视频播放器
 *
 * Phase 1: 基础播放功能
 * - 多视频连续播放
 * - 播放/暂停控制
 * - 进度条（帧级精确）
 * - 音量控制
 */

import React, { useRef } from 'react';
import { Box, Typography, IconButton, Slider, Stack, Chip, alpha, useTheme, CircularProgress } from '@mui/material';
import { PlayArrow as PlayIcon, Pause as PauseIcon, VolumeUp as VolumeIcon, VolumeOff as MuteIcon } from '@mui/icons-material';
import { useAVCanvas } from '../../hooks/useAVCanvas';
import type { Shot, GeneratedVideo } from '../../api/types';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

interface AVCanvasPlayerProps {
    orderedShots: ShotWithVideo[];
    // Optional callbacks for parent component integration
    onTimeUpdate?: (time: number) => void;
    onShotChange?: (index: number) => void;
    onPlayStateChange?: (isPlaying: boolean) => void;
    // Optional external control
    externalSeekTime?: number | null;
}

const formatTime = (seconds: number): string => {
    return `${seconds.toFixed(2)}s`;
};

export const AVCanvasPlayer: React.FC<AVCanvasPlayerProps> = ({
    orderedShots,
    onTimeUpdate,
    onShotChange,
    onPlayStateChange,
    externalSeekTime
}) => {
    const theme = useTheme();
    const containerRef = useRef<HTMLDivElement>(null);

    // 检查是否有可播放的视频（不包括图片）
    const hasVideos = orderedShots.length > 0 && orderedShots.some(shot =>
        shot.videoPath || (shot as any).videoData?.videoPath
    );

    // 使用 AVCanvas Hook
    const {
        isReady,
        isPlaying,
        currentTime,
        totalDuration,
        currentShotIndex,
        volume,
        isMuted,
        error,
        handlePlayPause,
        handleSeek,
        handleVolumeChange,
        toggleMute
    } = useAVCanvas({ orderedShots, containerRef });

    // Notify parent of time updates
    React.useEffect(() => {
        if (onTimeUpdate) {
            onTimeUpdate(currentTime);
        }
    }, [currentTime, onTimeUpdate]);

    // Notify parent of shot changes
    React.useEffect(() => {
        if (onShotChange) {
            onShotChange(currentShotIndex);
        }
    }, [currentShotIndex, onShotChange]);

    // Notify parent of play state changes
    React.useEffect(() => {
        if (onPlayStateChange) {
            onPlayStateChange(isPlaying);
        }
    }, [isPlaying, onPlayStateChange]);

    // Handle external seek requests
    React.useEffect(() => {
        if (externalSeekTime !== null && externalSeekTime !== undefined) {
            // 外部 seek 应该保持当前播放状态
            handleSeek(externalSeekTime, isPlaying);
        }
    }, [externalSeekTime, handleSeek, isPlaying]);

    // 音量拖动
    const handleVolumeSliderChange = (_: Event, value: number | number[]) => {
        handleVolumeChange(value as number);
    };

    return (
        <Box sx={{
            flex: 1,
            bgcolor: '#050505',
            display: 'flex',
            flexDirection: 'column',
            position: 'relative'
        }}>
            {/* AVCanvas 容器 */}
            <Box
                ref={containerRef}
                sx={{
                    width: '100%',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                    overflow: 'hidden',
                    bgcolor: '#000',
                    '& canvas': {
                        maxWidth: '100%',
                        maxHeight: '100%',
                        objectFit: 'contain'
                    }
                }}
            >
                {/* 正在生成中占位符 */}
                {!hasVideos && (
                    <Box sx={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        textAlign: 'center',
                        zIndex: 10
                    }}>
                        <CircularProgress size={48} sx={{ color: '#6366f1', mb: 2 }} />
                        <Typography variant="h6" sx={{ color: 'white', mb: 1, fontWeight: 600 }}>
                            正在生成视频...
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#888' }}>
                            请在右侧查看生成进度
                        </Typography>
                    </Box>
                )}

                {/* 加载指示器 */}
                {hasVideos && !isReady && !error && (
                    <Box sx={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        textAlign: 'center',
                        zIndex: 10
                    }}>
                        <CircularProgress />
                        <Typography variant="body2" sx={{ mt: 2, color: 'white' }}>
                            Loading AVCanvas Player...
                        </Typography>
                    </Box>
                )}

                {/* 错误提示 */}
                {hasVideos && error && (
                    <Box sx={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        textAlign: 'center',
                        zIndex: 10,
                        maxWidth: '80%'
                    }}>
                        <Typography variant="h6" color="error" sx={{ mb: 2 }}>
                            播放器错误
                        </Typography>
                        <Typography variant="body2" color="error">
                            {error}
                        </Typography>
                    </Box>
                )}

                {/* 镜头信息 */}
                {isReady && (
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
                )}

                {/* AVCanvas 标识 */}
                {isReady && (
                    <Chip
                        label="AVCanvas"
                        size="small"
                        color="success"
                        sx={{
                            position: 'absolute',
                            top: 16,
                            right: 16,
                            bgcolor: alpha(theme.palette.success.main, 0.8),
                            backdropFilter: 'blur(10px)',
                            fontWeight: 600,
                            zIndex: 10
                        }}
                    />
                )}
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
                        disabled={!isReady}
                        sx={{
                            bgcolor: alpha('#FF4081', 0.1),
                            '&:hover': { bgcolor: alpha('#FF4081', 0.2) },
                            '&:disabled': { bgcolor: alpha('#666', 0.1) }
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
                        onChange={handleVolumeSliderChange}
                        disabled={!isReady}
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
