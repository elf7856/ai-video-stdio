import React, { useState } from 'react';
import {
    Box,
    Paper,
    TextField,
    Typography,
    IconButton,
    Button,
    Stack,
    Chip,
    alpha,
    useTheme
} from '@mui/material';
import {
    Edit as EditIcon,
    Delete as DeleteIcon,
    Add as AddIcon,
    Check as CheckIcon,
    Close as CloseIcon
} from '@mui/icons-material';
import type { Shot } from '../api/types';

interface ShotEditorProps {
    shots: Shot[];
    onShotsChange: (shots: Shot[]) => void;
    onConfirm: () => void;
    loading?: boolean;
    compact?: boolean;
}

const ShotEditor: React.FC<ShotEditorProps> = ({ shots, onShotsChange, onConfirm, loading = false, compact = false }) => {
    const theme = useTheme();
    const [editingIndex, setEditingIndex] = useState<number | null>(null);
    const [editedShot, setEditedShot] = useState<Shot | null>(null);

    // 开始编辑
    const handleStartEdit = (index: number) => {
        setEditingIndex(index);
        setEditedShot({ ...shots[index] });
    };

    // 取消编辑
    const handleCancelEdit = () => {
        setEditingIndex(null);
        setEditedShot(null);
    };

    // 保存编辑
    const handleSaveEdit = () => {
        if (editingIndex !== null && editedShot) {
            const newShots = [...shots];
            newShots[editingIndex] = editedShot;
            onShotsChange(newShots);
            setEditingIndex(null);
            setEditedShot(null);
        }
    };

    // 删除镜头
    const handleDelete = (index: number) => {
        const newShots = shots.filter((_, i) => i !== index);
        // 重新排序 sequence
        newShots.forEach((shot, i) => {
            shot.sequence = i + 1;
        });
        onShotsChange(newShots);
    };

    // 添加新镜头
    const handleAdd = () => {
        const newShot: Shot = {
            sequence: shots.length + 1,
            prompt: '',
            duration: 6.0,
            shotType: 'medium shot'
        };
        onShotsChange([...shots, newShot]);
        setEditingIndex(shots.length);
        setEditedShot(newShot);
    };

    // 计算总时长
    const totalDuration = shots.reduce((sum, shot) => sum + shot.duration, 0);

    const renderCard = (shot: Shot, index: number) => {
        const isEditing = editingIndex === index;
        return (
            <Paper
                key={shot.sequence}
                sx={{
                    p: 2,
                    background: alpha(theme.palette.background.paper, 0.6),
                    backdropFilter: 'blur(10px)',
                    border: `1px solid ${alpha(theme.palette.common.white, 0.1)}`,
                    borderRadius: 3,
                    transition: 'all 0.3s',
                    minWidth: compact ? 300 : 'auto',
                    width: compact ? 300 : 'auto',
                    flexShrink: 0,
                    '&:hover': {
                        borderColor: alpha(theme.palette.primary.main, 0.5),
                        boxShadow: `0 4px 20px ${alpha(theme.palette.primary.main, 0.15)}`
                    }
                }}
            >
                {isEditing ? (
                    // 编辑模式
                    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                        <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                            <Chip label={`Shot ${shot.sequence}`} color="primary" size="small" />
                            <Chip label="Editing" color="warning" size="small" />
                        </Box>

                        <Stack spacing={2} sx={{ flex: 1 }}>
                            <TextField
                                fullWidth
                                multiline
                                rows={compact ? 2 : 3}
                                label="Prompt"
                                value={editedShot?.prompt || ''}
                                onChange={(e) => setEditedShot(editedShot ? { ...editedShot, prompt: e.target.value } : null)}
                                variant="outlined"
                                size={compact ? "small" : "medium"}
                                sx={{ 
                                    '& .MuiOutlinedInput-root': { bgcolor: alpha('#000', 0.2) }
                                }}
                            />

                            <Box sx={{ display: 'flex', gap: 1 }}>
                                <TextField
                                    label="Duration"
                                    type="number"
                                    size="small"
                                    value={editedShot?.duration || 0}
                                    onChange={(e) => setEditedShot(editedShot ? { ...editedShot, duration: parseFloat(e.target.value) } : null)}
                                    inputProps={{ min: 1, max: 8, step: 0.5 }}
                                    sx={{ width: 80 }}
                                />
                                <TextField
                                    label="Type"
                                    size="small"
                                    value={editedShot?.shotType || ''}
                                    onChange={(e) => setEditedShot(editedShot ? { ...editedShot, shotType: e.target.value } : null)}
                                    sx={{ flex: 1 }}
                                />
                            </Box>
                        </Stack>

                        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', mt: 2 }}>
                            <IconButton size="small" onClick={handleCancelEdit} sx={{ bgcolor: alpha(theme.palette.error.main, 0.1) }}>
                                <CloseIcon fontSize="small" />
                            </IconButton>
                            <IconButton size="small" onClick={handleSaveEdit} disabled={!editedShot?.prompt.trim()} sx={{ bgcolor: alpha(theme.palette.success.main, 0.1), color: 'success.light' }}>
                                <CheckIcon fontSize="small" />
                            </IconButton>
                        </Box>
                    </Box>
                ) : (
                    // 查看模式
                    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                                <Chip label={`#${shot.sequence}`} color="primary" size="small" sx={{ height: 20 }} />
                                <Typography variant="caption" color="text.secondary">{shot.duration}s</Typography>
                            </Box>
                            <Box sx={{ display: 'flex', gap: 0.5 }}>
                                <IconButton
                                    size="small"
                                    onClick={() => handleStartEdit(index)}
                                    sx={{ color: 'primary.main', p: 0.5 }}
                                >
                                    <EditIcon fontSize="small" />
                                </IconButton>
                                <IconButton
                                    size="small"
                                    onClick={() => handleDelete(index)}
                                    sx={{ color: 'error.main', p: 0.5 }}
                                    disabled={shots.length <= 1}
                                >
                                    <DeleteIcon fontSize="small" />
                                </IconButton>
                            </Box>
                        </Box>
                        <Typography variant="body2" color="white" sx={{ 
                            lineHeight: 1.5, 
                            fontSize: '0.85rem',
                            flex: 1,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            display: '-webkit-box',
                            WebkitLineClamp: compact ? 3 : 10,
                            WebkitBoxOrient: 'vertical'
                         }}>
                            {shot.prompt}
                        </Typography>
                        <Box sx={{ mt: 'auto', pt: 1 }}>
                             {shot.shotType && (
                                <Typography variant="caption" color="text.secondary" sx={{ bgcolor: alpha('#fff', 0.05), px: 0.5, borderRadius: 0.5 }}>
                                    {shot.shotType}
                                </Typography>
                            )}
                        </Box>
                    </Box>
                )}
            </Paper>
        );
    };

    return (
        <Box>
            {/* Header - Only show in non-compact mode */}
            {!compact && (
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                    <Box>
                        <Typography variant="h6" fontWeight={700}>
                            Shot List & Editing
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Total {shots.length} shots, {totalDuration.toFixed(1)}s duration
                        </Typography>
                    </Box>
                    <Button
                        variant="contained"
                        color="primary"
                        size="large"
                        onClick={onConfirm}
                        disabled={loading || shots.length === 0}
                    >
                        {loading ? 'Generating...' : 'Confirm & Generate Videos'}
                    </Button>
                </Box>
            )}

            {/* List */}
            {compact ? (
                <Box sx={{ display: 'flex', gap: 2, height: '100%', alignItems: 'stretch' }}>
                     {shots.map((shot, index) => renderCard(shot, index))}
                     <Button
                        variant="outlined"
                        onClick={handleAdd}
                        sx={{
                            minWidth: 100,
                            borderRadius: 3,
                            borderStyle: 'dashed',
                            borderColor: alpha(theme.palette.common.white, 0.2),
                            color: 'text.secondary',
                            flexShrink: 0,
                            '&:hover': {
                                borderColor: 'primary.main',
                                color: 'primary.main',
                                borderStyle: 'dashed'
                            }
                        }}
                    >
                        <AddIcon />
                    </Button>
                     {/* Floating Confirm Button for Compact Mode */}
                     <Button
                         variant="contained"
                         color="primary"
                         onClick={onConfirm}
                         disabled={loading || shots.length === 0}
                         sx={{
                             position: 'fixed',
                             bottom: 220, // Above the bottom panel
                             right: 32,
                             zIndex: 100,
                             boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
                         }}
                     >
                         {loading ? 'Generating...' : 'Render All Shots'}
                     </Button>
                </Box>
            ) : (
                <Stack spacing={2}>
                    {shots.map((shot, index) => renderCard(shot, index))}
                    <Button
                        fullWidth
                        variant="outlined"
                        startIcon={<AddIcon />}
                        onClick={handleAdd}
                        sx={{ py: 2, borderStyle: 'dashed' }}
                    >
                        Add New Shot
                    </Button>
                </Stack>
            )}
        </Box>
    );
};

export default ShotEditor;
