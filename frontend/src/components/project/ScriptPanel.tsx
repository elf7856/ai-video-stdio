import React from 'react';
import { Box, Paper, Typography, Tabs, Tab, Stack, Button } from '@mui/material';
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
}

export const ScriptPanel: React.FC<ScriptPanelProps> = ({
    projectData,
    currentShot,
    currentShotIndex,
    activeTab,
    onTabChange,
    onEditShot,
    onDeleteShot,
}) => {
    return (
        <Paper sx={{
            width: 320,
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
                <Tab label="Logs" />
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
                            minHeight: 200
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

                {activeTab === 1 && (
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
