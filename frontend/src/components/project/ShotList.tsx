import React from 'react';
import { Box, Paper, Typography, Tabs, Tab, Grid, useTheme } from '@mui/material';
import { VideoLibrary as VideoIcon, TextFields as TextIcon, MusicNote as MusicIcon } from '@mui/icons-material';
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
}

export const ShotList: React.FC<ShotListProps> = ({
    orderedShots,
    currentShotIndex,
    activeTab,
    onTabChange,
    onShotSelect,
}) => {
    const theme = useTheme();

    return (
        <Paper sx={{
            width: 300,
            bgcolor: '#0f0f0f',
            borderRight: '1px solid #222',
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
                {/* Asset Grid */}
                <Grid container spacing={1}>
                    {orderedShots.map((shot, i) => (
                        <Grid item xs={6} key={i}>
                            <Box sx={{
                                aspectRatio: '16/9',
                                bgcolor: '#000',
                                borderRadius: 1,
                                border: currentShotIndex === i ? '2px solid #FF4081' : '1px solid #333',
                                cursor: 'pointer',
                                overflow: 'hidden',
                                position: 'relative',
                                '&:hover': { borderColor: theme.palette.primary.main }
                            }}
                                onClick={() => onShotSelect(i)}
                            >
                                {shot.videoData?.videoPath ? (
                                    <video
                                        src={getFullUrl(shot.videoData.videoPath)}
                                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                        muted
                                        onMouseOver={e => e.currentTarget.play()}
                                        onMouseOut={e => { e.currentTarget.pause(); e.currentTarget.currentTime = 0; }}
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
                                        <Typography variant="caption" color="#666">Shot {shot.sequence}</Typography>
                                    </Box>
                                )}
                                <Box sx={{ position: 'absolute', bottom: 2, right: 2, bgcolor: 'rgba(0,0,0,0.8)', px: 0.5, borderRadius: 0.5 }}>
                                    <Typography variant="caption" sx={{ fontSize: '0.6rem' }}>#{shot.sequence}</Typography>
                                </Box>
                            </Box>
                        </Grid>
                    ))}
                </Grid>
            </Box>
        </Paper>
    );
};
