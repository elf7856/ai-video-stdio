import React from 'react';
import {
    Box, Container, Paper, Typography, TextField, Button, Chip, Slider, Grid,
    Stack, Divider, InputAdornment, IconButton, alpha
} from '@mui/material';
import {
    AutoAwesome as MagicIcon,
    ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';
import { STYLE_CONFIG } from '../../constants/styles';

interface InitialSearchViewProps {
    topic: string;
    setTopic: (topic: string) => void;
    style: string;
    setStyle: (style: string) => void;
    targetDuration: number;
    setTargetDuration: (duration: number) => void;
    shotCount: number;
    setShotCount: (count: number) => void;
    onGenerate: () => void;
    onSkipToStudio: () => void;
    onLoadHistory: () => void;
}

const InitialSearchView: React.FC<InitialSearchViewProps> = ({
    topic,
    setTopic,
    style,
    setStyle,
    targetDuration,
    setTargetDuration,
    shotCount,
    setShotCount,
    onGenerate,
    onSkipToStudio,
    onLoadHistory
}) => {
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
                position: 'absolute',
                top: '20%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                width: '60vw',
                height: '60vw',
                background: 'radial-gradient(circle, rgba(255, 64, 129, 0.05) 0%, transparent 70%)',
                zIndex: 0,
                pointerEvents: 'none'
            }} />

            <Container maxWidth="md" sx={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
                <Box>
                    <Box sx={{ mb: 6 }}>
                        <Typography variant="h2" fontWeight={700} sx={{
                            background: 'linear-gradient(to right, #fff 20%, #888 100%)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent',
                            letterSpacing: '-1px',
                            mb: 2
                        }}>
                            Orenix AI
                        </Typography>
                        <Typography variant="h6" color="#666" fontWeight={300}>
                            Next Generation Generative Video Platform
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
                                if (e.key === 'Enter' && topic.trim()) onGenerate();
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
                            onClick={onGenerate}
                            disabled={!topic.trim()}
                        >
                            <ArrowForwardIcon />
                        </IconButton>
                    </Paper>

                    {/* Styles Row */}
                    <Box sx={{ mt: 6 }}>
                        <Typography variant="caption" color="#666" fontWeight={700} sx={{
                            letterSpacing: 1,
                            mb: 3,
                            display: 'block'
                        }}>
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
                                const IconComponent = config.IconComponent;
                                const isActive = style === s;
                                return (
                                    <Chip
                                        key={s}
                                        icon={<span style={{ fontSize: '1.2rem', display: 'flex' }}><IconComponent /></span>}
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
                    <Paper sx={{
                        mt: 4,
                        p: 3,
                        bgcolor: 'rgba(255,255,255,0.05)',
                        borderRadius: 2,
                        border: '1px solid rgba(255,255,255,0.1)'
                    }}>
                        <Grid container spacing={4} alignItems="center">
                            <Grid item xs={12} md={6}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                    <Typography variant="body2" color="#888" fontWeight={700}>DURATION</Typography>
                                    <Typography variant="body2" color="#FF4081" fontWeight={700}>{targetDuration}s</Typography>
                                </Box>
                                <Slider
                                    value={targetDuration}
                                    onChange={(_, v) => setTargetDuration(v as number)}
                                    min={10}
                                    max={300}
                                    step={5}
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
                                    min={3}
                                    max={20}
                                    step={1}
                                    sx={{ color: '#4facfe' }}
                                />
                            </Grid>
                        </Grid>
                    </Paper>

                    <Stack direction="row" spacing={2} justifyContent="center" sx={{ mt: 4 }}>
                        <Button
                            variant="contained"
                            size="large"
                            onClick={onGenerate}
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
                            onClick={onSkipToStudio}
                            sx={{ color: '#666', '&:hover': { color: 'white' } }}
                        >
                            Skip to Studio
                        </Button>
                        <Button
                            variant="text"
                            onClick={onLoadHistory}
                            sx={{ color: '#666', '&:hover': { color: 'white' } }}
                        >
                            History
                        </Button>
                    </Stack>
                </Box>
            </Container>
        </Box>
    );
};

export default InitialSearchView;
