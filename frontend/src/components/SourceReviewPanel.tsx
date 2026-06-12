import React, { useRef } from 'react';
import { Box, Chip, Divider, LinearProgress, Paper, Stack, Typography } from '@mui/material';
import {
  ContentCut as SegmentIcon,
  Image as ImageIcon,
  PlayCircle as PlayIcon,
  Source as SourceIcon,
} from '@mui/icons-material';
import type { SourceMaterial, SourceRecommendedSegment } from '../api/types';
import { getFullUrl } from '../utils/url';

interface SourceReviewPanelProps {
  sourceMaterial: SourceMaterial;
  compact?: boolean;
}

const useLabel: Record<string, string> = {
  keep: '保留',
  rewrite: '改写',
  remix: '混剪',
  reference: '参考',
  skip: '跳过',
};

const typeLabel: Record<string, string> = {
  hook: '钩子',
  context: '背景',
  demo: '演示',
  turning_point: '转折',
  evidence: '论据',
  payoff: '结论',
  reference: '参考',
  skip: '跳过',
};

const formatTime = (seconds?: number): string => {
  if (seconds === undefined || seconds === null || Number.isNaN(Number(seconds))) return '--';
  const value = Math.max(0, Number(seconds));
  const minutes = Math.floor(value / 60);
  const secs = Math.floor(value % 60);
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
};

const segmentColor = (segment: SourceRecommendedSegment): 'default' | 'primary' | 'success' | 'warning' => {
  if (segment.suggestedUse === 'skip') return 'default';
  if (segment.type === 'hook') return 'primary';
  if (segment.seedanceReady) return 'success';
  return 'warning';
};

export const SourceReviewPanel: React.FC<SourceReviewPanelProps> = ({ sourceMaterial, compact = false }) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const analysis = sourceMaterial.videoAnalysis;
  const segments = analysis?.recommendedSegments?.segments || [];
  const keyframes = analysis?.keyframes || [];
  const videoUrl = sourceMaterial.publicPath ? getFullUrl(sourceMaterial.publicPath) : undefined;
  const summary =
    sourceMaterial.summary ||
    analysis?.summary?.summary ||
    analysis?.videoUnderstanding?.analysis?.overall_summary;
  const hasAnalysis = Boolean(analysis);

  const seekToSegment = (segment: SourceRecommendedSegment) => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = Math.max(0, Number(segment.start) || 0);
    videoRef.current.play().catch(() => {});
  };

  return (
    <Paper sx={{
      p: compact ? 1.5 : 2,
      bgcolor: '#171717',
      border: '1px solid #282828',
      borderRadius: 1,
    }}>
      <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
        <SourceIcon sx={{ fontSize: 18, color: '#4facfe' }} />
        <Typography variant="caption" color="#888" fontWeight={700}>
          Source Review
        </Typography>
        {sourceMaterial.status && (
          <Chip
            size="small"
            label={sourceMaterial.status}
            sx={{ height: 20, color: '#aaa', borderColor: '#333' }}
            variant="outlined"
          />
        )}
      </Stack>

      <Typography variant="subtitle2" color="white" sx={{ wordBreak: 'break-word', mb: 0.5 }}>
        {sourceMaterial.title || sourceMaterial.domain || sourceMaterial.url}
      </Typography>
      <Typography variant="caption" color="#666" sx={{ display: 'block', wordBreak: 'break-word' }}>
        {sourceMaterial.url}
      </Typography>

      {videoUrl && (
        <Box
          component="video"
          ref={videoRef}
          src={videoUrl}
          controls
          preload="metadata"
          sx={{
            width: '100%',
            mt: 1.5,
            aspectRatio: '16 / 9',
            bgcolor: '#050505',
            borderRadius: 1,
            border: '1px solid #333',
          }}
        />
      )}

      {!hasAnalysis && sourceMaterial.type === 'video' && (
        <Box sx={{ mt: 1.5 }}>
          <Typography variant="caption" color="#888">
            正在等待后台完成视频理解、转写和片段选择
          </Typography>
          <LinearProgress sx={{ mt: 1, bgcolor: '#222', '& .MuiLinearProgress-bar': { bgcolor: '#4facfe' } }} />
        </Box>
      )}

      {summary && (
        <Typography variant="body2" color="#aaa" sx={{
          mt: 1.5,
          lineHeight: 1.55,
          display: '-webkit-box',
          WebkitLineClamp: compact ? 3 : 5,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
        }}>
          {summary}
        </Typography>
      )}

      {segments.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
            <SegmentIcon sx={{ fontSize: 18, color: '#ccc' }} />
            <Typography variant="caption" color="#888" fontWeight={700}>
              推荐二创片段
            </Typography>
            <Chip size="small" label={`${segments.length} 段`} sx={{ height: 20, color: '#aaa', borderColor: '#333' }} variant="outlined" />
          </Stack>
          <Stack spacing={1}>
            {segments.slice(0, compact ? 4 : 8).map((segment) => (
              <Box
                key={`${segment.sequence}-${segment.start}-${segment.end}`}
                onClick={() => seekToSegment(segment)}
                sx={{
                  p: 1,
                  bgcolor: '#111',
                  border: '1px solid #2a2a2a',
                  borderRadius: 1,
                  cursor: videoUrl ? 'pointer' : 'default',
                  '&:hover': videoUrl ? {
                    borderColor: '#4facfe',
                    bgcolor: 'rgba(79,172,254,0.08)',
                  } : undefined,
                }}
              >
                <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.75, flexWrap: 'wrap', rowGap: 0.75 }}>
                  <PlayIcon sx={{ fontSize: 16, color: '#888' }} />
                  <Typography variant="caption" color="#ddd" fontWeight={700}>
                    {formatTime(segment.start)} - {formatTime(segment.end)}
                  </Typography>
                  <Chip size="small" color={segmentColor(segment)} label={useLabel[segment.suggestedUse] || segment.suggestedUse} sx={{ height: 20 }} />
                  <Chip size="small" label={typeLabel[segment.type] || segment.type} sx={{ height: 20, color: '#aaa', borderColor: '#333' }} variant="outlined" />
                  {segment.seedanceReady && (
                    <Chip size="small" label="2-15s" sx={{ height: 20, color: '#8fd19e', borderColor: '#2f6b3a' }} variant="outlined" />
                  )}
                </Stack>
                <Typography variant="body2" color="#ddd" sx={{ lineHeight: 1.45 }}>
                  {segment.title}
                </Typography>
                {!compact && segment.reason && (
                  <Typography variant="caption" color="#888" sx={{ display: 'block', mt: 0.5, lineHeight: 1.45 }}>
                    {segment.reason}
                  </Typography>
                )}
              </Box>
            ))}
          </Stack>
        </Box>
      )}

      {keyframes.length > 0 && (
        <>
          <Divider sx={{ borderColor: '#282828', my: 2 }} />
          <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
            <ImageIcon sx={{ fontSize: 18, color: '#ccc' }} />
            <Typography variant="caption" color="#888" fontWeight={700}>
              关键帧
            </Typography>
          </Stack>
          <Box sx={{ display: 'grid', gridTemplateColumns: compact ? 'repeat(3, 1fr)' : 'repeat(4, 1fr)', gap: 1 }}>
            {keyframes.slice(0, compact ? 6 : 8).map((frame) => (
              <Box key={`${frame.index}-${frame.timestamp}`}>
                {frame.publicPath && (
                  <Box
                    component="img"
                    src={getFullUrl(frame.publicPath)}
                    alt={`keyframe ${frame.index}`}
                    sx={{
                      width: '100%',
                      aspectRatio: '16 / 9',
                      objectFit: 'cover',
                      bgcolor: '#080808',
                      borderRadius: 1,
                      border: '1px solid #333',
                    }}
                  />
                )}
                <Typography variant="caption" color="#777">
                  {formatTime(frame.timestamp)}
                </Typography>
              </Box>
            ))}
          </Box>
        </>
      )}
    </Paper>
  );
};

export default SourceReviewPanel;
