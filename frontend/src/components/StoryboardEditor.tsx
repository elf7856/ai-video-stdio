import React, { useState } from 'react';
import {
    Box,
    Grid,
    Card,
    CardContent,
    CardMedia,
    CardActions,
    Typography,
    Button,
    IconButton,
    TextField,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Chip,
    Paper,
    alpha,
    useTheme,
    Tooltip,
    CircularProgress
} from '@mui/material';
import {
    Edit as EditIcon,
    Delete as DeleteIcon,
    Refresh as RefreshIcon,
    Add as AddIcon,
    Check as CheckIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import type { Shot } from '../api/types';

interface StoryboardEditorProps {
    script: string;
    shots: Shot[];
    onConfirm: (script: string, shots: Shot[]) => void;
    onCancel: () => void;
    onRegenerateShot: (shotIndex: number, newPrompt?: string) => Promise<void>;
}

interface EditDialogState {
    open: boolean;
    shot: Shot | null;
    index: number;
}

const StoryboardEditor: React.FC<StoryboardEditorProps> = ({
    script,
    shots,
    onConfirm,
    onCancel,
    onRegenerateShot
}) => {
    const theme = useTheme();
    const [editableScript, setEditableScript] = useState(script);
    const [editableShots, setEditableShots] = useState<Shot[]>(shots);
    const [editDialog, setEditDialog] = useState<EditDialogState>({ open: false, shot: null, index: -1 });
    const [addDialogOpen, setAddDialogOpen] = useState(false);
    const [regeneratingIndex, setRegeneratingIndex] = useState<number | null>(null);

    // 计算总时长
    const totalDuration = editableShots.reduce((sum, shot) => sum + shot.duration, 0);

    // 编辑镜头
    const handleEditShot = (shot: Shot, index: number) => {
        setEditDialog({ open: true, shot: { ...shot }, index });
    };

    // 保存编辑
    const handleSaveEdit = () => {
        if (editDialog.shot && editDialog.index >= 0) {
            const newShots = [...editableShots];
            newShots[editDialog.index] = editDialog.shot;
            setEditableShots(newShots);
            setEditDialog({ open: false, shot: null, index: -1 });
        }
    };

    // 删除镜头
    const handleDeleteShot = (index: number) => {
        if (window.confirm('确定要删除这个镜头吗？')) {
            const newShots = editableShots.filter((_, i) => i !== index);
            // 重新编号
            newShots.forEach((shot, i) => {
                shot.sequence = i + 1;
            });
            setEditableShots(newShots);
        }
    };

    // 重新生成镜头
    const handleRegenerateShot = async (index: number) => {
        setRegeneratingIndex(index);
        try {
            await onRegenerateShot(index, editableShots[index].prompt);
            // 父组件会更新shots
        } catch (error) {
            console.error('重新生成失败:', error);
            alert('重新生成失败，请稍后重试');
        } finally {
            setRegeneratingIndex(null);
        }
    };

    // 添加新镜头
    const handleAddShot = () => {
        setAddDialogOpen(true);
    };

    // 确认添加新镜头
    const handleConfirmAddShot = (prompt: string, duration: number) => {
        const newShot: Shot = {
            sequence: editableShots.length + 1,
            prompt,
            duration,
            shotType: 'medium shot'
        };
        setEditableShots([...editableShots, newShot]);
        setAddDialogOpen(false);
    };

    // 确认并生成视频
    const handleConfirm = () => {
        onConfirm(editableScript, editableShots);
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* 脚本编辑区 */}
            <Paper
                elevation={2}
                sx={{
                    p: 3,
                    mb: 4,
                    bgcolor: alpha(theme.palette.background.paper, 0.8),
                    backdropFilter: 'blur(10px)',
                    border: `1px solid ${alpha(theme.palette.common.white, 0.1)}`,
                    borderRadius: 3
                }}
            >
                <Typography variant="h6" gutterBottom sx={{ color: 'primary.light', fontWeight: 600 }}>
                    📝 脚本 (可编辑)
                </Typography>
                <TextField
                    fullWidth
                    multiline
                    rows={6}
                    value={editableScript}
                    onChange={(e) => setEditableScript(e.target.value)}
                    variant="outlined"
                    sx={{
                        '& .MuiOutlinedInput-root': {
                            bgcolor: alpha(theme.palette.common.black, 0.2),
                            fontFamily: 'monospace',
                            fontSize: '0.95rem',
                            lineHeight: 1.8
                        }
                    }}
                />
            </Paper>

            {/* 分镜图预览区 */}
            <Paper
                elevation={2}
                sx={{
                    p: 3,
                    mb: 4,
                    bgcolor: alpha(theme.palette.background.paper, 0.8),
                    backdropFilter: 'blur(10px)',
                    border: `1px solid ${alpha(theme.palette.common.white, 0.1)}`,
                    borderRadius: 3
                }}
            >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Typography variant="h6" sx={{ color: 'primary.light', fontWeight: 600 }}>
                        🎬 分镜图预览
                    </Typography>
                    <Chip
                        label={`总时长: ${totalDuration}秒 | ${editableShots.length}个镜头`}
                        color="primary"
                        sx={{ fontWeight: 600 }}
                    />
                </Box>

                <Grid container spacing={3}>
                    <AnimatePresence>
                        {editableShots.map((shot, index) => (
                            <Grid item xs={12} sm={6} md={4} key={shot.sequence}>
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
                                            bgcolor: alpha(theme.palette.background.paper, 0.6),
                                            border: `1px solid ${alpha(theme.palette.common.white, 0.1)}`,
                                            borderRadius: 2,
                                            transition: 'all 0.3s',
                                            '&:hover': {
                                                transform: 'translateY(-4px)',
                                                borderColor: alpha(theme.palette.primary.main, 0.5),
                                                boxShadow: `0 8px 24px ${alpha(theme.palette.primary.main, 0.2)}`
                                            }
                                        }}
                                    >
                                        {/* 缩略图 */}
                                        <CardMedia
                                            component="img"
                                            height="180"
                                            image={shot.imagePath || 'https://via.placeholder.com/400x300?text=Generating...'}
                                            alt={`Shot ${shot.sequence}`}
                                            sx={{
                                                bgcolor: alpha(theme.palette.common.black, 0.3),
                                                objectFit: 'cover'
                                            }}
                                        />

                                        <CardContent>
                                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                                <Typography variant="subtitle1" fontWeight={700}>
                                                    Shot {shot.sequence}
                                                </Typography>
                                                <Chip
                                                    label={`${shot.duration}秒`}
                                                    size="small"
                                                    sx={{ bgcolor: alpha(theme.palette.info.main, 0.2) }}
                                                />
                                            </Box>

                                            {shot.shotType && (
                                                <Chip
                                                    label={shot.shotType}
                                                    size="small"
                                                    sx={{ mb: 1, fontSize: '0.7rem' }}
                                                />
                                            )}

                                            <Typography
                                                variant="body2"
                                                color="text.secondary"
                                                sx={{
                                                    overflow: 'hidden',
                                                    textOverflow: 'ellipsis',
                                                    display: '-webkit-box',
                                                    WebkitLineClamp: 2,
                                                    WebkitBoxOrient: 'vertical',
                                                    minHeight: '2.8em'
                                                }}
                                            >
                                                {shot.prompt}
                                            </Typography>
                                        </CardContent>

                                        <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                                            <Box>
                                                <Tooltip title="编辑">
                                                    <IconButton
                                                        size="small"
                                                        onClick={() => handleEditShot(shot, index)}
                                                        sx={{ color: 'primary.main' }}
                                                    >
                                                        <EditIcon fontSize="small" />
                                                    </IconButton>
                                                </Tooltip>
                                                <Tooltip title="重新生成">
                                                    <IconButton
                                                        size="small"
                                                        onClick={() => handleRegenerateShot(index)}
                                                        disabled={regeneratingIndex === index}
                                                        sx={{ color: 'info.main' }}
                                                    >
                                                        {regeneratingIndex === index ? (
                                                            <CircularProgress size={20} />
                                                        ) : (
                                                            <RefreshIcon fontSize="small" />
                                                        )}
                                                    </IconButton>
                                                </Tooltip>
                                            </Box>
                                            <Tooltip title="删除">
                                                <IconButton
                                                    size="small"
                                                    onClick={() => handleDeleteShot(index)}
                                                    sx={{ color: 'error.main' }}
                                                >
                                                    <DeleteIcon fontSize="small" />
                                                </IconButton>
                                            </Tooltip>
                                        </CardActions>
                                    </Card>
                                </motion.div>
                            </Grid>
                        ))}

                        {/* 添加新镜头按钮 */}
                        <Grid item xs={12} sm={6} md={4}>
                            <Card
                                sx={{
                                    height: '100%',
                                    minHeight: 380,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    bgcolor: alpha(theme.palette.background.paper, 0.3),
                                    border: `2px dashed ${alpha(theme.palette.primary.main, 0.3)}`,
                                    borderRadius: 2,
                                    cursor: 'pointer',
                                    transition: 'all 0.3s',
                                    '&:hover': {
                                        bgcolor: alpha(theme.palette.primary.main, 0.1),
                                        borderColor: alpha(theme.palette.primary.main, 0.6)
                                    }
                                }}
                                onClick={handleAddShot}
                            >
                                <Box sx={{ textAlign: 'center', p: 3 }}>
                                    <AddIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
                                    <Typography variant="h6" color="primary">
                                        添加新镜头
                                    </Typography>
                                </Box>
                            </Card>
                        </Grid>
                    </AnimatePresence>
                </Grid>
            </Paper>

            {/* 操作按钮 */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', gap: 2 }}>
                <Button
                    variant="outlined"
                    onClick={onCancel}
                    sx={{ borderRadius: 2 }}
                >
                    返回
                </Button>
                <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                        variant="contained"
                        color="primary"
                        startIcon={<CheckIcon />}
                        onClick={handleConfirm}
                        sx={{
                            borderRadius: 2,
                            px: 4,
                            py: 1.5,
                            background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                            fontWeight: 600,
                            fontSize: '1rem'
                        }}
                    >
                        确认并生成视频
                    </Button>
                </Box>
            </Box>

            {/* 编辑对话框 */}
            <Dialog
                open={editDialog.open}
                onClose={() => setEditDialog({ open: false, shot: null, index: -1 })}
                maxWidth="sm"
                fullWidth
                PaperProps={{
                    sx: {
                        bgcolor: '#1e293b',
                        backgroundImage: 'none',
                        border: `1px solid ${alpha(theme.palette.common.white, 0.1)}`,
                        borderRadius: 3
                    }
                }}
            >
                <DialogTitle>编辑镜头 {editDialog.shot?.sequence}</DialogTitle>
                <DialogContent>
                    {editDialog.shot && (
                        <Box sx={{ pt: 2 }}>
                            <TextField
                                fullWidth
                                label="提示词"
                                multiline
                                rows={4}
                                value={editDialog.shot.prompt}
                                onChange={(e) =>
                                    setEditDialog({
                                        ...editDialog,
                                        shot: { ...editDialog.shot!, prompt: e.target.value }
                                    })
                                }
                                sx={{ mb: 2 }}
                            />
                            <TextField
                                fullWidth
                                label="时长 (秒)"
                                type="number"
                                value={editDialog.shot.duration}
                                onChange={(e) =>
                                    setEditDialog({
                                        ...editDialog,
                                        shot: { ...editDialog.shot!, duration: parseFloat(e.target.value) || 5 }
                                    })
                                }
                                inputProps={{ min: 2, max: 10, step: 0.5 }}
                                sx={{ mb: 2 }}
                            />
                            <TextField
                                fullWidth
                                label="镜头类型"
                                value={editDialog.shot.shotType}
                                onChange={(e) =>
                                    setEditDialog({
                                        ...editDialog,
                                        shot: { ...editDialog.shot!, shotType: e.target.value }
                                    })
                                }
                            />
                        </Box>
                    )}
                </DialogContent>
                <DialogActions sx={{ p: 3 }}>
                    <Button onClick={() => setEditDialog({ open: false, shot: null, index: -1 })}>
                        取消
                    </Button>
                    <Button onClick={handleSaveEdit} variant="contained">
                        保存
                    </Button>
                </DialogActions>
            </Dialog>

            {/* 添加镜头对话框 */}
            <AddShotDialog
                open={addDialogOpen}
                onClose={() => setAddDialogOpen(false)}
                onConfirm={handleConfirmAddShot}
            />
        </Box>
    );
};

// 添加镜头对话框组件
interface AddShotDialogProps {
    open: boolean;
    onClose: () => void;
    onConfirm: (prompt: string, duration: number) => void;
}

const AddShotDialog: React.FC<AddShotDialogProps> = ({ open, onClose, onConfirm }) => {
    const theme = useTheme();
    const [prompt, setPrompt] = useState('');
    const [duration, setDuration] = useState(5);

    const handleConfirm = () => {
        if (prompt.trim()) {
            onConfirm(prompt, duration);
            setPrompt('');
            setDuration(5);
        }
    };

    return (
        <Dialog
            open={open}
            onClose={onClose}
            maxWidth="sm"
            fullWidth
            PaperProps={{
                sx: {
                    bgcolor: '#1e293b',
                    backgroundImage: 'none',
                    border: `1px solid ${alpha(theme.palette.common.white, 0.1)}`,
                    borderRadius: 3
                }
            }}
        >
            <DialogTitle>添加新镜头</DialogTitle>
            <DialogContent>
                <Box sx={{ pt: 2 }}>
                    <TextField
                        fullWidth
                        label="镜头描述"
                        multiline
                        rows={4}
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        placeholder="描述这个镜头的内容..."
                        sx={{ mb: 2 }}
                    />
                    <TextField
                        fullWidth
                        label="时长 (秒)"
                        type="number"
                        value={duration}
                        onChange={(e) => setDuration(parseFloat(e.target.value) || 5)}
                        inputProps={{ min: 2, max: 10, step: 0.5 }}
                    />
                </Box>
            </DialogContent>
            <DialogActions sx={{ p: 3 }}>
                <Button onClick={onClose}>取消</Button>
                <Button onClick={handleConfirm} variant="contained" disabled={!prompt.trim()}>
                    添加
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default StoryboardEditor;
