/**
 * AssetPanel - 资源面板
 * 显示库存素材、上传素材、AI生成素材和配音资源
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Paper,
  IconButton,
  Tooltip,
  Stack,
  Chip
} from '@mui/material';
import {
  VideoLibrary as VideoIcon,
  AutoAwesome as AIIcon,
  MusicNote as MusicIcon,
  RecordVoiceOver as VoiceIcon,
  Add as AddIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useWorkflowStore } from '../../stores/workflowStore';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <Box
    role="tabpanel"
    hidden={value !== index}
    sx={{ height: '100%', overflow: 'auto' }}
  >
    {value === index && children}
  </Box>
);

const AssetPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);

  const { shots } = useWorkflowStore();

  // 从shots生成资源列表
  const generatedAssets = shots.map((shot: any) => ({
    id: `shot-${shot.sequence}`,
    name: `镜头 ${shot.sequence}`,
    type: 'video',
    prompt: shot.prompt,
    provider: 'google_veo' as const,
    shotSequence: shot.sequence,
    status: 'pending' as const,
    duration: shot.duration,
    thumbnailUrl: undefined as string | undefined
  }));

  // 获取状态图标
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
      case 'completed':
        return <SuccessIcon sx={{ fontSize: 14, color: '#4CAF50' }} />;
      case 'failed':
        return <ErrorIcon sx={{ fontSize: 14, color: '#f44336' }} />;
      case 'generating':
        return <PendingIcon sx={{ fontSize: 14, color: '#FF9800' }} />;
      default:
        return null;
    }
  };

  // 渲染资源卡片
  const renderAssetCard = (asset: typeof generatedAssets[number], index: number) => (
    <motion.div
      key={asset.id}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.05 }}
    >
      <Paper sx={{
        p: 1,
        bgcolor: '#1a1a1a',
        border: '1px solid #333',
        borderRadius: 1,
        cursor: 'pointer',
        transition: 'all 0.2s',
        '&:hover': {
          borderColor: '#555',
          transform: 'translateY(-2px)'
        }
      }}>
        {/* 缩略图区域 */}
        <Box sx={{
          width: '100%',
          aspectRatio: '16/9',
          bgcolor: '#0a0a0a',
          borderRadius: 0.5,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          mb: 1,
          position: 'relative',
          overflow: 'hidden'
        }}>
          {asset.thumbnailUrl ? (
            <img
              src={asset.thumbnailUrl}
              alt={asset.name}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          ) : (
            <VideoIcon sx={{ fontSize: 24, color: '#333' }} />
          )}

          {/* 状态标识 */}
          <Box sx={{
            position: 'absolute',
            top: 4,
            right: 4
          }}>
            {getStatusIcon(asset.status)}
          </Box>

          {/* 时长标识 */}
          {asset.duration && (
            <Chip
              label={`${asset.duration}s`}
              size="small"
              sx={{
                position: 'absolute',
                bottom: 4,
                right: 4,
                height: 18,
                bgcolor: 'rgba(0,0,0,0.7)',
                color: '#fff',
                fontSize: '0.65rem'
              }}
            />
          )}
        </Box>

        {/* 信息区域 */}
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="caption" color="#aaa" noWrap sx={{ flex: 1 }}>
            {asset.name}
          </Typography>
          <Chip
            label={`#${asset.shotSequence}`}
            size="small"
            sx={{
              height: 16,
              bgcolor: '#333',
              color: '#888',
              fontSize: '0.6rem'
            }}
          />
        </Stack>
      </Paper>
    </motion.div>
  );

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 标题栏和Tabs */}
      <Box sx={{ borderBottom: '1px solid #222' }}>
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          variant="fullWidth"
          sx={{
            minHeight: 36,
            '& .MuiTab-root': {
              color: '#666',
              minHeight: 36,
              fontSize: '0.75rem',
              py: 0.5
            },
            '& .Mui-selected': { color: '#fff' },
            '& .MuiTabs-indicator': { backgroundColor: '#FF4081' }
          }}
        >
          <Tab icon={<AIIcon sx={{ fontSize: 16 }} />} iconPosition="start" label="AI生成" />
          <Tab icon={<VoiceIcon sx={{ fontSize: 16 }} />} iconPosition="start" label="配音" />
          <Tab icon={<MusicIcon sx={{ fontSize: 16 }} />} iconPosition="start" label="音乐" />
        </Tabs>
      </Box>

      {/* AI生成素材 */}
      <TabPanel value={activeTab} index={0}>
        <Box sx={{ p: 1.5 }}>
          {generatedAssets.length > 0 ? (
            <Box sx={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))',
              gap: 1
            }}>
              {generatedAssets.map((asset: any, idx: number) => renderAssetCard(asset, idx))}
            </Box>
          ) : (
            <Box sx={{ textAlign: 'center', py: 3 }}>
              <AIIcon sx={{ fontSize: 32, color: '#333', mb: 1 }} />
              <Typography variant="caption" color="#666" display="block">
                生成的素材将显示在这里
              </Typography>
            </Box>
          )}
        </Box>
      </TabPanel>

      {/* 配音资源 */}
      <TabPanel value={activeTab} index={1}>
        <Box sx={{ p: 1.5, textAlign: 'center' }}>
          <VoiceIcon sx={{ fontSize: 32, color: '#333', mb: 1 }} />
          <Typography variant="caption" color="#666" display="block">
            配音资源将显示在这里
          </Typography>
          <Tooltip title="生成配音">
            <IconButton
              size="small"
              sx={{
                mt: 1,
                bgcolor: '#1a1a1a',
                border: '1px dashed #333',
                '&:hover': { bgcolor: '#222' }
              }}
            >
              <AddIcon sx={{ color: '#666' }} />
            </IconButton>
          </Tooltip>
        </Box>
      </TabPanel>

      {/* 背景音乐 */}
      <TabPanel value={activeTab} index={2}>
        <Box sx={{ p: 1.5, textAlign: 'center' }}>
          <MusicIcon sx={{ fontSize: 32, color: '#333', mb: 1 }} />
          <Typography variant="caption" color="#666" display="block">
            背景音乐将显示在这里
          </Typography>
          <Tooltip title="添加音乐">
            <IconButton
              size="small"
              sx={{
                mt: 1,
                bgcolor: '#1a1a1a',
                border: '1px dashed #333',
                '&:hover': { bgcolor: '#222' }
              }}
            >
              <AddIcon sx={{ color: '#666' }} />
            </IconButton>
          </Tooltip>
        </Box>
      </TabPanel>
    </Box>
  );
};

export default AssetPanel;
