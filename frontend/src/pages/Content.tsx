import React, { useState, useEffect } from 'react';
import {
    Container,
    Typography,
    Box,
    Grid,
    Card,
    CardContent,
    CardActions,
    Button,
    Chip,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    CircularProgress,
    Paper,
    useTheme,
    alpha,
    InputAdornment,
    TextField,
    Tooltip
} from '@mui/material';
import {
    Delete as DeleteIcon,
    Visibility as ViewIcon,
    ContentCopy as CopyIcon,
    Download as DownloadIcon,
    Movie as MovieIcon,
    Search as SearchIcon,
    Edit as EditIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import type { Shot, VideoGenerationTask } from '../api/types';

interface SavedScript {
    id: string;
    topic: string;
    style: string;
    script: string;
    shots: Shot[];
    totalDuration: number;
    createdAt: string;
    videoTask?: VideoGenerationTask; // 添加视频任务数据
}

const ContentPage: React.FC = () => {
    const theme = useTheme();
    const navigate = useNavigate();
    const [scripts, setScripts] = useState<SavedScript[]>([]);
    const [selectedScript, setSelectedScript] = useState<SavedScript | null>(null);
    const [dialogOpen, setDialogOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        loadScripts();
    }, []);

    const loadScripts = async () => {
        setLoading(true);
        try {
            // 1. 加载本地缓存
            const localSaved = localStorage.getItem('savedScripts');
            let allScripts: SavedScript[] = localSaved ? JSON.parse(localSaved) : [];

            // 2. 从后端数据库加载 (新增加逻辑)
            try {
                // 使用 editorApi 加载 editor_projects 表的数据
                const { editorApi } = await import('../api');
                const backendProjects = await editorApi.listProjects();
                
                // 将后端项目转换为 SavedScript 格式
                const mappedBackend: SavedScript[] = backendProjects.map(p => ({
                    id: p.id,
                    topic: p.name,
                    style: '专业', // EditorProject 表里暂时没有存 style，使用默认值
                    script: p.description || '',
                    shots: [], // 暂时留空，点击编辑时会加载
                    totalDuration: 60, // 默认值，timeline 里有更准确的
                    createdAt: p.created_at,
                    videoTask: p.output_path ? {
                        taskId: p.id,
                        status: 'completed',
                        progress: 100,
                        finalVideo: p.output_path
                    } as any : undefined
                }));

                // 合并去重 (以ID为准)
                const existingIds = new Set(allScripts.map(s => s.id));
                mappedBackend.forEach(p => {
                    if (!existingIds.has(p.id)) {
                        allScripts.push(p);
                    }
                });
            } catch (apiErr) {
                console.warn('Failed to fetch from backend, showing local only:', apiErr);
            }

            setScripts(allScripts.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()));
        } catch (error) {
            console.error('Failed to load history:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = (id: string) => {
        if (window.confirm('Are you sure you want to delete this script?')) {
            const newScripts = scripts.filter(s => s.id !== id);
            setScripts(newScripts);
            localStorage.setItem('savedScripts', JSON.stringify(newScripts));
        }
    };

    const handleView = (script: SavedScript) => {
        setSelectedScript(script);
        setDialogOpen(true);
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
    };

    const downloadScript = (script: SavedScript) => {
        let content = `# Video Script\n\n`;
        content += `**Topic:** ${script.topic}\n`;
        content += `**Style:** ${script.style}\n`;
        content += `**Duration:** ${script.totalDuration}s\n`;
        content += `**Created:** ${new Date(script.createdAt).toLocaleString()}\n\n`;
        content += `## Full Script\n\n${script.script}\n\n`;
        content += `## Storyboard\n\n`;

        script.shots.forEach((shot: Shot) => {
            content += `### Shot ${shot.sequence}\n`;
            content += `- **Type:** ${shot.shotType || 'N/A'}\n`;
            content += `- **Duration:** ${shot.duration}s\n`;
            content += `- **Prompt:** ${shot.prompt}\n\n`;
        });

        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `script_${script.topic.slice(0, 20).replace(/\s+/g, '_')}_${Date.now()}.md`;
        link.click();
        URL.revokeObjectURL(url);
    };

    const handleClearAll = () => {
        if (window.confirm('Clear all history? This cannot be undone.')) {
            setScripts([]);
            localStorage.removeItem('savedScripts');
        }
    };

    const handleEnterEditor = (script: SavedScript) => {
        // 构建编辑器需要的数据
        const editorData = {
            taskId: script.id,
            topic: script.topic,
            style: script.style,
            script: script.script,
            shots: script.shots,
            totalDuration: script.totalDuration,
            // 如果有视频任务数据，合并进来
            ...(script.videoTask || {}),
            generatedVideos: script.videoTask?.generatedVideos || [],
            finalVideo: script.videoTask?.finalVideo || null,
            status: script.videoTask?.status || 'draft'
        };

        // 构造项目ID：确保有 proj_ 前缀
        // 后端同步逻辑是 f"proj_{task_id}"
        let projectId = script.id;
        if (!projectId.startsWith('proj_')) {
            projectId = `proj_${projectId}`;
        }

        // 跳转到带ID的路由，同时传递 state 作为后备或快速加载数据
        navigate(`/editor/${projectId}`, { state: editorData });
    };

    const filteredScripts = scripts.filter(script => 
        script.topic.toLowerCase().includes(searchTerm.toLowerCase()) ||
        script.style.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Styles extracted
    const searchFieldSx = {
        borderRadius: 3,
        bgcolor: alpha(theme.palette.background.paper, 0.2),
        backdropFilter: 'blur(10px)',
        color: 'white',
        '& fieldset': { borderColor: alpha(theme.palette.common.white, 0.1) },
        '&:hover fieldset': { borderColor: alpha(theme.palette.common.white, 0.3) },
        width: { xs: '100%', md: 300 }
    };

    const actionButtonSx = {
        color: 'text.secondary',
        '&:hover': { color: 'white' }
    };

    const deleteButtonSx = {
        color: 'text.secondary',
        '&:hover': { color: 'error.main' }
    };

    const dialogPaperSx = {
        bgcolor: '#1e293b',
        backgroundImage: 'none',
        border: `1px solid ${alpha(theme.palette.common.white, 0.1)}`,
        borderRadius: 3
    };

    return (
        <Box sx={{ 
            minHeight: '100vh', 
            background: 'radial-gradient(circle at 50% 10%, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
            pt: '80px',
            pb: 8,
            px: { xs: 2, md: 4 },
            color: 'white'
        }}>
            <Container maxWidth="xl">
                {/* Header */}
                <Box sx={{ mb: 6, display: 'flex', flexDirection: { xs: 'column', md: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'start', md: 'center' }, gap: 3 }}>
                    <Box>
                        <Typography variant="h3" fontWeight={800} gutterBottom sx={{ 
                            background: 'linear-gradient(45deg, #4facfe 30%, #00f2fe 90%)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 2
                        }}>
                            <MovieIcon fontSize="large" /> My Library
                        </Typography>
                        <Typography variant="body1" color="text.secondary">
                            Manage your generated scripts and videos.
                        </Typography>
                    </Box>

                    <Box sx={{ display: 'flex', gap: 2, width: { xs: '100%', md: 'auto' } }}>
                        <TextField
                            placeholder="Search scripts..."
                            variant="outlined"
                            size="small"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            InputProps={{
                                startAdornment: <InputAdornment position="start"><SearchIcon color="action" /></InputAdornment>,
                                sx: searchFieldSx
                            }}
                        />
                         {scripts.length > 0 && (
                            <Button
                                variant="outlined"
                                color="error"
                                onClick={handleClearAll}
                                startIcon={<DeleteIcon />}
                                sx={{ borderRadius: 3 }}
                            >
                                Clear
                            </Button>
                        )}
                    </Box>
                </Box>

                {/* Content */}
                {loading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 20 }}>
                        <CircularProgress />
                    </Box>
                ) : scripts.length === 0 ? (
                    <Paper
                        sx={{
                            p: 8,
                            textAlign: 'center',
                            backgroundColor: alpha(theme.palette.background.paper, 0.1),
                            backdropFilter: 'blur(10px)',
                            border: `1px solid ${alpha(theme.palette.common.white, 0.1)}`,
                            borderRadius: 4
                        }}
                    >
                        <MovieIcon sx={{ fontSize: 100, color: alpha(theme.palette.common.white, 0.1), mb: 3 }} />
                        <Typography variant="h5" color="text.primary" gutterBottom>
                            No content yet
                        </Typography>
                        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                            Start generating amazing videos to build your library.
                        </Typography>
                        <Button
                            variant="contained"
                            size="large"
                            href="/generate"
                            sx={{
                                borderRadius: 50,
                                px: 4,
                                py: 1.5,
                                background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)',
                            }}
                        >
                            Create New Project
                        </Button>
                    </Paper>
                ) : (
                    <>
                        {/* Stats */}
                        <Box sx={{ mb: 4, display: 'flex', gap: 2 }}>
                             <Chip
                                label={`${filteredScripts.length} Projects`}
                                sx={{ bgcolor: alpha(theme.palette.primary.main, 0.2), color: 'primary.light', border: 'none' }}
                            />
                            <Chip
                                label={`Total Duration: ${scripts.reduce((sum, s) => sum + s.totalDuration, 0)}s`}
                                sx={{ bgcolor: alpha(theme.palette.secondary.main, 0.2), color: 'secondary.light', border: 'none' }}
                            />
                        </Box>

                        {/* Grid */}
                        <Grid container spacing={3}>
                            <AnimatePresence>
                                {filteredScripts.map((script) => (
                                    <Grid item xs={12} sm={6} md={4} lg={3} key={script.id}>
                                        <motion.div
                                            layout
                                            initial={{ opacity: 0, scale: 0.9 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            exit={{ opacity: 0, scale: 0.9 }}
                                            transition={{ duration: 0.2 }}
                                        >
                                            <Card
                                                sx={{
                                                    height: '100%',
                                                    display: 'flex',
                                                    flexDirection: 'column',
                                                    background: alpha(theme.palette.background.paper, 0.3),
                                                    backdropFilter: 'blur(10px)',
                                                    border: `1px solid ${alpha(theme.palette.common.white, 0.05)}`,
                                                    borderRadius: 3,
                                                    transition: 'all 0.3s ease',
                                                    '&:hover': {
                                                        transform: 'translateY(-5px)',
                                                        boxShadow: `0 10px 30px -10px ${alpha(theme.palette.primary.main, 0.3)}`,
                                                        borderColor: alpha(theme.palette.primary.main, 0.3)
                                                    }
                                                }}
                                            >
                                                <CardContent sx={{ flexGrow: 1, p: 3 }}>
                                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                                                        <Chip 
                                                            label={script.style} 
                                                            size="small" 
                                                            sx={{ 
                                                                bgcolor: alpha(theme.palette.info.main, 0.2), 
                                                                color: 'info.light', 
                                                                fontSize: '0.75rem', 
                                                                height: 24 
                                                            }} 
                                                        />
                                                        <Typography variant="caption" color="text.secondary">
                                                            {new Date(script.createdAt).toLocaleDateString()}
                                                        </Typography>
                                                    </Box>
                                                    
                                                    <Typography variant="h6" fontWeight={600} gutterBottom sx={{
                                                        overflow: 'hidden',
                                                        textOverflow: 'ellipsis',
                                                        display: '-webkit-box',
                                                        WebkitLineClamp: 2,
                                                        WebkitBoxOrient: 'vertical',
                                                        minHeight: '3.2em',
                                                        lineHeight: 1.3
                                                    }}>
                                                        {script.topic}
                                                    </Typography>

                                                    <Typography
                                                        variant="body2"
                                                        color="text.secondary"
                                                        sx={{
                                                            overflow: 'hidden',
                                                            textOverflow: 'ellipsis',
                                                            display: '-webkit-box',
                                                            WebkitLineClamp: 3,
                                                            WebkitBoxOrient: 'vertical',
                                                            mb: 2,
                                                            minHeight: '4.5em'
                                                        }}
                                                    >
                                                        {script.script}
                                                    </Typography>

                                                    <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                                                        <Chip label={`${script.shots.length} shots`} size="small" variant="outlined" sx={{ borderColor: alpha(theme.palette.common.white, 0.1), color: 'text.secondary' }} />
                                                        <Chip label={`${script.totalDuration}s`} size="small" variant="outlined" sx={{ borderColor: alpha(theme.palette.common.white, 0.1), color: 'text.secondary' }} />
                                                    </Box>
                                                </CardContent>

                                                <CardActions sx={{ p: 2, pt: 0, justifyContent: 'space-between', borderTop: `1px solid ${alpha(theme.palette.common.white, 0.05)}` }}>
                                                    <Box>
                                                        <Tooltip title="View Details">
                                                            <IconButton size="small" onClick={() => handleView(script)} sx={{ color: 'primary.main' }}>
                                                                <ViewIcon />
                                                            </IconButton>
                                                        </Tooltip>
                                                    </Box>
                                                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                        <Button
                                                            variant="contained"
                                                            size="small"
                                                            startIcon={<EditIcon />}
                                                            onClick={() => handleEnterEditor(script)}
                                                            sx={{
                                                                background: 'linear-gradient(45deg, #9c27b0 30%, #e91e63 90%)',
                                                                borderRadius: 2,
                                                                textTransform: 'none',
                                                                fontSize: '0.75rem',
                                                                py: 0.5,
                                                                px: 1.5
                                                            }}
                                                        >
                                                            编辑
                                                        </Button>
                                                        <Tooltip title="Download Script">
                                                            <IconButton size="small" onClick={() => downloadScript(script)} sx={actionButtonSx}>
                                                                <DownloadIcon />
                                                            </IconButton>
                                                        </Tooltip>
                                                        <Tooltip title="Delete">
                                                            <IconButton size="small" onClick={() => handleDelete(script.id)} sx={deleteButtonSx}>
                                                                <DeleteIcon />
                                                            </IconButton>
                                                        </Tooltip>
                                                    </Box>
                                                </CardActions>
                                            </Card>
                                        </motion.div>
                                    </Grid>
                                ))}
                            </AnimatePresence>
                        </Grid>
                    </>
                )}

                {/* Details Dialog */}
                <Dialog
                    open={dialogOpen}
                    onClose={() => setDialogOpen(false)}
                    maxWidth="md"
                    fullWidth
                    PaperProps={{
                        sx: dialogPaperSx
                    }}
                >
                    {selectedScript && (
                        <>
                            <DialogTitle sx={{ borderBottom: `1px solid ${alpha(theme.palette.common.white, 0.1)}`, p: 3 }}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <Typography variant="h5" fontWeight={700}>{selectedScript.topic}</Typography>
                                    <Box>
                                        <Chip label={selectedScript.style} size="small" sx={{ mr: 1, bgcolor: 'primary.dark' }} />
                                        <Chip label={`${selectedScript.totalDuration}s`} size="small" variant="outlined" />
                                    </Box>
                                </Box>
                            </DialogTitle>
                            <DialogContent sx={{ p: 3 }}>
                                {/* Full Script */}
                                <Box sx={{ mb: 4 }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                                        <Typography variant="h6" fontWeight={600} color="primary.light">
                                            Script
                                        </Typography>
                                        <Button 
                                            size="small" 
                                            startIcon={<CopyIcon />} 
                                            onClick={() => copyToClipboard(selectedScript.script)}
                                        >
                                            Copy
                                        </Button>
                                    </Box>
                                    <Paper variant="outlined" sx={{ p: 3, bgcolor: alpha(theme.palette.common.black, 0.3), borderColor: alpha(theme.palette.common.white, 0.1), borderRadius: 2 }}>
                                        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8, fontFamily: 'monospace' }}>
                                            {selectedScript.script}
                                        </Typography>
                                    </Paper>
                                </Box>

                                {/* Storyboard */}
                                <Box>
                                    <Typography variant="h6" fontWeight={600} color="primary.light" sx={{ mb: 2 }}>
                                        Storyboard ({selectedScript.shots.length} shots)
                                    </Typography>
                                    <Grid container spacing={2}>
                                        {selectedScript.shots.map((shot: Shot) => (
                                            <Grid item xs={12} key={shot.sequence}>
                                                <Paper sx={{ 
                                                    p: 2, 
                                                    bgcolor: alpha(theme.palette.background.paper, 0.5),
                                                    border: `1px solid ${alpha(theme.palette.common.white, 0.05)}`
                                                }}>
                                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                                        <Typography variant="subtitle2" fontWeight={700}>
                                                            Shot {shot.sequence}
                                                        </Typography>
                                                        <Box>
                                                            {shot.shotType && <Chip label={shot.shotType} size="small" sx={{ mr: 1, height: 20, fontSize: '0.7rem' }} />}
                                                            <Typography variant="caption" color="text.secondary">{shot.duration}s</Typography>
                                                        </Box>
                                                    </Box>
                                                    <Typography variant="body2" color="text.secondary">
                                                        {shot.prompt}
                                                    </Typography>
                                                </Paper>
                                            </Grid>
                                        ))}
                                    </Grid>
                                </Box>
                            </DialogContent>
                            <DialogActions sx={{ p: 3, borderTop: `1px solid ${alpha(theme.palette.common.white, 0.1)}` }}>
                                <Button onClick={() => downloadScript(selectedScript)} startIcon={<DownloadIcon />}>
                                    Download
                                </Button>
                                <Button onClick={() => setDialogOpen(false)} variant="contained">
                                    Close
                                </Button>
                            </DialogActions>
                        </>
                    )}
                </Dialog>
            </Container>
        </Box>
    );
};

export default ContentPage;
