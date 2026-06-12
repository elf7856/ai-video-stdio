import React, { useState, useRef, useEffect } from 'react';
import { Box, Typography, TextField, IconButton, CircularProgress, Paper, Chip, Tooltip } from '@mui/material';
import { Send as SendIcon, AutoFixHigh as AIIcon, CheckCircle as ApplyIcon } from '@mui/icons-material';
import axios from 'axios';
import type { Shot, GeneratedVideo } from '../../api/types';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

interface ConversationMessage {
    role: 'user' | 'assistant';
    content: string;
    operations?: Operation[];
    applied?: boolean;
}

interface Operation {
    type: 'update_shot' | 'delete_shot' | 'reorder_shots' | 'update_script' | 'regenerate_shot';
    shot_index?: number;
    changes?: { prompt?: string; duration?: number; shotType?: string };
    new_order?: number[];
    script?: string;
}

interface AIAssistantProps {
    taskId: string;
    projectScript: string;
    orderedShots: ShotWithVideo[];
    onApplyOperations: (operations: Operation[]) => void;
}

const OP_LABEL: Record<string, string> = {
    update_shot: '修改镜头',
    delete_shot: '删除镜头',
    reorder_shots: '重新排序',
    update_script: '更新脚本',
    regenerate_shot: '重新生成',
};

export const AIAssistant: React.FC<AIAssistantProps> = ({
    taskId,
    projectScript,
    orderedShots,
    onApplyOperations,
}) => {
    const [messages, setMessages] = useState<ConversationMessage[]>([
        {
            role: 'assistant',
            content: '你好！我是 AI 剪辑助手。你可以告诉我需要怎么修改这个视频项目，例如：\n• "把第2个镜头的时长改为5秒"\n• "把所有镜头的风格改成夜景"\n• "删除第3个镜头"\n• "把镜头1和镜头2的顺序对调"',
        },
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [history, setHistory] = useState<{ role: string; content: string }[]>([]);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, loading]);

    const sendMessage = async () => {
        const text = input.trim();
        if (!text || loading) return;
        setInput('');

        const userMsg: ConversationMessage = { role: 'user', content: text };
        setMessages(prev => [...prev, userMsg]);
        setLoading(true);

        try {
            const { data } = await axios.post('/api/editor/ai-command', {
                message: text,
                task_id: taskId,
                current_script: projectScript,
                current_shots: orderedShots.map(s => ({
                    sequence: s.sequence,
                    prompt: s.prompt,
                    duration: s.duration,
                    shotType: s.shotType,
                    status: s.status,
                })),
                conversation_history: history,
            });

            setHistory(data.conversation_history || []);

            const assistantMsg: ConversationMessage = {
                role: 'assistant',
                content: data.ai_response,
                operations: data.operations?.length > 0 ? data.operations : undefined,
            };
            setMessages(prev => [...prev, assistantMsg]);
        } catch {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: '抱歉，请求失败，请检查网络后重试。',
            }]);
        } finally {
            setLoading(false);
        }
    };

    const applyOps = (msgIndex: number, ops: Operation[]) => {
        onApplyOperations(ops);
        setMessages(prev => prev.map((m, i) =>
            i === msgIndex ? { ...m, applied: true } : m
        ));
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            {/* 消息列表 */}
            <Box sx={{ flex: 1, overflowY: 'auto', p: 2, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                {messages.map((msg, i) => (
                    <Box key={i} sx={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                        <Paper
                            sx={{
                                px: 1.5, py: 1,
                                maxWidth: '90%',
                                bgcolor: msg.role === 'user' ? '#FF4081' : '#1e1e1e',
                                border: msg.role === 'assistant' ? '1px solid #333' : 'none',
                                borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                            }}
                        >
                            <Typography variant="body2" sx={{ color: '#fff', whiteSpace: 'pre-wrap', lineHeight: 1.6, fontSize: '0.82rem' }}>
                                {msg.content}
                            </Typography>

                            {/* 操作列表 */}
                            {msg.operations && msg.operations.length > 0 && (
                                <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5, alignItems: 'center' }}>
                                    {msg.operations.map((op, j) => (
                                        <Chip
                                            key={j}
                                            label={`${OP_LABEL[op.type] || op.type}${op.shot_index !== undefined ? ` #${op.shot_index + 1}` : ''}`}
                                            size="small"
                                            sx={{ fontSize: '0.65rem', bgcolor: '#333', color: '#ccc', height: 20 }}
                                        />
                                    ))}
                                    {!msg.applied ? (
                                        <Tooltip title="应用这些修改">
                                            <IconButton
                                                size="small"
                                                onClick={() => applyOps(i, msg.operations!)}
                                                sx={{ ml: 0.5, color: '#4caf50', p: 0.3 }}
                                            >
                                                <ApplyIcon sx={{ fontSize: 16 }} />
                                            </IconButton>
                                        </Tooltip>
                                    ) : (
                                        <Chip label="已应用" size="small" sx={{ fontSize: '0.65rem', bgcolor: '#1b3a1b', color: '#4caf50', height: 20 }} />
                                    )}
                                </Box>
                            )}
                        </Paper>
                    </Box>
                ))}

                {loading && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <AIIcon sx={{ fontSize: 16, color: '#FF4081' }} />
                        <CircularProgress size={14} sx={{ color: '#FF4081' }} />
                        <Typography variant="caption" color="#666">AI 思考中...</Typography>
                    </Box>
                )}
                <div ref={bottomRef} />
            </Box>

            {/* 输入框 */}
            <Box sx={{ p: 1.5, borderTop: '1px solid #222', display: 'flex', gap: 1, alignItems: 'flex-end' }}>
                <TextField
                    fullWidth
                    multiline
                    maxRows={4}
                    size="small"
                    placeholder="描述你想要的修改..."
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                    disabled={loading}
                    sx={{
                        '& .MuiOutlinedInput-root': {
                            bgcolor: '#1a1a1a',
                            color: '#fff',
                            fontSize: '0.85rem',
                            '& fieldset': { borderColor: '#333' },
                            '&:hover fieldset': { borderColor: '#555' },
                            '&.Mui-focused fieldset': { borderColor: '#FF4081' },
                        },
                        '& .MuiInputBase-input::placeholder': { color: '#555' },
                    }}
                />
                <IconButton
                    onClick={sendMessage}
                    disabled={!input.trim() || loading}
                    sx={{
                        bgcolor: '#FF4081', color: '#fff', width: 36, height: 36, flexShrink: 0,
                        '&:hover': { bgcolor: '#e91e63' },
                        '&.Mui-disabled': { bgcolor: '#333', color: '#555' },
                    }}
                >
                    <SendIcon sx={{ fontSize: 18 }} />
                </IconButton>
            </Box>
        </Box>
    );
};
