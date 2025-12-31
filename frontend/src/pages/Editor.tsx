import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
    Box,
    Typography,
    Container,
    Paper,
    Button,
    Grid,
    IconButton,
    Chip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Slider,
    useTheme,
    alpha,
    Stack,
    Tooltip,
    CircularProgress,
    LinearProgress,
    Switch,
    FormControlLabel,
    Snackbar,
    Alert,
    TextField,
} from '@mui/material';
import {
    ArrowBack as BackIcon,
    PlayArrow as PlayIcon,
    Pause as PauseIcon,
    SkipNext as NextIcon,
    SkipPrevious as PrevIcon,
    ArrowUpward as UpIcon,
    ArrowDownward as DownIcon,
    MovieFilter as TransitionIcon,
    MusicNote as MusicIcon,
    Merge as MergeIcon,
    Palette as FilterIcon,
    VolumeUp as VolumeIcon,
    Brightness6 as BrightnessIcon,
    Contrast as ContrastIcon,
    BlurOn as BlurIcon,
    InvertColors as SaturateIcon,
    AutoAwesome as VintageIcon,
    AcUnit as CoolIcon,
    WbSunny as WarmIcon,
    VolumeOff as MuteIcon,
    Replay as ReplayIcon,
    Edit as EditIcon,
    Delete as DeleteIcon,
    ContentCut as CutIcon,
    Save as SaveIcon,
    Undo as UndoIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import type { Shot, GeneratedVideo } from '../api/types';
import { editorApi } from '../api';
import { getFullUrl } from '../utils/url';
import TimelineFilmstrip from '../components/studio/TimelineFilmstrip';

interface ShotWithVideo extends Shot {
    videoData?: GeneratedVideo;
}

interface EditorData {
    taskId: string;
    topic?: string;
    style?: string;
    script?: string;
    shots: Shot[];
    totalDuration?: number;
    generatedVideos?: GeneratedVideo[];
    finalVideo?: string | null;
    status?: string;
}

// 滤镜配置
const FILTERS = [
    { id: 'brightness', name: '亮度', icon: <BrightnessIcon />, min: 0, max: 2, default: 1, cssProperty: 'brightness' },
    { id: 'contrast', name: '对比度', icon: <ContrastIcon />, min: 0, max: 2, default: 1, cssProperty: 'contrast' },
    { id: 'saturate', name: '饱和度', icon: <SaturateIcon />, min: 0, max: 2, default: 1, cssProperty: 'saturate' },
    { id: 'blur', name: '模糊', icon: <BlurIcon />, min: 0, max: 10, default: 0, cssProperty: 'blur', unit: 'px' },
];

// 预设滤镜
const PRESETS = [
    { id: 'vintage', name: '复古', icon: <VintageIcon />, filter: 'sepia(0.4) contrast(1.1) brightness(0.9)' },
    { id: 'cool', name: '冷色调', icon: <CoolIcon />, filter: 'saturate(1.2) hue-rotate(180deg) brightness(1.05)' },
    { id: 'warm', name: '暖色调', icon: <WarmIcon />, filter: 'sepia(0.3) saturate(1.3) brightness(1.05)' },
    { id: 'bw', name: '黑白', icon: <ContrastIcon />, filter: 'grayscale(1) contrast(1.2)' },
];

// 转场效果配置
const TRANSITIONS = [
    { id: 'fade', name: '淡入淡出', description: '平滑的淡入淡出效果' },
    { id: 'dissolve', name: '溶解', description: '两个画面逐渐融合' },
    { id: 'wipe', name: '擦除', description: '新画面从一侧擦入' },
    { id: 'slide', name: '滑动', description: '画面滑动切换' },
];

const EditorPage: React.FC = () => {
    const theme = useTheme();
    const location = useLocation();
    const navigate = useNavigate();
    const videoRef = useRef<HTMLVideoElement>(null);

    // 从路由state接收数据
    const taskData = location.state as EditorData | null;

    const [orderedShots, setOrderedShots] = useState<ShotWithVideo[]>([]);
    const [loading, setLoading] = useState(true);
    const [merging, setMerging] = useState(false);
    const [mergeProgress, setMergeProgress] = useState(0);

    // 预览状态
    const [currentShotIndex, setCurrentShotIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    
    // 【核心升级】全局时间轴引擎
    const [globalTime, setGlobalTime] = useState(0); // 全局播放时间（秒）
    const [totalDuration, setTotalDuration] = useState(0); // 真实总时长
    
    // ... existing states ...

    // Initialize shots and sync real duration
    useEffect(() => {
        if (taskData?.shots) {
            setLoading(true);
            
            // 1. 初步合并数据
            const initialShots = taskData.shots.map(shot => ({
                ...shot,
                videoData: taskData.generatedVideos?.find(v => v.sequence === shot.sequence),
            }));

            // 2. 【关键】异步获取所有视频的真实时长
            const syncDurations = async () => {
                const syncedShots = await Promise.all(initialShots.map(async (shot) => {
                    if (!shot.videoData?.videoPath) return shot;

                    return new Promise<ShotWithVideo>((resolve) => {
                        const video = document.createElement('video');
                        video.src = getFullUrl(shot.videoData!.videoPath);
                        video.preload = 'metadata';
                        
                        video.onloadedmetadata = () => {
                            const realDuration = video.duration;
                            if (realDuration && realDuration > 0) {
                                console.log(`[DurationSync] Shot ${shot.sequence}: ${realDuration.toFixed(2)}s (was ${shot.duration}s)`);
                                resolve({ ...shot, duration: realDuration });
                            } else {
                                console.warn(`[DurationSync] Shot ${shot.sequence}: Invalid duration ${realDuration}`);
                                resolve(shot);
                            }
                        };
                        
                        video.onerror = (e) => {
                            console.warn(`[DurationSync] Failed to load metadata for shot ${shot.sequence}`, e);
                            resolve(shot);
                        };

                        // 增加超时时间到 15秒，给大文件更多机会
                        setTimeout(() => {
                            // console.warn(`[DurationSync] Timeout for shot ${shot.sequence}`);
                            resolve(shot);
                        }, 15000);
                    });
                }));

                // 恢复之前的编辑状态（如果有）
                const savedState = taskData.taskId ? localStorage.getItem(getStorageKey(taskData.taskId)) : null;
                let finalShots = syncedShots;

                if (savedState) {
                    try {
                        const parsed = JSON.parse(savedState);
                        // ... restore other settings ...
                        if (parsed.filterSettings) setFilterSettings(parsed.filterSettings);
                        if (parsed.selectedPreset) setSelectedPreset(parsed.selectedPreset);
                        if (parsed.appliedFilter) setAppliedFilter(parsed.appliedFilter);
                        if (parsed.shotTransitions) setShotTransitions(parsed.shotTransitions);
                        if (parsed.appliedTransitions) setAppliedTransitions(parsed.appliedTransitions);
                        if (parsed.musicEnabled !== undefined) setMusicEnabled(parsed.musicEnabled);
                        if (parsed.musicVolume !== undefined) setMusicVolume(parsed.musicVolume);
                        if (parsed.musicFadeIn !== undefined) setMusicFadeIn(parsed.musicFadeIn);
                        if (parsed.musicFadeOut !== undefined) setMusicFadeOut(parsed.musicFadeOut);
                        if (parsed.appliedMusic !== undefined) setAppliedMusic(parsed.appliedMusic);

                        // 恢复顺序，但使用 sync 过的时长
                        if (parsed.shotOrder && parsed.shotOrder.length > 0) {
                            finalShots = parsed.shotOrder
                                .map((seq: number) => syncedShots.find(s => s.sequence === seq))
                                .filter(Boolean) as ShotWithVideo[];
                        }
                    } catch (e) {
                        console.error("State restore failed", e);
                    }
                }

                setOrderedShots(finalShots);
                // 计算真实的总时长
                const realTotal = finalShots.reduce((sum, s) => sum + s.duration, 0);
                setTotalDuration(realTotal);
                setLoading(false);
            };

            syncDurations();
        } else {
            setTimeout(() => navigate('/content'), 2000);
        }
    }, [taskData, navigate]);

    // Recalculate total duration whenever shots change (e.g. trimming)
    useEffect(() => {
        const total = orderedShots.reduce((sum, s) => sum + s.duration, 0);
        setTotalDuration(total);
    }, [orderedShots]);

    // Save state to localStorage whenever it changes (debounced)
    useEffect(() => {
        if (taskData?.taskId && !loading && orderedShots.length > 0) {
            const stateToSave = {
                filterSettings,
                selectedPreset,
                appliedFilter,
                shotTransitions,
                appliedTransitions,
                musicEnabled,
                musicVolume,
                musicFadeIn,
                musicFadeOut,
                appliedMusic,
                shotOrder: orderedShots.map(s => s.sequence),
                savedAt: new Date().toISOString()
            };
            localStorage.setItem(getStorageKey(taskData.taskId), JSON.stringify(stateToSave));
        }
    }, [taskData?.taskId, filterSettings, selectedPreset, appliedFilter, shotTransitions,
        appliedTransitions, musicEnabled, musicVolume, musicFadeIn, musicFadeOut,
        appliedMusic, orderedShots, loading]);

    // 监听 currentShotIndex 变化，如果在播放状态，则继续播放
    useEffect(() => {
        if (isPlaying && videoRef.current) {
            videoRef.current.play().catch(() => {});
        }
    }, [currentShotIndex]);

    // 视频播放控制
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
            
            // 计算当前 Shot 之前的总时长
            const prevDuration = orderedShots.slice(0, currentShotIndex).reduce((acc, s) => acc + s.duration, 0);
            const newGlobalTime = prevDuration + shotLocalTime;
            
            setGlobalTime(newGlobalTime);

            // 检查是否播放完当前 Shot (精度缓冲)
            if (currentShot && shotLocalTime >= currentShot.duration - 0.05) {
                if (currentShotIndex < orderedShots.length - 1) {
                    // 自动无缝切换到下一个 Shot
                    setCurrentShotIndex(prev => prev + 1);
                    // 时间重置为 0 (虽然后续 src 改变会自动重置，显式设置更稳妥)
                    // videoRef.current.currentTime = 0; 
                } else {
                    // 整个时间轴播放结束
                    setIsPlaying(false);
                }
            }
        }
    };

    const handleLoadedMetadata = () => {
        // 单个视频加载完元数据，不需要更新全局 duration (已经在初始化时 sync 了)
        // 但如果是在播放中切换过来，可能需要 seek 到正确位置（如果是 Seek 触发的切换）
        // 这里简化处理：如果在播放中，自然会从 0 开始播
    };

    const handleVideoEnded = () => {
        // 主要逻辑移到了 timeUpdate 中处理，这里作为兜底
        if (currentShotIndex < orderedShots.length - 1) {
            setCurrentShotIndex(currentShotIndex + 1);
        } else {
            setIsPlaying(false);
        }
    };

    const handleSeek = (_: Event, value: number | number[]) => {
        const seekTime = value as number;
        setGlobalTime(seekTime);
        
        let acc = 0;
        for (let i = 0; i < orderedShots.length; i++) {
            const shot = orderedShots[i];
            // 找到包含该时间的 shot
            if (seekTime >= acc && seekTime <= acc + shot.duration + 0.01) {
                if (currentShotIndex !== i) {
                    setCurrentShotIndex(i);
                    // 注意：切换 index 后，video src 会变，需要等待 loadedmetadata 才能 seek
                    // 这里我们设置一个标记或者利用 state 闭包，简单起见我们直接设置
                    // 实际应用中可能需要更复杂的流式加载处理
                }
                
                if (videoRef.current) {
                     // 如果是同一个视频，直接跳
                     if (currentShotIndex === i) {
                         videoRef.current.currentTime = seekTime - acc;
                     } else {
                         // 如果切换了视频，我们需要在下一次渲染（src更新后）再seek
                         // 这里通过副作用或者 autoPlay 暂时简化
                         // 改进：我们可以用一个 ref 存 pendingSeekTime
                     }
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

    const handlePrevShot = () => {
        if (currentShotIndex > 0) {
            setCurrentShotIndex(currentShotIndex - 1);
        }
    };

    const handleNextShot = () => {
        if (currentShotIndex < orderedShots.length - 1) {
            setCurrentShotIndex(currentShotIndex + 1);
        }
    };

    const handleShotSelect = (index: number) => {
        setCurrentShotIndex(index);
    };

    // 生成CSS滤镜字符串
    const getFilterStyle = () => {
        if (!previewFilter) return 'none';

        if (selectedPreset) {
            const preset = PRESETS.find(p => p.id === selectedPreset);
            return preset?.filter || 'none';
        }

        const filters = FILTERS.map(f => {
            const value = filterSettings[f.id] ?? f.default;
            if (f.unit) {
                return `${f.cssProperty}(${value}${f.unit})`;
            }
            return `${f.cssProperty}(${value})`;
        }).join(' ');

        return filters;
    };

    const handleMoveUp = (index: number) => {
        if (index === 0) return;
        const newOrder = [...orderedShots];
        [newOrder[index - 1], newOrder[index]] = [newOrder[index], newOrder[index - 1]];
        setOrderedShots(newOrder);
        if (currentShotIndex === index) setCurrentShotIndex(index - 1);
        else if (currentShotIndex === index - 1) setCurrentShotIndex(index);
    };

    const handleMoveDown = (index: number) => {
        if (index === orderedShots.length - 1) return;
        const newOrder = [...orderedShots];
        [newOrder[index], newOrder[index + 1]] = [newOrder[index + 1], newOrder[index]];
        setOrderedShots(newOrder);
        if (currentShotIndex === index) setCurrentShotIndex(index + 1);
        else if (currentShotIndex === index + 1) setCurrentShotIndex(index);
    };

    const handleAddTransition = (index: number) => {
        setSelectedTransitionIndex(index);
        if (shotTransitions[index]) {
            setTransitionType(shotTransitions[index].type);
            setTransitionDuration(shotTransitions[index].duration);
        }
        setTransitionDialogOpen(true);
    };

    // Shot editing functions
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

    const handleDuplicateShot = (index: number) => {
        const shot = orderedShots[index];
        const newShot = {
            ...shot,
            sequence: Math.max(...orderedShots.map(s => s.sequence)) + 1,
        };
        const newShots = [...orderedShots];
        newShots.splice(index + 1, 0, newShot);
        setOrderedShots(newShots);
        setSnackbar({
            open: true,
            message: `镜头 ${index + 1} 已复制`,
            severity: 'success'
        });
    };

    const handleResetEdits = () => {
        if (taskData?.taskId) {
            localStorage.removeItem(getStorageKey(taskData.taskId));
            // Reset all state
            setFilterSettings({ brightness: 1, contrast: 1, saturate: 1, blur: 0 });
            setSelectedPreset(null);
            setAppliedFilter(null);
            setShotTransitions({});
            setAppliedTransitions(0);
            setMusicEnabled(false);
            setMusicVolume(0.3);
            setMusicFadeIn(2);
            setMusicFadeOut(2);
            setAppliedMusic(false);
            // Reset shot order
            const merged = taskData.shots.map(shot => ({
                ...shot,
                videoData: taskData.generatedVideos?.find(v => v.sequence === shot.sequence),
            }));
            setOrderedShots(merged);
            setSnackbar({
                open: true,
                message: '已重置所有编辑',
                severity: 'info'
            });
        }
    };

    const handleConfirmTransition = () => {
        if (selectedTransitionIndex !== null) {
            setShotTransitions(prev => ({
                ...prev,
                [selectedTransitionIndex]: { type: transitionType, duration: transitionDuration }
            }));
            setAppliedTransitions(prev => prev + 1);
            setSnackbar({
                open: true,
                message: `转场效果已添加: ${TRANSITIONS.find(t => t.id === transitionType)?.name} (${transitionDuration}s)`,
                severity: 'success'
            });
        }
        setTransitionDialogOpen(false);
    };

    const handleApplyFilter = () => {
        const filterName = selectedPreset
            ? PRESETS.find(p => p.id === selectedPreset)?.name
            : '自定义滤镜';
        setAppliedFilter(filterName || null);
        setSnackbar({
            open: true,
            message: `滤镜已应用: ${filterName}`,
            severity: 'success'
        });
        setFilterDialogOpen(false);
    };

    const handleApplyMusic = () => {
        setAppliedMusic(musicEnabled);
        setSnackbar({
            open: true,
            message: musicEnabled ? `背景音乐已设置: 音量${Math.round(musicVolume * 100)}%` : '背景音乐已禁用',
            severity: 'success'
        });
        setMusicDialogOpen(false);
    };

    const handleFinalMerge = async () => {
        // Check if we have videos to merge
        const videosReady = orderedShots.filter(s => s.videoData?.status === 'success').length;
        if (videosReady === 0) {
            setSnackbar({
                open: true,
                message: '没有可合成的视频，请先生成视频',
                severity: 'warning'
            });
            return;
        }

        setMerging(true);
        setMergeProgress(0);

        try {
            // Create editor project with timeline data
            const timeline = {
                id: `timeline_${Date.now()}`,
                name: taskData?.topic || 'Merged Video',
                tracks: [{
                    id: `track_${Date.now()}`,
                    name: 'Main Track',
                    type: 'media' as const,
                    elements: orderedShots.map((shot, index) => ({
                        id: `element_${index}`,
                        name: `Shot ${index + 1}`,
                        type: 'media' as const,
                        media_id: shot.videoData?.videoPath || '',
                        duration: shot.duration,
                        start_time: orderedShots.slice(0, index).reduce((sum, s) => sum + s.duration, 0),
                    }))
                }]
            };

            // Show progress
            setMergeProgress(20);

            const project = await editorApi.createProject({
                name: taskData?.topic || 'Merged Video',
                description: `合成于 ${new Date().toLocaleString()}`,
                timeline
            });

            setMergeProgress(40);

            // Start render
            await editorApi.renderVideo({
                project_id: project.id,
                quality: 'high'
            });

            // Poll for completion
            const pollRender = async () => {
                const updated = await editorApi.getProject(project.id);
                setMergeProgress(40 + (updated.render_progress * 0.6));

                if (updated.status === 'completed') {
                    setMerging(false);
                    setMergeProgress(100);
                    setSnackbar({
                        open: true,
                        message: '视频合成完成！',
                        severity: 'success'
                    });
                    return;
                }

                if (updated.status === 'failed') {
                    throw new Error(updated.render_error || '渲染失败');
                }

                setTimeout(pollRender, 2000);
            };

            await pollRender();
        } catch (error: any) {
            console.error('Merge error:', error);
            setMerging(false);
            setSnackbar({
                open: true,
                message: `合成失败: ${error.message || '未知错误'}`,
                severity: 'error'
            });
        }
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    if (loading) {
        return (
            <Box sx={{
                minHeight: '100vh',
                background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
                pt: '80px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }}>
                <Box sx={{ textAlign: 'center' }}>
                    <CircularProgress size={60} />
                    <Typography variant="h6" color="text.secondary" sx={{ mt: 3 }}>
                        {taskData ? '加载编辑器...' : '未找到数据，正在返回...'}
                    </Typography>
                </Box>
            </Box>
        );
    }

    const currentShot = orderedShots[currentShotIndex];
    const totalDuration = orderedShots.reduce((sum, shot) => sum + shot.duration, 0);
    const completedCount = orderedShots.filter(s => s.videoData?.status === 'success').length;

    return (
        <Box sx={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
            pt: '80px',
            pb: 4,
            color: 'white'
        }}>
            <Container maxWidth="xl">
                {/* Header */}
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Box>
                        <Button
                            startIcon={<BackIcon />}
                            onClick={() => navigate('/content')}
                            sx={{ color: 'white', mb: 1 }}
                        >
                            返回Library
                        </Button>
                        <Typography variant="h4" fontWeight={700} sx={{
                            background: 'linear-gradient(45deg, #9c27b0 30%, #e91e63 90%)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                        }}>
                            视频后期编辑
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            {taskData?.topic || '项目'} • {orderedShots.length} 个镜头 • {totalDuration}秒
                        </Typography>
                        {/* Applied effects summary */}
                        <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                            {appliedFilter && (
                                <Chip
                                    icon={<FilterIcon />}
                                    label={appliedFilter}
                                    size="small"
                                    color="secondary"
                                    onDelete={() => {
                                        setAppliedFilter(null);
                                        setSelectedPreset(null);
                                        setFilterSettings({ brightness: 1, contrast: 1, saturate: 1, blur: 0 });
                                        setSnackbar({ open: true, message: '滤镜已移除', severity: 'info' });
                                    }}
                                />
                            )}
                            {appliedTransitions > 0 && (
                                <Chip
                                    icon={<TransitionIcon />}
                                    label={`${appliedTransitions} 个转场`}
                                    size="small"
                                    color="primary"
                                />
                            )}
                            {appliedMusic && (
                                <Chip
                                    icon={<MusicIcon />}
                                    label={`音乐 ${Math.round(musicVolume * 100)}%`}
                                    size="small"
                                    color="success"
                                    onDelete={() => {
                                        setAppliedMusic(false);
                                        setMusicEnabled(false);
                                        setSnackbar({ open: true, message: '背景音乐已移除', severity: 'info' });
                                    }}
                                />
                            )}
                        </Stack>
                    </Box>
                    <Stack direction="row" spacing={2}>
                        <Button
                            variant={appliedFilter ? "contained" : "outlined"}
                            startIcon={<FilterIcon />}
                            onClick={() => setFilterDialogOpen(true)}
                            sx={{
                                borderColor: alpha(theme.palette.common.white, 0.3),
                                color: 'white',
                                bgcolor: appliedFilter ? alpha(theme.palette.secondary.main, 0.3) : 'transparent'
                            }}
                        >
                            滤镜{appliedFilter ? ' ✓' : ''}
                        </Button>
                        <Button
                            variant={appliedMusic ? "contained" : "outlined"}
                            startIcon={<MusicIcon />}
                            onClick={() => setMusicDialogOpen(true)}
                            sx={{
                                borderColor: alpha(theme.palette.common.white, 0.3),
                                color: 'white',
                                bgcolor: appliedMusic ? alpha(theme.palette.success.main, 0.3) : 'transparent'
                            }}
                        >
                            音乐{appliedMusic ? ' ✓' : ''}
                        </Button>
                        <Button
                            variant="contained"
                            size="large"
                            startIcon={<MergeIcon />}
                            onClick={handleFinalMerge}
                            disabled={merging}
                            sx={{ background: 'linear-gradient(45deg, #9c27b0 30%, #e91e63 90%)' }}
                        >
                            {merging ? '合成中...' : '合成视频'}
                        </Button>
                        <Tooltip title="重置所有编辑">
                            <IconButton
                                onClick={handleResetEdits}
                                sx={{ color: 'text.secondary' }}
                            >
                                <UndoIcon />
                            </IconButton>
                        </Tooltip>
                    </Stack>
                </Box>

                {merging && (
                    <Paper sx={{ p: 2, mb: 3, bgcolor: alpha(theme.palette.background.paper, 0.1) }}>
                        <Typography variant="body2" gutterBottom>正在合成视频... {mergeProgress}%</Typography>
                        <LinearProgress variant="determinate" value={mergeProgress} />
                    </Paper>
                )}

                <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 160px)', gap: 3 }}>
                    {/* 上部：视频预览区 */}
                    <Box sx={{ flex: 1, minHeight: 0, display: 'flex', justifyContent: 'center' }}>
                        <Paper sx={{
                            width: '100%',
                            maxWidth: '1000px',
                            bgcolor: alpha(theme.palette.background.paper, 0.1),
                            backdropFilter: 'blur(10px)',
                            border: `1px solid ${alpha(theme.palette.common.white, 0.1)}`,
                            borderRadius: 2,
                            overflow: 'hidden',
                            display: 'flex',
                            flexDirection: 'column'
                        }}>
                            {/* 视频播放器 */}
                            <Box sx={{ flex: 1, position: 'relative', bgcolor: 'black', minHeight: 0 }}>
                                {currentShot?.videoData?.videoPath ? (
                                    <video
                                        ref={videoRef}
                                        src={getFullUrl(currentShot.videoData.videoPath)}
                                        style={{
                                            width: '100%',
                                            height: '100%',
                                            objectFit: 'contain',
                                            filter: getFilterStyle(),
                                        }}
                                        onTimeUpdate={handleTimeUpdate}
                                        onLoadedMetadata={handleLoadedMetadata}
                                        onEnded={handleVideoEnded}
                                        onPlay={() => setIsPlaying(true)}
                                        onPause={() => setIsPlaying(false)}
                                    />
                                ) : (
                                    <Box sx={{
                                        width: '100%',
                                        height: '100%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        flexDirection: 'column',
                                        gap: 2
                                    }}>
                                        <Typography variant="h6" color="text.secondary">
                                            镜头 #{currentShotIndex + 1}
                                        </Typography>
                                        <Typography color="text.secondary">
                                            {currentShot?.videoData?.status === 'generating' ? '视频生成中...' : '等待视频生成'}
                                        </Typography>
                                    </Box>
                                )}

                                {/* 当前镜头信息 */}
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

                                {/* 滤镜预览标签 */}
                                {previewFilter && (selectedPreset || Object.values(filterSettings).some((v, i) => v !== FILTERS[i]?.default)) && (
                                    <Chip
                                        icon={<FilterIcon />}
                                        label="滤镜预览"
                                        size="small"
                                        sx={{
                                            position: 'absolute',
                                            top: 16,
                                            right: 16,
                                            bgcolor: alpha(theme.palette.secondary.main, 0.9)
                                        }}
                                    />
                                )}
                            </Box>

                            {/* 播放控制栏 */}
                            <Box sx={{ p: 2 }}>
                                {/* 进度条 */}
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

                                {/* 控制按钮 */}
                                <Stack direction="row" justifyContent="space-between" alignItems="center">
                                    <Stack direction="row" spacing={1} alignItems="center">
                                        <Tooltip title="上一个镜头">
                                            <IconButton onClick={handlePrevShot} disabled={currentShotIndex === 0}>
                                                <PrevIcon />
                                            </IconButton>
                                        </Tooltip>
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
                                        <Tooltip title="下一个镜头">
                                            <IconButton onClick={handleNextShot} disabled={currentShotIndex === orderedShots.length - 1}>
                                                <NextIcon />
                                            </IconButton>
                                        </Tooltip>
                                        <Tooltip title="重播">
                                            <IconButton onClick={() => { if (videoRef.current) videoRef.current.currentTime = 0; }}>
                                                <ReplayIcon />
                                            </IconButton>
                                        </Tooltip>
                                    </Stack>

                                    <Stack direction="row" spacing={1} alignItems="center">
                                        <IconButton onClick={toggleMute}>
                                            {isMuted ? <MuteIcon /> : <VolumeIcon />}
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

                            {/* 当前镜头Prompt */}
                            <Box sx={{ p: 2, borderTop: `1px solid ${alpha(theme.palette.common.white, 0.1)}`, flexShrink: 0 }}>
                                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                                    Prompt:
                                </Typography>
                                <Typography variant="body2" noWrap>
                                    {currentShot?.prompt}
                                </Typography>
                            </Box>
                        </Paper>
                    </Box>

                    {/* 下部：镜头时间轴 */}
                    <Paper sx={{
                        height: 240,
                        flexShrink: 0,
                        bgcolor: alpha(theme.palette.background.paper, 0.1),
                        backdropFilter: 'blur(10px)',
                        border: `1px solid ${alpha(theme.palette.common.white, 0.1)}`,
                        borderRadius: 2,
                        display: 'flex',
                        flexDirection: 'column',
                        overflow: 'hidden'
                    }}>
    // Timeline State
    const [pxPerSec, setPxPerSec] = useState(40); // 默认缩放：1秒=40px
    const timelineRef = useRef<HTMLDivElement>(null);

    // ... existing code ...

    // 生成CSS滤镜字符串
    const getFilterStyle = () => {
        // ... existing code ...
    };

    // 计算点击时间轴的位置
    const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!timelineRef.current) return;
        const rect = timelineRef.current.getBoundingClientRect();
        const offsetX = e.clientX - rect.left + timelineRef.current.scrollLeft;
        const clickTime = Math.max(0, offsetX / pxPerSec);
        
        // 找到对应的 shot 并跳转
        if (videoRef.current) {
            // 这里我们需要计算全局时间对应的 shot
            let accumulated = 0;
            for (let i = 0; i < orderedShots.length; i++) {
                const shot = orderedShots[i];
                if (clickTime >= accumulated && clickTime < accumulated + shot.duration) {
                    setCurrentShotIndex(i);
                    // 视频播放器目前是播放单个片段，所以我们要把全局时间转换为片段内时间
                    const localTime = clickTime - accumulated;
                    videoRef.current.currentTime = localTime;
                    setCurrentTime(localTime);
                    break;
                }
                accumulated += shot.duration;
            }
        }
    };

    // ... existing code ...

                            {/* 下部：镜头时间轴 - 改为专业Timeline样式 */}
                            <Box sx={{ p: 1.5, borderBottom: `1px solid ${alpha(theme.palette.common.white, 0.1)}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center', bgcolor: '#1e1e1e' }}>
                                <Stack direction="row" spacing={2} alignItems="center">
                                    <Typography variant="subtitle1" fontWeight={700}>时间轴</Typography>
                                    <Stack direction="row" spacing={1} alignItems="center">
                                        <IconButton size="small" onClick={() => setPxPerSec(Math.max(10, pxPerSec - 10))}><Typography>-</Typography></IconButton>
                                        <Slider 
                                            value={pxPerSec} 
                                            min={10} max={200} 
                                            onChange={(_, v) => setPxPerSec(v as number)} 
                                            sx={{ width: 100 }} 
                                            size="small"
                                        />
                                        <IconButton size="small" onClick={() => setPxPerSec(Math.min(200, pxPerSec + 10))}><Typography>+</Typography></IconButton>
                                    </Stack>
                                </Stack>
                                <Typography variant="caption" color="text.secondary">
                                    总时长: {formatTime(totalDuration)}
                                </Typography>
                            </Box>

                            <Box 
                                ref={timelineRef}
                                sx={{ 
                                    flex: 1, 
                                    overflowX: 'auto', 
                                    overflowY: 'hidden',
                                    position: 'relative',
                                    bgcolor: '#121212',
                                    cursor: 'text', // 指示可以点击设定光标
                                    '&::-webkit-scrollbar': { height: 10 },
                                    '&::-webkit-scrollbar-thumb': { bgcolor: '#444', borderRadius: 5 }
                                }}
                                onClick={handleTimelineClick}
                            >
                                {/* 刻度尺 (Ruler) */}
                                <Box sx={{ height: 24, borderBottom: '1px solid #333', position: 'sticky', top: 0, bgcolor: '#121212', zIndex: 10, display: 'flex' }}>
                                    {Array.from({ length: Math.ceil(totalDuration) + 5 }).map((_, sec) => (
                                        <Box key={sec} sx={{ 
                                            width: pxPerSec, 
                                            height: '100%', 
                                            borderLeft: '1px solid #333', 
                                            position: 'relative',
                                            flexShrink: 0
                                        }}>
                                            <Typography variant="caption" color="#666" sx={{ position: 'absolute', left: 2, top: 0, fontSize: '0.6rem' }}>
                                                {formatTime(sec)}
                                            </Typography>
                                        </Box>
                                    ))}
                                </Box>

                                {/* 轨道区域 */}
                                <Box sx={{ p: 2, minWidth: totalDuration * pxPerSec + 200, display: 'flex', position: 'relative' }}>
                                    
                                    {/* 全局播放指针 (Global Playhead) */}
                                    <Box sx={{
                                        position: 'absolute',
                                        left: 16 + (globalTime * pxPerSec), // 16px is left padding
                                        top: 0, 
                                        bottom: 0,
                                        width: 2,
                                        bgcolor: '#FF4081',
                                        zIndex: 20,
                                        pointerEvents: 'none',
                                        transition: 'left 0.1s linear', // 平滑移动
                                        boxShadow: '0 0 8px rgba(255, 64, 129, 0.8)'
                                    }}>
                                        <Box sx={{
                                            position: 'absolute', top: -4, left: -6,
                                            width: 14, height: 14,
                                            bgcolor: '#FF4081', 
                                            transform: 'rotate(45deg)',
                                            borderRadius: '2px 2px 2px 8px'
                                        }}/>
                                    </Box>

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
                                                // 移除右边距，实现无缝衔接
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
                                                    borderRadius: 0, // 直角，像剪辑软件
                                                    overflow: 'hidden',
                                                    cursor: 'pointer',
                                                    display: 'flex',
                                                    flexDirection: 'column',
                                                    position: 'relative',
                                                    '&:hover': { border: '1px solid #888' }
                                                }}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    // 点击 Shot 时跳转到该 Shot 的起始位置
                                                    const startOffset = orderedShots.slice(0, index).reduce((acc, s) => acc + s.duration, 0);
                                                    handleSeek(e as any, startOffset);
                                                }}
                                            >
                                                {/* 缩略图条 - 真实的视频胶卷 */}
                                                <Box sx={{ height: 40, bgcolor: '#000', display: 'flex', overflow: 'hidden', opacity: 0.9 }}>
                                                    {shot.videoData?.videoPath ? (
                                                        <TimelineFilmstrip 
                                                            videoUrl={getFullUrl(shot.videoData.videoPath)} 
                                                            duration={shot.duration}
                                                            height={40}
                                                            pxPerSec={pxPerSec}
                                                        />
                                                    ) : (
                                                        // 没有视频时，使用分镜图作为重复背景
                                                        Array.from({ length: Math.ceil(shot.duration) }).map((_, i) => (
                                                            <Box key={i} sx={{ 
                                                                width: pxPerSec, 
                                                                height: '100%', 
                                                                borderRight: '1px solid rgba(255,255,255,0.1)',
                                                                backgroundImage: shot.imagePath ? `url(${getFullUrl(shot.imagePath)})` : 'none',
                                                                backgroundSize: 'cover',
                                                                backgroundPosition: 'center'
                                                            }} />
                                                        ))
                                                    )}
                                                </Box>

                                                {/* 信息区 */}
                                                <Box sx={{ flex: 1, p: 0.5, px: 1 }}>
                                                    <Typography variant="caption" display="block" noWrap fontWeight={700} color="white">
                                                        Shot {index + 1}
                                                    </Typography>
                                                    <Typography variant="caption" color="text.secondary" noWrap sx={{ fontSize: '0.65rem' }}>
                                                        {shot.duration.toFixed(1)}s • {shot.prompt.substring(0, 15)}...
                                                    </Typography>
                                                </Box>
                                                
                                                {/* 剪辑把手 (Handles) - 仅选中时显示 */}
                                                {isSelected && (
                                                    <>
                                                        {/* 右把手 - 调整时长 */}
                                                        <Box 
                                                            sx={{
                                                                position: 'absolute', right: 0, top: 0, bottom: 0, width: 10,
                                                                cursor: 'ew-resize',
                                                                bgcolor: 'rgba(255,255,255,0.2)',
                                                                '&:hover': { bgcolor: '#FF4081' },
                                                                zIndex: 10,
                                                                display: 'flex', alignItems: 'center', justifyContent: 'center'
                                                            }}
                                                            onMouseDown={(e) => {
                                                                e.stopPropagation();
                                                                handleEditShot(index); // 暂时先调用原来的弹窗，后续改为拖拽逻辑
                                                            }}
                                                        >
                                                            <Box sx={{ width: 2, height: 12, bgcolor: 'white', borderRadius: 1 }} />
                                                        </Box>
                                                    </>
                                                )}
                                            </Paper>
                                        </motion.div>
                                    )})}
                                </Box>
                            </Box>
                        </Paper>
                </Box>
            </Container>
        </Box>
    );
};

                {/* Transition Dialog */}
                <Dialog open={transitionDialogOpen} onClose={() => setTransitionDialogOpen(false)} maxWidth="sm" fullWidth
                    PaperProps={{ sx: { bgcolor: '#1e293b', backgroundImage: 'none' } }}>
                    <DialogTitle>添加转场效果</DialogTitle>
                    <DialogContent>
                        <Stack spacing={3} sx={{ mt: 2 }}>
                            <FormControl fullWidth>
                                <InputLabel>转场类型</InputLabel>
                                <Select value={transitionType} onChange={(e) => setTransitionType(e.target.value)} label="转场类型">
                                    {TRANSITIONS.map(t => (
                                        <MenuItem key={t.id} value={t.id}>
                                            <Box>
                                                <Typography>{t.name}</Typography>
                                                <Typography variant="caption" color="text.secondary">{t.description}</Typography>
                                            </Box>
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                            <Box>
                                <Typography gutterBottom>转场时长: {transitionDuration}秒</Typography>
                                <Slider
                                    value={transitionDuration}
                                    onChange={(_, value) => setTransitionDuration(value as number)}
                                    min={0.5}
                                    max={3}
                                    step={0.5}
                                    marks
                                    valueLabelDisplay="auto"
                                />
                            </Box>
                        </Stack>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setTransitionDialogOpen(false)}>取消</Button>
                        <Button variant="contained" onClick={handleConfirmTransition}>确认</Button>
                    </DialogActions>
                </Dialog>

                {/* Filter Dialog */}
                <Dialog open={filterDialogOpen} onClose={() => setFilterDialogOpen(false)} maxWidth="md" fullWidth
                    PaperProps={{ sx: { bgcolor: '#1e293b', backgroundImage: 'none' } }}>
                    <DialogTitle>
                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                            <span>视频滤镜效果</span>
                            <FormControlLabel
                                control={<Switch checked={previewFilter} onChange={(e) => setPreviewFilter(e.target.checked)} />}
                                label="实时预览"
                            />
                        </Stack>
                    </DialogTitle>
                    <DialogContent>
                        <Grid container spacing={3} sx={{ mt: 1 }}>
                            <Grid item xs={12} md={6}>
                                <Typography variant="subtitle2" gutterBottom>基础调整</Typography>
                                {FILTERS.map(filter => (
                                    <Box key={filter.id} sx={{ mb: 2 }}>
                                        <Stack direction="row" alignItems="center" spacing={1}>
                                            {filter.icon}
                                            <Typography>{filter.name}</Typography>
                                            <Typography variant="caption" color="text.secondary">
                                                ({filterSettings[filter.id]?.toFixed(1) || filter.default})
                                            </Typography>
                                        </Stack>
                                        <Slider
                                            value={filterSettings[filter.id] ?? filter.default}
                                            onChange={(_, value) => {
                                                setFilterSettings(prev => ({ ...prev, [filter.id]: value as number }));
                                                setSelectedPreset(null);
                                            }}
                                            min={filter.min}
                                            max={filter.max}
                                            step={0.1}
                                            valueLabelDisplay="auto"
                                        />
                                    </Box>
                                ))}
                            </Grid>
                            <Grid item xs={12} md={6}>
                                <Typography variant="subtitle2" gutterBottom>预设滤镜</Typography>
                                <Stack spacing={1}>
                                    {PRESETS.map(preset => (
                                        <Paper
                                            key={preset.id}
                                            sx={{
                                                p: 2,
                                                cursor: 'pointer',
                                                bgcolor: selectedPreset === preset.id ? 'primary.dark' : alpha(theme.palette.common.white, 0.05),
                                                '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.2) }
                                            }}
                                            onClick={() => setSelectedPreset(selectedPreset === preset.id ? null : preset.id)}
                                        >
                                            <Stack direction="row" alignItems="center" spacing={2}>
                                                {preset.icon}
                                                <Typography>{preset.name}</Typography>
                                            </Stack>
                                        </Paper>
                                    ))}
                                </Stack>
                            </Grid>
                        </Grid>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => {
                            setFilterSettings({ brightness: 1, contrast: 1, saturate: 1, blur: 0 });
                            setSelectedPreset(null);
                        }}>
                            重置
                        </Button>
                        <Button onClick={() => setFilterDialogOpen(false)}>取消</Button>
                        <Button variant="contained" onClick={handleApplyFilter}>应用滤镜</Button>
                    </DialogActions>
                </Dialog>

                {/* Music Dialog */}
                <Dialog open={musicDialogOpen} onClose={() => setMusicDialogOpen(false)} maxWidth="sm" fullWidth
                    PaperProps={{ sx: { bgcolor: '#1e293b', backgroundImage: 'none' } }}>
                    <DialogTitle>背景音乐设置</DialogTitle>
                    <DialogContent>
                        <Stack spacing={3} sx={{ mt: 2 }}>
                            <FormControlLabel
                                control={<Switch checked={musicEnabled} onChange={(e) => setMusicEnabled(e.target.checked)} />}
                                label="启用背景音乐"
                            />
                            <Box>
                                <Stack direction="row" alignItems="center" spacing={1}>
                                    <VolumeIcon />
                                    <Typography>音量: {Math.round(musicVolume * 100)}%</Typography>
                                </Stack>
                                <Slider
                                    value={musicVolume}
                                    onChange={(_, value) => setMusicVolume(value as number)}
                                    min={0}
                                    max={1}
                                    step={0.1}
                                    disabled={!musicEnabled}
                                />
                            </Box>
                            <Box>
                                <Typography gutterBottom>淡入时长: {musicFadeIn}秒</Typography>
                                <Slider
                                    value={musicFadeIn}
                                    onChange={(_, value) => setMusicFadeIn(value as number)}
                                    min={0}
                                    max={5}
                                    step={0.5}
                                    disabled={!musicEnabled}
                                />
                            </Box>
                            <Box>
                                <Typography gutterBottom>淡出时长: {musicFadeOut}秒</Typography>
                                <Slider
                                    value={musicFadeOut}
                                    onChange={(_, value) => setMusicFadeOut(value as number)}
                                    min={0}
                                    max={5}
                                    step={0.5}
                                    disabled={!musicEnabled}
                                />
                            </Box>
                            <Button variant="outlined" startIcon={<MusicIcon />} disabled={!musicEnabled}>
                                选择音乐文件
                            </Button>
                        </Stack>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setMusicDialogOpen(false)}>取消</Button>
                        <Button variant="contained" onClick={handleApplyMusic}>应用设置</Button>
                    </DialogActions>
                </Dialog>

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
                            <span>编辑镜头 {editingShotIndex !== null ? editingShotIndex + 1 : ''}</span>
                        </Stack>
                    </DialogTitle>
                    <DialogContent>
                        <Stack spacing={3} sx={{ mt: 2 }}>
                            {/* Duration */}
                            <Box>
                                <Typography gutterBottom>
                                    时长: {editingDuration}秒
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
                                    placeholder="描述这个镜头的内容..."
                                    sx={{
                                        '& .MuiOutlinedInput-root': {
                                            bgcolor: alpha(theme.palette.background.paper, 0.3),
                                        }
                                    }}
                                />
                            </Box>

                            {/* Quick actions */}
                            <Box>
                                <Typography gutterBottom>快捷操作:</Typography>
                                <Stack direction="row" spacing={1}>
                                    <Button
                                        variant="outlined"
                                        size="small"
                                        startIcon={<CutIcon />}
                                        onClick={() => {
                                            if (editingShotIndex !== null) {
                                                handleDuplicateShot(editingShotIndex);
                                                setEditingShotIndex(null);
                                            }
                                        }}
                                    >
                                        复制镜头
                                    </Button>
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
                                        删除镜头
                                    </Button>
                                </Stack>
                            </Box>
                        </Stack>
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setEditingShotIndex(null)}>取消</Button>
                        <Button
                            variant="contained"
                            startIcon={<SaveIcon />}
                            onClick={handleSaveShot}
                        >
                            保存
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
            </Container>
        </Box>
    );
};

export default EditorPage;
