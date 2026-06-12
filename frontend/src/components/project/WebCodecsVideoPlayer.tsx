/**
 * WebCodecsVideoPlayer - 使用完整 WebCodecs 引擎的视频播放器
 *
 * 特点：
 * - 帧级精确 seek
 * - 专业后期编辑能力
 * - 真正的无缝切换
 */

import React, { useRef } from 'react';
import { Box, Typography, IconButton, Slider, Stack, Chip, alpha, useTheme, CircularProgress } from '@mui/material';
import { PlayArrow as PlayIcon, Pause as PauseIcon, VolumeUp as VolumeIcon, VolumeOff as MuteIcon } from '@mui/icons-material';
import { useWebCodecsNLEEngine } from '../../hooks/useWebCodecsNLEEngine';
import type { Shot, GeneratedVideo } from '../../api/types';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

interface WebCodecsVideoPlayerProps {
    orderedShots: ShotWithVideo[];
}

const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export const WebCodecsVideoPlayer: React.FC<WebCodecsVideoPlayerProps> = ({ orderedShots }) => {
    const theme = useTheme();
    const canvasRef = useRef<HTMLCanvasElement>(null);

    // 本地 state 用于拖动时的临时值
    const [localTime, setLocalTime] = React.useState<number | null>(null);

    const {
        isReady,
        isPlaying,
        currentTime,
        totalDuration,
        currentSegmentIndex,
        volume,
        isMuted,
        error,
        handlePlayPause,
        handleSeek,
        handleVolumeChange,
        toggleMute
    } = useWebCodecsNLEEngine({ orderedShots, canvasRef });

    // 防御性编程：确保值有效
    const safeCurrentTime = isNaN(currentTime) || !isFinite(currentTime) ? 0 : currentTime;
    const safeTotalDuration = isNaN(totalDuration) || !isFinite(totalDuration) || totalDuration <= 0 ? 100 : totalDuration;
    const safeVolume = isNaN(volume) || !isFinite(volume) ? 1 : volume;

    // 显示的时间：拖动时用本地值，否则用引擎的值
    const displayTime = localTime !== null ? localTime : safeCurrentTime;

    // 处理进度条变化（拖动中）
    const handleSliderChange = (_event: unknown, value: number | number[]) => {
        setLocalTime(value as number);
    };

    // 处理进度条松开（跳转）
    const handleSliderChangeCommitted = async (_event: Event | React.SyntheticEvent, value: number | number[]) => {
        const seekTime = value as number;
        setLocalTime(seekTime); // 立即更新显示
        await handleSeek(_event, value);
        setLocalTime(null); // seek 完成后清除
    };

    return (
        <Box sx={{
            flex: 1,
            bgcolor: '#050505',
            display: 'flex',
            flexDirection: 'column',
            position: 'relative'
        }}>
            {/* Canvas 容器 */}
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
                {/* Canvas 元素 */}
                <canvas
                    ref={canvasRef}
                    style={{
                        maxWidth: '100%',
                        maxHeight: '100%',
                        objectFit: 'contain',
                        backgroundColor: '#000'
                    }}
                />

                {/* 加载指示器 */}
                {!isReady && !error && (
                    <Box sx={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        textAlign: 'center',
                        zIndex: 10
                    }}>
                        <CircularProgress />
                        <Typography variant="body2" sx={{ mt: 2 }}>
                            Loading WebCodecs Engine...
                        </Typography>
                    </Box>
                )}

                {/* 错误提示 */}
                {error && (
                    <Box sx={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        textAlign: 'center',
                        zIndex: 10,
                        maxWidth: '80%'
                    }}>
                        <Typography variant="h6" color="error" gutterBottom>
                            {error}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Please use Chrome 94+, Edge 94+, or Safari 17+
                        </Typography>
                    </Box>
                )}

                {/* 镜头信息 */}
                <Chip
                    label={`镜头 ${currentSegmentIndex + 1} / ${orderedShots.length}`}
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

                {/* WebCodecs 标识 */}
                <Chip
                    label="WebCodecs Engine"
                    size="small"
                    color="success"
                    sx={{
                        position: 'absolute',
                        top: 16,
                        right: 16,
                        bgcolor: alpha(theme.palette.success.main, 0.9),
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
                bgcolor: alpha('#000', 0.7),
                backdropFilter: 'blur(10px)',
                p: 2,
                zIndex: 100
            }}>
                {/* 进度条 */}
                <Slider
                    value={displayTime}
                    min={0}
                    max={safeTotalDuration}
                    onChange={handleSliderChange}
                    onChangeCommitted={handleSliderChangeCommitted}
                    disabled={!isReady}
                    sx={{
                        mb: 1,
                        '& .MuiSlider-thumb': {
                            width: 16,
                            height: 16,
                            '&:hover, &.Mui-focusVisible': {
                                boxShadow: '0 0 0 8px rgba(76, 175, 80, 0.16)'
                            }
                        },
                        '& .MuiSlider-track': {
                            height: 4,
                            bgcolor: '#4CAF50'
                        },
                        '& .MuiSlider-rail': {
                            height: 4,
                            bgcolor: alpha('#fff', 0.2)
                        }
                    }}
                />

                {/* 控制按钮 */}
                <Stack direction="row" alignItems="center" spacing={2}>
                    {/* 播放/暂停 */}
                    <IconButton
                        onClick={handlePlayPause}
                        disabled={!isReady}
                        sx={{
                            bgcolor: alpha('#4CAF50', 0.1),
                            '&:hover': { bgcolor: alpha('#4CAF50', 0.2) }
                        }}
                    >
                        {isPlaying ? <PauseIcon /> : <PlayIcon />}
                    </IconButton>

                    {/* 时间显示 */}
                    <Typography variant="body2" sx={{ minWidth: 100 }}>
                        {formatTime(displayTime)} / {formatTime(safeTotalDuration)}
                    </Typography>

                    <Box sx={{ flex: 1 }} />

                    {/* 音量控制 */}
                    <IconButton onClick={toggleMute} size="small">
                        {isMuted ? <MuteIcon /> : <VolumeIcon />}
                    </IconButton>

                    <Slider
                        value={safeVolume}
                        min={0}
                        max={1}
                        step={0.01}
                        onChange={handleVolumeChange}
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
