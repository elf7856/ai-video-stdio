import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
    Box, Paper, Typography, IconButton, Slider, Stack, Tooltip,
    Menu, MenuItem, ListItemIcon, ListItemText
} from '@mui/material';
import ZoomInIcon from '@mui/icons-material/ZoomIn';
import ZoomOutIcon from '@mui/icons-material/ZoomOut';
import AddIcon from '@mui/icons-material/Add';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import LockIcon from '@mui/icons-material/Lock';
import LockOpenIcon from '@mui/icons-material/LockOpen';
import DeleteIcon from '@mui/icons-material/Delete';
import SubtitlesIcon from '@mui/icons-material/Subtitles';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import ColorLensIcon from '@mui/icons-material/ColorLens';
import StickerIcon from '@mui/icons-material/EmojiEmotions';
import MusicNoteIcon from '@mui/icons-material/MusicNote';
import type { Shot, GeneratedVideo } from '../../api/types';
import { getFullUrl } from '../../utils/url';

// ─── Types ──────────────────────────────────────────────────────────────────

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

export type TrackType = 'video' | 'audio' | 'subtitle' | 'effect' | 'filter' | 'sticker';

export interface TrackClip {
    id: string;
    startTime: number;   // seconds
    duration: number;
    label?: string;
    color?: string;
    data?: any;
}

export interface Track {
    id: string;
    type: TrackType;
    label: string;
    height: number;      // px
    visible: boolean;
    locked: boolean;
    color: string;       // accent color
    clips: TrackClip[];
    deletable: boolean;  // video/audio are not deletable
}

const TRACK_CONFIGS: Record<TrackType, { label: string; color: string; minHeight: number }> = {
    video:    { label: '视频',  color: '#6366f1', minHeight: 60  },
    audio:    { label: '音频',  color: '#22c55e', minHeight: 40  },
    subtitle: { label: '字幕',  color: '#f59e0b', minHeight: 36  },
    effect:   { label: '特效',  color: '#ec4899', minHeight: 36  },
    filter:   { label: '滤镜',  color: '#06b6d4', minHeight: 36  },
    sticker:  { label: '贴纸',  color: '#a855f7', minHeight: 36  },
};

const TRACK_ICONS: Record<TrackType, React.ReactNode> = {
    video:    <AutoAwesomeIcon sx={{ fontSize: 12 }} />,
    audio:    <MusicNoteIcon sx={{ fontSize: 12 }} />,
    subtitle: <SubtitlesIcon sx={{ fontSize: 12 }} />,
    effect:   <AutoAwesomeIcon sx={{ fontSize: 12 }} />,
    filter:   <ColorLensIcon sx={{ fontSize: 12 }} />,
    sticker:  <StickerIcon sx={{ fontSize: 12 }} />,
};

const ADDABLE_TRACKS: TrackType[] = ['subtitle', 'effect', 'filter', 'sticker', 'audio'];

const DEFAULT_TRACKS: Track[] = [
    { id: 'video-main', type: 'video', label: '视频', height: 100, visible: true, locked: false, color: '#6366f1', clips: [], deletable: false },
    { id: 'audio-main', type: 'audio', label: '音频', height: 72, visible: true, locked: false, color: '#22c55e', clips: [], deletable: false },
];

const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    const ms = Math.floor((s % 1) * 10);
    return `${m}:${sec.toString().padStart(2, '0')}.${ms}`;
};

// ─── MultiTrackTimeline Props ────────────────────────────────────────────────

interface MultiTrackTimelineProps {
    orderedShots: ShotWithVideo[];
    currentShotIndex: number;
    globalTime: number;
    totalDuration: number;
    onSeek: (time: number, shouldResume?: boolean) => void;
    isPlaying: boolean;
    onShotDurationChange?: (index: number, newDuration: number) => void;
    height?: number;
}

// ─── Track Label (left column) ───────────────────────────────────────────────

interface TrackLabelProps {
    track: Track;
    onToggleVisible: () => void;
    onToggleLock: () => void;
    onDelete: () => void;
}

const TrackLabel: React.FC<TrackLabelProps> = ({ track, onToggleVisible, onToggleLock, onDelete }) => (
    <Box onClick={e => e.stopPropagation()} sx={{
        position: 'sticky', left: 0, top: 0,
        width: 80, height: '100%',
        bgcolor: '#1e1e1e',
        borderRight: '1px solid #333',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        gap: 0.3, zIndex: 50, flexShrink: 0,
        opacity: track.visible ? 1 : 0.4,
    }}>
        <Box sx={{ color: track.color, mb: 0.2 }}>{TRACK_ICONS[track.type]}</Box>
        <Typography variant="caption" color={track.visible ? 'text.secondary' : '#555'} fontWeight={600} sx={{ fontSize: '0.65rem' }}>
            {track.label}
        </Typography>
        <Stack direction="row" spacing={0} sx={{ mt: 0.3 }}>
            <Tooltip title={track.visible ? '隐藏' : '显示'} placement="top">
                <IconButton size="small" onClick={onToggleVisible} sx={{ p: 0.2, color: '#555', '&:hover': { color: '#fff' } }}>
                    {track.visible ? <VisibilityIcon sx={{ fontSize: 11 }} /> : <VisibilityOffIcon sx={{ fontSize: 11 }} />}
                </IconButton>
            </Tooltip>
            <Tooltip title={track.locked ? '解锁' : '锁定'} placement="top">
                <IconButton size="small" onClick={onToggleLock} sx={{ p: 0.2, color: '#555', '&:hover': { color: '#fff' } }}>
                    {track.locked ? <LockIcon sx={{ fontSize: 11 }} /> : <LockOpenIcon sx={{ fontSize: 11 }} />}
                </IconButton>
            </Tooltip>
            {track.deletable && (
                <Tooltip title="删除轨道" placement="top">
                    <IconButton size="small" onClick={onDelete} sx={{ p: 0.2, color: '#555', '&:hover': { color: '#f44336' } }}>
                        <DeleteIcon sx={{ fontSize: 11 }} />
                    </IconButton>
                </Tooltip>
            )}
        </Stack>
    </Box>
);

// ─── Track Resize Handle ─────────────────────────────────────────────────────

interface TrackResizeHandleProps {
    onResize: (delta: number) => void;
    minHeight: number;
    currentHeight: number;
}

const TrackResizeHandle: React.FC<TrackResizeHandleProps> = ({ onResize, minHeight, currentHeight }) => {
    const handleMouseDown = (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        const startY = e.clientY;
        const startH = currentHeight;
        const onMove = (mv: MouseEvent) => {
            const delta = mv.clientY - startY;
            onResize(Math.max(minHeight, startH + delta) - startH);
        };
        const onUp = () => {
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
        };
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    };

    return (
        <Box
            onMouseDown={handleMouseDown}
            sx={{
                position: 'absolute', bottom: 0, left: 0, right: 0,
                height: 4, cursor: 'ns-resize', zIndex: 60,
                bgcolor: 'transparent',
                '&:hover': { bgcolor: 'rgba(255,64,129,0.4)' },
                transition: 'background-color 0.15s',
            }}
        />
    );
};

// ─── Generic Clip (subtitle / effect / filter / sticker) ────────────────────

interface GenericClipProps {
    clip: TrackClip;
    pxPerSec: number;
    trackColor: string;
}

const GenericClip: React.FC<GenericClipProps> = ({ clip, pxPerSec, trackColor }) => (
    <Box sx={{
        position: 'absolute',
        left: 80 + clip.startTime * pxPerSec,
        top: 4, bottom: 4,
        width: clip.duration * pxPerSec,
        bgcolor: `${trackColor}22`,
        border: `1px solid ${trackColor}88`,
        borderRadius: 0.5,
        overflow: 'hidden',
        display: 'flex', alignItems: 'center', px: 0.5,
        cursor: 'pointer',
        '&:hover': { bgcolor: `${trackColor}44` },
    }}>
        <Typography variant="caption" noWrap sx={{ fontSize: '0.65rem', color: trackColor }}>
            {clip.label || clip.id}
        </Typography>
    </Box>
);

// ─── VideoClip ───────────────────────────────────────────────────────────────

interface VideoClipProps {
    shot: ShotWithVideo;
    index: number;
    startOffset: number;
    pxPerSec: number;
    isSelected: boolean;
    onShotDurationChange?: (index: number, newDuration: number) => void;
}

const VideoClip: React.FC<VideoClipProps> = ({ shot, index, startOffset, pxPerSec, isSelected, onShotDurationChange }) => {
    const [thumbnails, setThumbnails] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);
    const [dragDuration, setDragDuration] = useState<number | null>(null);
    const generationInProgressRef = useRef(false);
    const displayDuration = dragDuration ?? shot.duration;

    useEffect(() => {
        if (!shot.videoData?.videoPath) { setLoading(false); return; }
        if (generationInProgressRef.current) return;

        const generate = async () => {
            generationInProgressRef.current = true;
            setLoading(true);
            try {
                const video = document.createElement('video');
                video.src = getFullUrl(shot.videoData!.videoPath);
                video.crossOrigin = 'anonymous';
                video.muted = true;
                await new Promise((res, rej) => {
                    video.onloadedmetadata = res;
                    video.onerror = rej;
                    setTimeout(() => rej(new Error('Timeout')), 5000);
                });
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d')!;
                const h = 80, w = (video.videoWidth / video.videoHeight) * h;
                canvas.width = w; canvas.height = h;
                const frames: string[] = [];
                for (let i = 0; i < 8; i++) {
                    video.currentTime = i * (shot.duration / 8);
                    await new Promise(r => { video.onseeked = r; setTimeout(r, 200); });
                    ctx.drawImage(video, 0, 0, w, h);
                    frames.push(canvas.toDataURL('image/jpeg', 0.7));
                }
                setThumbnails(frames);
            } catch { /* ignore */ } finally {
                setLoading(false);
                generationInProgressRef.current = false;
            }
        };
        generate();
    }, [shot.videoData?.videoPath]);

    return (
        <Box onClick={e => e.stopPropagation()} sx={{
            position: 'absolute',
            left: 80 + startOffset * pxPerSec, top: 0,
            width: displayDuration * pxPerSec, height: '100%',
            bgcolor: isSelected ? '#252525' : '#1a1a1a',
            border: isSelected ? `2px solid #6366f1` : '1px solid #333',
            borderRadius: 0.5, overflow: 'hidden',
            transition: dragDuration !== null ? 'none' : 'border-color 0.15s',
            '&:hover': { borderColor: '#555' },
        }}>
            {/* Thumbnails */}
            {!loading && thumbnails.length > 0 ? (
                <Box sx={{ width: '100%', height: '100%', display: 'flex', bgcolor: '#000' }}>
                    {thumbnails.map((src, i) => (
                        <img key={i} src={src} style={{ height: '100%', flex: 1, objectFit: 'cover' }} alt="" />
                    ))}
                </Box>
            ) : (
                <Box sx={{ width: '100%', height: '100%', bgcolor: '#111', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Typography variant="caption" color="#444">{loading ? '加载中...' : '无预览'}</Typography>
                </Box>
            )}
            {/* Info bar */}
            <Box sx={{ position: 'absolute', bottom: 0, left: 0, right: 0, bgcolor: 'rgba(0,0,0,0.7)', px: 1, py: 0.3 }}>
                <Typography variant="caption" color="white" sx={{ fontSize: '0.6rem' }} noWrap>
                    Shot {shot.sequence} · {Number(displayDuration).toFixed(1)}s
                </Typography>
            </Box>
            {/* Resize handle */}
            {onShotDurationChange && (
                <Box
                    sx={{
                        position: 'absolute', right: 0, top: 0, bottom: 0, width: 8,
                        cursor: 'ew-resize', zIndex: 10,
                        bgcolor: isSelected ? 'rgba(99,102,241,0.3)' : 'transparent',
                        '&:hover': { bgcolor: 'rgba(99,102,241,0.6)' },
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}
                    onMouseDown={(e) => {
                        e.stopPropagation(); e.preventDefault();
                        const startX = e.clientX;
                        const startDuration = shot.duration;
                        const videoEl = document.createElement('video');
                        videoEl.src = getFullUrl(shot.videoData?.videoPath || '');
                        let maxDuration = startDuration * 2;
                        videoEl.addEventListener('loadedmetadata', () => { maxDuration = videoEl.duration; });
                        videoEl.load();
                        let cur = startDuration;
                        const onMove = (mv: MouseEvent) => {
                            cur = Math.max(0.5, Math.min(maxDuration, startDuration + (mv.clientX - startX) / pxPerSec));
                            setDragDuration(cur);
                        };
                        const onUp = () => {
                            document.removeEventListener('mousemove', onMove);
                            document.removeEventListener('mouseup', onUp);
                            setDragDuration(null);
                            onShotDurationChange(index, cur);
                        };
                        document.addEventListener('mousemove', onMove);
                        document.addEventListener('mouseup', onUp);
                    }}
                >
                    <Box sx={{ width: 2, height: 16, bgcolor: 'white', borderRadius: 1, opacity: 0.7 }} />
                </Box>
            )}
        </Box>
    );
};

// ─── AudioClip ───────────────────────────────────────────────────────────────

interface AudioClipProps {
    shot: ShotWithVideo;
    startOffset: number;
    pxPerSec: number;
}

const AudioClip: React.FC<AudioClipProps> = ({ shot, startOffset, pxPerSec }) => {
    const [waveformData, setWaveformData] = useState<number[]>([]);
    const [loading, setLoading] = useState(true);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const generationInProgressRef = useRef(false);

    useEffect(() => {
        if (!shot.videoData?.videoPath) { setLoading(false); return; }
        if (generationInProgressRef.current) return;
        const generate = async () => {
            generationInProgressRef.current = true;
            try {
                const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
                const res = await fetch(getFullUrl(shot.videoData!.videoPath), { mode: 'cors', cache: 'no-cache', credentials: 'omit' });
                const buf = await ctx.decodeAudioData(await res.arrayBuffer());
                const raw = buf.getChannelData(0);
                const samples = 200, blockSize = Math.floor(raw.length / samples);
                const data: number[] = [];
                for (let i = 0; i < samples; i++) {
                    let s = 0;
                    for (let j = 0; j < blockSize; j++) s += Math.abs(raw[i * blockSize + j]);
                    data.push(s / blockSize);
                }
                const max = Math.max(...data);
                setWaveformData(data.map(v => v / max));
            } catch { /* ignore */ } finally {
                setLoading(false);
                generationInProgressRef.current = false;
            }
        };
        generate();
    }, [shot.videoData?.videoPath]);

    useEffect(() => {
        if (!canvasRef.current || waveformData.length === 0) return;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d')!;
        const { width: w, height: h } = canvas;
        const cy = h / 2;
        ctx.clearRect(0, 0, w, h);
        ctx.strokeStyle = '#333'; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(0, cy); ctx.lineTo(w, cy); ctx.stroke();
        ctx.fillStyle = '#22c55e';
        const bw = w / waveformData.length;
        waveformData.forEach((amp, i) => {
            const bh = amp * cy * 0.9;
            ctx.fillRect(i * bw, cy - bh, Math.max(bw - 1, 1), bh * 2);
        });
    }, [waveformData]);

    return (
        <Box onClick={e => e.stopPropagation()} sx={{
            position: 'absolute',
            left: 80 + startOffset * pxPerSec, top: 0,
            width: shot.duration * pxPerSec, height: '100%',
            bgcolor: '#0f1a13', border: '1px solid #1a3520',
            borderRadius: 0.5, overflow: 'hidden',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
            {loading ? (
                <Typography variant="caption" color="#444">加载中...</Typography>
            ) : waveformData.length > 0 ? (
                <canvas ref={canvasRef} width={shot.duration * pxPerSec} height={72}
                    style={{ width: '100%', height: '100%', display: 'block' }} />
            ) : (
                <Typography variant="caption" color="#444">无音频</Typography>
            )}
        </Box>
    );
};

// ─── Main Component ──────────────────────────────────────────────────────────

export const MultiTrackTimeline: React.FC<MultiTrackTimelineProps> = ({
    orderedShots,
    currentShotIndex,
    globalTime,
    totalDuration,
    onSeek,
    isPlaying,
    onShotDurationChange,
    height = 280,
}) => {
    const [pxPerSec, setPxPerSec] = useState(50);
    const [isDragging, setIsDragging] = useState(false);
    const [tracks, setTracks] = useState<Track[]>(DEFAULT_TRACKS);
    const [addMenuAnchor, setAddMenuAnchor] = useState<null | HTMLElement>(null);
    const timelineRef = useRef<HTMLDivElement>(null);
    const playheadRef = useRef<HTMLDivElement>(null);

    // Auto-scroll playhead into view
    useEffect(() => {
        if (isPlaying && timelineRef.current) {
            const container = timelineRef.current;
            const pos = 80 + globalTime * pxPerSec;
            const { scrollLeft, clientWidth } = container;
            if (pos < scrollLeft + clientWidth * 0.33 || pos > scrollLeft + clientWidth * 0.66) {
                container.scrollTo({ left: pos - clientWidth / 2, behavior: 'smooth' });
            }
        }
    }, [globalTime, isPlaying, pxPerSec]);

    const calcTimeFromMouseX = (clientX: number) => {
        if (!timelineRef.current) return null;
        const rect = timelineRef.current.getBoundingClientRect();
        const x = clientX - rect.left + timelineRef.current.scrollLeft - 80;
        if (x < 0) return null;
        return Math.max(0, Math.min(totalDuration, x / pxPerSec));
    };

    const handleTrackAreaClick = (e: React.MouseEvent) => {
        const t = calcTimeFromMouseX(e.clientX);
        if (t !== null) onSeek(t, isPlaying);
    };

    const handlePlayheadDrag = (e: React.MouseEvent) => {
        e.preventDefault(); e.stopPropagation();
        setIsDragging(true);
        const wasPlaying = isPlaying;
        let lastSeek = Date.now(), pendingTime: number | null = null;
        const onMove = (mv: MouseEvent) => {
            const t = calcTimeFromMouseX(mv.clientX);
            if (t === null) return;
            const now = Date.now();
            if (now - lastSeek >= 50) { onSeek(t, false); lastSeek = now; pendingTime = null; }
            else pendingTime = t;
        };
        const onUp = () => {
            setIsDragging(false);
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
            if (pendingTime !== null) onSeek(pendingTime, wasPlaying);
            else if (wasPlaying) onSeek(globalTime, true);
        };
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    };

    const updateTrack = useCallback((id: string, patch: Partial<Track>) => {
        setTracks(prev => prev.map(t => t.id === id ? { ...t, ...patch } : t));
    }, []);

    const deleteTrack = useCallback((id: string) => {
        setTracks(prev => prev.filter(t => t.id !== id));
    }, []);

    const resizeTrack = useCallback((id: string, delta: number) => {
        setTracks(prev => prev.map(t => {
            if (t.id !== id) return t;
            const min = TRACK_CONFIGS[t.type].minHeight;
            return { ...t, height: Math.max(min, t.height + delta) };
        }));
    }, []);

    const addTrack = (type: TrackType) => {
        const cfg = TRACK_CONFIGS[type];
        const newTrack: Track = {
            id: `${type}-${Date.now()}`,
            type, label: cfg.label,
            height: Math.max(cfg.minHeight, 40),
            visible: true, locked: false,
            color: cfg.color, clips: [],
            deletable: true,
        };
        setTracks(prev => [...prev, newTrack]);
        setAddMenuAnchor(null);
    };

    const timelineWidth = Math.max(80 + totalDuration * pxPerSec, 1000);
    return (
        <Paper sx={{ height, bgcolor: '#111', borderTop: 'none', display: 'flex', flexDirection: 'column', overflow: 'hidden' }} square>

            {/* ── Toolbar ── */}
            <Box sx={{ height: 48, borderBottom: '1px solid #333', display: 'flex', alignItems: 'center', px: 2, justifyContent: 'space-between', bgcolor: '#1e1e1e', flexShrink: 0 }}>
                <Stack direction="row" spacing={1} alignItems="center">
                    <Typography variant="body2" color="text.secondary" sx={{ minWidth: 36, fontSize: '0.75rem' }}>缩放</Typography>
                    <IconButton size="small" onClick={() => setPxPerSec(Math.max(20, pxPerSec - 10))} sx={{ color: '#888' }}>
                        <ZoomOutIcon fontSize="small" />
                    </IconButton>
                    <Slider value={pxPerSec} min={20} max={200}
                        onChange={(_, v) => setPxPerSec(v as number)}
                        sx={{ width: 100, '& .MuiSlider-thumb': { color: '#FF4081' }, '& .MuiSlider-track': { color: '#FF4081' }, '& .MuiSlider-rail': { color: '#444' } }}
                        size="small"
                    />
                    <IconButton size="small" onClick={() => setPxPerSec(Math.min(200, pxPerSec + 10))} sx={{ color: '#888' }}>
                        <ZoomInIcon fontSize="small" />
                    </IconButton>
                    <Typography variant="caption" color="text.secondary">{pxPerSec}px/s</Typography>
                </Stack>

                <Stack direction="row" spacing={2} alignItems="center">
                    <Typography variant="caption" color="text.secondary">
                        {formatTime(globalTime)} / {formatTime(totalDuration)}
                    </Typography>
                    <Tooltip title="添加轨道">
                        <IconButton size="small" onClick={e => setAddMenuAnchor(e.currentTarget)}
                            sx={{ color: '#888', bgcolor: '#2a2a2a', '&:hover': { color: '#fff', bgcolor: '#333' } }}>
                            <AddIcon fontSize="small" />
                        </IconButton>
                    </Tooltip>
                </Stack>
            </Box>

            {/* ── Add Track Menu ── */}
            <Menu anchorEl={addMenuAnchor} open={Boolean(addMenuAnchor)} onClose={() => setAddMenuAnchor(null)}
                PaperProps={{ sx: { bgcolor: '#1e1e1e', border: '1px solid #333', color: '#fff' } }}>
                {ADDABLE_TRACKS.map(type => (
                    <MenuItem key={type} onClick={() => addTrack(type)} sx={{ '&:hover': { bgcolor: '#2a2a2a' }, gap: 1 }}>
                        <ListItemIcon sx={{ color: TRACK_CONFIGS[type].color, minWidth: 28 }}>
                            {TRACK_ICONS[type]}
                        </ListItemIcon>
                        <ListItemText primary={<Typography variant="body2">{TRACK_CONFIGS[type].label}轨道</Typography>} />
                    </MenuItem>
                ))}
            </Menu>

            {/* ── Scrollable Timeline Area ── */}
            <Box ref={timelineRef} onClick={handleTrackAreaClick} sx={{
                flex: 1, overflowX: 'auto', overflowY: 'auto', position: 'relative',
                bgcolor: '#141414', cursor: isDragging ? 'grabbing' : 'crosshair',
                '&::-webkit-scrollbar': { height: 10, width: 10 },
                '&::-webkit-scrollbar-track': { bgcolor: '#0a0a0a' },
                '&::-webkit-scrollbar-thumb': { bgcolor: '#333', borderRadius: 5, '&:hover': { bgcolor: '#444' } },
            }}>
                <Box sx={{ width: timelineWidth, minHeight: '100%', position: 'relative' }}>

                    {/* Time Ruler */}
                    <Box sx={{ height: 28, borderBottom: '1px solid #333', position: 'sticky', top: 0, bgcolor: '#1e1e1e', zIndex: 100, display: 'flex' }}>
                        <Box sx={{ width: 80, flexShrink: 0, borderRight: '1px solid #333', bgcolor: '#1e1e1e' }} />
                        {Array.from({ length: Math.ceil(totalDuration) + 1 }).map((_, sec) => (
                            <Box key={sec} sx={{ width: pxPerSec, flexShrink: 0, borderLeft: sec % 5 === 0 ? '2px solid #555' : '1px solid #333', position: 'relative' }}>
                                {sec % 5 === 0 && (
                                    <Typography variant="caption" sx={{ position: 'absolute', left: 3, top: 2, fontSize: '0.6rem', color: '#888', userSelect: 'none' }}>
                                        {formatTime(sec)}
                                    </Typography>
                                )}
                            </Box>
                        ))}
                    </Box>

                    {/* Tracks */}
                    {tracks.map(track => {
                        const isVideo = track.type === 'video';
                        const isAudio = track.type === 'audio';
                        return (
                            <Box key={track.id} sx={{
                                height: track.height,
                                borderBottom: '1px solid #2a2a2a',
                                position: 'relative',
                                bgcolor: track.visible
                                    ? isVideo ? '#181818' : isAudio ? '#141414' : '#141414'
                                    : '#111',
                                opacity: track.locked ? 0.6 : 1,
                                transition: 'opacity 0.2s',
                            }}>
                                {/* Label */}
                                <TrackLabel
                                    track={track}
                                    onToggleVisible={() => updateTrack(track.id, { visible: !track.visible })}
                                    onToggleLock={() => updateTrack(track.id, { locked: !track.locked })}
                                    onDelete={() => deleteTrack(track.id)}
                                />

                                {/* Clips */}
                                {track.visible && !track.locked && (
                                    <>
                                        {isVideo && orderedShots.filter(s => s.duration > 0).map((shot, i, arr) => {
                                            const offset = arr.slice(0, i).reduce((a, s) => a + s.duration, 0);
                                            const orig = orderedShots.indexOf(shot);
                                            return (
                                                <VideoClip key={orig} shot={shot} index={orig}
                                                    startOffset={offset} pxPerSec={pxPerSec}
                                                    isSelected={currentShotIndex === orig}
                                                    onShotDurationChange={onShotDurationChange} />
                                            );
                                        })}
                                        {isAudio && orderedShots.filter(s => s.duration > 0).map((shot, i, arr) => {
                                            const offset = arr.slice(0, i).reduce((a, s) => a + s.duration, 0);
                                            return <AudioClip key={orderedShots.indexOf(shot)} shot={shot} startOffset={offset} pxPerSec={pxPerSec} />;
                                        })}
                                        {!isVideo && !isAudio && track.clips.map(clip => (
                                            <GenericClip key={clip.id} clip={clip} pxPerSec={pxPerSec} trackColor={track.color} />
                                        ))}
                                        {!isVideo && !isAudio && track.clips.length === 0 && (
                                            <Box sx={{ position: 'absolute', left: 88, top: 0, bottom: 0, display: 'flex', alignItems: 'center' }}>
                                                <Typography variant="caption" color="#333" sx={{ fontSize: '0.65rem', fontStyle: 'italic' }}>
                                                    空轨道 — 拖入片段或由 AI 自动填充
                                                </Typography>
                                            </Box>
                                        )}
                                    </>
                                )}

                                {/* Vertical resize handle */}
                                <TrackResizeHandle
                                    currentHeight={track.height}
                                    minHeight={TRACK_CONFIGS[track.type].minHeight}
                                    onResize={delta => resizeTrack(track.id, delta)}
                                />
                            </Box>
                        );
                    })}

                    {/* Playhead */}
                    <Box ref={playheadRef} sx={{
                        position: 'absolute', left: 80 + globalTime * pxPerSec,
                        top: 28, bottom: 0, width: 2, bgcolor: '#FF4081',
                        zIndex: 200, pointerEvents: 'none',
                    }}>
                        <Box sx={{
                            position: 'absolute', top: -6, left: '50%',
                            transform: 'translateX(-50%)',
                            width: 0, height: 0,
                            borderLeft: '6px solid transparent',
                            borderRight: '6px solid transparent',
                            borderTop: '8px solid #FF4081',
                        }} />
                    </Box>

                    {/* Ruler click area for seeking */}
                    <Box sx={{
                        position: 'absolute', left: 80, top: 0, right: 0, height: 28,
                        cursor: 'pointer', zIndex: 150,
                    }} onMouseDown={handlePlayheadDrag} />

                </Box>
            </Box>
        </Paper>
    );
};
