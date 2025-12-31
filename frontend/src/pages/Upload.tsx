import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Container,
    Paper,
    TextField,
    Button,
    Grid,
    Chip,
    Card,
    CardContent,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Alert,
    Divider,
    Stack,
    CircularProgress
} from '@mui/material';
import {
    YouTube as YouTubeIcon,
    CloudUpload as UploadIcon,
    CheckCircle as SuccessIcon,
    Error as ErrorIcon,
    Schedule as PendingIcon,
    Refresh as RetryIcon,
    Settings as SettingsIcon,
    Launch as LaunchIcon
} from '@mui/icons-material';
import { uploadApi } from '../api/upload';
import type { Platform, UploadTask, UploadResult } from '../api/upload';

// 平台配置
const PLATFORMS = [
    { id: 'youtube', name: 'YouTube', icon: <YouTubeIcon />, color: '#FF0000' },
    { id: 'bilibili', name: '哔哩哔哩', icon: '📺', color: '#00A1D6' },
    { id: 'douyin', name: '抖音', icon: '🎵', color: '#000000' },
    { id: 'kuaishou', name: '快手', icon: '⚡', color: '#FF6600' },
    { id: 'xiaohongshu', name: '小红书', icon: '📖', color: '#FF2442' },
    { id: 'wechat_channels', name: '微信视频号', icon: '💬', color: '#07C160' },
];

const UploadPage: React.FC = () => {
    // 状态
    const [videoPath, setVideoPath] = useState('');
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [tags, setTags] = useState('');
    const [selectedPlatforms, setSelectedPlatforms] = useState<Platform[]>([]);
    const [configuredPlatforms, setConfiguredPlatforms] = useState<string[]>([]);

    const [uploading, setUploading] = useState(false);
    const [currentTask, setCurrentTask] = useState<UploadTask | null>(null);
    const [uploadHistory, setUploadHistory] = useState<UploadTask[]>([]);

    const [configDialogOpen, setConfigDialogOpen] = useState(false);

    // 加载已配置的平台
    useEffect(() => {
        loadConfiguredPlatforms();
        loadUploadHistory();
    }, []);

    const loadConfiguredPlatforms = async () => {
        try {
            const { platforms } = await uploadApi.getConfiguredPlatforms();
            setConfiguredPlatforms(platforms);
        } catch (error) {
            console.error('Failed to load configured platforms:', error);
        }
    };

    const loadUploadHistory = async () => {
        try {
            const { tasks } = await uploadApi.getAllTasks();
            setUploadHistory(tasks);
        } catch (error) {
            console.error('Failed to load upload history:', error);
        }
    };

    const handlePlatformToggle = (platform: Platform) => {
        if (selectedPlatforms.includes(platform)) {
            setSelectedPlatforms(selectedPlatforms.filter(p => p !== platform));
        } else {
            setSelectedPlatforms([...selectedPlatforms, platform]);
        }
    };

    const handleUpload = async () => {
        if (!videoPath || !title || selectedPlatforms.length === 0) {
            alert('请填写完整信息并选择至少一个平台');
            return;
        }

        setUploading(true);

        try {
            const { task_id } = await uploadApi.uploadVideo({
                video_path: videoPath,
                title,
                description,
                tags: tags ? tags.split(',').map(t => t.trim()) : [],
                platforms: selectedPlatforms,
                privacy: 'public',
                allow_comment: true,
                allow_download: true,
                allow_duet: true
            });

            // 开始轮询任务状态
            await uploadApi.pollTaskStatus(
                task_id,
                (task) => {
                    setCurrentTask(task);
                },
                1800000 // 30分钟
            );

            // 上传完成
            alert('视频上传完成！');
            loadUploadHistory();
        } catch (error: any) {
            console.error('Upload failed:', error);
            alert(`上传失败: ${error.message}`);
        } finally {
            setUploading(false);
        }
    };

    const handleRetry = async (taskId: string) => {
        try {
            await uploadApi.retryFailedUploads(taskId);
            alert('重试已开始');
            loadUploadHistory();
        } catch (error: any) {
            console.error('Retry failed:', error);
            alert(`重试失败: ${error.message}`);
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'success':
                return <SuccessIcon sx={{ color: '#4CAF50' }} />;
            case 'failed':
                return <ErrorIcon sx={{ color: '#F44336' }} />;
            case 'uploading':
            case 'processing':
                return <CircularProgress size={20} />;
            default:
                return <PendingIcon sx={{ color: '#FFC107' }} />;
        }
    };

    const getPlatformInfo = (platformId: string) => {
        return PLATFORMS.find(p => p.id === platformId) || { name: platformId, icon: '📹', color: '#666' };
    };

    return (
        <Box sx={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            pt: '80px',
            pb: 4,
            px: { xs: 2, md: 4 }
        }}>
            <Container maxWidth="xl">
                <Grid container spacing={4}>
                    {/* 左侧：上传表单 */}
                    <Grid item xs={12} lg={6}>
                        <Paper sx={{ p: 4, borderRadius: 4 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                                <Typography variant="h4" fontWeight={800}>
                                    多平台分发
                                </Typography>
                                <IconButton onClick={() => setConfigDialogOpen(true)}>
                                    <SettingsIcon />
                                </IconButton>
                            </Box>

                            <Stack spacing={3}>
                                {/* 视频路径 */}
                                <TextField
                                    fullWidth
                                    label="视频文件路径"
                                    placeholder="/path/to/video.mp4 或 ./outputs/videos/xxx.mp4"
                                    value={videoPath}
                                    onChange={(e) => setVideoPath(e.target.value)}
                                    variant="outlined"
                                />

                                {/* 标题 */}
                                <TextField
                                    fullWidth
                                    label="视频标题"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    variant="outlined"
                                />

                                {/* 描述 */}
                                <TextField
                                    fullWidth
                                    multiline
                                    minRows={3}
                                    label="视频描述"
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    variant="outlined"
                                />

                                {/* 标签 */}
                                <TextField
                                    fullWidth
                                    label="标签（逗号分隔）"
                                    placeholder="AI, 视频创作, 教程"
                                    value={tags}
                                    onChange={(e) => setTags(e.target.value)}
                                    variant="outlined"
                                />

                                <Divider />

                                {/* 平台选择 */}
                                <Box>
                                    <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                                        选择发布平台
                                    </Typography>
                                    <Grid container spacing={2}>
                                        {PLATFORMS.map((platform) => {
                                            const isConfigured = configuredPlatforms.includes(platform.id);
                                            const isSelected = selectedPlatforms.includes(platform.id as Platform);

                                            return (
                                                <Grid item xs={6} sm={4} key={platform.id}>
                                                    <Card
                                                        onClick={() => isConfigured && handlePlatformToggle(platform.id as Platform)}
                                                        sx={{
                                                            cursor: isConfigured ? 'pointer' : 'not-allowed',
                                                            opacity: isConfigured ? 1 : 0.5,
                                                            border: isSelected ? `2px solid ${platform.color}` : '1px solid #ddd',
                                                            transition: 'all 0.3s',
                                                            '&:hover': isConfigured ? {
                                                                transform: 'translateY(-4px)',
                                                                boxShadow: 4
                                                            } : {}
                                                        }}
                                                    >
                                                        <CardContent sx={{ textAlign: 'center', p: 2 }}>
                                                            <Box sx={{ fontSize: '2rem', mb: 1 }}>
                                                                {platform.icon}
                                                            </Box>
                                                            <Typography variant="caption" fontWeight={600}>
                                                                {platform.name}
                                                            </Typography>
                                                            {!isConfigured && (
                                                                <Chip label="未配置" size="small" color="warning" sx={{ mt: 1 }} />
                                                            )}
                                                            {isSelected && (
                                                                <Chip label="已选择" size="small" color="success" sx={{ mt: 1 }} />
                                                            )}
                                                        </CardContent>
                                                    </Card>
                                                </Grid>
                                            );
                                        })}
                                    </Grid>
                                </Box>

                                {/* 上传按钮 */}
                                <Button
                                    fullWidth
                                    variant="contained"
                                    size="large"
                                    startIcon={uploading ? <CircularProgress size={20} color="inherit" /> : <UploadIcon />}
                                    onClick={handleUpload}
                                    disabled={uploading || !videoPath || !title || selectedPlatforms.length === 0}
                                    sx={{
                                        py: 2,
                                        fontSize: '1.1rem',
                                        fontWeight: 700,
                                        background: 'linear-gradient(45deg, #667eea 30%, #764ba2 90%)',
                                        '&:hover': {
                                            background: 'linear-gradient(45deg, #764ba2 30%, #667eea 90%)',
                                        }
                                    }}
                                >
                                    {uploading ? '正在上传...' : `发布到 ${selectedPlatforms.length} 个平台`}
                                </Button>
                            </Stack>
                        </Paper>
                    </Grid>

                    {/* 右侧：上传进度和历史 */}
                    <Grid item xs={12} lg={6}>
                        {/* 当前上传进度 */}
                        {currentTask && (
                            <Paper sx={{ p: 4, borderRadius: 4, mb: 3 }}>
                                <Typography variant="h6" fontWeight={700} gutterBottom>
                                    上传进度
                                </Typography>
                                <List>
                                    {currentTask.results.map((result: UploadResult, index: number) => {
                                        const platformInfo = getPlatformInfo(result.platform);
                                        return (
                                            <ListItem key={index}>
                                                <ListItemIcon>
                                                    {getStatusIcon(result.status)}
                                                </ListItemIcon>
                                                <ListItemText
                                                    primary={platformInfo.name}
                                                    secondary={
                                                        <>
                                                            <Typography component="span" variant="body2" color="text.primary">
                                                                {result.status === 'success' ? '上传成功' :
                                                                 result.status === 'failed' ? `失败: ${result.error}` :
                                                                 '上传中...'}
                                                            </Typography>
                                                            {result.video_url && (
                                                                <IconButton
                                                                    size="small"
                                                                    href={result.video_url}
                                                                    target="_blank"
                                                                    sx={{ ml: 1 }}
                                                                >
                                                                    <LaunchIcon fontSize="small" />
                                                                </IconButton>
                                                            )}
                                                        </>
                                                    }
                                                />
                                            </ListItem>
                                        );
                                    })}
                                </List>
                            </Paper>
                        )}

                        {/* 上传历史 */}
                        <Paper sx={{ p: 4, borderRadius: 4 }}>
                            <Typography variant="h6" fontWeight={700} gutterBottom>
                                上传历史
                            </Typography>
                            <List>
                                {uploadHistory.slice(0, 10).map((task) => (
                                    <ListItem
                                        key={task.task_id}
                                        secondaryAction={
                                            task.status === 'failed' && (
                                                <IconButton onClick={() => handleRetry(task.task_id)}>
                                                    <RetryIcon />
                                                </IconButton>
                                            )
                                        }
                                    >
                                        <ListItemIcon>
                                            {task.status === 'completed' ? <SuccessIcon color="success" /> :
                                             task.status === 'failed' ? <ErrorIcon color="error" /> :
                                             <PendingIcon color="warning" />}
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={`${task.platforms.length} 个平台`}
                                            secondary={`${new Date(task.created_at).toLocaleString()} - ${task.status}`}
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        </Paper>
                    </Grid>
                </Grid>
            </Container>

            {/* 平台配置对话框 */}
            <Dialog open={configDialogOpen} onClose={() => setConfigDialogOpen(false)} maxWidth="md" fullWidth>
                <DialogTitle>平台配置</DialogTitle>
                <DialogContent>
                    <Alert severity="info" sx={{ mb: 2 }}>
                        目前支持通过API配置平台。请参考文档配置各平台的认证信息。
                    </Alert>
                    <Typography variant="body2" color="text.secondary">
                        已配置平台: {configuredPlatforms.join(', ') || '无'}
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setConfigDialogOpen(false)}>关闭</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default UploadPage;