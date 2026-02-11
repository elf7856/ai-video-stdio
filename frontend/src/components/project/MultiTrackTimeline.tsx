import React, { useState, useRef, useEffect } from 'react';
import { Box, Paper, Typography, IconButton, Slider, Stack } from '@mui/material';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import type { Shot, GeneratedVideo } from '../../api/types';
import { getFullUrl } from '../../utils/url';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

interface MultiTrackTimelineProps {
    orderedShots: ShotWithVideo[];
    currentShotIndex: number;
    globalTime: number;
    totalDuration: number;
    onSeek: (time: number, shouldResume?: boolean) => void;
    isPlaying: boolean;
    onShotDurationChange?: (index: number, newDuration: number) => void;
}

const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 10);
    return `${mins}:${secs.toString().padStart(2, '0')}.${ms}`;
};

export const MultiTrackTimeline: React.FC<MultiTrackTimelineProps> = ({
    orderedShots,
    currentShotIndex,
    globalTime,
    totalDuration,
    onSeek,
    isPlaying,
    onShotDurationChange,
}) => {
    const [pxPerSec, setPxPerSec] = useState(50);
    const [isDragging, setIsDragging] = useState(false);
    const timelineRef = useRef<HTMLDivElement>(null);
    const playheadRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to keep playhead visible during playback
    useEffect(() => {
        if (isPlaying && timelineRef.current && playheadRef.current) {
            const container = timelineRef.current;
            const playheadPos = 80 + globalTime * pxPerSec; // 加上左侧标签宽度
            const scrollLeft = container.scrollLeft;
            const containerWidth = container.clientWidth;

            // Keep playhead in center third of viewport
            if (playheadPos < scrollLeft + containerWidth * 0.33 ||
                playheadPos > scrollLeft + containerWidth * 0.66) {
                container.scrollTo({
                    left: playheadPos - containerWidth / 2,
                    behavior: 'smooth'
                });
            }
        }
    }, [globalTime, isPlaying, pxPerSec]);

    const handlePlayheadDrag = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);

        const wasPlaying = isPlaying;
        let lastSeekTime = Date.now();
        let pendingTime: number | null = null;

        const handleMouseMove = (moveEvent: MouseEvent) => {
            if (!timelineRef.current) return;

            const rect = timelineRef.current.getBoundingClientRect();
            const moveX = moveEvent.clientX - rect.left + timelineRef.current.scrollLeft - 80; // 减去左侧标签宽度
            const newTime = Math.max(0, Math.min(totalDuration, moveX / pxPerSec));

            // Throttle: 只在距离上次 seek 超过 50ms 时才调用
            const now = Date.now();
            if (now - lastSeekTime >= 50) {
                onSeek(newTime, false);
                lastSeekTime = now;
                pendingTime = null;
            } else {
                // 保存待处理的时间，在 mouseup 时执行
                pendingTime = newTime;
            }
        };

        const handleMouseUp = () => {
            setIsDragging(false);
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);

            // 如果有待处理的时间，先跳转到那个位置
            if (pendingTime !== null) {
                onSeek(pendingTime, wasPlaying);
            } else if (wasPlaying) {
                // Resume playback if it was playing before drag
                onSeek(globalTime, true);
            }
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    };

    const timelineWidth = Math.max(80 + totalDuration * pxPerSec, 1000);

    return (
        <Paper sx={{
            height: 320,
            bgcolor: '#0a0a0a',
            borderTop: '1px solid #222',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
        }} square>
            {/* Toolbar */}
            <Box sx={{
                height: 48,
                borderBottom: '1px solid #222',
                display: 'flex',
                alignItems: 'center',
                px: 2,
                justifyContent: 'space-between',
                bgcolor: '#1a1a1a'
            }}>
                <Stack direction="row" spacing={2} alignItems="center">
                    <Typography variant="body2" color="text.secondary" sx={{ minWidth: 60 }}>
                        缩放
                    </Typography>
                    <IconButton
                        size="small"
                        onClick={() => setPxPerSec(Math.max(20, pxPerSec - 10))}
                        sx={{ color: '#888' }}
                    >
                        <ZoomOutIcon fontSize="small" />
                    </IconButton>
                    <Slider
                        value={pxPerSec}
                        min={20}
                        max={200}
                        onChange={(_, v) => setPxPerSec(v as number)}
                        sx={{
                            width: 120,
                            '& .MuiSlider-thumb': { color: '#FF4081' },
                            '& .MuiSlider-track': { color: '#FF4081' },
                            '& .MuiSlider-rail': { color: '#444' }
                        }}
                        size="small"
                    />
                    <IconButton
                        size="small"
                        onClick={() => setPxPerSec(Math.min(200, pxPerSec + 10))}
                        sx={{ color: '#888' }}
                    >
                        <ZoomInIcon fontSize="small" />
                    </IconButton>
                    <Typography variant="caption" color="text.secondary">
                        {pxPerSec}px/s
                    </Typography>
                </Stack>
                <Stack direction="row" spacing={2} alignItems="center">
                    <Typography variant="caption" color="text.secondary">
                        {formatTime(globalTime)} / {formatTime(totalDuration)}
                    </Typography>
                </Stack>
            </Box>

            {/* Timeline Area */}
            <Box
                ref={timelineRef}
                sx={{
                    flex: 1,
                    overflowX: 'auto',
                    overflowY: 'auto',
                    position: 'relative',
                    bgcolor: '#0f0f0f',
                    cursor: isDragging ? 'grabbing' : 'default',
                    '&::-webkit-scrollbar': {
                        height: 12,
                        width: 12
                    },
                    '&::-webkit-scrollbar-track': {
                        bgcolor: '#0a0a0a'
                    },
                    '&::-webkit-scrollbar-thumb': {
                        bgcolor: '#333',
                        borderRadius: 6,
                        '&:hover': { bgcolor: '#444' }
                    }
                }}
            >
                <Box sx={{
                    width: timelineWidth,
                    minHeight: '100%',
                    position: 'relative'
                }}>
                    {/* Time Ruler */}
                    <Box sx={{
                        height: 32,
                        borderBottom: '1px solid #333',
                        position: 'sticky',
                        top: 0,
                        bgcolor: '#1a1a1a',
                        zIndex: 100,
                        display: 'flex'
                    }}>
                        {/* 左侧空白区域，对齐轨道标签 */}
                        <Box sx={{
                            width: 80,
                            height: '100%',
                            borderRight: '1px solid #333',
                            bgcolor: '#1a1a1a',
                            flexShrink: 0
                        }} />

                        {/* 时间刻度 */}
                        {Array.from({ length: Math.ceil(totalDuration) + 1 }).map((_, sec) => (
                            <Box key={sec} sx={{
                                width: pxPerSec,
                                height: '100%',
                                borderLeft: sec % 5 === 0 ? '2px solid #444' : '1px solid #2a2a2a',
                                position: 'relative',
                                flexShrink: 0
                            }}>
                                {sec % 5 === 0 && (
                                    <Typography variant="caption" sx={{
                                        position: 'absolute',
                                        left: 4,
                                        top: 2,
                                        fontSize: '0.65rem',
                                        color: '#888',
                                        fontWeight: 500
                                    }}>
                                        {formatTime(sec)}
                                    </Typography>
                                )}
                            </Box>
                        ))}
                    </Box>

                    {/* Video Track */}
                    <Box sx={{
                        height: 100,
                        borderBottom: '1px solid #222',
                        position: 'relative',
                        bgcolor: '#121212'
                    }}>
                        {/* Track Label */}
                        <Box sx={{
                            position: 'sticky',
                            left: 0,
                            top: 0,
                            width: 80,
                            height: '100%',
                            bgcolor: '#1a1a1a',
                            borderRight: '1px solid #333',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            zIndex: 50
                        }}>
                            <Typography variant="caption" color="text.secondary" fontWeight={600}>
                                视频
                            </Typography>
                        </Box>

                        {/* Video Clips */}
                        {orderedShots.filter(shot => shot.duration > 0).map((shot, index, filteredShots) => {
                            const startOffset = filteredShots.slice(0, index).reduce((acc, s) => acc + s.duration, 0);
                            const originalIndex = orderedShots.indexOf(shot);
                            const isSelected = currentShotIndex === originalIndex;

                            return (
                                <VideoClip
                                    key={originalIndex}
                                    shot={shot}
                                    index={originalIndex}
                                    startOffset={startOffset}
                                    pxPerSec={pxPerSec}
                                    isSelected={isSelected}
                                    onShotDurationChange={onShotDurationChange}
                                />
                            );
                        })}
                    </Box>

                    {/* Audio Track */}
                    <Box sx={{
                        height: 80,
                        borderBottom: '1px solid #222',
                        position: 'relative',
                        bgcolor: '#0d0d0d'
                    }}>
                        {/* Track Label */}
                        <Box sx={{
                            position: 'sticky',
                            left: 0,
                            top: 0,
                            width: 80,
                            height: '100%',
                            bgcolor: '#1a1a1a',
                            borderRight: '1px solid #333',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            zIndex: 50
                        }}>
                            <Typography variant="caption" color="text.secondary" fontWeight={600}>
                                音频
                            </Typography>
                        </Box>

                        {/* Audio Clips */}
                        {orderedShots.filter(shot => shot.duration > 0).map((shot, index, filteredShots) => {
                            const startOffset = filteredShots.slice(0, index).reduce((acc, s) => acc + s.duration, 0);
                            const originalIndex = orderedShots.indexOf(shot);

                            return (
                                <AudioClip
                                    key={originalIndex}
                                    shot={shot}
                                    startOffset={startOffset}
                                    pxPerSec={pxPerSec}
                                />
                            );
                        })}
                    </Box>

                    {/* Playhead */}
                    <Box
                        ref={playheadRef}
                        sx={{
                            position: 'absolute',
                            left: 80 + globalTime * pxPerSec,
                            top: 32,
                            bottom: 0,
                            width: 2,
                            bgcolor: '#FF4081',
                            zIndex: 200,
                            cursor: 'ew-resize',
                            transition: isDragging ? 'none' : 'left 0.05s linear',
                            boxShadow: '0 0 10px rgba(255, 64, 129, 0.6)',
                            pointerEvents: 'auto',
                            '&::before': {
                                content: '""',
                                position: 'absolute',
                                top: -32,
                                left: -6,
                                width: 0,
                                height: 0,
                                borderLeft: '6px solid transparent',
                                borderRight: '6px solid transparent',
                                borderTop: '8px solid #FF4081'
                            },
                            '&:hover': {
                                width: 3,
                                boxShadow: '0 0 15px rgba(255, 64, 129, 0.8)'
                            }
                        }}
                        onMouseDown={handlePlayheadDrag}
                    />
                </Box>
            </Box>
        </Paper>
    );
};

// Video Clip Component
interface VideoClipProps {
    shot: ShotWithVideo;
    index: number;
    startOffset: number;
    pxPerSec: number;
    isSelected: boolean;
    onShotDurationChange?: (index: number, newDuration: number) => void;
}

const VideoClip: React.FC<VideoClipProps> = ({
    shot,
    index,
    startOffset,
    pxPerSec,
    isSelected,
    onShotDurationChange
}) => {
    const [thumbnails, setThumbnails] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);
    const generationInProgressRef = useRef(false);

    useEffect(() => {
        if (!shot.videoData?.videoPath) {
            setLoading(false);
            return;
        }

        // 防止重复生成
        if (generationInProgressRef.current) {
            return;
        }

        const generateThumbnails = async () => {
            generationInProgressRef.current = true;
            setLoading(true);

            try {
                const video = document.createElement('video');
                video.src = getFullUrl(shot.videoData!.videoPath);
                video.crossOrigin = 'anonymous';
                video.muted = true;

                await new Promise((resolve, reject) => {
                    video.onloadedmetadata = resolve;
                    video.onerror = reject;
                    setTimeout(() => reject(new Error('Timeout')), 5000);
                });

                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                if (!ctx) throw new Error('Canvas context failed');

                const thumbHeight = 80;
                const thumbWidth = (video.videoWidth / video.videoHeight) * thumbHeight;
                canvas.width = thumbWidth;
                canvas.height = thumbHeight;

                // 固定生成8张缩略图，不随缩放级别变化
                const thumbCount = 8;
                const interval = shot.duration / thumbCount;

                const frames: string[] = [];
                for (let i = 0; i < thumbCount; i++) {
                    video.currentTime = i * interval;
                    await new Promise(r => {
                        video.onseeked = r;
                        setTimeout(r, 200);
                    });
                    ctx.drawImage(video, 0, 0, thumbWidth, thumbHeight);
                    frames.push(canvas.toDataURL('image/jpeg', 0.7));
                }

                setThumbnails(frames);
                setLoading(false);
            } catch (err) {
                console.error('Thumbnail generation failed:', err);
                setLoading(false);
            } finally {
                generationInProgressRef.current = false;
            }
        };

        generateThumbnails();
    }, [shot.videoData?.videoPath]);

    return (
        <Box
            sx={{
                position: 'absolute',
                left: 80 + startOffset * pxPerSec,
                top: 0,
                width: shot.duration * pxPerSec,
                height: '100%',
                bgcolor: isSelected ? '#252525' : '#1a1a1a',
                border: isSelected ? '2px solid #FF4081' : '1px solid #333',
                borderRadius: 0.5,
                overflow: 'hidden',
                transition: 'all 0.15s',
                '&:hover': {
                    bgcolor: '#252525',
                    borderColor: '#555'
                }
            }}
        >
            {/* Thumbnails */}
            {loading ? (
                <Box sx={{
                    width: '100%',
                    height: '100%',
                    bgcolor: '#0a0a0a',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <Typography variant="caption" color="#555">
                        加载中...
                    </Typography>
                </Box>
            ) : thumbnails.length > 0 ? (
                <Box sx={{
                    width: '100%',
                    height: '100%',
                    display: 'flex',
                    bgcolor: '#000'
                }}>
                    {thumbnails.map((src, i) => (
                        <img
                            key={i}
                            src={src}
                            style={{
                                height: '100%',
                                flex: 1,
                                objectFit: 'cover',
                                borderRight: i < thumbnails.length - 1 ? '1px solid rgba(255,255,255,0.1)' : 'none',
                                pointerEvents: 'none'
                            }}
                            alt=""
                        />
                    ))}
                </Box>
            ) : (
                <Box sx={{
                    width: '100%',
                    height: '100%',
                    bgcolor: '#0a0a0a',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}>
                    <Typography variant="caption" color="#555">
                        无预览
                    </Typography>
                </Box>
            )}

            {/* Clip Info Overlay */}
            <Box sx={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                bgcolor: 'rgba(0,0,0,0.7)',
                backdropFilter: 'blur(4px)',
                px: 1,
                py: 0.5,
                borderTop: '1px solid rgba(255,255,255,0.1)'
            }}>
                <Typography variant="caption" color="white" fontWeight={500} noWrap>
                    Shot {index + 1} • {Number(shot.duration).toFixed(2)}s
                </Typography>
            </Box>

            {/* Resize Handle */}
            {onShotDurationChange && (
                <Box
                    sx={{
                        position: 'absolute',
                        right: 0,
                        top: 0,
                        bottom: 0,
                        width: 8,
                        cursor: 'ew-resize',
                        bgcolor: isSelected ? 'rgba(255,64,129,0.3)' : 'transparent',
                        '&:hover': { bgcolor: 'rgba(255,64,129,0.6)' },
                        zIndex: 10,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'background-color 0.2s'
                    }}
                    onMouseDown={(e) => {
                        e.stopPropagation();
                        e.preventDefault();

                        const startX = e.clientX;
                        const startDuration = shot.duration;

                        // Get actual video duration
                        const videoElement = document.createElement('video');
                        videoElement.src = getFullUrl(shot.videoData?.videoPath || '');

                        let maxDuration = startDuration * 2; // Default max

                        videoElement.addEventListener('loadedmetadata', () => {
                            maxDuration = videoElement.duration;
                        });

                        videoElement.load();

                        const handleMouseMove = (moveEvent: MouseEvent) => {
                            const deltaX = moveEvent.clientX - startX;
                            const deltaDuration = deltaX / pxPerSec;
                            const newDuration = Math.max(0.5, Math.min(maxDuration, startDuration + deltaDuration));

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
                    <Box sx={{ width: 2, height: 16, bgcolor: 'white', borderRadius: 1, opacity: 0.8 }} />
                </Box>
            )}
        </Box>
    );
};

// Audio Clip Component
interface AudioClipProps {
    shot: ShotWithVideo;
    startOffset: number;
    pxPerSec: number;
}

const AudioClip: React.FC<AudioClipProps> = ({
    shot,
    startOffset,
    pxPerSec
}) => {
    const [waveformData, setWaveformData] = useState<number[]>([]);
    const [loading, setLoading] = useState(true);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const generationInProgressRef = useRef(false);

    useEffect(() => {
        if (!shot.videoData?.videoPath) {
            setLoading(false);
            return;
        }

        // 防止重复生成
        if (generationInProgressRef.current) {
            return;
        }

        const generateWaveform = async () => {
            generationInProgressRef.current = true;
            setLoading(true);

            try {
                const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
                const response = await fetch(getFullUrl(shot.videoData!.videoPath), {
                    mode: 'cors',
                    cache: 'no-cache',
                    credentials: 'omit'
                });
                const arrayBuffer = await response.arrayBuffer();
                const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

                const rawData = audioBuffer.getChannelData(0);
                // 固定生成200个采样点，不随缩放级别变化
                const samples = 200;
                const blockSize = Math.floor(rawData.length / samples);
                const filteredData: number[] = [];

                for (let i = 0; i < samples; i++) {
                    let sum = 0;
                    for (let j = 0; j < blockSize; j++) {
                        sum += Math.abs(rawData[i * blockSize + j]);
                    }
                    filteredData.push(sum / blockSize);
                }

                // Normalize
                const max = Math.max(...filteredData);
                const normalized = filteredData.map(v => (v / max));

                setWaveformData(normalized);
                setLoading(false);
            } catch (err) {
                console.error('Waveform generation failed:', err);
                setLoading(false);
            } finally {
                generationInProgressRef.current = false;
            }
        };

        generateWaveform();
    }, [shot.videoData?.videoPath]);

    // Draw waveform on canvas
    useEffect(() => {
        if (!canvasRef.current || waveformData.length === 0) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const width = canvas.width;
        const height = canvas.height;
        const centerY = height / 2;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Draw center line
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0, centerY);
        ctx.lineTo(width, centerY);
        ctx.stroke();

        // Draw waveform
        ctx.fillStyle = '#4CAF50';
        const barWidth = width / waveformData.length;

        waveformData.forEach((amplitude, i) => {
            const x = i * barWidth;
            const barHeight = amplitude * (height / 2) * 0.9; // 90% of half height

            // Draw bar from center upward and downward
            ctx.fillRect(x, centerY - barHeight, Math.max(barWidth - 1, 1), barHeight * 2);
        });
    }, [waveformData]);

    return (
        <Box
            sx={{
                position: 'absolute',
                left: 80 + startOffset * pxPerSec,
                top: 0,
                width: shot.duration * pxPerSec,
                height: '100%',
                bgcolor: '#0a0a0a',
                border: '1px solid #222',
                borderRadius: 0.5,
                overflow: 'hidden',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }}
        >
            {loading ? (
                <Typography variant="caption" color="#444">
                    加载中...
                </Typography>
            ) : waveformData.length > 0 ? (
                <canvas
                    ref={canvasRef}
                    width={shot.duration * pxPerSec}
                    height={80}
                    style={{
                        width: '100%',
                        height: '100%',
                        display: 'block'
                    }}
                />
            ) : (
                <Typography variant="caption" color="#444">
                    无音频
                </Typography>
            )}
        </Box>
    );
};
