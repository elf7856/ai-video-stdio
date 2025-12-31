import React, { useEffect, useState, useRef } from 'react';
import { Box, Skeleton } from '@mui/material';

interface TimelineFilmstripProps {
    videoUrl: string;
    duration: number;
    height: number;
    pxPerSec: number; // 每秒对应的像素数，用于计算密度
}

const TimelineFilmstrip: React.FC<TimelineFilmstripProps> = ({ videoUrl, duration, height, pxPerSec }) => {
    const [thumbnails, setThumbnails] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const generationRef = useRef(false);

    useEffect(() => {
        if (!videoUrl || generationRef.current) return;
        
        generationRef.current = true;
        setLoading(true);
        setError(null);

        const generateThumbnails = async () => {
            try {
                const video = document.createElement('video');
                video.src = videoUrl;
                video.crossOrigin = "anonymous"; // 处理跨域图片
                video.muted = true;
                video.preload = "auto";

                // 等待元数据加载
                await new Promise((resolve, reject) => {
                    video.onloadedmetadata = () => resolve(true);
                    video.onerror = (e) => reject(new Error(`Video load error: ${e}`));
                    setTimeout(() => reject(new Error("Video load timeout")), 10000);
                });

                if (!video.duration) throw new Error("Invalid duration");

                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                if (!ctx) throw new Error("Canvas context failed");
// ... existing code ...
            } catch (err: any) {
                console.error("Thumbnail generation failed:", err);
                setError(err.message || "Failed to load");
                setLoading(false);
            }
        };

        generateThumbnails();

    }, [videoUrl, duration, pxPerSec]);

    if (error) {
        // Fallback: 如果生成缩略图失败（例如CORS），直接显示视频
        return (
            <Box sx={{ width: '100%', height: '100%', bgcolor: '#000', overflow: 'hidden' }}>
                <video 
                    src={videoUrl}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    muted
                />
            </Box>
        );
    }

    if (loading) {
        return (
            <Box sx={{ width: '100%', height: '100%', display: 'flex', overflow: 'hidden' }}>
                {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} variant="rectangular" height="100%" width={80} sx={{ mr: 0.5, bgcolor: '#333' }} />
                ))}
            </Box>
        );
    }

    return (
        <Box sx={{ 
            width: '100%', 
            height: '100%', 
            display: 'flex', 
            overflow: 'hidden',
            bgcolor: '#000' 
        }}>
            {thumbnails.map((src, i) => (
                <img 
                    key={i} 
                    src={src} 
                    style={{ 
                        height: '100%', 
                        flex: 1, // 均分宽度
                        objectFit: 'cover',
                        borderRight: '1px solid rgba(255,255,255,0.2)',
                        pointerEvents: 'none'
                    }} 
                    alt="" 
                />
            ))}
        </Box>
    );
};

export default TimelineFilmstrip;
