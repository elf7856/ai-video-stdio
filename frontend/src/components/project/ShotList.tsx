import React from 'react';
import { Box, Paper, Typography, Tabs, Tab, Grid, useTheme, CircularProgress, Tooltip } from '@mui/material';
import { VideoLibrary as VideoIcon, TextFields as TextIcon, MusicNote as MusicIcon, CheckCircle as CheckIcon, ErrorOutline as ErrorIcon, HourglassEmpty as PendingIcon } from '@mui/icons-material';
import type { Shot, GeneratedVideo } from '../../api/types';
import { getFullUrl } from '../../utils/url';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

interface ShotListProps {
    orderedShots: ShotWithVideo[];
    currentShotIndex: number;
    activeTab: number;
    onTabChange: (value: number) => void;
    onShotSelect: (index: number) => void;
    width?: number | string;
}

const StatusBadge: React.FC<{ status?: string }> = ({ status }) => {
    if (!status || status === 'success' || status === 'completed') {
        return status === 'success' || status === 'completed' ? (
            <CheckIcon sx={{ fontSize: 12, color: '#4caf50' }} />
        ) : null;
    }
    if (status === 'generating') {
        return <CircularProgress size={10} sx={{ color: '#FF4081' }} />;
    }
    if (status === 'failed') {
        return <ErrorIcon sx={{ fontSize: 12, color: '#f44336' }} />;
    }
    return <PendingIcon sx={{ fontSize: 12, color: '#888' }} />;
};

export const ShotList: React.FC<ShotListProps> = ({
    orderedShots,
    currentShotIndex,
    activeTab,
    onTabChange,
    onShotSelect,
    width = '100%',
}) => {
    const theme = useTheme();

    return (
        <Paper sx={{
            width,
            flexShrink: 0,
            bgcolor: '#161616',
            borderRight: '1px solid #2e2e2e',
            display: 'flex',
            flexDirection: 'column'
        }} square>
            <Tabs
                value={activeTab}
                onChange={(_, v) => onTabChange(v)}
                variant="fullWidth"
                sx={{
                    minHeight: 48,
                    '& .MuiTab-root': { minHeight: 48, fontSize: '0.75rem', color: '#666' },
                    '& .Mui-selected': { color: '#fff' },
                    borderBottom: '1px solid #2e2e2e',
                    '& .MuiTabs-indicator': { backgroundColor: '#FF4081' }
                }}
            >
                <Tab icon={<VideoIcon fontSize="small" />} label="Media" />
                <Tab icon={<TextIcon fontSize="small" />} label="Text" />
                <Tab icon={<MusicIcon fontSize="small" />} label="Audio" />
            </Tabs>

            <Box sx={{ flex: 1, p: 2, overflowY: 'auto' }}>
                <Typography variant="caption" color="text.secondary" display="block" mb={2}>
                    Project Assets ({orderedShots.length})
                </Typography>

                <Grid container spacing={1}>
                    {orderedShots.map((shot, i) => {
                        const videoPath = shot.videoData?.videoPath || shot.videoPath;
                        const imagePath = shot.imagePath;
                        const status = shot.status;
                        const isSelected = currentShotIndex === i;
                        const isGenerating = status === 'generating';
                        const tooltip = status === 'failed'
                            ? `Shot ${shot.sequence} 生成失败：${shot.error || '请查看执行日志'}`
                            : (shot.prompt || '');

                        return (
                            <Grid item xs={6} key={i}>
                                <Tooltip title={tooltip} placement="right" arrow>
                                    <Box
                                        onClick={() => onShotSelect(i)}
                                        sx={{
                                            aspectRatio: '16/9',
                                            bgcolor: '#000',
                                            borderRadius: 1,
                                            border: isSelected ? '2px solid #FF4081' : '1px solid #333',
                                            cursor: 'pointer',
                                            overflow: 'hidden',
                                            position: 'relative',
                                            '&:hover': { borderColor: theme.palette.primary.main }
                                        }}
                                    >
                                        {/* 优先显示视频，其次分镜图，最后占位符 */}
                                        {videoPath ? (
                                            <video
                                                src={getFullUrl(videoPath)}
                                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                                muted
                                                onMouseOver={e => e.currentTarget.play()}
                                                onMouseOut={e => { e.currentTarget.pause(); e.currentTarget.currentTime = 0; }}
                                            />
                                        ) : imagePath ? (
                                            <img
                                                src={getFullUrl(imagePath)}
                                                alt={`Shot ${shot.sequence}`}
                                                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                            />
                                        ) : (
                                            <Box sx={{
                                                width: '100%',
                                                height: '100%',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                bgcolor: '#1a1a1a'
                                            }}>
                                                {isGenerating
                                                    ? <CircularProgress size={20} sx={{ color: '#FF4081' }} />
                                                    : <Typography variant="caption" color="#555">#{shot.sequence}</Typography>
                                                }
                                            </Box>
                                        )}

                                        {/* 生成中遮罩 */}
                                        {isGenerating && (videoPath || imagePath) && (
                                            <Box sx={{
                                                position: 'absolute', inset: 0,
                                                bgcolor: 'rgba(0,0,0,0.45)',
                                                display: 'flex', alignItems: 'center', justifyContent: 'center'
                                            }}>
                                                <CircularProgress size={20} sx={{ color: '#FF4081' }} />
                                            </Box>
                                        )}
                                        {status === 'failed' && (
                                            <Box sx={{
                                                position: 'absolute',
                                                inset: 0,
                                                bgcolor: 'rgba(0,0,0,0.42)',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                textAlign: 'center',
                                                px: 1
                                            }}>
                                                <Typography variant="caption" sx={{ color: '#ff8a80', fontWeight: 700, fontSize: '0.65rem' }}>
                                                    生成失败
                                                </Typography>
                                            </Box>
                                        )}

                                        {/* 底部角标：序号 + 状态 */}
                                        <Box sx={{
                                            position: 'absolute', bottom: 2, left: 2, right: 2,
                                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                            px: 0.5
                                        }}>
                                            <Box sx={{ bgcolor: 'rgba(0,0,0,0.75)', px: 0.5, borderRadius: 0.5 }}>
                                                <Typography variant="caption" sx={{ fontSize: '0.6rem', color: '#ccc' }}>
                                                    #{shot.sequence}
                                                </Typography>
                                            </Box>
                                            <Box sx={{ bgcolor: 'rgba(0,0,0,0.75)', px: 0.5, borderRadius: 0.5, display: 'flex', alignItems: 'center' }}>
                                                <StatusBadge status={status} />
                                            </Box>
                                        </Box>
                                    </Box>
                                </Tooltip>
                            </Grid>
                        );
                    })}
                </Grid>
            </Box>
        </Paper>
    );
};
