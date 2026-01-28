import React from 'react';
import { Box, Typography, IconButton, Slider, Stack, Chip, CircularProgress, alpha, useTheme } from '@mui/material';
import { PlayArrow as PlayIcon, Pause as PauseIcon, MusicNote as MusicIcon } from '@mui/icons-material';
import type { Shot, GeneratedVideo } from '../../api/types';
import { getFullUrl } from '../../utils/url';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

interface VideoPlayerProps {
    videoRef: React.RefObject<HTMLVideoElement>;
    currentShot: ShotWithVideo | undefined;
    currentShotIndex: number;
    totalShots: number;
    isPlaying: boolean;
    globalTime: number;
    totalDuration: number;
    volume: number;
    isMuted: boolean;
    error: string | null;
    onTimeUpdate: () => void;
    onPlay: () => void;
    onPause: () => void;
    onPlayPause: () => void;
    onSeek: (_: Event, value: number | number[]) => void;
    onVolumeChange: (_: Event, value: number | number[]) => void;
    onToggleMute: () => void;
}

const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
    videoRef,
    currentShot,
    currentShotIndex,
    totalShots,
    isPlaying,
    globalTime,
    totalDuration,
    volume,
    isMuted,
    error,
    onTimeUpdate,
    onPlay,
    onPause,
    onPlayPause,
    onSeek,
    onVolumeChange,
    onToggleMute,
}) => {
    const theme = useTheme();

    // 本地状态用于拖动时的临时显示
    const [localTime, setLocalTime] = React.useState<number | null>(null);

    // 显示的时间：拖动时用本地值，否则用全局值
    const displayTime = localTime !== null ? localTime : globalTime;

    return (
        <Box sx={{
            flex: 1,
            bgcolor: '#050505',
            display: 'flex',
            flexDirection: 'column',
            position: 'relative'
        }}>
            {/* Video Player - 100% Size */}
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
                {currentShot?.videoData?.videoPath ? (
                    <video
                        ref={videoRef}
                        src={getFullUrl(currentShot.videoData.videoPath)}
                        style={{
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover',
                            backgroundColor: '#000'
                        }}
                        onTimeUpdate={onTimeUpdate}
                        onPlay={onPlay}
                        onPause={onPause}
                    />
                ) : (
                    <Box sx={{ textAlign: 'center' }}>
                        <CircularProgress sx={{ mb: 2 }} />
                        <Typography variant="h6" color="text.secondary">
                            镜头 #{currentShotIndex + 1}
                        </Typography>
                        <Typography color="text.secondary">
                            {error || '等待视频生成'}
                        </Typography>
                    </Box>
                )}

                {/* Current Shot Info Overlay */}
                <Box sx={{
                    position: 'absolute',
                    top: 16,
                    left: 16,
                    display: 'flex',
                    gap: 1
                }}>
                    <Chip
                        label={`镜头 ${currentShotIndex + 1}/${totalShots}`}
                        size="small"
                        sx={{ bgcolor: alpha(theme.palette.background.paper, 0.9) }}
                    />
                    {currentShot?.shotType && (
                        <Chip
                            label={currentShot.shotType}
                            size="small"
                            sx={{ bgcolor: alpha(theme.palette.primary.main, 0.9) }}
                        />
                    )}
                </Box>

                {/* Player Controls Overlay */}
                <Box sx={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    right: 0,
                    bgcolor: 'rgba(0,0,0,0.7)',
                    backdropFilter: 'blur(10px)',
                    p: 2
                }}>
                    {/* Progress Bar */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                        <Typography variant="caption" sx={{ minWidth: 40, color: 'white' }}>
                            {formatTime(displayTime)}
                        </Typography>
                        <Slider
                            value={displayTime}
                            max={totalDuration || 100}
                            onChange={(_, value) => setLocalTime(value as number)}
                            onChangeCommitted={(e, value) => {
                                onSeek(e as Event, value);
                                setLocalTime(null);
                            }}
                            sx={{
                                flex: 1,
                                '& .MuiSlider-thumb': {
                                    width: 16,
                                    height: 16
                                },
                                '& .MuiSlider-rail': {
                                    bgcolor: 'rgba(255,255,255,0.3)'
                                }
                            }}
                        />
                        <Typography variant="caption" sx={{ minWidth: 40, color: 'white' }}>
                            {formatTime(totalDuration)}
                        </Typography>
                    </Box>

                    {/* Control Buttons */}
                    <Stack direction="row" justifyContent="center" alignItems="center" spacing={2}>
                        <IconButton
                            onClick={onPlayPause}
                            sx={{
                                bgcolor: 'primary.main',
                                color: 'white',
                                '&:hover': { bgcolor: 'primary.dark' },
                                width: 40,
                                height: 40
                            }}
                        >
                            {isPlaying ? <PauseIcon /> : <PlayIcon />}
                        </IconButton>
                        <Stack direction="row" spacing={1} alignItems="center">
                            <IconButton onClick={onToggleMute} size="small" sx={{ color: 'white' }}>
                                <MusicIcon />
                            </IconButton>
                            <Slider
                                value={isMuted ? 0 : volume}
                                max={1}
                                step={0.1}
                                onChange={onVolumeChange}
                                sx={{ width: 100 }}
                            />
                        </Stack>
                    </Stack>
                </Box>
            </Box>
        </Box>
    );
};
