/**
 * PropertiesPanel - 属性面板
 * 显示选中元素的属性、全局设置
 */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Stack,
  TextField,
  Select,
  MenuItem,
  Slider,
  Switch,
  FormControlLabel,
  Paper,
  Divider,
  Chip,
  alpha
} from '@mui/material';
import {
  Tune as TuneIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
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

const PropertiesPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [selectedShotIndex, setSelectedShotIndex] = useState<number | null>(null);

  const {
    creative,
    outputConfig,
    shots,
    setCreativeConfig,
    setOutputConfig,
    updateShot
  } = useWorkflowStore();

  const selectedShot = selectedShotIndex !== null ? shots[selectedShotIndex] : null;

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Tabs */}
      <Box sx={{ borderBottom: '1px solid #222' }}>
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          variant="fullWidth"
          sx={{
            minHeight: 40,
            '& .MuiTab-root': {
              color: '#666',
              minHeight: 40,
              fontSize: '0.75rem'
            },
            '& .Mui-selected': { color: '#fff' },
            '& .MuiTabs-indicator': { backgroundColor: '#FF4081' }
          }}
        >
          <Tab icon={<TuneIcon sx={{ fontSize: 16 }} />} iconPosition="start" label="属性" />
          <Tab icon={<SettingsIcon sx={{ fontSize: 16 }} />} iconPosition="start" label="设置" />
        </Tabs>
      </Box>

      {/* 属性面板 */}
      <TabPanel value={activeTab} index={0}>
        <Box sx={{ p: 2 }}>
          {selectedShot ? (
            // 选中镜头的属性
            <Stack spacing={2}>
              <Typography variant="subtitle2" fontWeight={700} color="#fff">
                镜头 #{selectedShot.sequence}
              </Typography>

              <Box>
                <Typography variant="caption" color="#888" display="block" mb={0.5}>
                  提示词
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  minRows={3}
                  value={selectedShot.prompt}
                  onChange={(e) => {
                    if (selectedShotIndex !== null) {
                      updateShot(selectedShotIndex, { prompt: e.target.value });
                    }
                  }}
                  size="small"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      bgcolor: '#1a1a1a',
                      color: 'white',
                      '& fieldset': { borderColor: '#333' }
                    }
                  }}
                />
              </Box>

              <Box>
                <Typography variant="caption" color="#888" display="block" mb={0.5}>
                  时长 ({selectedShot.duration}s)
                </Typography>
                <Slider
                  value={selectedShot.duration}
                  min={2}
                  max={20}
                  step={0.5}
                  onChange={(_, v) => {
                    if (selectedShotIndex !== null) {
                      updateShot(selectedShotIndex, { duration: v as number });
                    }
                  }}
                  sx={{ color: '#FF4081' }}
                />
              </Box>

              <Box>
                <Typography variant="caption" color="#888" display="block" mb={0.5}>
                  镜头类型
                </Typography>
                <Select
                  fullWidth
                  size="small"
                  value={selectedShot.shotType || 'medium'}
                  onChange={(e) => {
                    if (selectedShotIndex !== null) {
                      updateShot(selectedShotIndex, { shotType: e.target.value });
                    }
                  }}
                  sx={{
                    bgcolor: '#1a1a1a',
                    color: 'white',
                    '& .MuiOutlinedInput-notchedOutline': { borderColor: '#333' }
                  }}
                >
                  <MenuItem value="wide">Wide Shot</MenuItem>
                  <MenuItem value="medium">Medium Shot</MenuItem>
                  <MenuItem value="close">Close-up</MenuItem>
                  <MenuItem value="detail">Detail Shot</MenuItem>
                </Select>
              </Box>
            </Stack>
          ) : shots.length > 0 ? (
            // 镜头列表
            <Stack spacing={1}>
              <Typography variant="subtitle2" fontWeight={700} color="#fff" mb={1}>
                镜头列表
              </Typography>
              {shots.map((shot, idx) => (
                <Paper
                  key={shot.sequence}
                  onClick={() => setSelectedShotIndex(idx)}
                  sx={{
                    p: 1.5,
                    bgcolor: selectedShotIndex === idx ? alpha('#FF4081', 0.1) : '#1a1a1a',
                    border: `1px solid ${selectedShotIndex === idx ? '#FF4081' : '#333'}`,
                    borderRadius: 1,
                    cursor: 'pointer',
                    '&:hover': { borderColor: '#555' }
                  }}
                >
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <Chip
                      label={`#${shot.sequence}`}
                      size="small"
                      sx={{ bgcolor: '#333', color: '#fff', height: 20 }}
                    />
                    <Typography variant="caption" color="#aaa" sx={{
                      flex: 1,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {shot.prompt}
                    </Typography>
                    <Typography variant="caption" color="#666">
                      {shot.duration}s
                    </Typography>
                  </Stack>
                </Paper>
              ))}
            </Stack>
          ) : (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <TuneIcon sx={{ fontSize: 32, color: '#333', mb: 1 }} />
              <Typography variant="body2" color="#666">
                选中元素查看属性
              </Typography>
            </Box>
          )}
        </Box>
      </TabPanel>

      {/* 设置面板 */}
      <TabPanel value={activeTab} index={1}>
        <Box sx={{ p: 2 }}>
          <Stack spacing={3}>
            {/* 输出设置 */}
            <Box>
              <Typography variant="subtitle2" fontWeight={700} color="#fff" mb={2}>
                输出设置
              </Typography>

              <Stack spacing={2}>
                <Box>
                  <Typography variant="caption" color="#888" display="block" mb={0.5}>
                    分辨率
                  </Typography>
                  <Select
                    fullWidth
                    size="small"
                    value={outputConfig.resolution}
                    onChange={(e) => setOutputConfig({ resolution: e.target.value as any })}
                    sx={{
                      bgcolor: '#1a1a1a',
                      color: 'white',
                      '& .MuiOutlinedInput-notchedOutline': { borderColor: '#333' }
                    }}
                  >
                    <MenuItem value="720p">720p HD</MenuItem>
                    <MenuItem value="1080p">1080p Full HD</MenuItem>
                    <MenuItem value="4K">4K Ultra HD</MenuItem>
                  </Select>
                </Box>

                <Box>
                  <Typography variant="caption" color="#888" display="block" mb={0.5}>
                    质量
                  </Typography>
                  <Select
                    fullWidth
                    size="small"
                    value={outputConfig.quality}
                    onChange={(e) => setOutputConfig({ quality: e.target.value as any })}
                    sx={{
                      bgcolor: '#1a1a1a',
                      color: 'white',
                      '& .MuiOutlinedInput-notchedOutline': { borderColor: '#333' }
                    }}
                  >
                    <MenuItem value="draft">草稿 (快速)</MenuItem>
                    <MenuItem value="standard">标准</MenuItem>
                    <MenuItem value="high">高质量</MenuItem>
                  </Select>
                </Box>
              </Stack>
            </Box>

            <Divider sx={{ borderColor: '#333' }} />

            {/* 旁白设置 */}
            <Box>
              <Typography variant="subtitle2" fontWeight={700} color="#fff" mb={2}>
                旁白设置
              </Typography>

              <Stack spacing={2}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={creative.narration.enabled}
                      onChange={(e) => setCreativeConfig({
                        narration: { ...creative.narration, enabled: e.target.checked }
                      })}
                      sx={{ '& .MuiSwitch-track': { bgcolor: '#555' } }}
                    />
                  }
                  label={<Typography variant="body2">启用AI旁白</Typography>}
                />

                {creative.narration.enabled && (
                  <>
                    <Box>
                      <Typography variant="caption" color="#888" display="block" mb={0.5}>
                        语音
                      </Typography>
                      <Select
                        fullWidth
                        size="small"
                        value={creative.narration.voice}
                        onChange={(e) => setCreativeConfig({
                          narration: { ...creative.narration, voice: e.target.value }
                        })}
                        sx={{
                          bgcolor: '#1a1a1a',
                          color: 'white',
                          '& .MuiOutlinedInput-notchedOutline': { borderColor: '#333' }
                        }}
                      >
                        <MenuItem value="chinese_female">中文女声</MenuItem>
                        <MenuItem value="chinese_male">中文男声</MenuItem>
                        <MenuItem value="english_female">英文女声</MenuItem>
                        <MenuItem value="english_male">英文男声</MenuItem>
                      </Select>
                    </Box>

                    <Box>
                      <Typography variant="caption" color="#888" display="block" mb={0.5}>
                        语速 ({creative.narration.speed}x)
                      </Typography>
                      <Slider
                        value={creative.narration.speed}
                        min={0.5}
                        max={2}
                        step={0.1}
                        onChange={(_, v) => setCreativeConfig({
                          narration: { ...creative.narration, speed: v as number }
                        })}
                        sx={{ color: '#FF4081' }}
                      />
                    </Box>
                  </>
                )}
              </Stack>
            </Box>

            <Divider sx={{ borderColor: '#333' }} />

            {/* 节奏设置 */}
            <Box>
              <Typography variant="subtitle2" fontWeight={700} color="#fff" mb={2}>
                节奏策略
              </Typography>
              <Select
                fullWidth
                size="small"
                value={creative.pacing}
                onChange={(e) => setCreativeConfig({ pacing: e.target.value as any })}
                sx={{
                  bgcolor: '#1a1a1a',
                  color: 'white',
                  '& .MuiOutlinedInput-notchedOutline': { borderColor: '#333' }
                }}
              >
                <MenuItem value="balanced">平衡</MenuItem>
                <MenuItem value="dynamic">动态 (快切)</MenuItem>
                <MenuItem value="crescendo">渐强</MenuItem>
                <MenuItem value="slow_paced">慢节奏</MenuItem>
              </Select>
            </Box>
          </Stack>
        </Box>
      </TabPanel>
    </Box>
  );
};

export default PropertiesPanel;
