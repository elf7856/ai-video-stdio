/**
 * CanvasPlayerTest - Canvas 播放器测试页面
 *
 * 这是一个独立的测试页面，用于验证 Canvas NLE 引擎的功能
 */

import React from 'react';
import { Box, Container, Typography, Paper } from '@mui/material';
import { CanvasVideoPlayer } from '../components/project/CanvasVideoPlayer';
import { useLocation } from 'react-router-dom';
import type { Shot, GeneratedVideo } from '../api/types';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

export const CanvasPlayerTestPage: React.FC = () => {
    const location = useLocation();
    const orderedShots = (location.state?.orderedShots || []) as ShotWithVideo[];

    if (orderedShots.length === 0) {
        return (
            <Container maxWidth="md" sx={{ mt: 4 }}>
                <Paper sx={{ p: 4, textAlign: 'center' }}>
                    <Typography variant="h5" gutterBottom>
                        Canvas 播放器测试
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        请从 Project 页面传入视频数据
                    </Typography>
                </Paper>
            </Container>
        );
    }

    return (
        <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: '#000' }}>
            {/* 标题栏 */}
            <Box sx={{ p: 2, bgcolor: '#1a1a1a', borderBottom: '1px solid #333' }}>
                <Typography variant="h6" color="white">
                    Canvas NLE Engine 测试
                </Typography>
                <Typography variant="caption" color="text.secondary">
                    使用 Video + Canvas + requestVideoFrameCallback 实现无缝切换
                </Typography>
            </Box>

            {/* 播放器 */}
            <Box sx={{ flex: 1, position: 'relative' }}>
                <CanvasVideoPlayer orderedShots={orderedShots} />
            </Box>

            {/* 信息栏 */}
            <Box sx={{ p: 2, bgcolor: '#1a1a1a', borderTop: '1px solid #333' }}>
                <Typography variant="body2" color="text.secondary">
                    共 {orderedShots.length} 个镜头
                </Typography>
            </Box>
        </Box>
    );
};
