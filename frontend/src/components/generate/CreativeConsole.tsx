import React from 'react';
import {
    Box, Paper, Tabs, Tab, Typography, TextField, Button, Slider, Stack,
    Accordion, AccordionSummary, AccordionDetails, Select, MenuItem,
    FormControlLabel, Switch
} from '@mui/material';
import {
    ExpandMore as ExpandMoreIcon,
    Terminal as TerminalIcon,
    Error as ErrorIcon
} from '@mui/icons-material';
import { AnimatePresence, motion } from 'framer-motion';
import { STYLE_CONFIG } from '../../constants/styles';
import StyleCard from './StyleCard';

interface CreativeConsoleProps {
    activeTab: number;
    setActiveTab: (tab: number) => void;
    topic: string;
    setTopic: (topic: string) => void;
    style: string;
    setStyle: (style: string) => void;
    targetDuration: number;
    setTargetDuration: (duration: number) => void;
    shotCount: number;
    setShotCount: (count: number) => void;
    additionalRequirements: string;
    setAdditionalRequirements: (req: string) => void;
    enableNarration: boolean;
    setEnableNarration: (enabled: boolean) => void;
    narrationVoice: string;
    setNarrationVoice: (voice: string) => void;
    narrationSpeed: number;
    setNarrationSpeed: (speed: number) => void;
    pacingStrategy: string;
    setPacingStrategy: (strategy: string) => void;
    scriptResult: any;
    videoTask: any;
    loading: boolean;
    videoGenerating: boolean;
    error: string | null;
    onGenerateVideo: () => void;
    onGenerateScript: () => void;
    estimatedDuration: number | null;
}

const CreativeConsole: React.FC<CreativeConsoleProps> = ({
    activeTab,
    setActiveTab,
    topic,
    setTopic,
    style,
    setStyle,
    targetDuration,
    setTargetDuration,
    shotCount,
    setShotCount,
    additionalRequirements,
    setAdditionalRequirements,
    enableNarration,
    setEnableNarration,
    narrationVoice,
    setNarrationVoice,
    narrationSpeed,
    setNarrationSpeed,
    pacingStrategy,
    setPacingStrategy,
    scriptResult,
    videoTask,
    loading,
    videoGenerating,
    error,
    onGenerateVideo,
    onGenerateScript,
    estimatedDuration
}) => {
    return (
        <Paper sx={{
            width: { xs: '100%', md: 400 },
            height: '100%',
            background: '#111111',
            borderRight: '1px solid #222',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 10,
            flexShrink: 0
        }} square elevation={0}>
            {/* Tabs */}
            <Box sx={{ borderBottom: '1px solid #222' }}>
                <Tabs
                    value={activeTab}
                    onChange={(_, v) => setActiveTab(v)}
                    variant="fullWidth"
                    sx={{
                        '& .MuiTab-root': { color: '#666', minHeight: 48 },
                        '& .Mui-selected': { color: '#fff' },
                        '& .MuiTabs-indicator': { backgroundColor: '#FF4081' }
                    }}
                >
                    <Tab label="Create" />
                    <Tab label="Script" disabled={!scriptResult} />
                    <Tab label="Settings" />
                    <Tab icon={<TerminalIcon fontSize="small" />} label="Logs" disabled={!videoTask} />
                </Tabs>
            </Box>

            {/* Content Area */}
            <Box sx={{ flex: 1, overflowY: 'auto', p: 3 }}>
                <AnimatePresence mode="wait">
                    {activeTab === 0 && (
                        <motion.div
                            key="create"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            transition={{ duration: 0.2 }}
                        >
                            <Typography variant="caption" color="#666" fontWeight={700} sx={{
                                letterSpacing: 1,
                                mb: 1,
                                display: 'block'
                            }}>
                                TOPIC & VISION
                            </Typography>
                            <TextField
                                fullWidth
                                multiline
                                minRows={4}
                                placeholder="What do you want to create today? (e.g. 'A futuristic city tour...')"
                                value={topic}
                                onChange={(e) => setTopic(e.target.value)}
                                variant="outlined"
                                sx={{
                                    mb: 3,
                                    '& .MuiOutlinedInput-root': {
                                        bgcolor: '#1a1a1a',
                                        color: 'white',
                                        borderRadius: 2,
                                        '& fieldset': { borderColor: '#333' },
                                        '&:hover fieldset': { borderColor: '#555' },
                                        '&.Mui-focused fieldset': { borderColor: '#FF4081' }
                                    }
                                }}
                            />

                            <Typography variant="caption" color="#666" fontWeight={700} sx={{
                                letterSpacing: 1,
                                mb: 2,
                                display: 'block'
                            }}>
                                STYLE
                            </Typography>
                            <Box sx={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(5, 1fr)',
                                gap: 2,
                                mb: 4
                            }}>
                                {Object.keys(STYLE_CONFIG).map((s) => (
                                    <StyleCard
                                        key={s}
                                        name={s}
                                        active={style === s}
                                        onClick={() => setStyle(s)}
                                    />
                                ))}
                            </Box>

                            <Typography variant="caption" color="#666" fontWeight={700} sx={{
                                letterSpacing: 1,
                                mb: 2,
                                display: 'block'
                            }}>
                                SPECIFICATIONS
                            </Typography>
                            <Paper sx={{
                                p: 2,
                                bgcolor: '#1a1a1a',
                                borderRadius: 2,
                                border: '1px solid #333',
                                mb: 3
                            }}>
                                <Box sx={{ mb: 2 }}>
                                    <Typography variant="caption" color="#888" display="block" mb={0.5}>
                                        Duration ({targetDuration}s)
                                    </Typography>
                                    <Slider
                                        value={targetDuration}
                                        onChange={(_, v) => setTargetDuration(v as number)}
                                        min={10}
                                        max={300}
                                        step={5}
                                        sx={{ color: '#FF4081' }}
                                    />
                                </Box>
                                <Box>
                                    <Typography variant="caption" color="#888" display="block" mb={0.5}>
                                        Shot Count ({shotCount})
                                    </Typography>
                                    <Slider
                                        value={shotCount}
                                        onChange={(_, v) => setShotCount(v as number)}
                                        min={3}
                                        max={20}
                                        step={1}
                                        sx={{ color: '#4facfe' }}
                                    />
                                </Box>
                            </Paper>

                            <Accordion sx={{
                                bgcolor: 'transparent',
                                boxShadow: 'none',
                                border: '1px solid #222',
                                borderRadius: 2,
                                mb: 3,
                                '&:before': { display: 'none' }
                            }}>
                                <AccordionSummary expandIcon={<ExpandMoreIcon sx={{ color: '#666' }} />}>
                                    <Typography variant="body2" color="#888">Advanced Requirements</Typography>
                                </AccordionSummary>
                                <AccordionDetails>
                                    <TextField
                                        fullWidth
                                        size="small"
                                        placeholder="Specific details, tone, keywords..."
                                        value={additionalRequirements}
                                        onChange={(e) => setAdditionalRequirements(e.target.value)}
                                        variant="outlined"
                                        sx={{
                                            '& .MuiOutlinedInput-root': {
                                                bgcolor: '#1a1a1a',
                                                color: 'white',
                                                '& fieldset': { borderColor: '#333' }
                                            }
                                        }}
                                    />
                                </AccordionDetails>
                            </Accordion>

                            {/* Action Buttons */}
                            <Stack spacing={2} sx={{ mt: 4 }}>
                                <Button
                                    fullWidth
                                    variant="contained"
                                    size="large"
                                    onClick={onGenerateVideo}
                                    disabled={loading || videoGenerating || !topic.trim()}
                                    sx={{
                                        bgcolor: '#FF4081',
                                        color: 'white',
                                        py: 1.5,
                                        fontWeight: 700,
                                        '&:hover': { bgcolor: '#F50057' },
                                        '&:disabled': { bgcolor: '#333', color: '#666' }
                                    }}
                                >
                                    {videoGenerating ? 'Directing AI...' : 'Generate Video'}
                                </Button>
                                <Button
                                    fullWidth
                                    variant="outlined"
                                    onClick={onGenerateScript}
                                    disabled={loading || videoGenerating || !topic.trim()}
                                    sx={{
                                        borderColor: '#333',
                                        color: '#888',
                                        '&:hover': { borderColor: '#666', color: 'white', bgcolor: 'transparent' }
                                    }}
                                >
                                    Generate Script Only
                                </Button>
                            </Stack>

                            {error && (
                                <Paper sx={{
                                    mt: 3,
                                    p: 2,
                                    bgcolor: 'rgba(211, 47, 47, 0.1)',
                                    color: '#ff5252',
                                    border: '1px solid rgba(211, 47, 47, 0.3)',
                                    display: 'flex',
                                    gap: 1
                                }}>
                                    <ErrorIcon fontSize="small" />
                                    <Typography variant="caption">{error}</Typography>
                                </Paper>
                            )}
                        </motion.div>
                    )}

                    {activeTab === 1 && scriptResult && (
                        <motion.div
                            key="script"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            transition={{ duration: 0.2 }}
                        >
                            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
                                <Typography variant="h6" fontSize="1rem" fontWeight={700}>Script</Typography>
                            </Stack>
                            <Paper sx={{
                                p: 2,
                                bgcolor: '#1a1a1a',
                                borderRadius: 2,
                                border: '1px solid #333',
                                minHeight: 300
                            }}>
                                <Typography variant="body2" color="#ccc" sx={{
                                    whiteSpace: 'pre-wrap',
                                    lineHeight: 1.6,
                                    fontFamily: 'monospace'
                                }}>
                                    {scriptResult.script}
                                </Typography>
                            </Paper>
                        </motion.div>
                    )}

                    {activeTab === 2 && (
                        <motion.div
                            key="settings"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            transition={{ duration: 0.2 }}
                        >
                            <Typography variant="caption" color="#666" fontWeight={700} sx={{
                                letterSpacing: 1,
                                mb: 2,
                                display: 'block'
                            }}>
                                VOICEOVER & AUDIO
                            </Typography>

                            <Paper sx={{
                                p: 2,
                                bgcolor: '#1a1a1a',
                                borderRadius: 2,
                                border: '1px solid #333',
                                mb: 3
                            }}>
                                <FormControlLabel
                                    control={
                                        <Switch
                                            checked={enableNarration}
                                            onChange={(e) => setEnableNarration(e.target.checked)}
                                            sx={{ '& .MuiSwitch-track': { bgcolor: '#555' } }}
                                        />
                                    }
                                    label={<Typography variant="body2">Enable AI Narration</Typography>}
                                />

                                {enableNarration && (
                                    <Stack spacing={2} sx={{ mt: 2 }}>
                                        <Box>
                                            <Typography variant="caption" color="#888" display="block" mb={0.5}>
                                                Voice
                                            </Typography>
                                            <Select
                                                fullWidth
                                                size="small"
                                                value={narrationVoice}
                                                onChange={(e) => setNarrationVoice(e.target.value)}
                                                sx={{
                                                    bgcolor: '#0f0f0f',
                                                    color: 'white',
                                                    '& .MuiOutlinedInput-notchedOutline': { borderColor: '#333' }
                                                }}
                                            >
                                                <MenuItem value="chinese_female">Chinese Female</MenuItem>
                                                <MenuItem value="chinese_male">Chinese Male</MenuItem>
                                                <MenuItem value="english_female">English Female</MenuItem>
                                                <MenuItem value="english_male">English Male</MenuItem>
                                            </Select>
                                        </Box>
                                        <Box>
                                            <Typography variant="caption" color="#888" display="block" mb={0.5}>
                                                Speed ({narrationSpeed}x)
                                            </Typography>
                                            <Slider
                                                value={narrationSpeed}
                                                onChange={(_, v) => setNarrationSpeed(v as number)}
                                                min={0.5}
                                                max={2.0}
                                                step={0.1}
                                                sx={{ color: '#FF4081' }}
                                            />
                                        </Box>
                                    </Stack>
                                )}
                            </Paper>

                            <Typography variant="caption" color="#666" fontWeight={700} sx={{
                                letterSpacing: 1,
                                mb: 2,
                                display: 'block'
                            }}>
                                PACING
                            </Typography>
                            <Paper sx={{
                                p: 2,
                                bgcolor: '#1a1a1a',
                                borderRadius: 2,
                                border: '1px solid #333'
                            }}>
                                <Select
                                    fullWidth
                                    size="small"
                                    value={pacingStrategy}
                                    onChange={(e) => setPacingStrategy(e.target.value)}
                                    sx={{
                                        bgcolor: '#0f0f0f',
                                        color: 'white',
                                        '& .MuiOutlinedInput-notchedOutline': { borderColor: '#333' }
                                    }}
                                >
                                    <MenuItem value="balanced">Balanced</MenuItem>
                                    <MenuItem value="dynamic">Dynamic (Fast Cuts)</MenuItem>
                                    <MenuItem value="crescendo">Crescendo</MenuItem>
                                    <MenuItem value="slow_paced">Slow & Cinematic</MenuItem>
                                </Select>
                            </Paper>
                        </motion.div>
                    )}

                    {activeTab === 3 && videoTask && (
                        <motion.div
                            key="logs"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            transition={{ duration: 0.2 }}
                        >
                            <Typography variant="caption" color="#666" fontWeight={700} sx={{
                                letterSpacing: 1,
                                mb: 2,
                                display: 'block'
                            }}>
                                EXECUTION LOGS
                            </Typography>
                            <Paper sx={{
                                p: 2,
                                bgcolor: '#0a0a0a',
                                borderRadius: 2,
                                border: '1px solid #333',
                                fontFamily: 'monospace',
                                fontSize: '0.85rem',
                                maxHeight: '600px',
                                overflowY: 'auto'
                            }}>
                                {videoTask.logs && videoTask.logs.length > 0 ? (
                                    <Stack spacing={1}>
                                        {videoTask.logs.map((log: any, index: number) => (
                                            <Box key={index} sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
                                                <Typography variant="caption" color="#666" sx={{
                                                    minWidth: 60,
                                                    fontFamily: 'monospace'
                                                }}>
                                                    {log.timestamp}
                                                </Typography>
                                                <Typography sx={{
                                                    color: log.level === 'error' ? '#ff5252' :
                                                        log.level === 'success' ? '#69f0ae' :
                                                            log.level === 'warning' ? '#ffd740' : '#e0e0e0',
                                                    fontFamily: 'monospace',
                                                    wordBreak: 'break-word'
                                                }}>
                                                    {log.level === 'success' && '✅ '}
                                                    {log.level === 'error' && '❌ '}
                                                    {log.level === 'warning' && '⚠️ '}
                                                    {log.message}
                                                </Typography>
                                            </Box>
                                        ))}
                                        <div id="logs-end" />
                                    </Stack>
                                ) : (
                                    <Typography color="#666" fontStyle="italic">Waiting for logs...</Typography>
                                )}
                            </Paper>
                        </motion.div>
                    )}
                </AnimatePresence>
            </Box>

            {/* Footer Info */}
            <Box sx={{ p: 2, borderTop: '1px solid #222' }}>
                <Typography variant="caption" color="#444" align="center" display="block">
                    AI Director v2.0 • {estimatedDuration ? `Est. ${estimatedDuration}s` : 'Ready'}
                </Typography>
            </Box>
        </Paper>
    );
};

export default CreativeConsole;
