import React, { useState, useEffect, useRef } from 'react';
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
import type { Shot, GeneratedVideo, StrategyDecision, SourceMaterial } from '../api/types';
import { videosApi } from '../api';

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
    strategyDecision?: StrategyDecision | null;
    sourceMaterial?: SourceMaterial | null;
}

// Layout Constants
const HEADER_HEIGHT = 50;

const ProjectPage: React.FC = () => {
    const location = useLocation();
    const { projectId } = useParams();
    const navigate = useNavigate();

    // State Management
    const [assetTab, setAssetTab] = useState(0);
    const [detailTab, setDetailTab] = useState(0);
    const [projectData, setProjectData] = useState<ProjectData | null>(null);
    const [orderedShots, setOrderedShots] = useState<ShotWithVideo[]>([]);
    const [loading, setLoading] = useState(true);
    const [confirmingGeneration, setConfirmingGeneration] = useState(false);

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

    // Panel resize — 用 ref 存当前值，拖动时直接操作 DOM，松手才 setState（避免拖动卡顿）
    const [leftPanelWidth,   setLeftPanelWidth]   = useState(260);
    const [rightPanelWidth,  setRightPanelWidth]  = useState(480);
    const [timelineHeight,   setTimelineHeight]   = useState(280);
    const pollingRef = useRef<number | null>(null);

    const leftPanelRef    = useRef<HTMLDivElement>(null);
    const rightPanelRef   = useRef<HTMLDivElement>(null);
    const timelineWrapRef = useRef<HTMLDivElement>(null);

    const makeDividerHandler = (
        startVal: number,
        ref: React.RefObject<HTMLDivElement>,
        setter: (v: number) => void,
        direction: 'left' | 'right',
        min: number, max: number,
        dim: 'width' | 'height' = 'width'
    ) => (e: React.MouseEvent) => {
        e.preventDefault();
        // for horizontal: use clientX; for vertical: use clientY
        const isHorizontal = dim === 'width';
        const start = isHorizontal ? e.clientX : e.clientY;
        let current = startVal;
        const onMove = (mv: MouseEvent) => {
            const pos = isHorizontal ? mv.clientX : mv.clientY;
            const delta = direction === 'right' ? start - pos : pos - start;
            current = Math.max(min, Math.min(max, startVal + delta));
            if (ref.current) ref.current.style[dim] = `${current}px`;
        };
        const onUp = () => {
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
            setter(current); // 松手时才触发 React re-render（1次）
        };
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    };

    const handleTimelineDividerMouseDown = (e: React.MouseEvent) => {
        e.preventDefault();
        const startY = e.clientY;
        let current = timelineHeight;
        const onMove = (mv: MouseEvent) => {
            current = Math.max(120, Math.min(600, timelineHeight + (startY - mv.clientY)));
            if (timelineWrapRef.current) timelineWrapRef.current.style.height = `${current}px`;
        };
        const onUp = () => {
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup', onUp);
            setTimelineHeight(current);
        };
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onUp);
    };

    // Snackbar
    const [snackbar, setSnackbar] = useState<{
        open: boolean;
        message: string;
        severity: 'success' | 'error' | 'info' | 'warning';
    }>({ open: false, message: '', severity: 'info' });

    const applyTaskData = (task: any) => {
        const shots = task.shots || [];
        const shotsWithVideo = shots.map((shot: Shot) => ({
            ...shot,
            videoData: shot
        }));

        setProjectData({
            taskId: task.taskId,
            topic: task.topic,
            style: task.style,
            script: task.script,
            shots: shotsWithVideo,
            totalDuration: shots.reduce((sum: number, s: any) => sum + (s.duration || 0), 0),
            generatedVideos: shots,
            finalVideo: task.finalVideo,
            status: task.status,
            progress: task.progress,
            logs: task.logs || [],
            strategyDecision: task.strategyDecision || null,
            sourceMaterial: task.sourceMaterial || location.state?.sourceMaterial || null
        });
    };

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

                const data = await videosApi.getTaskStatus(taskId);
                console.log('[Project] Loaded data:', data);
                applyTaskData(data);

                // 🆕 如果正在生成，启动轮询并切换到生成状态标签页
                if (isGenerating || ['pending', 'generating_script', 'generating', 'generating_videos', 'checking_quality', 'merging_videos'].includes(data.status)) {
                    startPolling(taskId);
                    setDetailTab(1); // 切换到生成状态/日志标签页
                }

                // 如果是等待确认状态，也启动轮询但保持在Script标签页
                if (data.status === 'waiting_confirmation') {
                    startPolling(taskId);
                    setDetailTab(0); // 保持在Script标签页以显示确认按钮
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
        if (pollingRef.current) {
            clearInterval(pollingRef.current);
        }
        const pollInterval = setInterval(async () => {
            try {
                const data = await videosApi.getTaskStatus(taskId);
                applyTaskData(data);

                console.log('[Project] Polling update:', data.status, 'Progress:', data.progress);

                // 如果完成或失败，停止轮询
                if (['completed', 'partial_success', 'failed', 'cancelled'].includes(data.status)) {
                    clearInterval(pollInterval);
                    console.log('[Project] Polling stopped, status:', data.status);
                }
            } catch (err) {
                console.error('[Project] Polling error:', err);
            }
        }, 2000); // 每2秒轮询一次
        pollingRef.current = pollInterval;

        // 清理函数
        return () => clearInterval(pollInterval);
    };

    useEffect(() => {
        return () => {
            if (pollingRef.current) {
                clearInterval(pollingRef.current);
            }
        };
    }, []);

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
            setConfirmingGeneration(true);
            // 从后端获取最新的任务数据，确保使用最新的shots
            const latestData = await videosApi.getTaskStatus(projectData.taskId);

            const confirmShots = (latestData.shots || []).map((shot: any) => ({
                    sequence: shot.sequence,
                    prompt: shot.prompt,
                    duration: typeof shot.duration === 'string' ? parseFloat(shot.duration.replace('s', '')) : shot.duration,
                    shotType: shot.shotType,
                    imagePath: shot.imagePath,
                    videoPath: shot.videoPath
                }));

            console.log('[Project] Confirming generation with data:', {
                script: latestData.script || '',
                shots: confirmShots,
                options: {}
            });

            await videosApi.confirmAndGenerate(projectData.taskId, latestData.script || '', confirmShots, {});
            setProjectData(prev => prev ? {
                ...prev,
                status: 'generating_videos',
                progress: Math.max(prev.progress || 30, 35),
                logs: [
                    ...(prev.logs || []),
                    {
                        timestamp: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
                        level: 'info',
                        message: '已确认方案，正在启动视频生成...'
                    }
                ]
            } : prev);
            startPolling(projectData.taskId);

            setSnackbar({
                open: true,
                message: '已确认生成，开始生成视频...',
                severity: 'success'
            });

            // 切换到生成状态标签页
            setDetailTab(1);
        } catch (err: any) {
            console.error('[Project] Confirm generation error:', err);
            setSnackbar({
                open: true,
                message: err.message || '确认生成失败',
                severity: 'error'
            });
        } finally {
            setConfirmingGeneration(false);
        }
    };

    const handleApplyAIOperations = (operations: any[]) => {
        setOrderedShots(prev => {
            let shots = [...prev];
            for (const op of operations) {
                if (op.type === 'update_shot' && op.shot_index != null) {
                    const i = op.shot_index;
                    if (shots[i]) shots[i] = { ...shots[i], ...op.changes };
                } else if (op.type === 'delete_shot' && op.shot_index != null) {
                    shots = shots.filter((_, i) => i !== op.shot_index);
                } else if (op.type === 'reorder_shots' && op.new_order) {
                    shots = op.new_order.map((i: number) => shots[i]).filter(Boolean);
                } else if (op.type === 'regenerate_shot' && op.shot_index != null) {
                    const i = op.shot_index;
                    if (shots[i]) shots[i] = { ...shots[i], status: 'pending', videoPath: undefined };
                }
            }
            const scriptOp = operations.find(o => o.type === 'update_script');
            if (scriptOp?.script && projectData) {
                setProjectData({ ...projectData, script: scriptOp.script });
            }
            return shots;
        });
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
                bgcolor: '#0d0d0d',
                color: 'white',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden'
            }}
        >
            {/* 1. Top: Header */}
            <Box sx={{
                height: HEADER_HEIGHT,
                borderBottom: '1px solid #333',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                px: 2,
                bgcolor: '#1c1c1c'
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
                {/* Left Sidebar wrapper — width controlled by ref during drag */}
                <Box ref={leftPanelRef} style={{ width: leftPanelWidth, flexShrink: 0, overflow: 'hidden', display: 'flex' }}>
                    <ShotList
                        orderedShots={orderedShots}
                        currentShotIndex={currentShotIndex}
                        activeTab={assetTab}
                        onTabChange={setAssetTab}
                        onShotSelect={setCurrentShotIndex}
                        width="100%"
                    />
                </Box>

                {/* Drag divider: left panel */}
                <Box
                    onMouseDown={makeDividerHandler(leftPanelWidth, leftPanelRef, setLeftPanelWidth, 'left', 180, 480)}
                    sx={{ width: 4, cursor: 'col-resize', bgcolor: '#252525', flexShrink: 0, '&:hover': { bgcolor: '#FF4081' }, transition: 'background-color 0.15s' }}
                />

                {/* Center: Video Player */}
                <AVCanvasPlayer
                    orderedShots={orderedShots}
                    status={projectData?.status}
                    onTimeUpdate={handleTimeUpdate}
                    onShotChange={handleShotChange}
                    onPlayStateChange={handlePlayStateChange}
                    externalSeekTime={externalSeekTime}
                />

                {/* Drag divider: right panel */}
                <Box
                    onMouseDown={makeDividerHandler(rightPanelWidth, rightPanelRef, setRightPanelWidth, 'right', 240, 700)}
                    sx={{ width: 4, cursor: 'col-resize', bgcolor: '#252525', flexShrink: 0, '&:hover': { bgcolor: '#FF4081' }, transition: 'background-color 0.15s' }}
                />

                {/* Right Sidebar wrapper */}
                <Box ref={rightPanelRef} style={{ width: rightPanelWidth, flexShrink: 0, overflow: 'hidden', display: 'flex' }}>
                    <ScriptPanel
                        projectData={projectData}
                        currentShot={currentShot}
                        currentShotIndex={currentShotIndex}
                        orderedShots={orderedShots}
                        activeTab={detailTab}
                        onTabChange={setDetailTab}
                        onEditShot={handleEditShot}
                        onDeleteShot={handleDeleteShot}
                        onConfirmGeneration={handleConfirmGeneration}
                        onApplyAIOperations={handleApplyAIOperations}
                        confirmingGeneration={confirmingGeneration}
                        width="100%"
                    />
                </Box>
            </Box>

            {/* 3. Timeline resize handle */}
            <Box
                onMouseDown={handleTimelineDividerMouseDown}
                sx={{
                    height: 4, flexShrink: 0,
                    cursor: 'ns-resize',
                    bgcolor: '#1e1e1e',
                    borderTop: '1px solid #333',
                    '&:hover': { bgcolor: '#FF4081' },
                    transition: 'background-color 0.15s',
                }}
            />

            {/* 4. Bottom: Timeline */}
            <MultiTrackTimeline
                orderedShots={orderedShots}
                currentShotIndex={currentShotIndex}
                globalTime={globalTime}
                totalDuration={totalDuration}
                onSeek={handleSeek}
                isPlaying={isPlaying}
                onShotDurationChange={handleShotDurationChange}
                height={timelineHeight}
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
