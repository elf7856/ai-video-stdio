/**
 * ConversationPanel - 体验增强版
 */

import React, { useRef, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box, Typography, Paper, Stack, CircularProgress, Divider, Button, alpha
} from '@mui/material';
import { AutoAwesome as MagicIcon } from '@mui/icons-material';
import { useWorkflowStore } from '../../stores/workflowStore';
import { getFullUrl } from '../../utils/url';

const ConversationPanel: React.FC = () => {
  const navigate = useNavigate();
  const { projectId } = useParams<{ projectId: string }>();
  const { conversation, stage, shots, taskStatus, syncTask, initiateTask, confirmAndGenerate } = useWorkflowStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (projectId?.startsWith('proj_task_')) {
      syncTask(projectId.replace('proj_', ''));
    } else if (stage === 'planning' && !projectId) {
      initiateTask(navigate);
    }
  }, [projectId, stage, syncTask, initiateTask, navigate]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation, shots]);

  const renderMessage = (msg: any) => {
    const isUser = msg.role === 'user';
    return (
      <Box key={msg.id} sx={{ display: 'flex', mb: 3, justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
        <Paper sx={{
          maxWidth: '92%', p: 2, borderRadius: 2,
          bgcolor: isUser ? alpha('#FF4081', 0.1) : '#1a1a1a',
          border: `1px solid ${isUser ? alpha('#FF4081', 0.2) : '#333'}`,
          boxShadow: isUser ? 'none' : '0 4px 12px rgba(0,0,0,0.5)'
        }}>
          <Typography variant="body2" sx={{ color: '#eee', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
            {msg.content}
          </Typography>
          
          {msg.planning && (
            <Box sx={{ mt: 2 }}>
              <Divider sx={{ mb: 2, borderColor: '#333' }} />
              <Stack spacing={1.5}>
                {msg.planning.shots.map((s: any) => (
                  <Box key={s.sequence} sx={{ display: 'flex', gap: 1.5, p: 1, bgcolor: '#000', borderRadius: 1, border: '1px solid #222' }}>
                    <Box sx={{ width: 80, height: 45, bgcolor: '#111', borderRadius: 0.5, overflow: 'hidden', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {s.imagePath ? (
                        <img src={getFullUrl(s.imagePath)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="p" />
                      ) : (
                        <CircularProgress size={10} thickness={2} sx={{ color: '#444' }} />
                      )}
                    </Box>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography variant="caption" color="#FF4081" display="block" fontWeight={700}>#{s.sequence}</Typography>
                      <Typography variant="caption" color="#888" sx={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                        {s.description}
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Stack>
            </Box>
          )}
        </Paper>
      </Box>
    );
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ px: 2, py: 1.5, borderBottom: '1px solid #222', display: 'flex', alignItems: 'center', gap: 1 }}>
        <MagicIcon sx={{ color: '#FF4081', fontSize: 18 }} />
        <Typography variant="subtitle2" fontWeight={700}>AI DIRECTOR</Typography>
      </Box>
      <Box sx={{ flex: 1, overflowY: 'auto', p: 2 }}>
        {conversation.map(renderMessage)}
        <div ref={messagesEndRef} />
      </Box>
      {shots.length > 0 && taskStatus?.status === 'waiting_confirmation' && (
        <Box sx={{ p: 2, borderTop: '1px solid #222' }}>
          <Button fullWidth variant="contained" color="success" onClick={confirmAndGenerate}>确认方案并生成视频</Button>
        </Box>
      )}
    </Box>
  );
};

export default ConversationPanel;