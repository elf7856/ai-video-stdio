import React, { useState, useEffect } from 'react';
import {
    Box, Button, Stack, IconButton, Snackbar, Alert,
    Dialog, DialogTitle, DialogContent, DialogActions, TextField, Slider, Typography
} from '@mui/material';
import { ArrowBack as BackIcon, Save as SaveIcon } from '@mui/icons-material';
import { useLocation, useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { AVCanvasPlayer } from '../components/project/AVCanvasPlayer';
import { MultiTrackTimeline } from '../components/project/MultiTrackTimeline';
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
    progress?: number;
    logs?: Array<{ timestamp: string; level: string; message: string }>;
}

// Layout Constants
const HEADER_HEIGHT = 50;

const ProjectPage: React.FC = () => {
    const location = useLocation();
    const { projectId } = useParams();
    const navigate = useNavigate();

    // State Management
    const [activeTab, setActiveTab] = useState(0);
    const [projectData, setProjectData] = useState<ProjectData | null>(null);
    const [orderedShots, setOrderedShots] = useState<ShotWithVideo[]>([]);
    const [loading, setLoading] = useState(true);

    // Playback State (synced with AVCanvasPlayer)
    const [currentShotIndex, setCurrentShotIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [globalTime, setGlobalTime] = useState(0);
    const [totalDuration, setTotalDuration] = useState(0);

    // Timeline State
    const [externalSeekTime, setExternalSeekTime] = useState<number | null>(null);

    // Editing State
    const [editingShotIndex, setEditingShotIndex] = useState<number | null>(null);
    const [editingDuration, setEditingDuration] = useState<number>(5);
    const [editingPrompt, setEditingPrompt] = useState<string>('');

    // Panel resize
    const [leftPanelWidth, setLeftPanelWidth] = useState(260);
    const [rightPanelWidth, setRightPanelWidth] = useState(480);

    const makeDividerHandler = (
        getCurrent: () => number,
        setter: (w: number) => void,
        direction: 'left' | 'right',
        min: number,
        max: number
    ) => (e: React.MouseEvent) => {
        e.preventDefault();
        const startX = e.clientX;
        const startWidth = getCurrent();
        const onMouseMove = (moveEvent: MouseEvent) => {
            const delta = direction === 'right'
                ? startX - moveEvent.clientX   // 右侧：向左拖 → 变宽
                : moveEvent.clientX - startX;  // 左侧：向右拖 → 变宽
            setter(Math.max(min, Math.min(max, startWidth + delta)));
        };
        const onMouseUp = () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        };
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    };

    // Snackbar
    const [snackbar, setSnackbar] = useState<{
        open: boolean;
        message: string;
        severity: 'success' | 'error' | 'info' | 'warning';
    }>({ open: false, message: '', severity: 'info' });

    // Callbacks from AVCanvasPlayer
    const handleTimeUpdate = (time: number) => {
        setGlobalTime(time);
    };

    const handleShotChange = (index: number) => {
        setCurrentShotIndex(index);
    };

    const handlePlayStateChange = (playing: boolean) => {
        setIsPlaying(playing);
    };

    // Handle seek from Timeline
    const handleSeek = (time: number) => {
        setExternalSeekTime(time);
        // Reset after a short delay to allow re-seeking to the same time
        setTimeout(() => setExternalSeekTime(null), 100);
    };

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

                // 🆕 检查是否正在生成中
                const isGenerating = location.state?.isGenerating;

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

                // 🆕 如果正在生成，启动轮询并切换到生成状态标签页
                if (isGenerating || ['pending', 'generating_script', 'generating_videos', 'checking_quality', 'merging_videos'].includes(data.status)) {
                    startPolling(taskId);
                    setActiveTab(1); // 切换到生成状态/日志标签页
                }

                // 如果是等待确认状态，也启动轮询但保持在Script标签页
                if (data.status === 'waiting_confirmation') {
                    startPolling(taskId);
                    setActiveTab(0); // 保持在Script标签页以显示确认按钮
                }

            } catch (err: any) {
                console.error('[Project] Load error:', err);
                // Show error in snackbar instead
                setSnackbar({
                    open: true,
                    message: err.message || 'Failed to load project data',
                    severity: 'error'
                });
            } finally {
                setLoading(false);
            }
        };

        loadProjectData();
    }, [projectId, location.state]);

    // 🆕 轮询函数
    const startPolling = (taskId: string) => {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/video-generation/task/${taskId}`);
                if (!response.ok) {
                    clearInterval(pollInterval);
                    return;
                }

                const result = await response.json();
                const data = result.data || result;
                const shots = data.shots || [];

                const shotsWithVideo = shots.map((shot: Shot) => {
                    return {
                        ...shot,
                        videoData: shot
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

                console.log('[Project] Polling update:', data.status, 'Progress:', data.progress);

                // 如果完成或失败，停止轮询
                if (['completed', 'failed', 'cancelled'].includes(data.status)) {
                    clearInterval(pollInterval);
                    console.log('[Project] Polling stopped, status:', data.status);
                }
            } catch (err) {
                console.error('[Project] Polling error:', err);
            }
        }, 2000); // 每2秒轮询一次

        // 清理函数
        return () => clearInterval(pollInterval);
    };

    // Initialize shots when projectData changes
    useEffect(() => {
        if (projectData?.shots) {
            const loadActualDurations = async () => {
                const shotsWithActualDuration = await Promise.all(
                    projectData.shots.map(async (shot) => {
                        // Use videoPath directly from shot object
                        const videoPath = shot.videoPath || (shot as any).videoData?.videoPath;

                        // 只有在有视频时才加载实际时长，否则duration为0
                        let actualDuration = 0;
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
                                        resolve(0);
                                    });
                                    // Add timeout to prevent hanging
                                    setTimeout(() => resolve(0), 5000);
                                    videoElement.load();
                                });

                                console.log(`[Shot ${shot.sequence}] Actual duration: ${actualDuration.toFixed(2)}s`);
                            } catch (error) {
                                console.error(`Error loading video duration for shot ${shot.sequence}:`, error);
                            }
                        } else {
                            console.log(`[Shot ${shot.sequence}] No video yet, duration = 0`);
                        }

                        return {
                            ...shot,
                            duration: actualDuration,
                            videoData: shot, // Keep videoData as the shot itself
                        };
                    })
                );

                setOrderedShots(shotsWithActualDuration);
                const total = shotsWithActualDuration.reduce((sum, s) => sum + Number(s.duration), 0);
                setTotalDuration(total);
                console.log(`[Project] Total duration: ${total.toFixed(2)}s`);
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

    const handleConfirmGeneration = async () => {
        if (!projectData?.taskId) return;

        try {
            // 从后端获取最新的任务数据，确保使用最新的shots
            const taskResponse = await fetch(`http://localhost:8000/api/video-generation/task/${projectData.taskId}`);
            if (!taskResponse.ok) {
                throw new Error('Failed to fetch latest task data');
            }
            const taskResult = await taskResponse.json();
            const latestData = taskResult.data || taskResult;

            // 准备确认请求的数据
            const confirmData = {
                script: latestData.script || '',
                shots: latestData.shots.map((shot: any) => ({
                    sequence: shot.sequence,
                    prompt: shot.prompt,
                    duration: typeof shot.duration === 'string' ? parseFloat(shot.duration.replace('s', '')) : shot.duration,
                    shotType: shot.shotType,
                    imagePath: shot.imagePath,
                    videoPath: shot.videoPath
                })),
                options: {}
            };

            console.log('[Project] Confirming generation with data:', confirmData);

            const response = await fetch(`http://localhost:8000/api/video-generation/task/${projectData.taskId}/confirm`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(confirmData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to confirm generation');
            }

            setSnackbar({
                open: true,
                message: '已确认生成，开始生成视频...',
                severity: 'success'
            });

            // 切换到生成状态标签页
            setActiveTab(1);
        } catch (err: any) {
            console.error('[Project] Confirm generation error:', err);
            setSnackbar({
                open: true,
                message: err.message || '确认生成失败',
                severity: 'error'
            });
        }
    };

    const handleShotDurationChange = (index: number, newDuration: number) => {
        console.log('[Project] handleShotDurationChange:', index, newDuration);
        setOrderedShots(prevShots => {
            const newShots = [...prevShots];
            newShots[index] = {
                ...newShots[index],
                duration: newDuration
            };
            return newShots;
        });
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
                    width={leftPanelWidth}
                />

                {/* Drag divider: left panel */}
                <Box
                    onMouseDown={makeDividerHandler(() => leftPanelWidth, setLeftPanelWidth, 'left', 180, 480)}
                    sx={{
                        width: 4,
                        cursor: 'col-resize',
                        bgcolor: '#1a1a1a',
                        flexShrink: 0,
                        '&:hover': { bgcolor: '#FF4081' },
                        transition: 'background-color 0.15s'
                    }}
                />

                {/* Center: Video Player */}
                <AVCanvasPlayer
                    orderedShots={orderedShots}
                    onTimeUpdate={handleTimeUpdate}
                    onShotChange={handleShotChange}
                    onPlayStateChange={handlePlayStateChange}
                    externalSeekTime={externalSeekTime}
                />

                {/* Drag divider: right panel */}
                <Box
                    onMouseDown={makeDividerHandler(() => rightPanelWidth, setRightPanelWidth, 'right', 240, 700)}
                    sx={{
                        width: 4,
                        cursor: 'col-resize',
                        bgcolor: '#1a1a1a',
                        flexShrink: 0,
                        '&:hover': { bgcolor: '#FF4081' },
                        transition: 'background-color 0.15s'
                    }}
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
                    onConfirmGeneration={handleConfirmGeneration}
                    width={rightPanelWidth}
                />
            </Box>

            {/* 3. Bottom: Timeline */}
            <MultiTrackTimeline
                orderedShots={orderedShots}
                currentShotIndex={currentShotIndex}
                globalTime={globalTime}
                totalDuration={totalDuration}
                onSeek={handleSeek}
                isPlaying={isPlaying}
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
