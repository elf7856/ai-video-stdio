import React, { useState, useEffect } from 'react';
import {
    Box, Button, Stack, IconButton, Snackbar, Alert,
    Dialog, DialogTitle, DialogContent, DialogActions, TextField, Slider, Typography
} from '@mui/material';
import { ArrowBack as BackIcon, Save as SaveIcon } from '@mui/icons-material';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useVideoPlayback } from '../hooks/useVideoPlayback';
import { VideoPlayer } from '../components/project/VideoPlayer';
import { Timeline } from '../components/project/Timeline';
import { ShotList } from '../components/project/ShotList';
import { ScriptPanel } from '../components/project/ScriptPanel';
import type { Shot, GeneratedVideo } from '../api/types';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
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

const ProjectPage: React.FC = () => {
    const location = useLocation();
    const { projectId } = useParams();
    const navigate = useNavigate();
    const timelineRef = React.useRef<HTMLDivElement>(null);

    // State Management
    const [activeTab, setActiveTab] = useState(0);
    const [projectData, setProjectData] = useState<ProjectData | null>(null);
    const [orderedShots, setOrderedShots] = useState<ShotWithVideo[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

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

    // Use video playback hook
    const {
        videoRef,
        currentShotIndex,
        setCurrentShotIndex,
        isPlaying,
        setIsPlaying,
        globalTime,
        totalDuration,
        volume,
        isMuted,
        handlePlayPause,
        handleTimeUpdate,
        handleSeek,
        handleVolumeChange,
        toggleMute,
    } = useVideoPlayback({ orderedShots });

    // Load project data from API
    useEffect(() => {
        const loadProjectData = async () => {
            try {
                setLoading(true);

                // Get taskId from route params or location state
                const taskId = projectId || location.state?.taskId;
                if (!taskId) {
                    throw new Error('No task ID provided');
                }

                const response = await fetch(`http://localhost:8000/api/video-generation/task/${taskId}`);
                if (!response.ok) throw new Error('Failed to load project');

                const result = await response.json();
                console.log('[Project] Loaded data:', result);

                // Extract actual data from the response
                const data = result.data || result;
                const shots = data.shots || [];

                const shotsWithVideo = shots.map((shot: Shot) => {
                    return {
                        ...shot,
                        videoData: shot // The shot itself contains video data
                    };
                });

                setProjectData({
                    taskId: data.taskId,
                    topic: data.config?.topic || data.topic,
                    style: data.config?.style || data.style,
                    script: data.script,
                    shots: shotsWithVideo,
                    totalDuration: shots.reduce((sum: number, s: any) => sum + (s.duration || 0), 0),
                    generatedVideos: shots,
                    finalVideo: data.finalVideo,
                    status: data.status,
                    logs: data.logs || []
                });
            } catch (err: any) {
                console.error('[Project] Load error:', err);
                setError(err.message || 'Failed to load project data');
            } finally {
                setLoading(false);
            }
        };

        loadProjectData();
    }, [projectId, location.state]);

    // Initialize shots when projectData changes
    useEffect(() => {
        if (projectData?.shots) {
            const loadActualDurations = async () => {
                const shotsWithActualDuration = await Promise.all(
                    projectData.shots.map(async (shot) => {
                        // Use videoPath directly from shot object
                        const videoPath = shot.videoPath || (shot as any).videoData?.videoPath;

                        // Load actual video duration
                        let actualDuration = shot.duration;
                        if (videoPath) {
                            try {
                                const videoElement = document.createElement('video');
                                // Use full URL - handle relative paths properly
                                let fullUrl = videoPath;
                                if (!videoPath.startsWith('http')) {
                                    // Remove leading ./ or . if present
                                    const cleanPath = videoPath.replace(/^\.\//, '/').replace(/^\.(?=\/)/, '');
                                    fullUrl = `http://localhost:8000${cleanPath.startsWith('/') ? cleanPath : '/' + cleanPath}`;
                                }
                                console.log(`[Shot ${shot.sequence}] Loading video from: ${fullUrl}`);
                                videoElement.src = fullUrl;

                                actualDuration = await new Promise<number>((resolve) => {
                                    videoElement.addEventListener('loadedmetadata', () => {
                                        resolve(videoElement.duration);
                                    });
                                    videoElement.addEventListener('error', () => {
                                        console.error(`Failed to load video: ${videoPath}`);
                                        resolve(shot.duration);
                                    });
                                    // Add timeout to prevent hanging
                                    setTimeout(() => resolve(shot.duration), 5000);
                                    videoElement.load();
                                });

                                console.log(`[Shot ${shot.sequence}] API duration: ${shot.duration}s, Actual duration: ${actualDuration.toFixed(2)}s`);
                            } catch (error) {
                                console.error(`Error loading video duration for shot ${shot.sequence}:`, error);
                            }
                        }

                        return {
                            ...shot,
                            duration: actualDuration,
                            videoData: shot, // Keep videoData as the shot itself
                        };
                    })
                );

                setOrderedShots(shotsWithActualDuration);
                console.log(`[Project] Total duration: ${shotsWithActualDuration.reduce((sum, s) => sum + s.duration, 0).toFixed(2)}s`);
            };

            loadActualDurations();
        }
    }, [projectData]);


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

    const handleShotDurationChange = (index: number, newDuration: number) => {
        const newShots = [...orderedShots];
        newShots[index] = {
            ...newShots[index],
            duration: newDuration
        };
        setOrderedShots(newShots);
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
                <Typography color="white">Loading project...</Typography>
            </Box>
        );
    }

    const currentShot = orderedShots[currentShotIndex];

    return (
        <Box
            component={motion.div}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            sx={{
                height: '100vh',
                bgcolor: '#0a0a0a',
                color: 'white',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden'
            }}
        >
            {/* 1. Top: Header */}
            <Box sx={{
                height: HEADER_HEIGHT,
                borderBottom: '1px solid #222',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                px: 2,
                bgcolor: '#111'
            }}>
                <Stack direction="row" spacing={2} alignItems="center">
                    <IconButton onClick={() => navigate('/')} sx={{ color: 'white' }}>
                        <BackIcon />
                    </IconButton>
                    <Typography variant="h6" fontWeight={600}>
                        {projectData?.topic || 'Untitled Project'}
                    </Typography>
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
                {/* Left Sidebar: Shot List */}
                <ShotList
                    orderedShots={orderedShots}
                    currentShotIndex={currentShotIndex}
                    activeTab={activeTab}
                    onTabChange={setActiveTab}
                    onShotSelect={setCurrentShotIndex}
                />

                {/* Center: Video Player */}
                <VideoPlayer
                    videoRef={videoRef}
                    currentShot={currentShot}
                    currentShotIndex={currentShotIndex}
                    totalShots={orderedShots.length}
                    isPlaying={isPlaying}
                    globalTime={globalTime}
                    totalDuration={totalDuration}
                    volume={volume}
                    isMuted={isMuted}
                    error={error}
                    onTimeUpdate={handleTimeUpdate}
                    onPlay={() => setIsPlaying(true)}
                    onPause={() => setIsPlaying(false)}
                    onPlayPause={handlePlayPause}
                    onSeek={handleSeek}
                    onVolumeChange={handleVolumeChange}
                    onToggleMute={toggleMute}
                />

                {/* Right Sidebar: Script & Logs */}
                <ScriptPanel
                    projectData={projectData}
                    currentShot={currentShot}
                    currentShotIndex={currentShotIndex}
                    activeTab={activeTab}
                    onTabChange={setActiveTab}
                    onEditShot={handleEditShot}
                    onDeleteShot={handleDeleteShot}
                />
            </Box>

            {/* 3. Bottom: Timeline */}
            <Timeline
                timelineRef={timelineRef}
                orderedShots={orderedShots}
                currentShotIndex={currentShotIndex}
                globalTime={globalTime}
                totalDuration={totalDuration}
                pxPerSec={pxPerSec}
                setPxPerSec={setPxPerSec}
                onSeek={handleSeek}
                onShotDurationChange={handleShotDurationChange}
            />

            {/* Edit Shot Dialog */}
            <Dialog
                open={editingShotIndex !== null}
                onClose={() => setEditingShotIndex(null)}
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle>Edit Shot {editingShotIndex !== null ? editingShotIndex + 1 : ''}</DialogTitle>
                <DialogContent>
                    <Box sx={{ pt: 2 }}>
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
                        <TextField
                            label="Prompt"
                            multiline
                            rows={4}
                            fullWidth
                            value={editingPrompt}
                            onChange={(e) => setEditingPrompt(e.target.value)}
                            sx={{ mt: 3 }}
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setEditingShotIndex(null)}>Cancel</Button>
                    <Button onClick={handleSaveShot} variant="contained">Save</Button>
                </DialogActions>
            </Dialog>

            {/* Snackbar */}
            <Snackbar
                open={snackbar.open}
                autoHideDuration={3000}
                onClose={() => setSnackbar({ ...snackbar, open: false })}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
            >
                <Alert severity={snackbar.severity} sx={{ width: '100%' }}>
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </Box>
    );
};

export default ProjectPage;
