/**
 * WebAVPlayer - 基于 WebAV 的专业视频播放器
 *
 * 使用 @webav/av-cliper 实现帧级精确控制和无缝视频合成
 */

import React, { useRef, useEffect, useState } from 'react';
import { Box, Typography, IconButton, Slider, Stack, Chip, alpha, useTheme, CircularProgress } from '@mui/material';
import { PlayArrow as PlayIcon, Pause as PauseIcon, VolumeUp as VolumeIcon, VolumeOff as MuteIcon } from '@mui/icons-material';
import { Combinator, OffscreenSprite, MP4Clip } from '@webav/av-cliper';
import type { Shot, GeneratedVideo } from '../../api/types';
import { getFullUrl } from '../../utils/url';

interface ShotWithVideo extends Shot {
    videoData?: Shot | GeneratedVideo;
}

interface WebAVPlayerProps {
    orderedShots: ShotWithVideo[];
}

const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export const WebAVPlayer: React.FC<WebAVPlayerProps> = ({ orderedShots }) => {
    const theme = useTheme();
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const combinatorRef = useRef<Combinator | null>(null);
    const animationFrameRef = useRef<number | null>(null);

    // 播放状态
    const [isReady, setIsReady] = useState(false);
    const [isPlaying, setIsPlaying] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [totalDuration, setTotalDuration] = useState(0);
    const [volume, setVolume] = useState(1);
    const [isMuted, setIsMuted] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [currentShotIndex, setCurrentShotIndex] = useState(0);

    // 拖动状态
    const [localTime, setLocalTime] = useState<number | null>(null);
    const displayTime = localTime !== null ? localTime : currentTime;

    // 初始化 WebAV Combinator
    useEffect(() => {
        if (!canvasRef.current || orderedShots.length === 0) return;

        const initWebAV = async () => {
            try {
                console.log('[WebAVPlayer] Initializing with', orderedShots.length, 'shots');

                // 创建 Combinator
                const combinator = new Combinator({
                    width: 1280,
                    height: 720
                });

                // 添加视频片段
                let accTime = 0;
                for (const shot of orderedShots) {
                    const videoPath = shot.videoData?.videoPath || '';
                    if (!videoPath) continue;

                    const fullUrl = getFullUrl(videoPath);
                    console.log('[WebAVPlayer] Loading shot:', fullUrl);

                    try {
                        // 创建视频 Sprite
                        const sprite = new OffscreenSprite(
                            new MP4Clip((await fetch(fullUrl)).body!)
                        );

                        // 设置时间偏移和持续时间
                        sprite.time = {
                            offset: accTime * 1e6, // 微秒
                            duration: shot.duration * 1e6
                        };

                        await combinator.addSprite(sprite);
                        accTime += shot.duration;
                    } catch (err) {
                        console.error('[WebAVPlayer] Failed to load shot:', err);
                    }
                }

                // 计算总时长
                const total = orderedShots.reduce((sum, shot) => sum + shot.duration, 0);
                setTotalDuration(total);

                combinatorRef.current = combinator;
                setIsReady(true);
                setError(null);

                console.log('[WebAVPlayer] Initialized successfully, duration:', total);
            } catch (err: any) {
                console.error('[WebAVPlayer] Initialization error:', err);
                setError(err.message || 'Failed to initialize player');
            }
        };

        initWebAV();

        return () => {
            if (combinatorRef.current) {
                combinatorRef.current.destroy();
                combinatorRef.current = null;
            }
            if (animationFrameRef.current) {
                cancelAnimationFrame(animationFrameRef.current);
            }
        };
    }, [orderedShots]);

    // 播放循环
    useEffect(() => {
        if (!isPlaying || !combinatorRef.current || !canvasRef.current) return;

        const ctx = canvasRef.current.getContext('2d');
        if (!ctx) return;

        let startTime = performance.now();
        let startOffset = currentTime;

        const render = async (timestamp: number) => {
            if (!isPlaying || !combinatorRef.current) return;

            const elapsed = (timestamp - startTime) / 1000;
            const newTime = startOffset + elapsed;

            if (newTime >= totalDuration) {
                // 播放完毕
                setIsPlaying(false);
                setCurrentTime(0);
                return;
            }

            setCurrentTime(newTime);

            // 更新当前镜头索引
            let acc = 0;
            for (let i = 0; i < orderedShots.length; i++) {
                acc += orderedShots[i].duration;
                if (newTime < acc) {
                    setCurrentShotIndex(i);
                    break;
                }
            }

            // 渲染当前帧
            try {
                const { video } = (await combinatorRef.current.output()) as any;
                if (video) {
                    ctx.clearRect(0, 0, canvasRef.current!.width, canvasRef.current!.height);
                    ctx.drawImage(video, 0, 0);
                    video.close();
                }
            } catch (err) {
                console.error('[WebAVPlayer] Render error:', err);
            }

            animationFrameRef.current = requestAnimationFrame(render);
        };

        animationFrameRef.current = requestAnimationFrame(render);

        return () => {
            if (animationFrameRef.current) {
                cancelAnimationFrame(animationFrameRef.current);
            }
        };
    }, [isPlaying, currentTime, totalDuration, orderedShots]);

    // 播放/暂停
    const handlePlayPause = () => {
        setIsPlaying(!isPlaying);
    };

    // Seek
    const handleSeek = async (_event: unknown, value: number | number[]) => {
        const seekTime = value as number;
        setCurrentTime(seekTime);
        setLocalTime(null);

        // WebAV 的 seek 会在下一次渲染时生效
    };

    // 音量控制
    const handleVolumeChange = (_: Event, value: number | number[]) => {
        const newVolume = value as number;
        setVolume(newVolume);
        setIsMuted(newVolume === 0);
        // WebAV 的音量控制需要在 Combinator 配置中设置
    };

    // 静音切换
    const toggleMute = () => {
        setIsMuted(!isMuted);
    };

    return (
        <Box sx={{
            flex: 1,
            bgcolor: '#050505',
            display: 'flex',
            flexDirection: 'column',
            position: 'relative'
        }}>
            {/* Canvas 容器 */}
            <Box sx={{
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
                overflow: 'hidden',
                bgcolor: '#000'
            }}>
                {/* Canvas 元素 */}
                <canvas
                    ref={canvasRef}
                    width={1280}
                    height={720}
                    style={{
                        maxWidth: '100%',
                        maxHeight: '100%',
                        objectFit: 'contain',
                        backgroundColor: '#000'
                    }}
                />

                {/* 加载指示器 */}
                {!isReady && !error && (
                    <Box sx={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        textAlign: 'center',
                        zIndex: 10
                    }}>
                        <CircularProgress />
                        <Typography variant="body2" sx={{ mt: 2, color: 'white' }}>
                            Loading WebAV Player...
                        </Typography>
                    </Box>
                )}

                {/* 错误提示 */}
                {error && (
                    <Box sx={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        textAlign: 'center',
                        zIndex: 10
                    }}>
                        <Typography variant="h6" color="error">
                            {error}
                        </Typography>
                    </Box>
                )}

                {/* 镜头信息 */}
                <Chip
                    label={`镜头 ${currentShotIndex + 1} / ${orderedShots.length}`}
                    size="small"
                    sx={{
                        position: 'absolute',
                        top: 16,
                        left: 16,
                        bgcolor: alpha(theme.palette.background.paper, 0.8),
                        backdropFilter: 'blur(10px)',
                        fontWeight: 600,
                        zIndex: 10
                    }}
                />
            </Box>

            {/* 控制栏 */}
            <Box sx={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                bgcolor: alpha('#000', 0.7),
                backdropFilter: 'blur(10px)',
                p: 2,
                zIndex: 100
            }}>
                {/* 进度条 */}
                <Slider
                    value={displayTime}
                    min={0}
                    max={totalDuration}
                    onChange={(_event, value) => setLocalTime(value as number)}
                    onChangeCommitted={(_event, value) => { void handleSeek(_event, value); }}
                    disabled={!isReady}
                    sx={{
                        mb: 1,
                        '& .MuiSlider-thumb': {
                            width: 16,
                            height: 16,
                            '&:hover, &.Mui-focusVisible': {
                                boxShadow: '0 0 0 8px rgba(255, 64, 129, 0.16)'
                            }
                        },
                        '& .MuiSlider-track': {
                            height: 4,
                            bgcolor: '#FF4081'
                        },
                        '& .MuiSlider-rail': {
                            height: 4,
                            bgcolor: alpha('#fff', 0.2)
                        }
                    }}
                />

                {/* 控制按钮 */}
                <Stack direction="row" alignItems="center" spacing={2}>
                    {/* 播放/暂停 */}
                    <IconButton
                        onClick={handlePlayPause}
                        disabled={!isReady}
                        sx={{
                            bgcolor: alpha('#FF4081', 0.1),
                            '&:hover': { bgcolor: alpha('#FF4081', 0.2) }
                        }}
                    >
                        {isPlaying ? <PauseIcon /> : <PlayIcon />}
                    </IconButton>

                    {/* 时间显示 */}
                    <Typography variant="body2" sx={{ minWidth: 100, color: 'white' }}>
                        {formatTime(displayTime)} / {formatTime(totalDuration)}
                    </Typography>

                    <Box sx={{ flex: 1 }} />

                    {/* 音量控制 */}
                    <IconButton onClick={toggleMute} size="small" sx={{ color: 'white' }}>
                        {isMuted ? <MuteIcon /> : <VolumeIcon />}
                    </IconButton>

                    <Slider
                        value={isMuted ? 0 : volume}
                        min={0}
                        max={1}
                        step={0.01}
                        onChange={handleVolumeChange}
                        sx={{
                            width: 100,
                            '& .MuiSlider-thumb': {
                                width: 12,
                                height: 12
                            },
                            '& .MuiSlider-track': {
                                height: 3
                            },
                            '& .MuiSlider-rail': {
                                height: 3
                            }
                        }}
                    />
                </Stack>
            </Box>
        </Box>
    );
};
