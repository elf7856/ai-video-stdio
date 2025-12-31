/**
 * Studio - 完整恢复与增强版
 * 1. 恢复了被删除的初始创意输入界面（Search View）
 * 2. 恢复了完整的项目加载与状态同步逻辑
 * 3. 保留并优化了可拖拽拉伸的布局
 */

import React, { useState, useCallback, useEffect } from 'react';
import {
  Box, Typography, Paper, IconButton, Button, Tooltip, Stack, Divider, alpha, 
  LinearProgress, Chip, TextField, InputAdornment, Container, Slider, Grid
} from '@mui/material';
import {
  AutoAwesome as MagicIcon, Download as ExportIcon, Settings as SettingsIcon,
  Save as SaveIcon, Undo as UndoIcon, Redo as RedoIcon, ArrowForward as ArrowForwardIcon,
  Business as BusinessIcon, Computer as TechIcon, LocalCafe as LifeIcon,
  School as EduIcon, TheaterComedy as FunIcon, Store as CommercialIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { useWorkflowStore } from '../stores/workflowStore';
import { editorApi, videosApi } from '../api';

// 面板组件
import ConversationPanel from '../components/studio/ConversationPanel';
import AssetPanel from '../components/studio/AssetPanel';
import PreviewPanel from '../components/studio/PreviewPanel';
import PropertiesPanel from '../components/studio/PropertiesPanel';
import TimelinePanel from '../components/studio/TimelinePanel';

// Style Configuration
const STYLE_CONFIG: Record<string, { icon: React.ReactNode; gradient: string; color: string }> = {
  '专业': { icon: <BusinessIcon />, gradient: 'linear-gradient(135deg, #2c3e50 0%, #3498db 100%)', color: '#3498db' },
  '科技': { icon: <TechIcon />, gradient: 'linear-gradient(135deg, #000428 0%, #004e92 100%)', color: '#004e92' },
  '生活': { icon: <LifeIcon />, gradient: 'linear-gradient(135deg, #56ab2f 0%, #a8e063 100%)', color: '#56ab2f' },
  '教育': { icon: <EduIcon />, gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', color: '#4facfe' },
  '娱乐': { icon: <FunIcon />, gradient: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', color: '#fa709a' },
  '商业': { icon: <CommercialIcon />, gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#667eea' },
};

const Studio: React.FC = () => {
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId: string }>();
  
  // Store state
  const {
    stage, creative, taskStatus, setTopic, setStyle, setCreativeConfig,
    setStage, setScript, setShots, setTaskStatus, syncTask
  } = useWorkflowStore();

  // --- 布局与状态 ---
  const [hasStarted, setHasStarted] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [leftWidth, setLeftWidth] = useState(400);
  const [rightWidth, setRightWidth] = useState(300);
  const [bottomHeight, setBottomHeight] = useState(250);
  const [isResizing, setIsResizing] = useState<string | null>(null);

  // --- 拖拽调整逻辑 ---
  const startResizing = (direction: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(direction);
  };

  const stopResizing = useCallback(() => setIsResizing(null), []);

  const resize = useCallback((e: MouseEvent) => {
    if (!isResizing) return;
    if (isResizing === 'left') {
      const newWidth = e.clientX;
      if (newWidth > 300 && newWidth < 800) setLeftWidth(newWidth);
    } else if (isResizing === 'right') {
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth > 200 && newWidth < 600) setRightWidth(newWidth);
    } else if (isResizing === 'bottom') {
      const newHeight = window.innerHeight - e.clientY;
      if (newHeight > 150 && newHeight < 600) setBottomHeight(newHeight);
    }
  }, [isResizing]);

  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', resize);
      window.addEventListener('mouseup', stopResizing);
    }
    return () => {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
    };
  }, [isResizing, resize, stopResizing]);

  // 从URL加载项目逻辑
  useEffect(() => {
    if (projectId?.startsWith('proj_task_')) {
      setHasStarted(true);
      syncTask(projectId.replace('proj_', ''));
    }
  }, [projectId, syncTask]);

  const handleStart = useCallback(() => {
    if (!creative.topic.trim()) return;
    // 立即进入 Studio 布局
    setHasStarted(true);
    setStage('planning');
    console.log("[Studio] Transitioning to planning stage immediately.");
  }, [creative.topic, setStage]);

  // === 1. 初始视图 (创意输入) ===
  if (!hasStarted) {
    return (
      <Box sx={{
        height: 'calc(100vh - 64px)', background: '#0a0a0a', color: 'white',
        display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', position: 'relative'
      }}>
        <Box sx={{
          position: 'absolute', top: '20%', left: '50%', transform: 'translate(-50%, -50%)',
          width: '60vw', height: '60vw', background: 'radial-gradient(circle, rgba(255, 64, 129, 0.05) 0%, transparent 70%)',
          zIndex: 0, pointerEvents: 'none'
        }} />

        <Container maxWidth="md" sx={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
            <Box sx={{ mb: 6 }}>
              <Typography variant="h2" fontWeight={700} sx={{ background: 'linear-gradient(to right, #fff 20%, #888 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', mb: 2 }}>
                What will you create?
              </Typography>
              <Typography variant="h6" color="#666" fontWeight={300}>Describe your vision, AI will plan and generate for you.</Typography>
            </Box>

            <Paper elevation={0} sx={{ width: '100%', borderRadius: 4, bgcolor: '#1a1a1a', border: '1px solid #333', overflow: 'hidden' }}>
              <TextField 
                fullWidth 
                variant="standard" 
                placeholder="A cinematic trailer for a sci-fi movie on Mars..."
                value={creative.topic} 
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && creative.topic.trim()) handleStart(); }}
                InputProps={{ 
                  disableUnderline: true, 
                  startAdornment: (
                    <InputAdornment position="start" sx={{ pl: 2 }}>
                      <MagicIcon sx={{ color: '#FF4081' }} />
                    </InputAdornment>
                  ),
                  endAdornment: (
                    <IconButton 
                      color="primary" 
                      sx={{ p: 2 }} 
                      onClick={handleStart} 
                      disabled={!creative.topic.trim()}
                    >
                      <ArrowForwardIcon />
                    </IconButton>
                  ),
                  sx: { 
                    p: 1, fontSize: '1.2rem', color: 'white',
                    '& input': { p: 2 },
                    '& input:-webkit-autofill': {
                      WebkitBoxShadow: '0 0 0 1000px #1a1a1a inset !important',
                      WebkitTextFillColor: 'white !important',
                      transition: 'background-color 5000s ease-in-out 0s',
                    }
                  } 
                }}
              />
            </Paper>

            <Box sx={{ mt: 6 }}>
              <Typography variant="caption" color="#666" fontWeight={700} sx={{ letterSpacing: 1, mb: 3, display: 'block' }}>CHOOSE A STYLE</Typography>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
                {Object.keys(STYLE_CONFIG).map((s) => {
                  const config = STYLE_CONFIG[s];
                  return (
                    <Chip key={s} icon={config.icon as any} label={s} clickable onClick={() => setStyle(s)}
                      sx={{ bgcolor: creative.style === s ? alpha(config.color, 0.2) : '#1a1a1a', color: creative.style === s ? config.color : '#888', border: `1px solid ${creative.style === s ? config.color : '#333'}`, borderRadius: 2, px: 1, py: 2.5 }}
                    />
                  );
                })}
              </Box>
            </Box>

            <Paper sx={{ mt: 4, p: 3, bgcolor: 'rgba(255,255,255,0.05)', borderRadius: 2, border: '1px solid rgba(255,255,255,0.1)' }}>
                <Grid container spacing={4}>
                    <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="#888" align="left">DURATION: {creative.targetDuration}s</Typography>
                        <Slider value={creative.targetDuration} onChange={(_, v) => setCreativeConfig({ targetDuration: v as number })} min={10} max={300} step={5} sx={{ color: '#FF4081' }} />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <Typography variant="body2" color="#888" align="left">SHOTS: {creative.shotCount}</Typography>
                        <Slider value={creative.shotCount} onChange={(_, v) => setCreativeConfig({ shotCount: v as number })} min={3} max={20} step={1} sx={{ color: '#4facfe' }} />
                    </Grid>
                </Grid>
            </Paper>

            <Stack direction="row" spacing={2} justifyContent="center" sx={{ mt: 6 }}>
              <Button variant="contained" size="large" onClick={handleStart} startIcon={<MagicIcon />} sx={{ borderRadius: 3, px: 4, py: 1.5, bgcolor: '#FF4081', fontWeight: 700 }}>Start Creating</Button>
              <Button variant="text" onClick={() => setHasStarted(true)} sx={{ color: '#666' }}>Skip to Studio</Button>
            </Stack>
          </motion.div>
        </Container>
      </Box>
    );
  }

  // === 2. 工作室主界面 (已启动) ===
  return (
    <Box sx={{
      height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: '#000', overflow: 'hidden',
      userSelect: isResizing ? 'none' : 'auto'
    }}>
      {/* 顶部栏 */}
      <Box sx={{ height: 52, bgcolor: '#111', borderBottom: '1px solid #222', display: 'flex', alignItems: 'center', px: 2, gap: 2, zIndex: 1000 }}>
        <Typography variant="subtitle2" sx={{ color: '#fff', fontWeight: 700 }}>{creative.topic || 'UNTITLED'}</Typography>
        <Box sx={{ flex: 1 }} />
        {taskStatus && (
          <Stack direction="row" spacing={2} alignItems="center">
            <Typography variant="caption" color="#666">{taskStatus.status}</Typography>
            <Box sx={{ width: 100 }}><LinearProgress variant="determinate" value={taskStatus.progress || 0} sx={{ height: 3, bgcolor: '#222' }} /></Box>
          </Stack>
        )}
        <Button variant="contained" size="small" startIcon={<ExportIcon />} sx={{ bgcolor: '#FF4081' }}>EXPORT</Button>
      </Box>

      {/* 主体区 */}
      <Box sx={{ flex: 1, display: 'flex', minHeight: 0, position: 'relative' }}>
        {/* 左侧 */}
        <Box sx={{ width: leftWidth, display: 'flex', flexDirection: 'column', bgcolor: '#0a0a0a', flexShrink: 0 }}>
          <Box sx={{ flex: 1, minHeight: 0 }}><ConversationPanel /></Box>
          <Box sx={{ height: 180, borderTop: '1px solid #222' }}><AssetPanel /></Box>
        </Box>

        {/* 左调节柄 */}
        <Box onMouseDown={startResizing('left')} sx={{ width: 6, cursor: 'col-resize', zIndex: 100, position: 'relative', '&:hover': { bgcolor: alpha('#FF4081', 0.2) }, '&::after': { content: '""', position: 'absolute', left: '50%', top: 0, bottom: 0, width: '1px', bgcolor: isResizing === 'left' ? '#FF4081' : '#222' } }} />

        {/* 预览区 */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          <PreviewPanel isPlaying={isPlaying} currentTime={currentTime} onPlayPause={() => setIsPlaying(!isPlaying)} onSeek={setCurrentTime} />
        </Box>

        {/* 右调节柄 */}
        <Box onMouseDown={startResizing('right')} sx={{ width: 6, cursor: 'col-resize', zIndex: 100, position: 'relative', '&:hover': { bgcolor: alpha('#FF4081', 0.2) }, '&::after': { content: '""', position: 'absolute', left: '50%', top: 0, bottom: 0, width: '1px', bgcolor: isResizing === 'right' ? '#FF4081' : '#222' } }} />

        {/* 右侧 */}
        <Box sx={{ width: rightWidth, borderLeft: '1px solid #222', bgcolor: '#0a0a0a', flexShrink: 0 }}><PropertiesPanel /></Box>
      </Box>

      {/* 底部调节柄 */}
      <Box onMouseDown={startResizing('bottom')} sx={{ height: 6, cursor: 'row-resize', zIndex: 100, position: 'relative', '&:hover': { bgcolor: alpha('#FF4081', 0.2) }, '&::after': { content: '""', position: 'absolute', top: '50%', left: 0, right: 0, height: '1px', bgcolor: isResizing === 'bottom' ? '#FF4081' : '#222' } }} />

      {/* 底部时间轴 */}
      <Box sx={{ height: bottomHeight, borderTop: '1px solid #222', bgcolor: '#050505', flexShrink: 0 }}>
        <TimelinePanel currentTime={currentTime} isPlaying={isPlaying} onTimeChange={setCurrentTime} />
      </Box>
    </Box>
  );
};

export default Studio;