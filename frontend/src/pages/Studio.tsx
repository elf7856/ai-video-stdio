import React, { useEffect } from 'react';
import {
  Box,
  Drawer,
  IconButton,
  Tooltip,
  Divider,
  Button,
  useTheme
} from '@mui/material';
import {
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
  AutoAwesome as MagicIcon,
  Download as ExportIcon,
  Save as SaveIcon,
  Undo as UndoIcon,
  Redo as RedoIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

import { useWorkflowStore } from '../stores/workflowStore';
import ConversationPanel from '../components/studio/ConversationPanel';
import AssetPanel from '../components/studio/AssetPanel';
import PropertiesPanel from '../components/studio/PropertiesPanel';
import TimelinePanel from '../components/studio/TimelinePanel';
import PreviewPanel from '../components/studio/PreviewPanel';

const drawerWidth = 320;
const rightDrawerWidth = 300;

const Studio: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { stage, setStage } = useWorkflowStore();

  const [leftOpen, setLeftOpen] = React.useState(true);
  const [rightOpen, setRightOpen] = React.useState(true);

  useEffect(() => {
    if (stage === 'ideation') {
      navigate('/generate');
    }
  }, [stage, navigate]);

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: '#0a0a0a', color: '#e0e0e0', overflow: 'hidden' }}>
      
      {/* Left Drawer: Copilot / Assets */}
      <Drawer
        variant="persistent"
        anchor="left"
        open={leftOpen}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            bgcolor: '#111',
            borderRight: '1px solid #222',
            top: 48, // Below Navbar
            height: 'calc(100% - 48px)'
          },
        }}
      >
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <Box sx={{ flex: 1, overflow: 'hidden' }}>
            {stage === 'planning' ? <ConversationPanel /> : <AssetPanel />}
          </Box>
        </Box>
      </Drawer>

      {/* Main Content Area */}
      <Box component="main" sx={{ flexGrow: 1, height: '100%', display: 'flex', flexDirection: 'column', pt: '48px', transition: 'margin 0.2s', ml: leftOpen ? 0 : `-${drawerWidth}px`, mr: rightOpen ? 0 : `-${rightDrawerWidth}px` }}>
        
        {/* Toolbar */}
        <Box sx={{ height: 48, px: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #222', bgcolor: '#0f0f0f' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Tooltip title={leftOpen ? "收起侧栏" : "展开侧栏"}>
              <IconButton size="small" onClick={() => setLeftOpen(!leftOpen)}>
                {leftOpen ? <ChevronLeftIcon /> : <ChevronRightIcon />}
              </IconButton>
            </Tooltip>
            <Divider orientation="vertical" flexItem sx={{ mx: 1, bgcolor: '#333' }} />
            <Tooltip title="撤销"><IconButton size="small"><UndoIcon fontSize="small" /></IconButton></Tooltip>
            <Tooltip title="重做"><IconButton size="small"><RedoIcon fontSize="small" /></IconButton></Tooltip>
            <Tooltip title="保存"><IconButton size="small"><SaveIcon fontSize="small" /></IconButton></Tooltip>
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {stage === 'planning' && (
              <Button 
                variant="contained" 
                size="small" 
                startIcon={<MagicIcon />}
                onClick={() => setStage('editing')}
                sx={{ bgcolor: '#FF4081', color: '#fff', '&:hover': { bgcolor: '#F50057' } }}
              >
                生成预览
              </Button>
            )}
            {stage === 'editing' && (
              <Button 
                variant="contained" 
                size="small" 
                startIcon={<ExportIcon />}
                sx={{ bgcolor: theme.palette.primary.main, color: '#fff' }}
              >
                导出视频
              </Button>
            )}
            <Divider orientation="vertical" flexItem sx={{ mx: 1, bgcolor: '#333' }} />
            <Tooltip title={rightOpen ? "收起属性" : "展开属性"}>
              <IconButton size="small" onClick={() => setRightOpen(!rightOpen)}>
                {rightOpen ? <ChevronRightIcon /> : <ChevronLeftIcon />}
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Workspace */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', bgcolor: '#050505', position: 'relative', overflow: 'hidden' }}>
          
          {/* Upper: Preview */}
          <Box sx={{ flex: 3, minHeight: 0, p: 2, display: 'flex', justifyContent: 'center' }}>
             <PreviewPanel />
          </Box>

          {/* Lower: Timeline */}
          <Box sx={{ height: 280, borderTop: '1px solid #222', bgcolor: '#111' }}>
            <TimelinePanel />
          </Box>

        </Box>
      </Box>

      {/* Right Drawer: Properties */}
      <Drawer
        variant="persistent"
        anchor="right"
        open={rightOpen}
        sx={{
          width: rightDrawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: rightDrawerWidth,
            boxSizing: 'border-box',
            bgcolor: '#111',
            borderLeft: '1px solid #222',
            top: 48,
            height: 'calc(100% - 48px)'
          },
        }}
      >
        <PropertiesPanel />
      </Drawer>

    </Box>
  );
};

export default Studio;