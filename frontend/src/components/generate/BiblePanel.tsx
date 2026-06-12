/**
 * BiblePanel — 展示 DirectorAgent 产出的 ProductionBible
 *
 * 让用户在视频渲染开始前就能看到：
 * - 整体 logline、tone、视觉风格
 * - 每个角色的参考图（保证多镜头里同一个人长得一样）
 * - 每个场景的参考图（保证切机位时世界保持一致）
 *
 * 看到参考图就能判断要不要重新生成；看不到等于黑盒。
 */

import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Stack,
  Avatar,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Tooltip,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Person as PersonIcon,
  Place as PlaceIcon,
  AutoAwesome as AutoAwesomeIcon,
  ImageNotSupported as ImageNotSupportedIcon,
} from '@mui/icons-material';
import { getFullUrl } from '../../utils/url';
import type { ProductionBible } from '../../api/types';

interface BiblePanelProps {
  bible: ProductionBible;
  defaultExpanded?: boolean;
}

const BiblePanel: React.FC<BiblePanelProps> = ({ bible, defaultExpanded = true }) => {
  const characterRefCount = bible.characters.filter((c) => c.reference_image_path).length;
  const sceneRefCount = bible.scenes.filter((s) => s.reference_image_path).length;

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        bgcolor: 'background.paper',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 2,
      }}
    >
      {/* 头部：logline + 概览 */}
      <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
        <AutoAwesomeIcon fontSize="small" color="primary" />
        <Typography variant="subtitle1" fontWeight={600}>
          导演蓝图
        </Typography>
        <Chip
          size="small"
          label={`${bible.characters.length} 角色 · ${characterRefCount} 参考图`}
          sx={{ ml: 1 }}
        />
        <Chip
          size="small"
          label={`${bible.scenes.length} 场景 · ${sceneRefCount} 参考图`}
        />
        <Chip size="small" label={bible.narrative_arc} variant="outlined" />
      </Stack>

      <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'text.secondary', mb: 1 }}>
        {bible.logline || '（无 logline）'}
      </Typography>

      {bible.tone && (
        <Typography variant="caption" color="text.secondary">
          基调：{bible.tone}
        </Typography>
      )}

      {/* 视觉风格摘要 */}
      <Box sx={{ mt: 1.5, mb: 1 }}>
        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
          {bible.visual_style.color_palette && (
            <Chip size="small" label={`色: ${bible.visual_style.color_palette}`} variant="outlined" />
          )}
          {bible.visual_style.lighting_style && (
            <Chip size="small" label={`光: ${bible.visual_style.lighting_style}`} variant="outlined" />
          )}
          {bible.visual_style.overall_mood && (
            <Chip size="small" label={`氛围: ${bible.visual_style.overall_mood}`} variant="outlined" />
          )}
        </Stack>
      </Box>

      <Divider sx={{ my: 1.5 }} />

      {/* 角色参考图 */}
      <Accordion
        defaultExpanded={defaultExpanded}
        disableGutters
        elevation={0}
        sx={{ '&:before': { display: 'none' }, bgcolor: 'transparent' }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ minHeight: 36, px: 0 }}>
          <Stack direction="row" alignItems="center" spacing={1}>
            <PersonIcon fontSize="small" />
            <Typography variant="subtitle2" fontWeight={600}>
              角色（{bible.characters.length}）
            </Typography>
          </Stack>
        </AccordionSummary>
        <AccordionDetails sx={{ px: 0 }}>
          {bible.characters.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              （未识别到角色）
            </Typography>
          ) : (
            <Stack spacing={1.5}>
              {bible.characters.map((c) => (
                <CharacterRow key={c.character_id} character={c} />
              ))}
            </Stack>
          )}
        </AccordionDetails>
      </Accordion>

      <Divider sx={{ my: 1 }} />

      {/* 场景参考图 */}
      <Accordion
        defaultExpanded={defaultExpanded}
        disableGutters
        elevation={0}
        sx={{ '&:before': { display: 'none' }, bgcolor: 'transparent' }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ minHeight: 36, px: 0 }}>
          <Stack direction="row" alignItems="center" spacing={1}>
            <PlaceIcon fontSize="small" />
            <Typography variant="subtitle2" fontWeight={600}>
              场景（{bible.scenes.length}）
            </Typography>
          </Stack>
        </AccordionSummary>
        <AccordionDetails sx={{ px: 0 }}>
          {bible.scenes.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              （未识别到场景）
            </Typography>
          ) : (
            <Stack spacing={1.5}>
              {bible.scenes.map((s) => (
                <SceneRow key={s.scene_id} scene={s} />
              ))}
            </Stack>
          )}
        </AccordionDetails>
      </Accordion>
    </Paper>
  );
};

// ---------- 子组件 ----------

const RefThumbnail: React.FC<{ path?: string | null; alt: string; size?: number }> = ({
  path,
  alt,
  size = 56,
}) => {
  if (!path) {
    return (
      <Box
        sx={{
          width: size,
          height: size,
          borderRadius: 1,
          bgcolor: 'action.hover',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'text.disabled',
          flexShrink: 0,
        }}
      >
        <ImageNotSupportedIcon fontSize="small" />
      </Box>
    );
  }
  return (
    <Tooltip title={alt}>
      <Avatar
        src={getFullUrl(path)}
        alt={alt}
        variant="rounded"
        sx={{ width: size, height: size, flexShrink: 0 }}
      />
    </Tooltip>
  );
};

const CharacterRow: React.FC<{ character: import('../../api/types').CharacterProfile }> = ({
  character,
}) => (
  <Stack direction="row" spacing={1.5} alignItems="flex-start">
    <RefThumbnail path={character.reference_image_path} alt={character.name} />
    <Box sx={{ flex: 1, minWidth: 0 }}>
      <Stack direction="row" alignItems="center" spacing={0.75}>
        <Typography variant="body2" fontWeight={600} noWrap>
          {character.name}
        </Typography>
        <Chip
          size="small"
          label={character.role}
          sx={{ height: 18, fontSize: '0.65rem' }}
        />
      </Stack>
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
          overflow: 'hidden',
        }}
      >
        {character.description}
      </Typography>
      {character.visual_keywords?.length > 0 && (
        <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }} flexWrap="wrap" useFlexGap>
          {character.visual_keywords.slice(0, 4).map((kw) => (
            <Chip
              key={kw}
              size="small"
              label={kw}
              sx={{ height: 18, fontSize: '0.65rem' }}
            />
          ))}
        </Stack>
      )}
    </Box>
  </Stack>
);

const SceneRow: React.FC<{ scene: import('../../api/types').SceneInfo }> = ({ scene }) => (
  <Stack direction="row" spacing={1.5} alignItems="flex-start">
    <RefThumbnail
      path={scene.reference_image_path}
      alt={`Scene ${scene.scene_id}: ${scene.location}`}
    />
    <Box sx={{ flex: 1, minWidth: 0 }}>
      <Stack direction="row" alignItems="center" spacing={0.75}>
        <Typography variant="body2" fontWeight={600} noWrap>
          场景 {scene.scene_id}：{scene.location}
        </Typography>
      </Stack>
      <Stack direction="row" spacing={0.5} sx={{ mt: 0.5 }} flexWrap="wrap" useFlexGap>
        <Chip
          size="small"
          label={scene.time_of_day}
          sx={{ height: 18, fontSize: '0.65rem' }}
          variant="outlined"
        />
        <Chip
          size="small"
          label={scene.mood}
          sx={{ height: 18, fontSize: '0.65rem' }}
          variant="outlined"
        />
      </Stack>
    </Box>
  </Stack>
);

export default BiblePanel;
