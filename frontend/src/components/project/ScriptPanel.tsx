import React from 'react';
import { Box, Paper, Typography, Tabs, Tab, Stack, Button, LinearProgress, CircularProgress } from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import type { Shot, GeneratedVideo } from '../../api/types';

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
}

interface ScriptPanelProps {
    projectData: ProjectData | null;
    currentShot: ShotWithVideo | undefined;
    currentShotIndex: number;
    activeTab: number;
    onTabChange: (value: number) => void;
    onEditShot: (index: number) => void;
    onDeleteShot: (index: number) => void;
    onConfirmGeneration?: () => void;
    width?: number;
}

export const ScriptPanel: React.FC<ScriptPanelProps> = ({
    projectData,
    currentShot,
    currentShotIndex,
    activeTab,
    onTabChange,
    onEditShot,
    onDeleteShot,
    onConfirmGeneration,
    width = 320,
}) => {
    // 判断是否正在生成
    const isGenerating = projectData?.status && ['pending', 'generating_script', 'generating_videos', 'checking_quality', 'merging_videos'].includes(projectData.status);

    // 判断是否等待确认
    const isWaitingConfirmation = projectData?.status === 'waiting_confirmation';

    // 状态文本映射
    const getStatusText = (status: string): string => {
        const statusMap: Record<string, string> = {
            'pending': '准备中...',
            'generating_script': '正在生成脚本...',
            'generating_videos': '正在生成视频片段...',
            'checking_quality': '正在检查质量...',
            'merging_videos': '正在合并视频...',
            'completed': '生成完成',
            'failed': '生成失败',
            'cancelled': '已取消'
        };
        return statusMap[status] || status;
    };

    return (
        <Paper sx={{
            width,
            flexShrink: 0,
            bgcolor: '#0f0f0f',
            borderLeft: '1px solid #222',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden'
        }} square>
            <Tabs
                value={activeTab === 0 ? 0 : activeTab === 1 ? 1 : 2}
                onChange={(_, v) => onTabChange(v)}
                variant="fullWidth"
                sx={{
                    minHeight: 48,
                    borderBottom: '1px solid #222',
                    '& .MuiTab-root': { minHeight: 48, fontSize: '0.75rem', color: '#666' },
                    '& .Mui-selected': { color: '#fff' },
                    '& .MuiTabs-indicator': { backgroundColor: '#FF4081' }
                }}
            >
                <Tab label="Script" />
                <Tab label={isGenerating ? "生成状态" : "Logs"} />
            </Tabs>

            <Box sx={{ flex: 1, p: 2, overflowY: 'auto' }}>
                {activeTab === 0 && (
                    <Box>
                        <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                            Script
                        </Typography>
                        <Paper sx={{
                            p: 2,
                            bgcolor: '#1a1a1a',
                            borderRadius: 1,
                            border: '1px solid #333',
                            minHeight: 150,
                            mb: 3
                        }}>
                            <Typography variant="body2" color="#ccc" sx={{
                                whiteSpace: 'pre-wrap',
                                lineHeight: 1.6,
                                fontFamily: 'monospace',
                                fontSize: '0.85rem'
                            }}>
                                {projectData?.script || 'No script available'}
                            </Typography>
                        </Paper>

                        <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                            镜头列表 ({projectData?.shots?.length || 0} 个镜头)
                        </Typography>

                        {/* 所有镜头的prompt列表 */}
                        <Stack spacing={1.5} mb={3}>
                            {projectData?.shots?.map((shot, index) => (
                                <Paper key={index} sx={{
                                    p: 2,
                                    bgcolor: currentShotIndex === index ? '#1a2332' : '#1a1a1a',
                                    borderRadius: 1,
                                    border: currentShotIndex === index ? '1px solid #6366f1' : '1px solid #333',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s',
                                    '&:hover': {
                                        bgcolor: '#1f1f1f',
                                        borderColor: '#555'
                                    }
                                }}>
                                    <Stack direction="row" spacing={1} alignItems="flex-start" mb={1}>
                                        <Typography variant="caption" sx={{
                                            bgcolor: currentShotIndex === index ? '#6366f1' : '#333',
                                            color: 'white',
                                            px: 1,
                                            py: 0.5,
                                            borderRadius: 0.5,
                                            fontWeight: 600,
                                            minWidth: 60,
                                            textAlign: 'center'
                                        }}>
                                            Shot {shot.sequence}
                                        </Typography>
                                        <Typography variant="caption" color="#888">
                                            {shot.duration}s
                                        </Typography>
                                    </Stack>
                                    <Typography variant="body2" color="#ccc" sx={{
                                        lineHeight: 1.5,
                                        fontSize: '0.85rem',
                                        mb: 1.5
                                    }}>
                                        {shot.prompt}
                                    </Typography>

                                    {/* 显示参考图 */}
                                    {shot.imagePath && (
                                        <Box sx={{
                                            width: '100%',
                                            borderRadius: 1,
                                            overflow: 'hidden',
                                            border: '1px solid #333',
                                            mb: 1
                                        }}>
                                            <img
                                                src={`http://localhost:8000${shot.imagePath}`}
                                                alt={`Shot ${shot.sequence} reference`}
                                                style={{
                                                    width: '100%',
                                                    height: 'auto',
                                                    display: 'block'
                                                }}
                                                onError={(e) => {
                                                    e.currentTarget.style.display = 'none';
                                                }}
                                            />
                                        </Box>
                                    )}

                                    {/* 显示图片或视频状态 */}
                                    <Stack direction="row" spacing={1}>
                                        {shot.imagePath && (
                                            <Typography variant="caption" sx={{
                                                bgcolor: '#2d5016',
                                                color: '#69f0ae',
                                                px: 1,
                                                py: 0.3,
                                                borderRadius: 0.5,
                                                fontSize: '0.7rem'
                                            }}>
                                                ✓ 分镜图
                                            </Typography>
                                        )}
                                        {shot.videoPath && (
                                            <Typography variant="caption" sx={{
                                                bgcolor: '#1a237e',
                                                color: '#82b1ff',
                                                px: 1,
                                                py: 0.3,
                                                borderRadius: 0.5,
                                                fontSize: '0.7rem'
                                            }}>
                                                ✓ 视频
                                            </Typography>
                                        )}
                                    </Stack>
                                </Paper>
                            ))}
                        </Stack>

                        {/* 确认生成按钮 - 只在等待确认状态显示 */}
                        {isWaitingConfirmation && onConfirmGeneration && (
                            <Button
                                fullWidth
                                variant="contained"
                                size="large"
                                onClick={onConfirmGeneration}
                                sx={{
                                    background: 'linear-gradient(45deg, #6366f1, #ec4899)',
                                    color: 'white',
                                    fontWeight: 600,
                                    py: 1.5,
                                    textTransform: 'none',
                                    fontSize: '1rem',
                                    '&:hover': {
                                        background: 'linear-gradient(45deg, #5558e3, #db3a87)',
                                    }
                                }}
                            >
                                确认生成视频
                            </Button>
                        )}

                        <Typography variant="subtitle2" fontWeight={700} gutterBottom sx={{ mt: 3 }}>
                            Current Shot
                        </Typography>
                        <Paper sx={{
                            p: 2,
                            bgcolor: '#1a1a1a',
                            borderRadius: 1,
                            border: '1px solid #333'
                        }}>
                            <Typography variant="caption" color="text.secondary" display="block" mb={1}>
                                Prompt:
                            </Typography>
                            <Typography variant="body2" color="#ccc">
                                {currentShot?.prompt || 'No prompt'}
                            </Typography>
                            <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                                <Button
                                    size="small"
                                    variant="outlined"
                                    startIcon={<EditIcon />}
                                    onClick={() => onEditShot(currentShotIndex)}
                                    sx={{ borderColor: '#333', color: '#888' }}
                                >
                                    Edit
                                </Button>
                                <Button
                                    size="small"
                                    variant="outlined"
                                    color="error"
                                    startIcon={<DeleteIcon />}
                                    onClick={() => onDeleteShot(currentShotIndex)}
                                    sx={{ borderColor: '#333' }}
                                >
                                    Delete
                                </Button>
                            </Stack>
                        </Paper>
                    </Box>
                )}

                {activeTab === 1 && isGenerating && (
                    <Box>
                        <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                            生成状态
                        </Typography>

                        {/* 进度信息 */}
                        <Paper sx={{
                            p: 2,
                            bgcolor: '#1a1a1a',
                            borderRadius: 1,
                            border: '1px solid #333',
                            mb: 2
                        }}>
                            <Stack spacing={2}>
                                {/* 状态指示器 */}
                                <Stack direction="row" spacing={2} alignItems="center">
                                    <CircularProgress size={24} sx={{ color: '#6366f1' }} />
                                    <Box flex={1}>
                                        <Typography variant="body2" color="white" fontWeight={600}>
                                            {getStatusText(projectData?.status || 'pending')}
                                        </Typography>
                                        <Typography variant="caption" color="#888">
                                            {Math.round(projectData?.progress || 0)}% 完成
                                        </Typography>
                                    </Box>
                                </Stack>

                                {/* 进度条 */}
                                <LinearProgress
                                    variant="determinate"
                                    value={projectData?.progress || 0}
                                    sx={{
                                        height: 6,
                                        borderRadius: 3,
                                        bgcolor: '#333',
                                        '& .MuiLinearProgress-bar': {
                                            background: 'linear-gradient(45deg, #6366f1, #ec4899)',
                                            borderRadius: 3
                                        }
                                    }}
                                />
                            </Stack>
                        </Paper>

                        {/* 项目信息 */}
                        <Paper sx={{
                            p: 2,
                            bgcolor: '#1a1a1a',
                            borderRadius: 1,
                            border: '1px solid #333',
                            mb: 2
                        }}>
                            <Typography variant="caption" color="#888" display="block" mb={0.5}>
                                主题
                            </Typography>
                            <Typography variant="body2" color="white" mb={1.5}>
                                {projectData?.topic || '未命名项目'}
                            </Typography>

                            <Typography variant="caption" color="#888" display="block" mb={0.5}>
                                风格
                            </Typography>
                            <Typography variant="body2" color="white">
                                {projectData?.style || '默认'}
                            </Typography>
                        </Paper>

                        {/* 实时日志 */}
                        <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                            实时日志
                        </Typography>
                        <Paper sx={{
                            p: 2,
                            bgcolor: '#0a0a0a',
                            borderRadius: 1,
                            border: '1px solid #333',
                            fontFamily: 'monospace',
                            fontSize: '0.75rem',
                            maxHeight: 300,
                            overflowY: 'auto'
                        }}>
                            {projectData?.logs && projectData.logs.length > 0 ? (
                                <Stack spacing={0.5}>
                                    {projectData.logs.slice(-10).map((log, index) => (
                                        <Typography key={index} sx={{
                                            color: log.level === 'error' ? '#ff5252' :
                                                log.level === 'success' ? '#69f0ae' :
                                                    log.level === 'warning' ? '#ffd740' : '#888',
                                            fontFamily: 'monospace',
                                            fontSize: '0.75rem',
                                            wordBreak: 'break-word'
                                        }}>
                                            [{log.timestamp}] {log.message}
                                        </Typography>
                                    ))}
                                </Stack>
                            ) : (
                                <Typography variant="body2" color="#666">
                                    等待日志输出...
                                </Typography>
                            )}
                        </Paper>
                    </Box>
                )}

                {activeTab === 1 && !isGenerating && (
                    <Box>
                        <Typography variant="subtitle2" fontWeight={700} gutterBottom>
                            Execution Logs
                        </Typography>
                        <Paper sx={{
                            p: 2,
                            bgcolor: '#0a0a0a',
                            borderRadius: 1,
                            border: '1px solid #333',
                            fontFamily: 'monospace',
                            fontSize: '0.85rem',
                            minHeight: 400
                        }}>
                            {projectData?.logs && projectData.logs.length > 0 ? (
                                <Stack spacing={1}>
                                    {projectData.logs.map((log, index) => (
                                        <Box key={index} sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
                                            <Typography variant="caption" color="#666" sx={{ minWidth: 60, fontFamily: 'monospace' }}>
                                                {log.timestamp}
                                            </Typography>
                                            <Typography sx={{
                                                color: log.level === 'error' ? '#ff5252' :
                                                    log.level === 'success' ? '#69f0ae' :
                                                        log.level === 'warning' ? '#ffd740' : '#e0e0e0',
                                                fontFamily: 'monospace',
                                                wordBreak: 'break-word',
                                                fontSize: '0.8rem'
                                            }}>
                                                {log.level === 'success' && '✅ '}
                                                {log.level === 'error' && '❌ '}
                                                {log.level === 'warning' && '⚠️ '}
                                                {log.message}
                                            </Typography>
                                        </Box>
                                    ))}
                                </Stack>
                            ) : (
                                <Typography color="#666" fontStyle="italic">No logs available</Typography>
                            )}
                        </Paper>
                    </Box>
                )}
            </Box>
        </Paper>
    );
};
