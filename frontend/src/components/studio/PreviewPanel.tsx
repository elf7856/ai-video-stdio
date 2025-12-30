import React, { useState, useRef, useEffect } from 'react';
import {
  Box, Typography, IconButton, Paper, alpha, CircularProgress, Slider, Stack, ToggleButton, ToggleButtonGroup
} from '@mui/material';
import { PlayArrow as PlayIcon, Pause as PauseIcon, Crop169 as Landscape, CropPortrait as Portrait, CropSquare as Square } from '@mui/icons-material';
import { useWorkflowStore } from '../../stores/workflowStore';
import apiClient from '../../api/client';

const PreviewPanel: React.FC = () => {
  const { taskStatus, shots, outputConfig, setOutputConfig } = useWorkflowStore();
  const videoRef = useRef<HTMLVideoElement>(null);
  
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const estimatedDuration = shots.reduce((a:number, b:any)=>a+b.duration, 0) || 60;
  const displayDuration = duration || estimatedDuration;

  // 【核心修复】更加稳健的 URL 拼接逻辑
  const getFullUrl = (path?: string) => {
    if (!path) return '';
    if (path.startsWith('http')) return path;
    
    const baseUrl = apiClient.defaults.baseURL?.replace(/\/$/, '') || 'http://localhost:8000';
    let cleanPath = path.replace(/^\//, '');
    
    // 如果路径里没有 outputs/，说明后端返回的是纯相对路径，需要补上挂载点
    if (!cleanPath.startsWith('outputs/')) {
        cleanPath = `outputs/${cleanPath}`;
    }
    
    const finalUrl = `${baseUrl}/${cleanPath}`;
    console.log("[PreviewPanel] Resolving URL:", { original: path, final: finalUrl });
    return finalUrl;
  };

  const videoUrl = taskStatus?.finalVideoPath 
    ? getFullUrl(taskStatus.finalVideoPath) 
    : (currentShot?.videoPath ? getFullUrl(currentShot.videoPath) : null);

  useEffect(() => {
    if (!videoRef.current || !videoUrl) return;
    if (isPlaying) {
      videoRef.current.play().catch(err => {
          console.warn("Autoplay blocked or failed:", err);
          setIsPlaying(false);
      });
    } else {
      videoRef.current.pause();
    }
  }, [isPlaying, videoUrl, currentShot]); // Add currentShot dependency to re-trigger play on shot change

  const onLoadedMetadata = () => {
    if (videoRef.current) {
      // If playing final video, use its duration. 
      // If playing shot video, we might want to stick to estimated/global duration or just let it play.
      // For simplicity in this preview mode, we just log it.
      console.log("[PreviewPanel] Video Metadata Loaded. Duration:", videoRef.current.duration);
    }
  };

  const onTimeUpdate = () => {
    if (videoRef.current && isPlaying) {
      if (taskStatus?.finalVideoPath) {
        setCurrentTime(videoRef.current.currentTime);
      } else {
        // Calculate global time based on shot offset
        const shotStart = shots.slice(0, shots.indexOf(currentShot)).reduce((sum:number, s:any) => sum + s.duration, 0);
        setCurrentTime(shotStart + videoRef.current.currentTime);
      }
    }
  };

  const handleSeek = (_: any, value: number | number[]) => {
    const time = value as number;
    setCurrentTime(time);
    
    if (videoRef.current && videoUrl) {
      if (taskStatus?.finalVideoPath) {
        videoRef.current.currentTime = time;
      } else {
        // Handle seeking within a shot or across shots
        // We need to determine the shot at the new time
        const targetShotIndex = shots.findIndex((s:any, idx:number) => {
            const acc = shots.slice(0, idx).reduce((sum:number, p:any)=>sum+p.duration, 0);
            return time >= acc && time < acc + s.duration;
        });
        
        if (targetShotIndex !== -1) {
            const acc = shots.slice(0, targetShotIndex).reduce((sum:number, p:any)=>sum+p.duration, 0);
            // If we are still on the same video/shot, we can seek
            if (shots[targetShotIndex] === currentShot) {
                videoRef.current.currentTime = time - acc;
            }
            // If we changed shots, the render cycle will update videoUrl, and it will start at 0
        }
      }
    }
  };

  const currentShot = shots.find((s:any, idx:number) => {
    const acc = shots.slice(0, idx).reduce((sum:number, p:any)=>sum+p.duration, 0);
    return currentTime >= acc && currentTime < acc + s.duration;
  }) || shots[0];

  const formatTime = (time: number) => {
    const mins = Math.floor(time / 60);
    const secs = Math.floor(time % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getPreviewStyle = () => {
    switch (outputConfig.aspectRatio) {
      case '9:16': return { aspectRatio: '9/16', maxHeight: '100%' };
      case '1:1': return { aspectRatio: '1/1', maxHeight: '100%' };
      default: return { aspectRatio: '16/9', maxWidth: '100%' };
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: '#000' }}>
      <Box sx={{ height: 40, px: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #222', flexShrink: 0 }}>
        <Typography variant="caption" color="#444" fontWeight={700}>PREVIEW</Typography>
        <ToggleButtonGroup value={outputConfig.aspectRatio} exclusive onChange={(_, v) => v && setOutputConfig({aspectRatio: v})} size="small" sx={{ height: 24 }}>
          <ToggleButton value="16:9"><Landscape sx={{ fontSize: 14 }} /></ToggleButton>
          <ToggleButton value="9:16"><Portrait sx={{ fontSize: 14 }} /></ToggleButton>
          <ToggleButton value="1:1"><Square sx={{ fontSize: 14 }} /></ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Box sx={{ flex: 1, minHeight: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', p: 2 }}>
        <Paper elevation={0} sx={{ 
          ...getPreviewStyle(), 
          bgcolor: '#000', overflow: 'hidden', position: 'relative', 
          display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #333' 
        }}>
          {videoUrl ? (
            <Box sx={{ width: '100%', height: '100%' }}>
                {/* 增加控制台打印以便调试 */}
                <video 
                  ref={videoRef}
                  src={videoUrl} 
                  onLoadedMetadata={onLoadedMetadata}
                  onTimeUpdate={onTimeUpdate}
                  onEnded={() => setIsPlaying(false)}
                  style={{ width: '100%', height: '100%', objectFit: 'contain' }} 
                  key={videoUrl}
                />
            </Box>
          ) : currentShot?.imagePath ? (
            <img 
              src={getFullUrl(currentShot.imagePath)} 
              style={{ width: '100%', height: '100%', objectFit: 'contain' }} 
              alt="preview" 
            />
          ) : (
            <Stack alignItems="center" spacing={2}>
              <CircularProgress size={32} sx={{ color: '#333' }} />
              <Typography variant="caption" color="#333">
                {taskStatus?.status === 'generating_script' ? 'AI 导演正在构思脚本...' : '正在绘制分镜图...'}
              </Typography>
            </Stack>
          )}
        </Paper>
      </Box>

      <Box sx={{ height: 48, px: 2, borderTop: '1px solid #222', bgcolor: '#0a0a0a', display: 'flex', alignItems: 'center', gap: 2, flexShrink: 0 }}>
        <IconButton size="small" onClick={() => setIsPlaying(!isPlaying)} sx={{ color: '#fff', bgcolor: alpha('#FF4081', 0.1) }}>
          {isPlaying ? <PauseIcon fontSize="small" /> : <PlayIcon fontSize="small" />}
        </IconButton>
        <Typography variant="caption" color="#666" sx={{ minWidth: 80, fontFamily: 'monospace' }}>
          {formatTime(currentTime)} / {formatTime(displayDuration)}
        </Typography>
        <Slider value={currentTime} max={displayDuration} onChange={handleSeek} sx={{ flex: 1, color: '#FF4081', '& .MuiSlider-thumb': { width: 10, height: 10 } }} />
      </Box>
    </Box>
  );
};

export default PreviewPanel;