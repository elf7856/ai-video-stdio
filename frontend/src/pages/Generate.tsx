import React, { useState, useRef, useEffect, useMemo } from 'react';
import {
    Box,
    Typography,
    Container,
    Paper,
    TextField,
    Button,
    Grid,
    IconButton,
    Chip,
    CircularProgress,
    useTheme,
    alpha,
    Tooltip,
    Stack,
    LinearProgress,
    Switch,
    FormControlLabel,
    Select,
    MenuItem,
    Slider,
    Divider,
    Tabs,
    Tab,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    InputAdornment
} from '@mui/material';
import {
    AutoAwesome as MagicIcon,
    MovieCreation as MovieIcon,
    ContentCopy as CopyIcon,
    Error as ErrorIcon,
    Business as BusinessIcon,
    Computer as TechIcon,
    LocalCafe as LifeIcon,
    TheaterComedy as FunIcon,
    Palette as ArtIcon,
    PhotoCamera as DocIcon,
    Edit as EditIcon,
    ExpandMore as ExpandMoreIcon,
    Refresh as RefreshIcon,
    ArrowForward as ArrowForwardIcon,
    Terminal as TerminalIcon,
    AutoStories as ComicIcon,
    Link as LinkIcon,
    Image as ImageIcon,
    VideoLibrary as VideoIcon,
    SmartToy as ProducerIcon,
    Close as CloseIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { scriptsApi, videosApi } from '../api';
import { getFullUrl } from '../utils/url';
import type {
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    NarrationVoice,
    Shot,
    VideoGenerationTask,
    SourceMaterial
} from '../api/types';
import ShotEditor from '../components/ShotEditor';
import StoryboardEditor from '../components/StoryboardEditor';
import BiblePanel from '../components/generate/BiblePanel';
import SourceReviewPanel from '../components/SourceReviewPanel';

// Style Configuration
const STYLE_CONFIG: Record<string, { icon: React.ReactNode; gradient: string; color: string }> = {
    '专业': { icon: <BusinessIcon />, gradient: 'linear-gradient(135deg, #2c3e50 0%, #3498db 100%)', color: '#3498db' },
    '科技': { icon: <TechIcon />, gradient: 'linear-gradient(135deg, #000428 0%, #004e92 100%)', color: '#004e92' },
    '生活': { icon: <LifeIcon />, gradient: 'linear-gradient(135deg, #56ab2f 0%, #a8e063 100%)', color: '#56ab2f' },
    '娱乐': { icon: <FunIcon />, gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', color: '#fa709a' },
    '艺术': { icon: <ArtIcon />, gradient: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%)', color: '#ff9a9e' },
    '纪录片': { icon: <DocIcon />, gradient: 'linear-gradient(135deg, #434343 0%, #000000 100%)', color: '#888' },
    '漫剧': { icon: <ComicIcon />, gradient: 'linear-gradient(135deg, #f953c6 0%, #b91d73 100%)', color: '#f953c6' },
};

// Full style prompts sent to the AI — richer than the display label
const STYLE_PROMPTS: Record<string, string> = {
    '专业': 'cinematic corporate style, clean and authoritative composition, neutral cool tones, high-end premium feel, sharp professional lighting, suitable for brand films and business presentations',
    '科技': 'cyberpunk tech aesthetic, dark background with neon blue and cyan glow, digital futurism, HUD overlays, precision industrial feel, glowing circuitry, suitable for tech products and AI themes',
    '生活': 'warm lifestyle aesthetic, soft natural window light, golden hour tones, authentic everyday moments, cozy and approachable atmosphere, real human stories, suitable for lifestyle vlogs',
    '娱乐': 'vibrant entertainment style, highly saturated colors, energetic dynamic pacing, trendy and youthful, pop culture aesthetic, bold typography energy, suitable for variety shows and short video',
    '艺术': 'avant-garde art film aesthetic, bold and unconventional composition, experimental cinematography, strong visual impact, rich color expression, fine art sensibility, suitable for creative and gallery work',
    '纪录片': 'documentary realism style, natural handheld camera feel, authentic available light, deep narrative storytelling, journalistic objectivity, human and social themes, raw and honest',
    '漫剧': 'anime manga style, vivid high-contrast colors, dynamic speed lines and motion blur, expressive exaggerated character movement, 2D cel-shading aesthetic, comic panel energy, suitable for animated and creative short films',
};

const URL_PATTERN = /https?:\/\/[^\s<>"{}|\\^`[\]]+/g;

const extractUrls = (value: string): string[] => {
    const matches = value.match(URL_PATTERN) || [];
    return Array.from(new Set(matches.map((url) => url.replace(/[).,;!?，。；！？]+$/, ''))));
};

const getUrlHost = (url: string): string => {
    try {
        return new URL(url).hostname;
    } catch {
        return url;
    }
};

const sourceTypeLabel: Record<string, string> = {
    webpage: 'Web',
    video: 'Video',
    image: 'Image',
    unknown: 'Source'
};

const GeneratePage: React.FC = () => {
    const theme = useTheme();
    const navigate = useNavigate();
    const videoRef = useRef<HTMLVideoElement>(null);

    // --- Resizable sidebar ---
    const [sidebarWidth, setSidebarWidth] = useState(520);
    const isResizing = useRef(false);
    const startX = useRef(0);
    const startWidth = useRef(0);

    const onResizeStart = (e: React.MouseEvent) => {
        isResizing.current = true;
        startX.current = e.clientX;
        startWidth.current = sidebarWidth;
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
    };

    useEffect(() => {
        const onMove = (e: MouseEvent) => {
            if (!isResizing.current) return;
            const delta = e.clientX - startX.current;
            setSidebarWidth(Math.min(900, Math.max(320, startWidth.current + delta)));
        };
        const onUp = () => {
            isResizing.current = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };
        window.addEventListener('mousemove', onMove);
        window.addEventListener('mouseup', onUp);
        return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
    }, []);

    // --- State ---
    const [hasStarted, setHasStarted] = useState(false); // Controls Initial vs Studio view
    const [activeTab, setActiveTab] = useState(0); // 0: Create, 1: Script, 2: Storyboard, 3: Logs
    const [topic, setTopic] = useState('');
    const [style, setStyle] = useState('专业');
    const [targetDuration, setTargetDuration] = useState(60);
    const [shotCount, setShotCount] = useState(6);
    const [estimatedDuration, setEstimatedDuration] = useState<number | null>(null);
    const [additionalRequirements, setAdditionalRequirements] = useState('');

    // Generation mode
    const [generationMode, setGenerationMode] = useState<'autopilot' | 'manual'>('manual');
    const [showStoryboardEditor, setShowStoryboardEditor] = useState(false);

    const [loading, setLoading] = useState(false);
    const [scriptResult, setScriptResult] = useState<ScriptGenerateResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const [videoGenerating, setVideoGenerating] = useState(false);
    const [videoTask, setVideoTask] = useState<VideoGenerationTask | null>(null);
    const [sourceMaterial, setSourceMaterial] = useState<SourceMaterial | null>(null);
    const [producerStatus, setProducerStatus] = useState<'idle' | 'analyzing' | 'ready' | 'needs_clarification' | 'error'>('idle');
    const [producerMessage, setProducerMessage] = useState('Describe the outcome you want. Sources are detected automatically.');
    const [producerSuggestions, setProducerSuggestions] = useState<string[]>([]);

    const [editableShots, setEditableShots] = useState<Shot[]>([]);
    const [isEditingShots, setIsEditingShots] = useState(false);

    // Settings
    const [enableNarration, setEnableNarration] = useState(false);
    const [narrationVoice, setNarrationVoice] = useState<NarrationVoice>('chinese_female');
    const [narrationSpeed, setNarrationSpeed] = useState(1.0);
    const [pacingStrategy, setPacingStrategy] = useState('balanced');

    // Dev / Production mode — determined at build time via VITE_DEV_MODE env var
    // .env.development  → VITE_DEV_MODE=true  (dev controls visible)
    // .env.production   → VITE_DEV_MODE=false (clean production UI)
    // Test deployment:  VITE_DEV_MODE=true npm run build
    const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true';

    // Reset state on mount to ensure we see the search view
    useEffect(() => {
        setHasStarted(false);
    }, []);

    const detectedUrls = useMemo(() => extractUrls(topic), [topic]);

    useEffect(() => {
        if (sourceMaterial && !detectedUrls.includes(sourceMaterial.url)) {
            setSourceMaterial(null);
            setProducerStatus('idle');
            setProducerSuggestions([]);
            setProducerMessage('Describe the outcome you want. Sources are detected automatically.');
        }
    }, [detectedUrls, sourceMaterial]);

    // --- Logic ---

    const saveToLocalStorage = (response: ScriptGenerateResponse, taskData?: VideoGenerationTask) => {
        try {
            const savedScript = {
                id: Date.now().toString(),
                topic,
                style,
                targetDuration,
                shotCount,
                script: response.script,
                shots: response.shots,
                totalDuration: response.totalDuration,
                createdAt: new Date().toISOString(),
                videoTask: taskData,
                sourceMaterial
            };
            const existing = localStorage.getItem('savedScripts');
            const scripts = existing ? JSON.parse(existing) : [];
            const existingIndex = scripts.findIndex((s: any) => s.topic === topic && s.style === style);
            if (existingIndex >= 0) {
                scripts[existingIndex] = savedScript;
            } else {
                scripts.unshift(savedScript);
            }
            localStorage.setItem('savedScripts', JSON.stringify(scripts.slice(0, 50)));
        } catch (e) { console.error(e); }
    };

    const handleGenerateScript = async () => {
        if (!topic.trim()) return;
        setHasStarted(true); // Switch to Studio Mode
        setLoading(true);
        setError(null);
        setScriptResult(null);
        setVideoTask(null);
        try {
            const request: ScriptGenerateRequest = {
                topic: topic.trim(),
                style: STYLE_PROMPTS[style] ?? style,
                targetDuration,
                shotCount,
                additionalRequirements: additionalRequirements.trim() || undefined
            };
            const response = await scriptsApi.generateScript(request);
            setScriptResult(response);
            setEstimatedDuration(response.totalDuration);
            setActiveTab(1); // Switch to Script tab
            saveToLocalStorage(response);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || err.message || 'Generation failed');
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateVideo = async () => {
        if (!topic.trim()) return;
        console.log("Starting video generation...");
        setLoading(true);
        setError(null);
        setProducerStatus('analyzing');
        setProducerMessage(detectedUrls.length > 0 ? 'Analyzing source and intent...' : 'Understanding creative intent...');
        setProducerSuggestions([]);

        try {
            console.log("Creating task from intent...");
            const response = await videosApi.createFromIntent({
                userInput: topic.trim(),
                style: STYLE_PROMPTS[style] ?? style,
                targetDuration,
                shotCount,
                generationMode,
                additionalRequirements: additionalRequirements.trim() || undefined,
                enableNarration,
                narrationVoice,
                narrationSpeed,
                pacingStrategy
            });

            if (response.sourceMaterial) {
                setSourceMaterial(response.sourceMaterial);
            }
            setProducerMessage(response.message || '');
            setProducerSuggestions(response.suggestions || []);

            if (response.action === 'needs_clarification') {
                setHasStarted(true);
                setActiveTab(0);
                setProducerStatus('needs_clarification');
                setLoading(false);
                return;
            }

            const taskId = response.taskId;
            if (!taskId) {
                throw new Error('No task id returned from intent generation');
            }

            setProducerStatus('ready');
            console.log("Task created:", taskId);

            // 🆕 立即跳转到 Project 页面，在那里实时显示生成进度
            navigate(`/project/${taskId}`, {
                state: {
                    taskId,
                    topic: topic.trim(),
                    style,
                    generationMode,
                    sourceMaterial: response.sourceMaterial || sourceMaterial,
                    isGenerating: true  // 标记正在生成
                }
            });

        } catch (err: any) {
            console.error("Generation error:", err);
            setError(err.response?.data?.detail || err.message || 'Video generation failed');
            setProducerStatus('error');
            setProducerMessage(err.response?.data?.detail || err.message || 'Generation failed');
            setLoading(false);
        }
    };

    // 处理分镜图确认
    const handleStoryboardConfirm = async (script: string, shots: Shot[]) => {
        if (!videoTask) return;

        setShowStoryboardEditor(false);
        setVideoGenerating(true);
        setActiveTab(4); // 切换到Logs标签
        setError(null);

        try {
            await videosApi.confirmAndGenerate(
                videoTask.taskId,
                script,
                shots
            );

            // 继续轮询
            const finalTask = await videosApi.pollTaskStatus(videoTask.taskId, (task) => {
                setVideoTask(task);
            }, 600000);

            // 完成后跳转
            if (finalTask.status === 'completed') {
                navigate('/project/' + videoTask.taskId, { state: finalTask });
            }
        } catch (err: any) {
            console.error("Video generation error:", err);
            setError(err.response?.data?.detail || err.message || 'Video generation failed');
        } finally {
            setVideoGenerating(false);
        }
    };

    // 处理取消编辑
    const handleStoryboardCancel = () => {
        setShowStoryboardEditor(false);
        setHasStarted(false);
        setActiveTab(0);
    };

    // 处理重新生成单个镜头
    const handleRegenerateShot = async (shotIndex: number, newPrompt?: string) => {
        if (!videoTask || !editableShots[shotIndex]) return;

        try {
            // 调用重新生成API
            await videosApi.regenerateShot(
                videoTask.taskId,
                editableShots[shotIndex].sequence,
                newPrompt || editableShots[shotIndex].prompt,
                editableShots[shotIndex].duration
            );

            // 重新加载任务数据
            const updatedTask = await videosApi.getTaskStatus(videoTask.taskId);
            setVideoTask(updatedTask);
            if (updatedTask.shots) {
                setEditableShots([...updatedTask.shots]);
            }
        } catch (error) {
            console.error('Regenerate shot failed:', error);
            throw error;
        }
    };

    const handleConfirmAndGenerate = async () => {
        if (!videoTask || !scriptResult) return;

        setVideoGenerating(true);
        setIsEditingShots(false);
        setError(null);
        setActiveTab(4); // Auto-switch to Logs

        try {
            await videosApi.confirmAndGenerate(
                videoTask.taskId,
                scriptResult.script,
                editableShots
            );

            await videosApi.pollTaskStatus(videoTask.taskId, (task) => {
                setVideoTask(task);
                if (task.finalVideo && scriptResult) {
                    saveToLocalStorage(scriptResult, task);
                }
            }, 600000);

        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || err.message || 'Video generation failed');
        } finally {
            setVideoGenerating(false);
        }
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    // --- Shared Components ---

    const CompactStyleCard = ({ name, active, onClick }: { name: string, active: boolean, onClick: () => void }) => {
        const config = STYLE_CONFIG[name] || { icon: <MovieIcon />, gradient: 'grey', color: 'grey' };
        return (
            <Tooltip title={name}>
                <Paper
                    component={motion.div}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={onClick}
                    sx={{
                        width: '100%',
                        aspectRatio: '1',
                        cursor: 'pointer',
                        background: active ? config.gradient : alpha(theme.palette.background.paper, 0.2),
                        border: `1px solid ${active ? 'transparent' : alpha(theme.palette.common.white, 0.1)}`,
                        borderRadius: 2,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        position: 'relative',
                        transition: 'all 0.2s',
                        boxShadow: active ? `0 0 15px ${alpha(config.color, 0.5)}` : 'none',
                    }}
                >
                    <Box sx={{ fontSize: '1.5rem' }}>{config.icon}</Box>
                    {active && (
                        <Box sx={{
                            position: 'absolute', bottom: -20, left: '50%', transform: 'translateX(-50%)',
                            whiteSpace: 'nowrap'
                        }}>
                            <Typography variant="caption" sx={{ fontSize: '0.7rem', color: config.color, fontWeight: 'bold' }}>
                                {name}
                            </Typography>
                        </Box>
                    )}
                </Paper>
            </Tooltip>
        );
    };

    const getSourceIcon = (type?: string) => {
        if (type === 'image') return <ImageIcon fontSize="small" />;
        if (type === 'video') return <VideoIcon fontSize="small" />;
        return <LinkIcon fontSize="small" />;
    };

    const removeSourceUrl = (url: string) => {
        setTopic((prev) => prev.replace(url, ' ').replace(/\s+/g, ' ').trim());
        setSourceMaterial(null);
        setProducerStatus('idle');
        setProducerSuggestions([]);
        setProducerMessage('Describe the outcome you want. Sources are detected automatically.');
    };

    const renderSourceChips = () => {
        const urls = sourceMaterial ? [sourceMaterial.url] : detectedUrls;
        if (urls.length === 0) return null;

        return (
            <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ mt: 2, mb: hasStarted ? 3 : 0, justifyContent: hasStarted ? 'flex-start' : 'center' }}>
                {urls.map((url) => (
                    <Chip
                        key={url}
                        icon={sourceMaterial?.url === url ? getSourceIcon(sourceMaterial.type) : <LinkIcon fontSize="small" />}
                        label={sourceMaterial?.url === url
                            ? `${sourceTypeLabel[sourceMaterial.type] || 'Source'}: ${sourceMaterial.title || sourceMaterial.domain || url}`
                            : `Link: ${getUrlHost(url)}`}
                        onDelete={sourceMaterial?.url === url ? () => removeSourceUrl(url) : undefined}
                        deleteIcon={<CloseIcon />}
                        sx={{
                            maxWidth: hasStarted ? '100%' : 520,
                            bgcolor: 'rgba(255,255,255,0.06)',
                            color: '#ddd',
                            border: '1px solid rgba(255,255,255,0.1)',
                            '& .MuiChip-label': {
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                            }
                        }}
                    />
                ))}
            </Stack>
        );
    };

    const appendSuggestion = (suggestion: string) => {
        setTopic((prev) => `${prev.trim()} ${suggestion}`.trim());
        setProducerStatus('ready');
        setProducerMessage('Intent updated. Ready to generate.');
        setProducerSuggestions([]);
    };

    const renderProducerPanel = () => (
        <Paper
            square
            elevation={0}
            sx={{
                width: 340,
                flexShrink: 0,
                height: '100%',
                bgcolor: '#0f0f0f',
                borderLeft: '1px solid #222',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden'
            }}
        >
            <Box sx={{ p: 2.5, borderBottom: '1px solid #222' }}>
                <Stack direction="row" alignItems="center" spacing={1}>
                    <ProducerIcon sx={{ color: '#4facfe' }} />
                    <Typography variant="subtitle2" fontWeight={700} color="white">AI Producer</Typography>
                </Stack>
                {producerStatus === 'analyzing' && <LinearProgress sx={{ mt: 2, bgcolor: '#222', '& .MuiLinearProgress-bar': { bgcolor: '#4facfe' } }} />}
            </Box>

            <Box sx={{ p: 2.5, overflowY: 'auto', flex: 1 }}>
                <Stack spacing={2}>
                    <Paper sx={{ p: 2, bgcolor: '#171717', border: '1px solid #282828', borderRadius: 2 }}>
                        <Typography variant="caption" color="#666" fontWeight={700} sx={{ letterSpacing: 1, display: 'block', mb: 1 }}>
                            STATUS
                        </Typography>
                        <Typography variant="body2" color={producerStatus === 'error' ? '#ff5252' : '#ddd'} sx={{ lineHeight: 1.6 }}>
                            {producerMessage}
                        </Typography>
                    </Paper>

                    {sourceMaterial && <SourceReviewPanel sourceMaterial={sourceMaterial} />}

                    {!sourceMaterial && detectedUrls.length > 0 && (
                        <Paper sx={{ p: 2, bgcolor: '#171717', border: '1px solid #282828', borderRadius: 2 }}>
                            <Typography variant="caption" color="#666" fontWeight={700} sx={{ letterSpacing: 1, display: 'block', mb: 1 }}>
                                DETECTED LINK
                            </Typography>
                            {renderSourceChips()}
                        </Paper>
                    )}

                    {producerSuggestions.length > 0 && (
                        <Stack spacing={1}>
                            {producerSuggestions.map((suggestion) => (
                                <Button
                                    key={suggestion}
                                    variant="outlined"
                                    size="small"
                                    onClick={() => appendSuggestion(suggestion)}
                                    sx={{
                                        justifyContent: 'flex-start',
                                        borderColor: '#333',
                                        color: '#ddd',
                                        textTransform: 'none',
                                        '&:hover': { borderColor: '#4facfe', bgcolor: 'rgba(79,172,254,0.08)' }
                                    }}
                                >
                                    {suggestion}
                                </Button>
                            ))}
                        </Stack>
                    )}
                </Stack>
            </Box>
        </Paper>
    );

    // --- RENDER: INITIAL SEARCH VIEW ---
    if (!hasStarted) {
        return (
            <Box sx={{
                height: 'calc(100vh - 64px)',
                background: 'linear-gradient(180deg, #111318 0%, #0b0d11 100%)',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden',
                position: 'relative',
                '&::before': {
                    content: '""',
                    position: 'absolute',
                    inset: 0,
                    backgroundImage: 'linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)',
                    backgroundSize: '56px 56px',
                    maskImage: 'linear-gradient(180deg, rgba(0,0,0,0.75), rgba(0,0,0,0.15))',
                    pointerEvents: 'none'
                }
            }}>
                <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1, textAlign: 'center', px: { xs: 2, md: 4 } }}>
                    <Box sx={{ maxWidth: 920, mx: 'auto' }}>
                        <Box sx={{ mb: 4 }}>
                             <Typography variant="h2" fontWeight={700} sx={{
                                 color: '#f8fafc',
                                 letterSpacing: 0,
                                 mb: 1.5
                             }}>
                                Orenix AI
                             </Typography>
                             <Typography variant="h6" color="#9aa4b2" fontWeight={400}>
                                 Next Generation Generative Video Platform
                             </Typography>
                        </Box>

                        <Paper
                            elevation={0}
                            sx={{
                                p: 1,
                                display: 'flex',
                                alignItems: 'center',
                                width: '100%',
                                borderRadius: 2,
                                bgcolor: 'rgba(18, 22, 29, 0.92)',
                                border: '1px solid rgba(148, 163, 184, 0.22)',
                                boxShadow: '0 24px 70px rgba(0, 0, 0, 0.34)',
                                transition: 'all 0.3s',
                                '&:hover': {
                                    borderColor: 'rgba(148, 163, 184, 0.36)',
                                    bgcolor: 'rgba(21, 25, 33, 0.96)'
                                },
                                '&:focus-within': {
                                    borderColor: '#38bdf8',
                                    boxShadow: '0 24px 70px rgba(0, 0, 0, 0.38), 0 0 0 3px rgba(56, 189, 248, 0.14)'
                                }
                            }}
                        >
                            <InputAdornment position="start" sx={{ pl: 1.5 }}>
                                <MagicIcon sx={{ color: '#38bdf8' }} />
                            </InputAdornment>
                            <TextField
                                fullWidth
                                variant="standard"
                                placeholder="A cinematic trailer for a sci-fi movie on Mars..."
                                value={topic}
                                onChange={(e) => setTopic(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && topic.trim() && !loading) handleGenerateVideo();
                                }}
                                InputProps={{
                                    disableUnderline: true,
                                    sx: {
                                        px: { xs: 1.5, sm: 2 },
                                        py: 1.75,
                                        fontSize: { xs: '1rem', sm: '1.1rem' },
                                        color: '#f8fafc',
                                        '&::placeholder': { color: '#64748b', opacity: 1 }
                                    }
                                }}
                            />
                            <Divider sx={{ height: 28, m: 0.5, borderColor: 'rgba(148, 163, 184, 0.2)' }} orientation="vertical" />
                            <IconButton 
                                color="primary" 
                                sx={{
                                    width: 48,
                                    height: 48,
                                    mr: 0.25,
                                    bgcolor: '#38bdf8',
                                    color: '#071018',
                                    borderRadius: 1.5,
                                    '&:hover': { bgcolor: '#7dd3fc' },
                                    '&.Mui-disabled': {
                                        bgcolor: 'rgba(148, 163, 184, 0.12)',
                                        color: 'rgba(148, 163, 184, 0.36)'
                                    }
                                }}
                                onClick={handleGenerateVideo}
                                disabled={!topic.trim() || loading}
                            >
                                {loading ? <CircularProgress size={22} sx={{ color: '#071018' }} /> : <ArrowForwardIcon />}
                            </IconButton>
                        </Paper>

                        {loading && (
                            <Paper
                                elevation={0}
                                sx={{
                                    mt: 2,
                                    mx: 'auto',
                                    maxWidth: 520,
                                    p: 1.5,
                                    bgcolor: 'rgba(18, 22, 29, 0.86)',
                                    border: '1px solid rgba(56, 189, 248, 0.22)',
                                    borderRadius: 2
                                }}
                            >
                                <Typography variant="body2" color="#b8c3cf" sx={{ mb: 1 }}>
                                    {producerMessage || 'Creating generation task...'}
                                </Typography>
                                <LinearProgress sx={{ bgcolor: 'rgba(148, 163, 184, 0.16)', '& .MuiLinearProgress-bar': { bgcolor: '#38bdf8' } }} />
                            </Paper>
                        )}

                        {renderSourceChips()}

                        {/* Styles Row */}
                        <Box sx={{ mt: 5 }}>
                            <Typography variant="caption" color="#7d8794" fontWeight={700} sx={{ letterSpacing: 0, mb: 2, display: 'block' }}>
                                CHOOSE A STYLE
                            </Typography>
                            <Box sx={{ 
                                display: 'flex', 
                                gap: 1.25,
                                justifyContent: 'center',
                                flexWrap: 'wrap'
                            }}>
                                {Object.keys(STYLE_CONFIG).map((s) => {
                                    const config = STYLE_CONFIG[s];
                                    const isActive = style === s;
                                    return (
                                        <Chip
                                            key={s}
                                            icon={<span style={{ fontSize: '1.2rem', display: 'flex' }}>{config.icon}</span>}
                                            label={s}
                                            clickable
                                            onClick={() => setStyle(s)}
                                            sx={{
                                                bgcolor: isActive ? 'rgba(56, 189, 248, 0.14)' : 'rgba(18, 22, 29, 0.84)',
                                                color: isActive ? '#e0f7ff' : '#9aa4b2',
                                                border: `1px solid ${isActive ? '#38bdf8' : 'rgba(148, 163, 184, 0.18)'}`,
                                                borderRadius: 1.5,
                                                px: 1.25,
                                                py: 2.25,
                                                fontSize: '0.9rem',
                                                transition: 'all 0.2s',
                                                boxShadow: isActive ? '0 0 0 3px rgba(56, 189, 248, 0.08)' : 'none',
                                                '& .MuiChip-icon': { color: isActive ? '#38bdf8' : '#9aa4b2' },
                                                '&:hover': {
                                                    bgcolor: 'rgba(56, 189, 248, 0.1)',
                                                    borderColor: isActive ? '#38bdf8' : 'rgba(148, 163, 184, 0.34)',
                                                    transform: 'translateY(-2px)'
                                                }
                                            }}
                                        />
                                    );
                                })}
                            </Box>
                        </Box>

                        {/* Specifications Card — DEV only */}
                        {DEV_MODE && (
                        <Paper sx={{ mt: 4, p: 3, bgcolor: 'rgba(18, 22, 29, 0.82)', borderRadius: 2, border: '1px solid rgba(148, 163, 184, 0.18)', boxShadow: '0 18px 50px rgba(0,0,0,0.24)' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
                                <TerminalIcon sx={{ fontSize: '1rem', color: '#f59e0b' }} />
                                <Typography variant="caption" color="#f59e0b" fontWeight={700} sx={{ letterSpacing: 0 }}>
                                    DEV CONTROLS
                                </Typography>
                            </Box>
                            <Grid container spacing={4} alignItems="center">
                                <Grid item xs={12} md={6}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="body2" color="#9aa4b2" fontWeight={700}>DURATION</Typography>
                                        <Typography variant="body2" color="#38bdf8" fontWeight={700}>{targetDuration}s</Typography>
                                    </Box>
                                    <Slider
                                        value={targetDuration}
                                        onChange={(_, v) => setTargetDuration(v as number)}
                                        min={10} max={300} step={5}
                                        sx={{ color: '#38bdf8' }}
                                    />
                                </Grid>
                                <Grid item xs={12} md={6}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="body2" color="#9aa4b2" fontWeight={700}>SHOTS</Typography>
                                        <Typography variant="body2" color="#38bdf8" fontWeight={700}>{shotCount}</Typography>
                                    </Box>
                                    <Slider
                                        value={shotCount}
                                        onChange={(_, v) => setShotCount(v as number)}
                                        min={3} max={20} step={1}
                                        sx={{ color: '#38bdf8' }}
                                    />
                                </Grid>
                            </Grid>
                        </Paper>
                        )}

                        {/* 生成模式选择 — DEV only */}
                        {DEV_MODE && (
                        <Paper sx={{
                            p: 3,
                            mt: 3,
                            background: 'rgba(18, 22, 29, 0.82)',
                            border: '1px solid rgba(148, 163, 184, 0.18)',
                            borderRadius: 2,
                            boxShadow: '0 18px 50px rgba(0,0,0,0.24)'
                        }}>
                            <Typography variant="subtitle1" fontWeight={600} gutterBottom sx={{ color: 'white', mb: 2 }}>
                                生成模式
                            </Typography>
                            <Grid container spacing={2}>
                                {/* 人工确认模式 */}
                                <Grid item xs={12} sm={6}>
                                    <Paper
                                        onClick={() => setGenerationMode('manual')}
                                        sx={{
                                            p: 3,
                                            cursor: 'pointer',
                                            border: `1px solid ${generationMode === 'manual' ? '#38bdf8' : 'rgba(148, 163, 184, 0.16)'}`,
                                            bgcolor: generationMode === 'manual' ? 'rgba(56, 189, 248, 0.12)' : 'rgba(11, 13, 17, 0.58)',
                                            borderRadius: 2,
                                            transition: 'all 0.3s',
                                            '&:hover': {
                                                borderColor: '#38bdf8',
                                                bgcolor: 'rgba(56, 189, 248, 0.1)'
                                            }
                                        }}
                                    >
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                            <EditIcon sx={{ mr: 1, color: '#38bdf8' }} />
                                            <Typography variant="h6" fontWeight={600} sx={{ color: 'white' }}>
                                                人工确认模式
                                            </Typography>
                                        </Box>
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                            生成分镜图后可编辑、重新生成，确认后才生成视频
                                        </Typography>
                                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                            <Chip label="精细控制" size="small" sx={{ bgcolor: 'rgba(56, 189, 248, 0.16)', color: '#bae6fd' }} />
                                            <Chip label="可编辑" size="small" sx={{ bgcolor: 'rgba(56, 189, 248, 0.16)', color: '#bae6fd' }} />
                                            <Chip label="成本优化" size="small" sx={{ bgcolor: 'rgba(56, 189, 248, 0.16)', color: '#bae6fd' }} />
                                        </Box>
                                    </Paper>
                                </Grid>

                                {/* 托管模式 */}
                                <Grid item xs={12} sm={6}>
                                    <Paper
                                        onClick={() => setGenerationMode('autopilot')}
                                        sx={{
                                            p: 3,
                                            cursor: 'pointer',
                                            border: `1px solid ${generationMode === 'autopilot' ? '#38bdf8' : 'rgba(148, 163, 184, 0.16)'}`,
                                            bgcolor: generationMode === 'autopilot' ? 'rgba(56, 189, 248, 0.12)' : 'rgba(11, 13, 17, 0.58)',
                                            borderRadius: 2,
                                            transition: 'all 0.3s',
                                            '&:hover': {
                                                borderColor: '#38bdf8',
                                                bgcolor: 'rgba(56, 189, 248, 0.1)'
                                            }
                                        }}
                                    >
                                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                            <MagicIcon sx={{ mr: 1, color: '#38bdf8' }} />
                                            <Typography variant="h6" fontWeight={600} sx={{ color: 'white' }}>
                                                托管模式
                                            </Typography>
                                        </Box>
                                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                            一键生成，全自动完成所有步骤，无需人工干预
                                        </Typography>
                                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                            <Chip label="快速" size="small" sx={{ bgcolor: 'rgba(56, 189, 248, 0.16)', color: '#bae6fd' }} />
                                            <Chip label="全自动" size="small" sx={{ bgcolor: 'rgba(56, 189, 248, 0.16)', color: '#bae6fd' }} />
                                            <Chip label="省心" size="small" sx={{ bgcolor: 'rgba(56, 189, 248, 0.16)', color: '#bae6fd' }} />
                                        </Box>
                                    </Paper>
                                </Grid>
                            </Grid>
                        </Paper>
                        )}

                        <Stack direction="row" spacing={2} justifyContent="center" sx={{ mt: 4 }}>
                            <Button 
                                variant="contained" 
                                size="large"
                                onClick={handleGenerateVideo}
                                disabled={!topic.trim() || loading}
                                startIcon={loading ? <CircularProgress size={18} sx={{ color: '#071018' }} /> : <MagicIcon />}
                                sx={{
                                    borderRadius: 2,
                                    px: 4,
                                    py: 1.5,
                                    bgcolor: '#38bdf8',
                                    color: '#071018',
                                    fontWeight: 700,
                                    boxShadow: '0 12px 30px rgba(56, 189, 248, 0.24)',
                                    '&:hover': { bgcolor: '#7dd3fc', boxShadow: '0 16px 38px rgba(56, 189, 248, 0.3)' },
                                    '&.Mui-disabled': {
                                        bgcolor: 'rgba(148, 163, 184, 0.12)',
                                        color: 'rgba(148, 163, 184, 0.42)'
                                    }
                                }}
                            >
                                {loading ? 'Creating Task...' : 'Generate Video'}
                            </Button>
                            <Button 
                                variant="text" 
                                onClick={() => setHasStarted(true)}
                                sx={{ color: '#8792a0', '&:hover': { color: 'white', bgcolor: 'rgba(148, 163, 184, 0.08)' } }}
                            >
                                Skip to Studio
                            </Button>
                            <Button 
                                variant="text" 
                                onClick={() => {
                                    const saved = localStorage.getItem('savedScripts');
                                    if (saved) {
                                        const scripts = JSON.parse(saved);
                                        if (scripts.length > 0) {
                                            const last = scripts[0];
                                            setTopic(last.topic);
                                            setStyle(last.style);
                                            if (last.targetDuration) setTargetDuration(last.targetDuration);
                                            if (last.shotCount) setShotCount(last.shotCount);
                                            setScriptResult({
                                                success: true,
                                                script: last.script,
                                                shots: last.shots,
                                                totalDuration: last.totalDuration
                                            });
                                            if (last.videoTask) setVideoTask(last.videoTask);
                                            if (last.sourceMaterial) setSourceMaterial(last.sourceMaterial);
                                            setHasStarted(true);
                                            setActiveTab(1);
                                            setEditableShots(last.shots);
                                            setIsEditingShots(true);
                                        }
                                    }
                                }}
                                sx={{ color: '#8792a0', '&:hover': { color: 'white', bgcolor: 'rgba(148, 163, 184, 0.08)' } }}
                            >
                                History
                            </Button>
                        </Stack>

                    </Box>
                </Container>
            </Box>
        );
    }

    // --- RENDER: STUDIO MODE ---
    return (
        <Box sx={{
            height: 'calc(100vh - 64px)', // Deduct navbar height
            background: '#0a0a0a',
            color: '#e0e0e0',
            display: 'flex',
            overflow: 'hidden'
        }}>
            {/* LEFT SIDEBAR: CREATIVE CONSOLE */}
            <Paper
                style={{ width: sidebarWidth, flexShrink: 0 }}
                sx={{
                    height: '100%',
                    background: '#111111',
                    borderRight: '1px solid #222',
                    display: 'flex',
                    flexDirection: 'column',
                    zIndex: 10,
                }} square elevation={0}>
                
                {/* Tabs */}
                <Box sx={{ borderBottom: '1px solid #222' }}>
                    <Tabs 
                        value={activeTab} 
                        onChange={(_, v) => setActiveTab(v)}
                        variant="fullWidth"
                        sx={{
                            '& .MuiTab-root': { color: '#666', minHeight: 48 },
                            '& .Mui-selected': { color: '#fff' },
                            '& .MuiTabs-indicator': { backgroundColor: '#FF4081' }
                        }}
                    >
                        <Tab label="Create" />
                        <Tab label="Script" disabled={!scriptResult} />
                        <Tab label="Director" disabled={!videoTask?.bible} />
                        <Tab label="Storyboard" disabled={!showStoryboardEditor} />
                        <Tab label="Settings" />
                        <Tab icon={<TerminalIcon fontSize="small" />} label="Logs" disabled={!videoTask} />
                    </Tabs>
                </Box>

                {/* Content Area */}
                <Box sx={{ flex: 1, overflowY: 'auto', p: 3 }}>
                    <AnimatePresence mode="wait">
                        {activeTab === 0 && (
                            <motion.div
                                key="create"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                transition={{ duration: 0.2 }}
                            >
                                <Typography variant="caption" color="#666" fontWeight={700} sx={{ letterSpacing: 1, mb: 1, display: 'block' }}>
                                    TOPIC & VISION
                                </Typography>
                                <TextField
                                    fullWidth
                                    multiline
                                    minRows={4}
                                    placeholder="What do you want to create today? (e.g. 'A futuristic city tour...')"
                                    value={topic}
                                    onChange={(e) => setTopic(e.target.value)}
                                    variant="outlined"
                                    sx={{
                                        mb: 3,
                                        '& .MuiOutlinedInput-root': {
                                            bgcolor: '#1a1a1a',
                                            color: 'white',
                                            borderRadius: 2,
                                            '& fieldset': { borderColor: '#333' },
                                            '&:hover fieldset': { borderColor: '#555' },
                                            '&.Mui-focused fieldset': { borderColor: '#FF4081' }
                                        }
                                    }}
                                />

                                {renderSourceChips()}

                                {/* ... (Rest of sidebar) ... */}
                                <Typography variant="caption" color="#666" fontWeight={700} sx={{ letterSpacing: 1, mb: 2, display: 'block' }}>
                                    STYLE
                                </Typography>
                                <Box sx={{ 
                                    display: 'grid', 
                                    gridTemplateColumns: 'repeat(5, 1fr)', 
                                    gap: 2,
                                    mb: 4
                                }}>
                                    {Object.keys(STYLE_CONFIG).map((s) => (
                                        <CompactStyleCard 
                                            key={s} 
                                            name={s} 
                                            active={style === s} 
                                            onClick={() => setStyle(s)} 
                                        />
                                    ))}
                                </Box>

                                <Typography variant="caption" color="#666" fontWeight={700} sx={{ letterSpacing: 1, mb: 2, display: 'block' }}>
                                    SPECIFICATIONS
                                </Typography>
                                <Paper sx={{ p: 2, bgcolor: '#1a1a1a', borderRadius: 2, border: '1px solid #333', mb: 3 }}>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="caption" color="#888" display="block" mb={0.5}>Duration ({targetDuration}s)</Typography>
                                        <Slider
                                            value={targetDuration}
                                            onChange={(_, v) => setTargetDuration(v as number)}
                                            min={10} max={300} step={5}
                                            sx={{ color: '#FF4081' }}
                                        />
                                    </Box>
                                    <Box>
                                        <Typography variant="caption" color="#888" display="block" mb={0.5}>Shot Count ({shotCount})</Typography>
                                        <Slider
                                            value={shotCount}
                                            onChange={(_, v) => setShotCount(v as number)}
                                            min={3} max={20} step={1}
                                            sx={{ color: '#4facfe' }}
                                        />
                                    </Box>
                                </Paper>

                                <Accordion sx={{ bgcolor: 'transparent', boxShadow: 'none', border: '1px solid #222', borderRadius: 2, mb: 3, '&:before': { display: 'none' } }}>
                                    <AccordionSummary expandIcon={<ExpandMoreIcon sx={{ color: '#666' }} />}>
                                        <Typography variant="body2" color="#888">Advanced Requirements</Typography>
                                    </AccordionSummary>
                                    <AccordionDetails>
                                        <TextField
                                            fullWidth
                                            size="small"
                                            placeholder="Specific details, tone, keywords..."
                                            value={additionalRequirements}
                                            onChange={(e) => setAdditionalRequirements(e.target.value)}
                                            variant="outlined"
                                            sx={{
                                                '& .MuiOutlinedInput-root': {
                                                    bgcolor: '#1a1a1a',
                                                    color: 'white',
                                                    '& fieldset': { borderColor: '#333' }
                                                }
                                            }}
                                        />
                                    </AccordionDetails>
                                </Accordion>

                                {/* Action Buttons */}
                                <Stack spacing={2} sx={{ mt: 4 }}>
                                    <Button
                                        fullWidth
                                        variant="contained"
                                        size="large"
                                        onClick={handleGenerateVideo}
                                        disabled={loading || videoGenerating || !topic.trim()}
                                        sx={{
                                            bgcolor: '#FF4081',
                                            color: 'white',
                                            py: 1.5,
                                            fontWeight: 700,
                                            '&:hover': { bgcolor: '#F50057' },
                                            '&:disabled': { bgcolor: '#333', color: '#666' }
                                        }}
                                    >
                                        {videoGenerating ? 'Directing AI...' : 'Generate Video'}
                                    </Button>
                                    <Button
                                        fullWidth
                                        variant="outlined"
                                        onClick={handleGenerateScript}
                                        disabled={loading || videoGenerating || !topic.trim()}
                                        sx={{
                                            borderColor: '#333',
                                            color: '#888',
                                            '&:hover': { borderColor: '#666', color: 'white', bgcolor: 'transparent' }
                                        }}
                                    >
                                        Generate Script Only
                                    </Button>
                                </Stack>

                                {error && (
                                    <Paper sx={{ mt: 3, p: 2, bgcolor: 'rgba(211, 47, 47, 0.1)', color: '#ff5252', border: '1px solid rgba(211, 47, 47, 0.3)', display: 'flex', gap: 1 }}>
                                        <ErrorIcon fontSize="small" />
                                        <Typography variant="caption">{error}</Typography>
                                    </Paper>
                                )}
                            </motion.div>
                        )}

                        {activeTab === 1 && scriptResult && (
                            <motion.div
                                key="script"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                transition={{ duration: 0.2 }}
                            >
                                <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                                    <Typography variant="h6" fontSize="1rem" fontWeight={700}>Script</Typography>
                                    <IconButton size="small" onClick={() => copyToClipboard(scriptResult.script)} sx={{ color: '#666' }}>
                                        <CopyIcon fontSize="small" />
                                    </IconButton>
                                </Stack>
                                <Paper sx={{ p: 2, bgcolor: '#1a1a1a', borderRadius: 2, border: '1px solid #333', minHeight: 300 }}>
                                    <Typography variant="body2" color="#ccc" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, fontFamily: 'monospace' }}>
                                        {scriptResult.script}
                                    </Typography>
                                </Paper>
                            </motion.div>
                        )}

                        {/* Director Tab — DirectorAgent 产出的全局蓝图 */}
                        {activeTab === 2 && videoTask?.bible && (
                            <motion.div
                                key="director"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                transition={{ duration: 0.2 }}
                            >
                                <BiblePanel bible={videoTask.bible} />
                            </motion.div>
                        )}

                        {activeTab === 2 && !videoTask?.bible && (
                            <Box sx={{ textAlign: 'center', py: 10 }}>
                                <MovieIcon sx={{ fontSize: 80, color: '#333', mb: 2 }} />
                                <Typography variant="h6" color="text.secondary">
                                    导演蓝图将在脚本生成后显示
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                    含角色参考图、场景参考图、镜头转场标注
                                </Typography>
                            </Box>
                        )}

                        {/* Storyboard Tab */}
                        {activeTab === 3 && showStoryboardEditor && videoTask && (
                            <motion.div
                                key="storyboard"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                transition={{ duration: 0.2 }}
                            >
                                <StoryboardEditor
                                    script={videoTask.script || ''}
                                    shots={videoTask.shots || []}
                                    onConfirm={handleStoryboardConfirm}
                                    onCancel={handleStoryboardCancel}
                                    onRegenerateShot={handleRegenerateShot}
                                />
                            </motion.div>
                        )}

                        {/* Storyboard Tab - Empty State */}
                        {activeTab === 3 && !showStoryboardEditor && (
                            <Box sx={{ textAlign: 'center', py: 10 }}>
                                <MovieIcon sx={{ fontSize: 80, color: '#333', mb: 2 }} />
                                <Typography variant="h6" color="text.secondary">
                                    分镜图编辑器将在脚本和分镜图生成后显示
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                    在人工确认模式下，生成分镜图后会自动显示编辑器
                                </Typography>
                            </Box>
                        )}

                        {activeTab === 4 && (
                            <motion.div
                                key="settings"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                transition={{ duration: 0.2 }}
                            >
                                <Typography variant="caption" color="#666" fontWeight={700} sx={{ letterSpacing: 1, mb: 2, display: 'block' }}>
                                    VOICEOVER & AUDIO
                                </Typography>
                                
                                <Paper sx={{ p: 2, bgcolor: '#1a1a1a', borderRadius: 2, border: '1px solid #333', mb: 3 }}>
                                    <FormControlLabel
                                        control={
                                            <Switch
                                                checked={enableNarration}
                                                onChange={(e) => setEnableNarration(e.target.checked)}
                                                sx={{ '& .MuiSwitch-track': { bgcolor: '#555' } }}
                                            />
                                        }
                                        label={<Typography variant="body2">Enable AI Narration</Typography>}
                                    />

                                    {enableNarration && (
                                        <Stack spacing={2} sx={{ mt: 2 }}>
                                            <Box>
                                                <Typography variant="caption" color="#888" display="block" mb={0.5}>Voice</Typography>
                                                <Select
                                                    fullWidth
                                                    size="small"
                                                    value={narrationVoice}
                                                    onChange={(e) => setNarrationVoice(e.target.value as NarrationVoice)}
                                                    sx={{ bgcolor: '#0f0f0f', color: 'white', '& .MuiOutlinedInput-notchedOutline': { borderColor: '#333' } }}
                                                >
                                                    <MenuItem value="chinese_female">Chinese Female</MenuItem>
                                                    <MenuItem value="chinese_male">Chinese Male</MenuItem>
                                                    <MenuItem value="english_female">English Female</MenuItem>
                                                    <MenuItem value="english_male">English Male</MenuItem>
                                                </Select>
                                            </Box>
                                            <Box>
                                                <Typography variant="caption" color="#888" display="block" mb={0.5}>Speed ({narrationSpeed}x)</Typography>
                                                <Slider
                                                    value={narrationSpeed}
                                                    onChange={(_, v) => setNarrationSpeed(v as number)}
                                                    min={0.5} max={2.0} step={0.1}
                                                    sx={{ color: '#FF4081' }}
                                                />
                                            </Box>
                                        </Stack>
                                    )}
                                </Paper>

                                <Typography variant="caption" color="#666" fontWeight={700} sx={{ letterSpacing: 1, mb: 2, display: 'block' }}>
                                    PACING
                                </Typography>
                                <Paper sx={{ p: 2, bgcolor: '#1a1a1a', borderRadius: 2, border: '1px solid #333' }}>
                                     <Select
                                        fullWidth
                                        size="small"
                                        value={pacingStrategy}
                                        onChange={(e) => setPacingStrategy(e.target.value)}
                                        sx={{ bgcolor: '#0f0f0f', color: 'white', '& .MuiOutlinedInput-notchedOutline': { borderColor: '#333' } }}
                                    >
                                        <MenuItem value="balanced">Balanced</MenuItem>
                                        <MenuItem value="dynamic">Dynamic (Fast Cuts)</MenuItem>
                                        <MenuItem value="crescendo">Crescendo</MenuItem>
                                        <MenuItem value="slow_paced">Slow & Cinematic</MenuItem>
                                    </Select>
                                </Paper>
                            </motion.div>
                        )}

                        {activeTab === 5 && videoTask && (
                            <motion.div
                                key="logs"
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                transition={{ duration: 0.2 }}
                            >
                                <Typography variant="caption" color="#666" fontWeight={700} sx={{ letterSpacing: 1, mb: 2, display: 'block' }}>
                                    EXECUTION LOGS
                                </Typography>
                                <Paper sx={{ 
                                    p: 2, 
                                    bgcolor: '#0a0a0a', 
                                    borderRadius: 2, 
                                    border: '1px solid #333',
                                    fontFamily: 'monospace',
                                    fontSize: '0.85rem',
                                    maxHeight: '600px',
                                    overflowY: 'auto'
                                }}>
                                    {videoTask.logs && videoTask.logs.length > 0 ? (
                                        <Stack spacing={1}>
                                            {videoTask.logs.map((log, index) => (
                                                <Box key={index} sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
                                                    <Typography variant="caption" color="#666" sx={{ minWidth: 60, fontFamily: 'monospace' }}>
                                                        {log.timestamp}
                                                    </Typography>
                                                    <Typography sx={{ 
                                                        color: log.level === 'error' ? '#ff5252' : 
                                                               log.level === 'success' ? '#69f0ae' : 
                                                               log.level === 'warning' ? '#ffd740' : '#e0e0e0',
                                                        fontFamily: 'monospace',
                                                        wordBreak: 'break-word'
                                                    }}>
                                                        {log.level === 'success' && '✅ '}
                                                        {log.level === 'error' && '❌ '}
                                                        {log.level === 'warning' && '⚠️ '}
                                                        {log.message}
                                                    </Typography>
                                                </Box>
                                            ))}
                                            <div id="logs-end" />
                                        </Stack>
                                    ) : (
                                        <Typography color="#666" fontStyle="italic">Waiting for logs...</Typography>
                                    )}
                                </Paper>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </Box>
                
                {/* Footer Info */}
                <Box sx={{ p: 2, borderTop: '1px solid #222' }}>
                     <Typography variant="caption" color="#444" align="center" display="block">
                         AI Director v2.0 • {estimatedDuration ? `Est. ${estimatedDuration}s` : 'Ready'}
                     </Typography>
                </Box>
            </Paper>

            {/* RESIZE HANDLE */}
            <Box
                onMouseDown={onResizeStart}
                sx={{
                    width: '4px',
                    height: '100%',
                    cursor: 'col-resize',
                    flexShrink: 0,
                    bgcolor: '#222',
                    '&:hover': { bgcolor: '#FF4081' },
                    transition: 'background-color 0.15s',
                    zIndex: 20,
                }}
            />

            {/* RIGHT MAIN: STAGE, TIMELINE & PRODUCER */}
            <Box sx={{ flex: 1, display: 'flex', minWidth: 0 }}>
                <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative', minWidth: 0 }}>
                
                {/* 1. Main Stage (Player) */}
                <Box sx={{ 
                    flex: 1, 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    background: '#050505',
                    position: 'relative',
                    p: 3
                }}>
                    {!scriptResult && !loading && !videoGenerating ? (
                        <Box sx={{ textAlign: 'center', color: '#333' }}>
                            <MagicIcon sx={{ fontSize: 60, mb: 2, opacity: 0.5 }} />
                            <Typography variant="h6" fontWeight={400}>Your canvas is empty</Typography>
                            <Typography variant="body2">Start by describing your vision on the left.</Typography>
                        </Box>
                    ) : (
                        <Paper 
                            elevation={10}
                            sx={{
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
                                border: '1px solid #222'
                            }}
                        >
                             {videoTask?.finalVideo ? (
                                <Box sx={{ width: '100%', height: '100%', position: 'relative' }}>
                                    <video
                                        ref={videoRef}
                                        src={getFullUrl(videoTask.finalVideo)}
                                        controls
                                        autoPlay
                                        style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                                    />
                                    <Box sx={{ position: 'absolute', top: 16, right: 16 }}>
                                         <Button
                                            variant="contained"
                                            startIcon={<EditIcon />}
                                            onClick={() => navigate('/editor', { state: videoTask })}
                                            sx={{ bgcolor: 'rgba(255,255,255,0.2)', backdropFilter: 'blur(10px)' }}
                                        >
                                            Open in Editor
                                        </Button>
                                    </Box>
                                </Box>
                            ) : videoTask?.generatedVideos?.some(v => v.status === 'success') ? (
                                <Box sx={{ textAlign: 'center' }}>
                                    <CircularProgress sx={{ color: '#4caf50', mb: 2 }} />
                                    <Typography variant="h6" color="#eee">Assembling Video...</Typography>
                                    <Typography variant="body2" color="#666">
                                        Rendered {videoTask.generatedVideos.filter(v => v.status === 'success').length} shots
                                    </Typography>
                                </Box>
                            ) : (loading || videoGenerating) ? (
                                <Box sx={{ textAlign: 'center' }}>
                                    <CircularProgress size={60} thickness={2} sx={{ color: '#FF4081', mb: 3 }} />
                                    <Typography variant="h5" fontWeight={300} color="white" gutterBottom>
                                        Creating Magic
                                    </Typography>
                                    <Typography variant="body2" color="#888" sx={{ fontFamily: 'monospace', mt: 1 }}>
                                        {videoTask?.logs && videoTask.logs.length > 0
                                            ? videoTask.logs[videoTask.logs.length - 1].message
                                            : (loading ? 'Initializing director...' : 'Processing scenes...')}
                                    </Typography>
                                    {/* Progress Percentage */}
                                    {typeof videoTask?.progress === 'number' && (
                                        <Typography variant="h4" fontWeight={600} color="#FF4081" sx={{ mt: 3 }}>
                                            {Math.round(videoTask.progress)}%
                                        </Typography>
                                    )}
                                </Box>
                            ) : (
                                <Box sx={{ p: 4, maxWidth: 600, textAlign: 'center' }}>
                                    <Typography variant="h5" color="white" gutterBottom>Script Ready</Typography>
                                    <Typography variant="body1" color="#888" sx={{ fontStyle: 'italic', mb: 3 }}>
                                        "{scriptResult?.script.substring(0, 150)}..."
                                    </Typography>
                                    <Button variant="outlined" color="primary" onClick={handleConfirmAndGenerate}>
                                        Render Video Now
                                    </Button>
                                </Box>
                            )}

                            {/* Progress Bar Overlay */}
                            {(loading || videoGenerating) && (
                                <Box sx={{ position: 'absolute', bottom: 0, left: 0, right: 0 }}>
                                    <LinearProgress
                                        variant={typeof videoTask?.progress === 'number' ? "determinate" : "indeterminate"}
                                        value={videoTask?.progress || 0}
                                        sx={{
                                            height: 8,
                                            bgcolor: 'rgba(255,64,129,0.15)',
                                            borderRadius: 0,
                                            '& .MuiLinearProgress-bar': {
                                                bgcolor: '#FF4081',
                                                boxShadow: '0 0 10px rgba(255, 64, 129, 0.5)',
                                                transition: 'transform 0.4s ease'
                                            }
                                        }}
                                    />
                                    {/* Progress Text on Bar */}
                                    {typeof videoTask?.progress === 'number' && videoTask.progress > 0 && (
                                        <Box sx={{
                                            position: 'absolute',
                                            top: -24,
                                            right: 16,
                                            bgcolor: 'rgba(0,0,0,0.8)',
                                            px: 1.5,
                                            py: 0.5,
                                            borderRadius: 1,
                                            backdropFilter: 'blur(10px)'
                                        }}>
                                            <Typography variant="caption" fontWeight={600} color="#FF4081" sx={{ fontFamily: 'monospace' }}>
                                                {Math.round(videoTask.progress)}%
                                            </Typography>
                                        </Box>
                                    )}
                                </Box>
                            )}
                        </Paper>
                    )}
                </Box>

                {/* 2. Bottom Panel: Storyboard / Shot List */}
                <Box sx={{ 
                    height: 200, 
                    background: '#111', 
                    borderTop: '1px solid #222',
                    display: 'flex',
                    flexDirection: 'column'
                }}>
                    <Box sx={{ px: 2, py: 1, borderBottom: '1px solid #222', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="subtitle2" color="#888" fontWeight={700}>STORYBOARD / SHOTS</Typography>
                        <Stack direction="row" spacing={1}>
                            <IconButton size="small" disabled={!scriptResult}><RefreshIcon fontSize="small" /></IconButton>
                        </Stack>
                    </Box>

                    <Box sx={{ 
                        flex: 1, 
                        overflowX: 'auto', 
                        p: 2, 
                        display: 'flex', 
                        gap: 2,
                        '&::-webkit-scrollbar': { height: 8 },
                        '&::-webkit-scrollbar-thumb': { bgcolor: '#333', borderRadius: 4 }
                    }}>
                        {scriptResult?.shots && (
                             isEditingShots ? (
                                <ShotEditor
                                    shots={editableShots}
                                    onShotsChange={setEditableShots}
                                    onConfirm={handleConfirmAndGenerate}
                                    loading={videoGenerating}
                                    compact={true} // Need to update ShotEditor to support compact mode or just styles
                                />
                             ) : (
                                scriptResult.shots.map((shot, idx) => {
                                    // 处理图片路径
                                    let bgImage = 'none';
                                    if (shot.imagePath) {
                                        bgImage = `url(${getFullUrl(shot.imagePath)})`;
                                    }

                                    // 从 bible 取本镜头的导演级标签（场景/角色/转场）
                                    const bibleShot = videoTask?.bible?.shot_graph?.find(g => g.sequence === shot.sequence);
                                    const transitionLabel: Record<string, string> = {
                                        cut: '',
                                        match_cut: 'match',
                                        continuous: '承接',
                                    };
                                    const transitionColor: Record<string, string> = {
                                        cut: 'transparent',
                                        match_cut: 'rgba(255, 152, 0, 0.7)',
                                        continuous: 'rgba(76, 175, 80, 0.75)',
                                    };

                                    return (
                                    <Paper
                                        key={idx}
                                        onClick={() => {
                                            if (videoRef.current && scriptResult.shots) {
                                                const startTime = scriptResult.shots.slice(0, idx).reduce((sum, s) => sum + s.duration, 0);
                                                videoRef.current.currentTime = startTime;
                                                videoRef.current.play().catch(e => console.warn("Play failed:", e));
                                            }
                                        }}
                                        sx={{
                                            minWidth: 200,
                                            height: '100%',
                                            bgcolor: '#1a1a1a',
                                            backgroundImage: bgImage,
                                            backgroundSize: 'cover',
                                            backgroundPosition: 'center',
                                            border: '1px solid #333',
                                            borderRadius: 2,
                                            p: 1.5,
                                            display: 'flex',
                                            flexDirection: 'column',
                                            justifyContent: 'flex-end', // 将文字推到底部
                                            cursor: 'pointer',
                                            position: 'relative',
                                            overflow: 'hidden',
                                            '&:hover': { borderColor: '#555' },
                                            // 添加遮罩以确保文字可读
                                            '&::before': shot.imagePath ? {
                                                content: '""',
                                                position: 'absolute',
                                                top: 0,
                                                left: 0,
                                                right: 0,
                                                bottom: 0,
                                                background: 'linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0) 60%)',
                                                zIndex: 1
                                            } : {}
                                        }}
                                    >
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, position: 'relative', zIndex: 2, alignItems: 'flex-start', marginTop: shot.imagePath ? '-100%' : 0 }}>
                                             {/* 如果有图片，把chip放到左上角 */}
                                            <Chip label={`#${shot.sequence}`} size="small" sx={{ height: 20, bgcolor: 'rgba(0,0,0,0.6)', color: '#fff', backdropFilter: 'blur(4px)' }} />
                                            <Typography variant="caption" sx={{ color: '#fff', textShadow: '0 1px 2px rgba(0,0,0,0.8)', bgcolor: 'rgba(0,0,0,0.4)', px: 0.5, borderRadius: 1 }}>{shot.duration}s</Typography>
                                        </Box>

                                        {/* Bible 标签：scene_id / 角色 / 转场（仅当存在时显示） */}
                                        {bibleShot && (
                                            <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap sx={{ position: 'relative', zIndex: 2, mb: 0.5 }}>
                                                <Chip
                                                    label={`S${bibleShot.scene_id}`}
                                                    size="small"
                                                    sx={{ height: 18, fontSize: '0.65rem', bgcolor: 'rgba(63, 81, 181, 0.75)', color: '#fff' }}
                                                />
                                                {bibleShot.characters_in_shot.slice(0, 2).map((name) => (
                                                    <Chip
                                                        key={name}
                                                        label={name}
                                                        size="small"
                                                        sx={{ height: 18, fontSize: '0.65rem', bgcolor: 'rgba(255,255,255,0.15)', color: '#fff' }}
                                                    />
                                                ))}
                                                {transitionLabel[bibleShot.continuity] && (
                                                    <Chip
                                                        label={transitionLabel[bibleShot.continuity]}
                                                        size="small"
                                                        sx={{
                                                            height: 18,
                                                            fontSize: '0.65rem',
                                                            bgcolor: transitionColor[bibleShot.continuity],
                                                            color: '#fff',
                                                        }}
                                                    />
                                                )}
                                            </Stack>
                                        )}

                                        <Typography variant="body2" color="#ccc" sx={{
                                            position: 'relative',
                                            zIndex: 2,
                                            flex: shot.imagePath ? 0 : 1,
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                            display: '-webkit-box',
                                            WebkitLineClamp: 3,
                                            WebkitBoxOrient: 'vertical',
                                            fontSize: '0.8rem',
                                            lineHeight: 1.4,
                                            textShadow: shot.imagePath ? '0 1px 2px black' : 'none'
                                        }}>
                                            {shot.prompt}
                                        </Typography>
                                    </Paper>
                                )})
                             )
                        )}
                        
                        {!scriptResult && (
                            <Box sx={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: 0.2 }}>
                                <Typography variant="caption" color="white">Generated shots will appear here</Typography>
                            </Box>
                        )}
                    </Box>
                </Box>
                </Box>
                {renderProducerPanel()}
            </Box>
        </Box>
    );
};

export default GeneratePage;
