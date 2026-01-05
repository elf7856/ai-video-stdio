import React, { useRef } from 'react';
import {
  Box, Typography, IconButton, Stack, alpha
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  SkipPrevious as PrevIcon,
  SkipNext as NextIcon,
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon
} from '@mui/icons-material';

const TimelinePanel: React.FC = () => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // 简化的 Timeline 面板，目前主要逻辑都在 EditorPage 里了
  
  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 1, borderBottom: '1px solid #222', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Stack direction="row" spacing={1}>
          <IconButton size="small"><PrevIcon /></IconButton>
          <IconButton size="small" sx={{ bgcolor: alpha('#FF4081', 0.1), color: '#FF4081' }}><PlayIcon /></IconButton>
          <IconButton size="small"><NextIcon /></IconButton>
        </Stack>
        <Stack direction="row" spacing={1}>
          <IconButton size="small"><ZoomOutIcon /></IconButton>
          <IconButton size="small"><ZoomInIcon /></IconButton>
        </Stack>
      </Box>
      <Box 
        ref={scrollRef}
        sx={{ 
          flex: 1, 
          overflowX: 'auto', 
          p: 2,
          '&::-webkit-scrollbar': { height: 8 },
          '&::-webkit-scrollbar-thumb': { bgcolor: '#333', borderRadius: 4 }
        }}
      >
        <Typography variant="caption" color="text.secondary">
          Timeline view is integrated in the main editor.
        </Typography>
      </Box>
    </Box>
  );
};

export default TimelinePanel;