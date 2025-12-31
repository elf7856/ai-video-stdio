/**
 * 多镜头预览和编辑组件
 * 显示所有生成的视频镜头，允许用户预览、调整顺序、添加转场等
 */
import React, { useState } from 'react';
import {
    Box,
    Paper,
    Typography,
    Grid,
    Card,
    CardContent,
    CardMedia,
    Button,
    IconButton,
    Stack,
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
    Tooltip,
} from '@mui/material';
import {
    PlayArrow as PlayIcon,
    ArrowUpward as UpIcon,
    ArrowDownward as DownIcon,
    MovieFilter as TransitionIcon,
    MusicNote as MusicIcon,
    Merge as MergeIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import type { Shot, GeneratedVideo } from '../api/types';

interface ShotWithVideo extends Shot {
    videoData?: GeneratedVideo;
}

interface MultiShotEditorProps {
    shots: Shot[];
    generatedVideos: GeneratedVideo[];
    onReorder?: (newOrder: Shot[]) => void;
    onAddTransition?: (fromIndex: number, toIndex: number, transitionType: string) => void;
    onAddMusic?: (musicFile: File) => void;
    onFinalMerge?: () => void;
}

const MultiShotEditor: React.FC<MultiShotEditorProps> = ({
    shots,
    generatedVideos,
    onReorder,
    onAddTransition,
    onAddMusic,
    onFinalMerge,
}) => {
    const theme = useTheme();
    const [orderedShots, setOrderedShots] = useState<ShotWithVideo[]>(
        shots.map(shot => ({
            ...shot,
            videoData: generatedVideos.find(v => v.sequence === shot.sequence),
        }))
    );

    const [transitionDialogOpen, setTransitionDialogOpen] = useState(false);
    const [selectedTransitionIndex, setSelectedTransitionIndex] = useState<number | null>(null);
    const [transitionType, setTransitionType] = useState('fade');
    const [transitionDuration, setTransitionDuration] = useState(1.0);

    const handleMoveUp = (index: number) => {
        if (index === 0) return;
        const newOrder = [...orderedShots];
        [newOrder[index - 1], newOrder[index]] = [newOrder[index], newOrder[index - 1]];
        setOrderedShots(newOrder);
        onReorder?.(newOrder);
    };

    const handleMoveDown = (index: number) => {
        if (index === orderedShots.length - 1) return;
        const newOrder = [...orderedShots];
        [newOrder[index], newOrder[index + 1]] = [newOrder[index + 1], newOrder[index]];
        setOrderedShots(newOrder);
        onReorder?.(newOrder);
    };

    const handleAddTransition = (index: number) => {
        setSelectedTransitionIndex(index);
        setTransitionDialogOpen(true);
    };

    const handleConfirmTransition = () => {
        if (selectedTransitionIndex !== null) {
            onAddTransition?.(selectedTransitionIndex, selectedTransitionIndex + 1, transitionType);
        }
        setTransitionDialogOpen(false);
        setSelectedTransitionIndex(null);
    };

    const getStatusColor = (status?: string) => {
        switch (status) {
            case 'success':
                return 'success';
            case 'generating':
                return 'info';
            case 'failed':
                return 'error';
            default:
                return 'default';
        }
    };

    const getStatusLabel = (status?: string) => {
        switch (status) {
            case 'success':
                return '✅ 已完成';
            case 'generating':
                return '⏳ 生成中';
            case 'failed':
                return '❌ 失败';
            default:
                return '⏸️ 等待中';
        }
    };

    return (
        <Box>
            {/* Header */}
            <Paper sx={{ p: 3, mb: 3, background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.secondary.main, 0.1)} 100%)` }}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Box>
                        <Typography variant="h5" fontWeight={700} gutterBottom>
                            🎬 多镜头后期编辑
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            共 {orderedShots.length} 个镜头 · 预览、排序、添加转场效果
                        </Typography>
                    </Box>
                    <Stack direction="row" spacing={2}>
                        <Button
                            variant="outlined"
                            startIcon={<MusicIcon />}
                            onClick={() => onAddMusic?.(new File([], ''))}
                        >
                            添加音乐
                        </Button>
                        <Button
                            variant="contained"
                            size="large"
                            startIcon={<MergeIcon />}
                            onClick={onFinalMerge}
                            disabled={orderedShots.some(s => s.videoData?.status !== 'success')}
                        >
                            合成最终视频
                        </Button>
                    </Stack>
                </Stack>
            </Paper>

            {/* Shots Grid */}
            <Grid container spacing={3}>
                {orderedShots.map((shot, index) => (
                    <Grid item xs={12} md={6} lg={4} key={shot.sequence}>
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.1 }}
                        >
                            <Card
                                sx={{
                                    height: '100%',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    border: `2px solid ${alpha(theme.palette.divider, 0.5)}`,
                                    '&:hover': {
                                        boxShadow: 6,
                                        borderColor: theme.palette.primary.main,
                                    },
                                }}
                            >
                                {/* Video Preview */}
                                <Box sx={{ position: 'relative', paddingTop: '56.25%', bgcolor: 'black' }}>
                                    {shot.videoData?.videoPath ? (
                                        <CardMedia
                                            component="video"
                                            src={shot.videoData.videoPath}
                                            controls
                                            sx={{
                                                position: 'absolute',
                                                top: 0,
                                                left: 0,
                                                width: '100%',
                                                height: '100%',
                                                objectFit: 'contain',
                                            }}
                                        />
                                    ) : (
                                        <Box
                                            sx={{
                                                position: 'absolute',
                                                top: 0,
                                                left: 0,
                                                width: '100%',
                                                height: '100%',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                bgcolor: alpha(theme.palette.background.paper, 0.05),
                                            }}
                                        >
                                            <Typography color="text.secondary">
                                                {shot.videoData?.status === 'generating' ? '生成中...' : '等待生成'}
                                            </Typography>
                                        </Box>
                                    )}

                                    {/* Shot Number Badge */}
                                    <Chip
                                        label={`镜头 ${shot.sequence}`}
                                        size="small"
                                        sx={{
                                            position: 'absolute',
                                            top: 12,
                                            left: 12,
                                            fontWeight: 700,
                                            bgcolor: alpha(theme.palette.background.paper, 0.9),
                                        }}
                                    />

                                    {/* Status Badge */}
                                    <Chip
                                        label={getStatusLabel(shot.videoData?.status)}
                                        color={getStatusColor(shot.videoData?.status) as any}
                                        size="small"
                                        sx={{
                                            position: 'absolute',
                                            top: 12,
                                            right: 12,
                                        }}
                                    />
                                </Box>

                                <CardContent sx={{ flexGrow: 1 }}>
                                    {/* Prompt */}
                                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                                        📝 Prompt:
                                    </Typography>
                                    <Typography variant="body2" paragraph>
                                        {shot.prompt}
                                    </Typography>

                                    {/* Shot Info */}
                                    <Stack direction="row" spacing={2} flexWrap="wrap" sx={{ mb: 2 }}>
                                        <Chip
                                            label={`${shot.duration}秒`}
                                            size="small"
                                            icon={<PlayIcon />}
                                            variant="outlined"
                                        />
                                        {shot.shotType && (
                                            <Chip
                                                label={shot.shotType}
                                                size="small"
                                                variant="outlined"
                                            />
                                        )}
                                        {shot.videoData?.fileSize && (
                                            <Chip
                                                label={`${(shot.videoData.fileSize / 1024 / 1024).toFixed(1)}MB`}
                                                size="small"
                                                variant="outlined"
                                            />
                                        )}
                                    </Stack>

                                    {/* Action Buttons */}
                                    <Stack direction="row" spacing={1} justifyContent="space-between">
                                        {/* Move Up/Down */}
                                        <Stack direction="row" spacing={0.5}>
                                            <Tooltip title="上移">
                                                <span>
                                                    <IconButton
                                                        size="small"
                                                        onClick={() => handleMoveUp(index)}
                                                        disabled={index === 0}
                                                    >
                                                        <UpIcon />
                                                    </IconButton>
                                                </span>
                                            </Tooltip>
                                            <Tooltip title="下移">
                                                <span>
                                                    <IconButton
                                                        size="small"
                                                        onClick={() => handleMoveDown(index)}
                                                        disabled={index === orderedShots.length - 1}
                                                    >
                                                        <DownIcon />
                                                    </IconButton>
                                                </span>
                                            </Tooltip>
                                        </Stack>

                                        {/* Add Transition */}
                                        {index < orderedShots.length - 1 && (
                                            <Tooltip title="添加转场">
                                                <IconButton
                                                    size="small"
                                                    color="primary"
                                                    onClick={() => handleAddTransition(index)}
                                                    disabled={shot.videoData?.status !== 'success'}
                                                >
                                                    <TransitionIcon />
                                                </IconButton>
                                            </Tooltip>
                                        )}
                                    </Stack>
                                </CardContent>
                            </Card>
                        </motion.div>
                    </Grid>
                ))}
            </Grid>

            {/* Transition Dialog */}
            <Dialog
                open={transitionDialogOpen}
                onClose={() => setTransitionDialogOpen(false)}
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle>🎨 添加转场效果</DialogTitle>
                <DialogContent>
                    <Stack spacing={3} sx={{ mt: 2 }}>
                        <FormControl fullWidth>
                            <InputLabel>转场类型</InputLabel>
                            <Select
                                value={transitionType}
                                onChange={(e) => setTransitionType(e.target.value)}
                                label="转场类型"
                            >
                                <MenuItem value="fade">淡入淡出 (Fade)</MenuItem>
                                <MenuItem value="dissolve">溶解 (Dissolve)</MenuItem>
                                <MenuItem value="wipe">擦除 (Wipe)</MenuItem>
                                <MenuItem value="slide">滑动 (Slide)</MenuItem>
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
                    <Button variant="contained" onClick={handleConfirmTransition}>
                        确认添加
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default MultiShotEditor;
