import React, { useState } from 'react';
import { Box, Paper, Typography, IconButton, Slider, Stack, Tooltip } from '@mui/material';
import type { Shot, GeneratedVideo } from '../../api/types';
import TimelineFilmstrip from '../studio/TimelineFilmstrip';
import { getFullUrl } from '../../utils/url';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

interface TimelineProps {
    timelineRef: React.RefObject<HTMLDivElement>;
    orderedShots: ShotWithVideo[];
    currentShotIndex: number;
    globalTime: number;
    totalDuration: number;
    pxPerSec: number;
    setPxPerSec: (value: number) => void;
    onSeek: (_: Event, value: number | number[]) => void;
    onShotDurationChange?: (index: number, newDuration: number) => void;
}

const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export const Timeline: React.FC<TimelineProps> = ({
    timelineRef,
    orderedShots,
    currentShotIndex,
    globalTime,
    totalDuration,
    pxPerSec,
    setPxPerSec,
    onSeek,
    onShotDurationChange,
}) => {
    const [isDraggingTimeline, setIsDraggingTimeline] = useState(false);

    return (
        <Paper sx={{
            height: 280,
            bgcolor: '#111',
            borderTop: '1px solid #222',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
        }} square>
            {/* Timeline Toolbar */}
            <Box sx={{
                height: 40,
                borderBottom: '1px solid #222',
                display: 'flex',
                alignItems: 'center',
                px: 2,
                justifyContent: 'space-between',
                bgcolor: '#1e1e1e'
            }}>
                <Stack direction="row" spacing={2} alignItems="center">
                    <Stack direction="row" spacing={1} alignItems="center">
                        <IconButton size="small" onClick={() => setPxPerSec(Math.max(10, pxPerSec - 10))}>
                            <Typography fontSize="small">-</Typography>
                        </IconButton>
                        <Slider
                            value={pxPerSec}
                            min={10}
                            max={200}
                            onChange={(_, v) => setPxPerSec(v as number)}
                            sx={{ width: 100 }}
                            size="small"
                        />
                        <IconButton size="small" onClick={() => setPxPerSec(Math.min(200, pxPerSec + 10))}>
                            <Typography fontSize="small">+</Typography>
                        </IconButton>
                    </Stack>
                </Stack>
                <Typography variant="caption" color="text.secondary">
                    Total: {formatTime(totalDuration)}
                </Typography>
            </Box>

            {/* Timeline Tracks Area */}
            <Box
                ref={timelineRef}
                sx={{
                    flex: 1,
                    overflowX: 'auto',
                    overflowY: 'hidden',
                    position: 'relative',
                    bgcolor: '#121212',
                    '&::-webkit-scrollbar': { height: 10 },
                    '&::-webkit-scrollbar-thumb': { bgcolor: '#444', borderRadius: 5 }
                }}
                onClick={(e) => {
                    // Click on timeline to seek
                    if (timelineRef.current && !isDraggingTimeline) {
                        const rect = timelineRef.current.getBoundingClientRect();
                        const clickX = e.clientX - rect.left + timelineRef.current.scrollLeft;
                        const clickTime = (clickX - 16) / pxPerSec;
                        if (clickTime >= 0 && clickTime <= totalDuration) {
                            onSeek({} as any, clickTime);
                        }
                    }
                }}
            >
                {/* Ruler */}
                <Box sx={{
                    height: 24,
                    borderBottom: '1px solid #333',
                    position: 'sticky',
                    top: 0,
                    bgcolor: '#121212',
                    zIndex: 10,
                    display: 'flex'
                }}>
                    {Array.from({ length: Math.ceil(totalDuration) + 5 }).map((_, sec) => (
                        <Box key={sec} sx={{
                            width: pxPerSec,
                            height: '100%',
                            borderLeft: '1px solid #333',
                            position: 'relative',
                            flexShrink: 0
                        }}>
                            <Typography variant="caption" color="#666" sx={{
                                position: 'absolute',
                                left: 2,
                                top: 0,
                                fontSize: '0.6rem'
                            }}>
                                {formatTime(sec)}
                            </Typography>
                        </Box>
                    ))}
                </Box>

                {/* Track with Shots */}
                <Box sx={{
                    p: 2,
                    minWidth: totalDuration * pxPerSec + 200,
                    display: 'flex',
                    position: 'relative'
                }}>
                    {/* Global Playhead - Draggable */}
                    <Box
                        sx={{
                            position: 'absolute',
                            left: 16 + (globalTime * pxPerSec),
                            top: 0,
                            bottom: 0,
                            width: 2,
                            bgcolor: '#FF4081',
                            zIndex: 20,
                            cursor: 'ew-resize',
                            transition: isDraggingTimeline ? 'none' : 'left 0.1s linear',
                            boxShadow: '0 0 8px rgba(255, 64, 129, 0.8)',
                            '&:hover': {
                                width: 4
                            }
                        }}
                        onMouseDown={(e) => {
                            e.preventDefault();
                            setIsDraggingTimeline(true);

                            const handleMouseMove = (moveEvent: MouseEvent) => {
                                if (timelineRef.current) {
                                    const rect = timelineRef.current.getBoundingClientRect();
                                    const moveX = moveEvent.clientX - rect.left + timelineRef.current.scrollLeft;
                                    const newTime = Math.max(0, Math.min(totalDuration, (moveX - 16) / pxPerSec));
                                    onSeek({} as any, newTime);
                                }
                            };

                            const handleMouseUp = () => {
                                setIsDraggingTimeline(false);
                                document.removeEventListener('mousemove', handleMouseMove);
                                document.removeEventListener('mouseup', handleMouseUp);
                            };

                            document.addEventListener('mousemove', handleMouseMove);
                            document.addEventListener('mouseup', handleMouseUp);
                        }}
                    />

                    {/* Shot Clips */}
                    {orderedShots.map((shot, index) => {
                        const startOffset = orderedShots.slice(0, index).reduce((acc, s) => acc + s.duration, 0);
                        const isSelected = currentShotIndex === index;

                        return (
                            <Box
                                key={index}
                                sx={{
                                    position: 'absolute',
                                    left: 16 + startOffset * pxPerSec,
                                    width: shot.duration * pxPerSec,
                                    height: 120,
                                    bgcolor: isSelected ? '#2a2a2a' : '#1a1a1a',
                                    border: isSelected ? '2px solid #FF4081' : '1px solid #333',
                                    borderRadius: 1,
                                    overflow: 'hidden',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s',
                                    '&:hover': {
                                        bgcolor: '#2a2a2a',
                                        borderColor: '#FF4081'
                                    }
                                }}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onSeek({} as any, startOffset);
                                }}
                            >
                                {/* Filmstrip Preview */}
                                {shot.videoData?.videoPath && (
                                    <Box sx={{ width: '100%', height: 80, overflow: 'hidden' }}>
                                        <TimelineFilmstrip
                                            videoUrl={getFullUrl(shot.videoData.videoPath)}
                                            duration={shot.duration}
                                            height={80}
                                            pxPerSec={pxPerSec}
                                        />
                                    </Box>
                                )}

                                {/* Shot Info */}
                                <Box sx={{ p: 0.5, bgcolor: 'rgba(0,0,0,0.5)' }}>
                                    <Typography variant="caption" color="white" noWrap>
                                        Shot {index + 1} • {shot.duration.toFixed(1)}s
                                    </Typography>
                                </Box>

                                {/* Resize Handle - Drag to change duration */}
                                {onShotDurationChange && (
                                    <Tooltip title="拖动调整时长">
                                        <Box
                                            sx={{
                                                position: 'absolute',
                                                right: 0,
                                                top: 0,
                                                bottom: 0,
                                                width: 10,
                                                cursor: 'ew-resize',
                                                bgcolor: isSelected ? 'rgba(255,64,129,0.3)' : 'rgba(255,255,255,0.1)',
                                                '&:hover': { bgcolor: '#FF4081' },
                                                zIndex: 10,
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center'
                                            }}
                                            onMouseDown={(e) => {
                                                e.stopPropagation();
                                                e.preventDefault();

                                                const startX = e.clientX;
                                                const startDuration = shot.duration;

                                                // Get actual video duration from the video element
                                                const videoElement = document.createElement('video');
                                                videoElement.src = getFullUrl(shot.videoData?.videoPath || '');

                                                let maxDuration = startDuration; // Default to current duration

                                                // Try to get actual video duration
                                                videoElement.addEventListener('loadedmetadata', () => {
                                                    maxDuration = videoElement.duration;
                                                    console.log(`[Resize] Shot ${index + 1} max duration: ${maxDuration}s`);
                                                });

                                                // Load the video metadata
                                                videoElement.load();

                                                const handleMouseMove = (moveEvent: MouseEvent) => {
                                                    const deltaX = moveEvent.clientX - startX;
                                                    const deltaDuration = deltaX / pxPerSec;
                                                    const newDuration = Math.max(1, Math.min(maxDuration, startDuration + deltaDuration));

                                                    // Update shot duration in real-time
                                                    onShotDurationChange(index, newDuration);
                                                };

                                                const handleMouseUp = () => {
                                                    document.removeEventListener('mousemove', handleMouseMove);
                                                    document.removeEventListener('mouseup', handleMouseUp);
                                                };

                                                document.addEventListener('mousemove', handleMouseMove);
                                                document.addEventListener('mouseup', handleMouseUp);
                                            }}
                                        >
                                            <Box sx={{ width: 2, height: 12, bgcolor: 'white', borderRadius: 1 }} />
                                        </Box>
                                    </Tooltip>
                                )}
                            </Box>
                        );
                    })}
                </Box>
            </Box>
        </Paper>
    );
};
