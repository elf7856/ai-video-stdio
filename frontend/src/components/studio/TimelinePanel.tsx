/**
 * TimelinePanel - 时间轴编辑面板 (实时同步版)
 * 即使视频未生成，也会根据 shots 数据渲染规划方块
 */

import React, { useRef, useState } from 'react';
import {
  Box, Typography, IconButton, Stack, Tooltip, Paper, Chip, alpha
} from '@mui/material';
import {
  ZoomIn as ZoomInIcon, ZoomOut as ZoomOutIcon,
  Movie as VideoIcon, TextFields as TextIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useWorkflowStore } from '../../stores/workflowStore';

interface TimelinePanelProps {
  currentTime: number;
  isPlaying: boolean;
  onTimeChange: (time: number) => void;
}

const TRACK_HEIGHT = 60;
const RULER_HEIGHT = 24;
const TRACK_HEADER_WIDTH = 100;

const TimelinePanel: React.FC<TimelinePanelProps> = ({
  currentTime, onTimeChange
}) => {
  const { shots, script } = useWorkflowStore();
  const [zoomLevel, setZoomLevel] = useState(20); // 像素/秒

  // 计算总时长
  const totalDuration = shots.reduce((sum: number, s: any) => sum + s.duration, 0) || 60;
  const timelineWidth = Math.max(1000, totalDuration * zoomLevel);

  const handleTimelineClick = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left - TRACK_HEADER_WIDTH;
    if (x >= 0) onTimeChange(x / zoomLevel);
  };

  // 渲染分镜方块
  const renderShots = () => {
    let accumulatedTime = 0;
    return shots.map((shot: any, idx: number) => {
      const left = accumulatedTime * zoomLevel;
      const width = shot.duration * zoomLevel;
      accumulatedTime += shot.duration;

      return (
        <Box key={idx} sx={{
          position: 'absolute', left, width: width - 2, height: TRACK_HEIGHT - 10, top: 5,
          bgcolor: alpha('#2196F3', 0.2), border: '1px solid #2196F3', borderRadius: 1,
          display: 'flex', alignItems: 'center', px: 1, overflow: 'hidden',
          cursor: 'pointer', transition: 'all 0.2s', '&:hover': { bgcolor: alpha('#2196F3', 0.4) }
        }}>
          <Typography variant="caption" sx={{ color: '#fff', fontSize: '0.65rem', whiteSpace: 'nowrap' }}>
            #{shot.sequence} {shot.prompt.substring(0, 20)}...
          </Typography>
        </Box>
      );
    });
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', bgcolor: '#0d0d0d' }}>
      {/* 1. 工具栏 */}
      <Box sx={{ height: 32, px: 2, display: 'flex', alignItems: 'center', bgcolor: '#111', borderBottom: '1px solid #222' }}>
        <Typography variant="caption" sx={{ color: '#666', fontWeight: 700 }}>TIMELINE</Typography>
        <Box sx={{ flex: 1 }} />
        <Stack direction="row" spacing={1}>
          <IconButton size="small" onClick={() => setZoomLevel(z => Math.max(5, z - 5))} sx={{ color: '#444' }}><ZoomOutIcon fontSize="small" /></IconButton>
          <IconButton size="small" onClick={() => setZoomLevel(z => Math.min(100, z + 5))} sx={{ color: '#444' }}><ZoomInIcon fontSize="small" /></IconButton>
        </Stack>
      </Box>

      {/* 2. 时间轴区域 */}
      <Box sx={{ flex: 1, overflow: 'auto', position: 'relative' }} onClick={handleTimelineClick}>
        <Box sx={{ width: timelineWidth + TRACK_HEADER_WIDTH, position: 'relative' }}>
          
          {/* 标尺 */}
          <Box sx={{ display: 'flex', height: RULER_HEIGHT, borderBottom: '1px solid #222', bgcolor: '#111' }}>
            <Box sx={{ width: TRACK_HEADER_WIDTH, flexShrink: 0, borderRight: '1px solid #222' }} />
            <Box sx={{ flex: 1, position: 'relative' }}>
              {[...Array(Math.ceil(totalDuration / 5))].map((_, i) => (
                <Typography key={i} variant="caption" sx={{ position: 'absolute', left: i * 5 * zoomLevel, color: '#444', fontSize: '0.6rem', ml: 0.5, mt: 0.5 }}>
                  {i * 5}s
                </Typography>
              ))}
            </Box>
          </Box>

          {/* 视频轨道 */}
          <Box sx={{ display: 'flex', height: TRACK_HEIGHT, borderBottom: '1px solid #1a1a1a' }}>
            <Box sx={{ width: TRACK_HEADER_WIDTH, flexShrink: 0, bgcolor: '#111', borderRight: '1px solid #222', display: 'flex', alignItems: 'center', px: 1, gap: 1 }}>
              <VideoIcon sx={{ fontSize: 14, color: '#2196F3' }} />
              <Typography variant="caption" color="#888">VIDEO</Typography>
            </Box>
            <Box sx={{ flex: 1, position: 'relative' }}>
              {renderShots()}
            </Box>
          </Box>

          {/* 脚本轨道 */}
          <Box sx={{ display: 'flex', height: TRACK_HEIGHT }}>
            <Box sx={{ width: TRACK_HEADER_WIDTH, flexShrink: 0, bgcolor: '#111', borderRight: '1px solid #222', display: 'flex', alignItems: 'center', px: 1, gap: 1 }}>
              <TextIcon sx={{ fontSize: 14, color: '#4CAF50' }} />
              <Typography variant="caption" color="#888">SCRIPT</Typography>
            </Box>
            <Box sx={{ flex: 1, p: 1 }}>
              <Typography variant="caption" color="#333" sx={{ fontStyle: 'italic' }}>{script ? script.substring(0, 100) + '...' : '等待脚本生成...'}</Typography>
            </Box>
          </Box>

          {/* 播放头 */}
          <Box sx={{ 
            position: 'absolute', left: TRACK_HEADER_WIDTH + currentTime * zoomLevel, 
            top: 0, bottom: 0, width: '2px', bgcolor: '#FF4081', zIndex: 10, pointerEvents: 'none' 
          }} />
        </Box>
      </Box>
    </Box>
  );
};

export default TimelinePanel;