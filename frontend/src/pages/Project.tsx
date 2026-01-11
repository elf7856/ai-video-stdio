import React, { useState, useEffect, useRef } from 'react';
import {
    Box, Paper, Typography, IconButton, Tabs, Tab, Grid, Slider, Button,
    useTheme, alpha, Stack, Chip, CircularProgress,
    Dialog, DialogTitle, DialogContent, DialogActions, TextField,
    Snackbar, Alert, Tooltip
} from '@mui/material';
import {
    VideoLibrary as VideoIcon,
    TextFields as TextIcon,
    MusicNote as MusicIcon,
    PlayArrow as PlayIcon,
    Pause as PauseIcon,
    Edit as EditIcon,
    Delete as DeleteIcon,
    Save as SaveIcon,
    ArrowBack as BackIcon
} from '@mui/icons-material';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { getFullUrl } from '../utils/url';
import TimelineFilmstrip from '../components/studio/TimelineFilmstrip';
import type { Shot, GeneratedVideo } from '../api/types';
import heroVideo from '../assets/videos/hero.mp4';

interface ShotWithVideo extends Shot {
    videoData?: GeneratedVideo;
}

interface ProjectData {
    taskId: string;
    topic?: string;
    style?: string;
    script?: string;
    shots: Shot[];
    totalDuration?: number;
    generatedVideos?: GeneratedVideo[];
    finalVideo?: string | null;
    status?: string;
    logs?: Array<{ timestamp: string; level: string; message: string }>;
}

// Layout Constants
const HEADER_HEIGHT = 50;
const TIMELINE_HEIGHT = 280;
const LEFT_SIDEBAR_WIDTH = 300;
const RIGHT_SIDEBAR_WIDTH = 320;

const ProjectPage: React.FC = () => {
    const theme = useTheme();
    const location = useLocation();
    const { projectId } = useParams();
    const navigate = useNavigate();
    const videoRef = useRef<HTMLVideoElement>(null);
    const timelineRef = useRef<HTMLDivElement>(null);

    // Default Mock Data
    const defaultMockData: ProjectData = {
        taskId: projectId || 'task_54e10280',
        topic: "Project Task 54e10280",
        shots: Array.from({ length: 6 }).map((_, i) => ({
            sequence: i + 1,
            prompt: `Shot ${i + 1} - A cinematic scene`,
            duration: 5,
            shotType: 'medium shot'
        })),
        generatedVideos: Array.from({ length: 6 }).map((_, i) => ({
            sequence: i + 1,
            videoPath: heroVideo,
            status: 'success'
        })),
        finalVideo: heroVideo,
        status: 'completed',
        logs: [
            { timestamp: '00:00', level: 'info', message: 'Project initialized' },
            { timestamp: '00:01', level: 'success', message: 'All shots generated successfully' }
        ]
    };

    // State Management
    const [activeTab, setActiveTab] = useState(0); // 0: Media, 1: Script, 2: Logs
    const [projectData] = useState<ProjectData>(location.state || defaultMockData);
    const [orderedShots, setOrderedShots] = useState<ShotWithVideo[]>([]);
    const [loading, setLoading] = useState(true);

    // Playback State
    const [currentShotIndex, setCurrentShotIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [globalTime, setGlobalTime] = useState(0);
    const [totalDuration, setTotalDuration] = useState(0);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);

    // Timeline State
    const [pxPerSec, setPxPerSec] = useState(40);

    // Editing State
    const [editingShotIndex, setEditingShotIndex] = useState<number | null>(null);
    const [editingDuration, setEditingDuration] = useState<number>(5);
    const [editingPrompt, setEditingPrompt] = useState<string>('');

    // Snackbar
    const [snackbar, setSnackbar] = useState<{
        open: boolean;
        message: string;
        severity: 'success' | 'error' | 'info' | 'warning';
    }>({ open: false, message: '', severity: 'info' });

    // Initialize shots
    useEffect(() => {
        if (projectData?.shots) {
            const initialShots = projectData.shots.map(shot => ({
                ...shot,
                videoData: projectData.generatedVideos?.find(v => v.sequence === shot.sequence),
            }));
            setOrderedShots(initialShots);
            const total = initialShots.reduce((sum, s) => sum + s.duration, 0);
            setTotalDuration(total);
            setLoading(false);
        }
    }, [projectData]);

    // Recalculate total duration when shots change
    useEffect(() => {
        const total = orderedShots.reduce((sum, s) => sum + s.duration, 0);
        setTotalDuration(total);
    }, [orderedShots]);

    // Playback handlers
    const handlePlayPause = () => {
        if (videoRef.current) {
            if (isPlaying) {
                videoRef.current.pause();
            } else {
                videoRef.current.play();
            }
            setIsPlaying(!isPlaying);
        }
    };

    const handleTimeUpdate = () => {
        if (videoRef.current) {
            const shotLocalTime = videoRef.current.currentTime;
            const prevDuration = orderedShots.slice(0, currentShotIndex).reduce((acc, s) => acc + s.duration, 0);
            const newGlobalTime = prevDuration + shotLocalTime;
            setGlobalTime(newGlobalTime);

            const currentShot = orderedShots[currentShotIndex];
            if (currentShot && shotLocalTime >= currentShot.duration - 0.05) {
                if (currentShotIndex < orderedShots.length - 1) {
                    setCurrentShotIndex(prev => prev + 1);
                } else {
                    setIsPlaying(false);
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
                if (currentShotIndex !== i) {
                    setCurrentShotIndex(i);
                }
                if (videoRef.current && currentShotIndex === i) {
                    videoRef.current.currentTime = seekTime - acc;
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

    // Shot editing handlers
    const handleEditShot = (index: number) => {
        const shot = orderedShots[index];
        setEditingShotIndex(index);
        setEditingDuration(shot.duration);
        setEditingPrompt(shot.prompt);
    };

    const handleSaveShot = () => {
        if (editingShotIndex !== null) {
            const newShots = [...orderedShots];
            newShots[editingShotIndex] = {
                ...newShots[editingShotIndex],
                duration: editingDuration,
                prompt: editingPrompt
            };
            setOrderedShots(newShots);
            setSnackbar({
                open: true,
                message: `镜头 ${editingShotIndex + 1} 已更新`,
                severity: 'success'
            });
        }
        setEditingShotIndex(null);
    };

    const handleDeleteShot = (index: number) => {
        if (orderedShots.length <= 1) {
            setSnackbar({
                open: true,
                message: '至少需要保留一个镜头',
                severity: 'warning'
            });
            return;
        }
        const newShots = orderedShots.filter((_, i) => i !== index);
        setOrderedShots(newShots);
        if (currentShotIndex >= newShots.length) {
            setCurrentShotIndex(newShots.length - 1);
        }
        setSnackbar({
            open: true,
            message: `镜头 ${index + 1} 已删除`,
            severity: 'info'
        });
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    if (loading) {
        return (
            <Box sx={{
                height: '100vh',
                bgcolor: '#0a0a0a',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }}>
                <CircularProgress />
            </Box>
        );
    }

    const currentShot = orderedShots[currentShotIndex];

    return (
        <Box sx={{
            height: '100vh',
            bgcolor: '#0a0a0a',
            color: '#e0e0e0',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
        }}>
            {/* 1. Header (Project Title, Export) */}
            <Box sx={{
                height: HEADER_HEIGHT,
                borderBottom: '1px solid #222',
                bgcolor: '#111',
                display: 'flex',
                alignItems: 'center',
                px: 2,
                justifyContent: 'space-between'
            }}>
                <Stack direction="row" spacing={2} alignItems="center">
                    <Tooltip title="返回">
                        <IconButton size="small" onClick={() => navigate('/generate')} sx={{ color: '#888' }}>
                            <BackIcon />
                        </IconButton>
                    </Tooltip>
                    <Typography variant="subtitle1" fontWeight={700} sx={{ color: 'white' }}>
                        {projectData?.topic || 'Untitled Project'}
                    </Typography>
                    <Chip
                        label={projectData?.status || 'In Progress'}
                        size="small"
                        color={projectData?.status === 'completed' ? 'success' : 'warning'}
                        sx={{ height: 24 }}
                    />
                </Stack>
                <Stack direction="row" spacing={1}>
                    <Button
                        variant="outlined"
                        size="small"
                        startIcon={<SaveIcon />}
                        sx={{
                            borderColor: '#333',
                            color: '#888',
                            '&:hover': { borderColor: '#666', color: 'white' }
                        }}
                    >
                        Save
                    </Button>
                    <Button
                        variant="contained"
                        size="small"
                        sx={{
                            background: 'linear-gradient(45deg, #6366f1, #ec4899)',
                            textTransform: 'none'
                        }}
                    >
                        Export Video
                    </Button>
                </Stack>
            </Box>

            {/* 2. Main Workspace (Flex Row) */}
            <Box sx={{ flex: 1, display: 'flex', minHeight: 0 }}>
                
                {/* Left Sidebar: Assets */}
                <Paper sx={{
                    width: LEFT_SIDEBAR_WIDTH,
                    bgcolor: '#0f0f0f',
                    borderRight: '1px solid #222',
                    display: 'flex',
                    flexDirection: 'column'
                }} square>
                    <Tabs
                        value={activeTab}
                        onChange={(_, v) => setActiveTab(v)}
                        variant="fullWidth"
                        sx={{
                            minHeight: 48,
                            '& .MuiTab-root': { minHeight: 48, fontSize: '0.75rem', color: '#666' },
                            '& .Mui-selected': { color: '#fff' },
                            '& .MuiTabs-indicator': { backgroundColor: '#FF4081' }
                        }}
                    >
                        <Tab icon={<VideoIcon fontSize="small" />} label="Media" />
                        <Tab icon={<TextIcon fontSize="small" />} label="Text" />
                        <Tab icon={<MusicIcon fontSize="small" />} label="Audio" />
                    </Tabs>
                    <Box sx={{ flex: 1, p: 2, overflowY: 'auto' }}>
                        <Typography variant="caption" color="text.secondary" display="block" mb={2}>
                            Project Assets ({orderedShots.length})
                        </Typography>
                        {/* Asset Grid */}
                        <Grid container spacing={1}>
                            {orderedShots.map((shot, i) => (
                                <Grid item xs={6} key={i}>
                                    <Box sx={{
                                        aspectRatio: '16/9',
                                        bgcolor: '#000',
                                        borderRadius: 1,
                                        border: currentShotIndex === i ? '2px solid #FF4081' : '1px solid #333',
                                        cursor: 'pointer',
                                        overflow: 'hidden',
                                        position: 'relative',
                                        '&:hover': { borderColor: theme.palette.primary.main }
                                    }}
                                    onClick={() => setCurrentShotIndex(i)}
                                    >
                                        {shot.videoData?.videoPath ? (
                                            <video
                                                src={getFullUrl(shot.videoData.videoPath)}
                                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                                muted
                                                onMouseOver={e => e.currentTarget.play()}
                                                onMouseOut={e => { e.currentTarget.pause(); e.currentTarget.currentTime = 0; }}
                                            />
                                        ) : (
                                            <Box sx={{
                                                width: '100%',
                                                height: '100%',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                bgcolor: '#1a1a1a'
                                            }}>
                                                <Typography variant="caption" color="#666">Shot {shot.sequence}</Typography>
                                            </Box>
                                        )}
                                        <Box sx={{ position: 'absolute', bottom: 2, right: 2, bgcolor: 'rgba(0,0,0,0.8)', px: 0.5, borderRadius: 0.5 }}>
                                            <Typography variant="caption" sx={{ fontSize: '0.6rem' }}>#{shot.sequence}</Typography>
                                        </Box>
                                    </Box>
                                </Grid>
                            ))}
                        </Grid>
                    </Box>
                </Paper>

                {/* Center: Canvas / Preview */}
                <Box sx={{
                    flex: 1,
                    bgcolor: '#050505',
                    display: 'flex',
                    flexDirection: 'column',
                    position: 'relative',
                    p: 3
                }}>
                    {/* Video Player */}
                    <Box sx={{
                        flex: 1,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}>
                        <Paper sx={{
                            width: '100%',
                            maxWidth: '1000px',
                            aspectRatio: '16/9',
                            bgcolor: 'black',
                            borderRadius: 1,
                            overflow: 'hidden',
                            position: 'relative',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: '1px solid #333'
                        }}>
                            {currentShot?.videoData?.videoPath ? (
                                <video
                                    ref={videoRef}
                                    src={getFullUrl(currentShot.videoData.videoPath)}
                                    style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                                    onTimeUpdate={handleTimeUpdate}
                                    onPlay={() => setIsPlaying(true)}
                                    onPause={() => setIsPlaying(false)}
                                />
                            ) : (
                                <Box sx={{ textAlign: 'center' }}>
                                    <Typography variant="h6" color="text.secondary">
                                        镜头 #{currentShotIndex + 1}
                                    </Typography>
                                    <Typography color="text.secondary">
                                        等待视频生成
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
                                    label={`镜头 ${currentShotIndex + 1}/${orderedShots.length}`}
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
                        </Paper>
                    </Box>

                    {/* Player Controls */}
                    <Box sx={{ mt: 2, maxWidth: '1000px', mx: 'auto', width: '100%' }}>
                        {/* Progress Bar */}
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                            <Typography variant="caption" sx={{ minWidth: 40 }}>
                                {formatTime(globalTime)}
                            </Typography>
                            <Slider
                                value={globalTime}
                                max={totalDuration || 100}
                                onChange={handleSeek}
                                sx={{ flex: 1 }}
                            />
                            <Typography variant="caption" sx={{ minWidth: 40 }}>
                                {formatTime(totalDuration)}
                            </Typography>
                        </Box>

                        {/* Control Buttons */}
                        <Stack direction="row" justifyContent="center" alignItems="center" spacing={2}>
                            <IconButton
                                onClick={handlePlayPause}
                                sx={{
                                    bgcolor: 'primary.main',
                                    '&:hover': { bgcolor: 'primary.dark' },
                                    width: 48,
                                    height: 48
                                }}
                            >
                                {isPlaying ? <PauseIcon /> : <PlayIcon />}
                            </IconButton>
                            <Stack direction="row" spacing={1} alignItems="center">
                                <IconButton onClick={toggleMute} size="small">
                                    {isMuted ? <MusicIcon /> : <MusicIcon />}
                                </IconButton>
                                <Slider
                                    value={isMuted ? 0 : volume}
                                    max={1}
                                    step={0.1}
                                    onChange={handleVolumeChange}
                                    sx={{ width: 100 }}
                                />
                            </Stack>
                        </Stack>
                    </Box>
                </Box>

                {/* Right Sidebar: Script & Logs */}
                <Paper sx={{
                    width: RIGHT_SIDEBAR_WIDTH,
                    bgcolor: '#0f0f0f',
                    borderLeft: '1px solid #222',
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden'
                }} square>
                    <Tabs
                        value={activeTab === 0 ? 0 : activeTab === 1 ? 1 : 2}
                        onChange={(_, v) => setActiveTab(v)}
                        variant="fullWidth"
                        sx={{
                            minHeight: 48,
                            borderBottom: '1px solid #222',
                            '& .MuiTab-root': { minHeight: 48, fontSize: '0.75rem', color: '#666' },
                            '& .Mui-selected': { color: '#fff' },
                            '& .MuiTabs-indicator': { backgroundColor: '#FF4081' }
                        }}
                    >
                        <Tab label="Script" />
                        <Tab label="Logs" />
                    </Tabs>

                    <Box sx={{ flex: 1, p: 2, overflowY: 'auto' }}>
                        {activeTab === 0 && (
                            <Box>
                                <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                                    Script
                                </Typography>
                                <Paper sx={{
                                    p: 2,
                                    bgcolor: '#1a1a1a',
                                    borderRadius: 1,
                                    border: '1px solid #333',
                                    minHeight: 200
                                }}>
                                    <Typography variant="body2" color="#ccc" sx={{
                                        whiteSpace: 'pre-wrap',
                                        lineHeight: 1.6,
                                        fontFamily: 'monospace',
                                        fontSize: '0.85rem'
                                    }}>
                                        {projectData?.script || 'No script available'}
                                    </Typography>
                                </Paper>

                                <Typography variant="subtitle2" fontWeight={700} gutterBottom sx={{ mt: 3 }}>
                                    Current Shot
                                </Typography>
                                <Paper sx={{
                                    p: 2,
                                    bgcolor: '#1a1a1a',
                                    borderRadius: 1,
                                    border: '1px solid #333'
                                }}>
                                    <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                                        Prompt:
                                    </Typography>
                                    <Typography variant="body2" color="#ccc">
                                        {currentShot?.prompt || 'No prompt'}
                                    </Typography>
                                    <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                                        <Button
                                            size="small"
                                            variant="outlined"
                                            startIcon={<EditIcon />}
                                            onClick={() => handleEditShot(currentShotIndex)}
                                            sx={{ borderColor: '#333', color: '#888' }}
                                        >
                                            Edit
                                        </Button>
                                        <Button
                                            size="small"
                                            variant="outlined"
                                            color="error"
                                            startIcon={<DeleteIcon />}
                                            onClick={() => handleDeleteShot(currentShotIndex)}
                                            sx={{ borderColor: '#333' }}
                                        >
                                            Delete
                                        </Button>
                                    </Stack>
                                </Paper>
                            </Box>
                        )}

                        {activeTab === 1 && (
                            <Box>
                                <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                                    Execution Logs
                                </Typography>
                                <Paper sx={{
                                    p: 2,
                                    bgcolor: '#0a0a0a',
                                    borderRadius: 1,
                                    border: '1px solid #333',
                                    fontFamily: 'monospace',
                                    fontSize: '0.85rem',
                                    minHeight: 400
                                }}>
                                    {projectData?.logs && projectData.logs.length > 0 ? (
                                        <Stack spacing={1}>
                                            {projectData.logs.map((log, index) => (
                                                <Box key={index} sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
                                                    <Typography variant="caption" color="#666" sx={{ minWidth: 60, fontFamily: 'monospace' }}>
                                                        {log.timestamp}
                                                    </Typography>
                                                    <Typography sx={{
                                                        color: log.level === 'error' ? '#ff5252' :
                                                               log.level === 'success' ? '#69f0ae' :
                                                               log.level === 'warning' ? '#ffd740' : '#e0e0e0',
                                                        fontFamily: 'monospace',
                                                        wordBreak: 'break-word',
                                                        fontSize: '0.8rem'
                                                    }}>
                                                        {log.level === 'success' && '✅ '}
                                                        {log.level === 'error' && '❌ '}
                                                        {log.level === 'warning' && '⚠️ '}
                                                        {log.message}
                                                    </Typography>
                                                </Box>
                                            ))}
                                        </Stack>
                                    ) : (
                                        <Typography color="#666" fontStyle="italic">No logs available</Typography>
                                    )}
                                </Paper>
                            </Box>
                        )}
                    </Box>
                </Paper>
            </Box>

            {/* 3. Bottom: Timeline */}
            <Paper sx={{
                height: TIMELINE_HEIGHT,
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
                        <Typography variant="subtitle2" fontWeight={700}>Timeline</Typography>
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
                        {/* Global Playhead */}
                        <Box sx={{
                            position: 'absolute',
                            left: 16 + (globalTime * pxPerSec),
                            top: 0,
                            bottom: 0,
                            width: 2,
                            bgcolor: '#FF4081',
                            zIndex: 20,
                            pointerEvents: 'none',
                            transition: 'left 0.1s linear',
                            boxShadow: '0 0 8px rgba(255, 64, 129, 0.8)'
                        }}>
                            <Box sx={{
                                position: 'absolute',
                                top: -4,
                                left: -6,
                                width: 14,
                                height: 14,
                                bgcolor: '#FF4081',
                                transform: 'rotate(45deg)',
                                borderRadius: '2px 2px 2px 8px'
                            }} />
                        </Box>

                        {/* Shot Clips */}
                        {orderedShots.map((shot, index) => {
                            const shotWidth = shot.duration * pxPerSec;
                            const isSelected = currentShotIndex === index;

                            return (
                                <motion.div
                                    key={`${shot.sequence}-${index}`}
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ delay: index * 0.05 }}
                                    style={{
                                        width: shotWidth,
                                        height: 100,
                                        borderRight: '1px solid #000',
                                        flexShrink: 0,
                                        position: 'relative'
                                    }}
                                >
                                    <Paper
                                        sx={{
                                            width: '100%',
                                            height: '100%',
                                            bgcolor: isSelected ? alpha(theme.palette.primary.main, 0.1) : '#222',
                                            border: isSelected ? `2px solid ${theme.palette.primary.main}` : '1px solid #333',
                                            borderRadius: 0,
                                            overflow: 'hidden',
                                            cursor: 'pointer',
                                            display: 'flex',
                                            flexDirection: 'column',
                                            position: 'relative',
                                            '&:hover': { border: '1px solid #888' }
                                        }}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            const startOffset = orderedShots.slice(0, index).reduce((acc, s) => acc + s.duration, 0);
                                            handleSeek({} as any, startOffset);
                                        }}
                                    >
                                        {/* Filmstrip Preview */}
                                        <Box sx={{ height: 40, bgcolor: '#000', display: 'flex', overflow: 'hidden', opacity: 0.9 }}>
                                            {shot.videoData?.videoPath ? (
                                                <TimelineFilmstrip
                                                    videoUrl={getFullUrl(shot.videoData.videoPath)}
                                                    duration={shot.duration}
                                                    height={40}
                                                    pxPerSec={pxPerSec}
                                                />
                                            ) : (
                                                <Box sx={{ width: '100%', height: '100%', bgcolor: '#333' }} />
                                            )}
                                        </Box>

                                        {/* Shot Info */}
                                        <Box sx={{ flex: 1, p: 0.5, px: 1 }}>
                                            <Typography variant="caption" display="block" noWrap fontWeight={700} color="white">
                                                Shot {index + 1}
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary" noWrap sx={{ fontSize: '0.65rem' }}>
                                                {shot.duration.toFixed(1)}s • {shot.prompt.substring(0, 15)}...
                                            </Typography>
                                        </Box>

                                        {/* Edit Handle */}
                                        {isSelected && (
                                            <Tooltip title="Edit Shot">
                                                <Box
                                                    sx={{
                                                        position: 'absolute',
                                                        right: 0,
                                                        top: 0,
                                                        bottom: 0,
                                                        width: 10,
                                                        cursor: 'ew-resize',
                                                        bgcolor: 'rgba(255,255,255,0.2)',
                                                        '&:hover': { bgcolor: '#FF4081' },
                                                        zIndex: 10,
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'center'
                                                    }}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleEditShot(index);
                                                    }}
                                                >
                                                    <Box sx={{ width: 2, height: 12, bgcolor: 'white', borderRadius: 1 }} />
                                                </Box>
                                            </Tooltip>
                                        )}
                                    </Paper>
                                </motion.div>
                            );
                        })}
                    </Box>
                </Box>
            </Paper>

            {/* Shot Edit Dialog */}
            <Dialog
                open={editingShotIndex !== null}
                onClose={() => setEditingShotIndex(null)}
                maxWidth="sm"
                fullWidth
                PaperProps={{ sx: { bgcolor: '#1e293b', backgroundImage: 'none' } }}
            >
                <DialogTitle>
                    <Stack direction="row" alignItems="center" spacing={1}>
                        <EditIcon />
                        <span>Edit Shot {editingShotIndex !== null ? editingShotIndex + 1 : ''}</span>
                    </Stack>
                </DialogTitle>
                <DialogContent>
                    <Stack spacing={3} sx={{ mt: 2 }}>
                        {/* Duration */}
                        <Box>
                            <Typography gutterBottom>
                                Duration: {editingDuration}s
                            </Typography>
                            <Slider
                                value={editingDuration}
                                onChange={(_, value) => setEditingDuration(value as number)}
                                min={1}
                                max={30}
                                step={1}
                                marks={[
                                    { value: 1, label: '1s' },
                                    { value: 5, label: '5s' },
                                    { value: 10, label: '10s' },
                                    { value: 20, label: '20s' },
                                    { value: 30, label: '30s' },
                                ]}
                                valueLabelDisplay="auto"
                            />
                        </Box>

                        {/* Prompt */}
                        <Box>
                            <Typography gutterBottom>Prompt:</Typography>
                            <TextField
                                fullWidth
                                multiline
                                rows={4}
                                value={editingPrompt}
                                onChange={(e) => setEditingPrompt(e.target.value)}
                                placeholder="Describe this shot..."
                                sx={{
                                    '& .MuiOutlinedInput-root': {
                                        bgcolor: alpha(theme.palette.background.paper, 0.3),
                                    }
                                }}
                            />
                        </Box>

                        {/* Quick Actions */}
                        <Box>
                            <Typography gutterBottom>Quick Actions:</Typography>
                            <Stack direction="row" spacing={1}>
                                <Button
                                    variant="outlined"
                                    size="small"
                                    color="error"
                                    startIcon={<DeleteIcon />}
                                    onClick={() => {
                                        if (editingShotIndex !== null) {
                                            handleDeleteShot(editingShotIndex);
                                            setEditingShotIndex(null);
                                        }
                                    }}
                                >
                                    Delete Shot
                                </Button>
                            </Stack>
                        </Box>
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setEditingShotIndex(null)}>Cancel</Button>
                    <Button
                        variant="contained"
                        startIcon={<SaveIcon />}
                        onClick={handleSaveShot}
                    >
                        Save
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Snackbar for feedback */}
            <Snackbar
                open={snackbar.open}
                autoHideDuration={4000}
                onClose={() => setSnackbar({ ...snackbar, open: false })}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert
                    onClose={() => setSnackbar({ ...snackbar, open: false })}
                    severity={snackbar.severity}
                    sx={{ width: '100%' }}
                >
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </Box>
    );
};

export default ProjectPage;
