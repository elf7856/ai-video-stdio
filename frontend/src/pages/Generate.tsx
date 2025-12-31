import React, { useState, useRef } from 'react';
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
    School as EduIcon,
    TheaterComedy as FunIcon,
    Store as CommercialIcon,
    Palette as ArtIcon,
    PhotoCamera as DocIcon,
    Weekend as RelaxIcon,
    Gavel as SeriousIcon,
    Edit as EditIcon,
    ExpandMore as ExpandMoreIcon,
    Refresh as RefreshIcon,
    ArrowForward as ArrowForwardIcon,
    Terminal as TerminalIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { scriptsApi, videosApi } from '../api';
import { getFullUrl } from '../utils/url';
import type {
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    Shot,
    VideoGenerationTask
} from '../api/types';
import ShotEditor from '../components/ShotEditor';

// Style Configuration
const STYLE_CONFIG: Record<string, { icon: React.ReactNode; gradient: string; color: string }> = {
    '专业': { icon: <BusinessIcon />, gradient: 'linear-gradient(135deg, #2c3e50 0%, #3498db 100%)', color: '#3498db' },
    '科技': { icon: <TechIcon />, gradient: 'linear-gradient(135deg, #000428 0%, #004e92 100%)', color: '#004e92' },
    '生活': { icon: <LifeIcon />, gradient: 'linear-gradient(135deg, #56ab2f 0%, #a8e063 100%)', color: '#56ab2f' },
    '教育': { icon: <EduIcon />, gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: '#4facfe' },
    '娱乐': { icon: <FunIcon />, gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', color: '#fa709a' },
    '商业': { icon: <CommercialIcon />, gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#667eea' },
    '艺术': { icon: <ArtIcon />, gradient: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%)', color: '#ff9a9e' },
    '纪录片': { icon: <DocIcon />, gradient: 'linear-gradient(135deg, #434343 0%, #000000 100%)', color: '#888' },
    '轻松': { icon: <RelaxIcon />, gradient: 'linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%)', color: '#66a6ff' },
    '严肃': { icon: <SeriousIcon />, gradient: 'linear-gradient(135deg, #20002c 0%, #cbb4d4 100%)', color: '#8e44ad' },
};

const GeneratePage: React.FC = () => {
    const theme = useTheme();
    const navigate = useNavigate();
    const videoRef = useRef<HTMLVideoElement>(null);

    // --- State ---
    const [hasStarted, setHasStarted] = useState(false); // Controls Initial vs Studio view
    const [activeTab, setActiveTab] = useState(0); // 0: Create, 1: Script, 2: Settings
    const [topic, setTopic] = useState('');
    const [style, setStyle] = useState('专业');
    const [targetDuration, setTargetDuration] = useState(60);
    const [shotCount, setShotCount] = useState(6);
    const [estimatedDuration, setEstimatedDuration] = useState<number | null>(null);
    const [additionalRequirements, setAdditionalRequirements] = useState('');

    const [loading, setLoading] = useState(false);
    const [scriptResult, setScriptResult] = useState<ScriptGenerateResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const [videoGenerating, setVideoGenerating] = useState(false);
    const [videoTask, setVideoTask] = useState<VideoGenerationTask | null>(null);

    const [editableShots, setEditableShots] = useState<Shot[]>([]);
    const [isEditingShots, setIsEditingShots] = useState(false);

    // Settings
    const [enableNarration, setEnableNarration] = useState(false);
    const [narrationVoice, setNarrationVoice] = useState('chinese_female');
    const [narrationSpeed, setNarrationSpeed] = useState(1.0);
    const [pacingStrategy, setPacingStrategy] = useState('balanced');

    // --- Logic ---

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
                style,
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
        setHasStarted(true); // Switch to Studio Mode
        setLoading(true);
        setError(null);
        
        // 【关键修复】彻底清空旧状态，防止闪现旧内容
        setScriptResult(null);
        setVideoTask(null);
        setEditableShots([]);
        
        setIsEditingShots(false);

        try {
            console.log("Creating task...");
            const { taskId } = await videosApi.createTask({
                topic: topic.trim(),
                style,
                targetDuration,
                shotCount,
                additionalRequirements: additionalRequirements.trim() || undefined,
                enableNarration,
                narrationVoice,
                narrationSpeed,
                pacingStrategy
            });
            console.log("Task created:", taskId);

            const finalTask = await videosApi.pollTaskStatus(taskId, (task) => {
                setVideoTask(task);
                if (task.script && task.shots && task.shots.length > 0) {
                    const totalDuration = task.shots.reduce((sum, s) => sum + s.duration, 0);
                    setScriptResult({
                        success: true,
                        script: task.script,
                        shots: task.shots,
                        totalDuration
                    });
                    setEstimatedDuration(totalDuration);
                    setEditableShots([...task.shots]);
                }
            }, 600000);

            console.log("Task polling finished:", finalTask);

            // Double check: Ensure scriptResult is set from the final task
            if (finalTask.script && finalTask.shots && (!scriptResult || !scriptResult.script)) {
                 const totalDuration = finalTask.shots.reduce((sum, s) => sum + s.duration, 0);
                 setScriptResult({
                    success: true,
                    script: finalTask.script,
                    shots: finalTask.shots,
                    totalDuration
                 });
                 setEstimatedDuration(totalDuration);
                 setEditableShots([...finalTask.shots]);
                 setVideoTask(finalTask);
            }

            setIsEditingShots(true);
            setActiveTab(1); // Show script/shots
        } catch (err: any) {
            console.error("Generation error:", err);
            setError(err.response?.data?.detail || err.message || 'Script generation failed');
        } finally {
            setLoading(false);
        }
    };
// ...
                                scriptResult.shots.map((shot, idx) => {
                                    // 处理图片路径
                                    let bgImage = 'none';
                                    if (shot.imagePath) {
                                        bgImage = `url(${getFullUrl(shot.imagePath)})`;
                                    }

                                    return (


    const handleConfirmAndGenerate = async () => {
        if (!videoTask || !scriptResult) return;

        setVideoGenerating(true);
        setIsEditingShots(false);
        setError(null);
        setActiveTab(3); // Auto-switch to Logs

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
                videoTask: taskData
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

    // --- RENDER: INITIAL SEARCH VIEW ---
    if (!hasStarted) {
        return (
            <Box sx={{
                height: 'calc(100vh - 64px)',
                background: '#0a0a0a',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                overflow: 'hidden',
                position: 'relative'
            }}>
                {/* Background ambient light */}
                <Box sx={{
                    position: 'absolute', top: '20%', left: '50%', transform: 'translate(-50%, -50%)',
                    width: '60vw', height: '60vw',
                    background: 'radial-gradient(circle, rgba(255, 64, 129, 0.05) 0%, transparent 70%)',
                    zIndex: 0,
                    pointerEvents: 'none'
                }} />

                <Container maxWidth="md" sx={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8 }}
                    >
                        <Box sx={{ mb: 6 }}>
                             <Typography variant="h2" fontWeight={700} sx={{ 
                                 background: 'linear-gradient(to right, #fff 20%, #888 100%)',
                                 WebkitBackgroundClip: 'text',
                                 WebkitTextFillColor: 'transparent',
                                 letterSpacing: '-1px',
                                 mb: 2
                             }}>
                                What will you create?
                             </Typography>
                             <Typography variant="h6" color="#666" fontWeight={300}>
                                 Describe your vision, choose a style, and let AI do the rest.
                             </Typography>
                        </Box>

                        <Paper
                            elevation={0}
                            sx={{
                                p: '2px 4px',
                                display: 'flex',
                                alignItems: 'center',
                                width: '100%',
                                borderRadius: 4,
                                bgcolor: '#1a1a1a',
                                border: '1px solid #333',
                                transition: 'all 0.3s',
                                '&:hover': {
                                    borderColor: '#555',
                                    boxShadow: '0 0 20px rgba(0,0,0,0.5)'
                                },
                                '&:focus-within': {
                                    borderColor: '#FF4081',
                                    boxShadow: '0 0 30px rgba(255, 64, 129, 0.15)'
                                }
                            }}
                        >
                            <InputAdornment position="start" sx={{ pl: 2 }}>
                                <MagicIcon sx={{ color: '#FF4081' }} />
                            </InputAdornment>
                            <TextField
                                fullWidth
                                variant="standard"
                                placeholder="A cinematic trailer for a sci-fi movie on Mars..."
                                value={topic}
                                onChange={(e) => setTopic(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && topic.trim()) handleGenerateVideo();
                                }}
                                InputProps={{
                                    disableUnderline: true,
                                    sx: {
                                        p: 2,
                                        fontSize: '1.2rem',
                                        color: 'white',
                                        '&::placeholder': { color: '#666', opacity: 1 }
                                    }
                                }}
                            />
                            <Divider sx={{ height: 28, m: 0.5, borderColor: '#333' }} orientation="vertical" />
                            <IconButton 
                                color="primary" 
                                sx={{ p: 2, mr: 0.5 }} 
                                onClick={handleGenerateVideo}
                                disabled={!topic.trim()}
                            >
                                <ArrowForwardIcon />
                            </IconButton>
                        </Paper>

                        {/* Styles Row */}
                        <Box sx={{ mt: 6 }}>
                            <Typography variant="caption" color="#666" fontWeight={700} sx={{ letterSpacing: 1, mb: 3, display: 'block' }}>
                                CHOOSE A STYLE
                            </Typography>
                            <Box sx={{ 
                                display: 'flex', 
                                gap: 2, 
                                justifyContent: 'center',
                                flexWrap: 'wrap'
                            }}>
                                {Object.keys(STYLE_CONFIG).slice(0, 6).map((s) => {
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
                                                bgcolor: isActive ? alpha(config.color, 0.2) : '#1a1a1a',
                                                color: isActive ? config.color : '#888',
                                                border: `1px solid ${isActive ? config.color : '#333'}`,
                                                borderRadius: 2,
                                                px: 1,
                                                py: 2.5,
                                                fontSize: '0.9rem',
                                                transition: 'all 0.2s',
                                                '&:hover': {
                                                    bgcolor: alpha(config.color, 0.1),
                                                    borderColor: isActive ? config.color : '#555',
                                                    transform: 'translateY(-2px)'
                                                }
                                            }}
                                        />
                                    );
                                })}
                            </Box>
                        </Box>

                        {/* Specifications Card */}
                        <Paper sx={{ mt: 4, p: 3, bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 2, border: '1px solid rgba(255,255,255,0.1)' }}>
                            <Grid container spacing={4} alignItems="center">
                                <Grid item xs={12} md={6}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="body2" color="#888" fontWeight={700}>DURATION</Typography>
                                        <Typography variant="body2" color="#FF4081" fontWeight={700}>{targetDuration}s</Typography>
                                    </Box>
                                    <Slider
                                        value={targetDuration}
                                        onChange={(_, v) => setTargetDuration(v as number)}
                                        min={10} max={300} step={5}
                                        sx={{ color: '#FF4081' }}
                                    />
                                </Grid>
                                <Grid item xs={12} md={6}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                        <Typography variant="body2" color="#888" fontWeight={700}>SHOTS</Typography>
                                        <Typography variant="body2" color="#4facfe" fontWeight={700}>{shotCount}</Typography>
                                    </Box>
                                    <Slider
                                        value={shotCount}
                                        onChange={(_, v) => setShotCount(v as number)}
                                        min={3} max={20} step={1}
                                        sx={{ color: '#4facfe' }}
                                    />
                                </Grid>
                            </Grid>
                        </Paper>

                        <Stack direction="row" spacing={2} justifyContent="center" sx={{ mt: 4 }}>
                            <Button 
                                variant="contained" 
                                size="large"
                                onClick={handleGenerateVideo}
                                disabled={!topic.trim()}
                                startIcon={<MagicIcon />}
                                sx={{
                                    borderRadius: 3,
                                    px: 4,
                                    py: 1.5,
                                    bgcolor: '#FF4081',
                                    fontWeight: 700,
                                    '&:hover': { bgcolor: '#F50057' }
                                }}
                            >
                                Generate Video
                            </Button>
                            <Button 
                                variant="text" 
                                onClick={() => setHasStarted(true)}
                                sx={{ color: '#666', '&:hover': { color: 'white' } }}
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
                                            setHasStarted(true);
                                            setActiveTab(1);
                                            setEditableShots(last.shots);
                                            setIsEditingShots(true);
                                        }
                                    }
                                }}
                                sx={{ color: '#666', '&:hover': { color: 'white' } }}
                            >
                                History
                            </Button>
                        </Stack>

                    </motion.div>
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
            <Paper sx={{
                width: { xs: '100%', md: 400 },
                height: '100%',
                background: '#111111',
                borderRight: '1px solid #222',
                display: 'flex',
                flexDirection: 'column',
                zIndex: 10,
                flexShrink: 0
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

                        {activeTab === 2 && (
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
                                                    onChange={(e) => setNarrationVoice(e.target.value)}
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

                        {activeTab === 3 && videoTask && (
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

            {/* RIGHT MAIN: STAGE & TIMELINE */}
            <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
                
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
                                <Box sx={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 4 }}>
                                    <LinearProgress
                                        variant={videoTask?.progress ? "determinate" : "indeterminate"}
                                        value={videoTask?.progress || 0}
                                        sx={{
                                            height: 4,
                                            bgcolor: 'rgba(255,64,129,0.2)',
                                            '& .MuiLinearProgress-bar': { bgcolor: '#FF4081' }
                                        }}
                                    />
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
        </Box>
    );
};

export default GeneratePage;