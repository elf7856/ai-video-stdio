/**
 * VideoLoader - 视频文件加载器
 *
 * 职责：
 * - 加载视频文件
 * - 提取视频元数据
 * - 解复用（demux）视频流
 */

import type { VideoMetadata } from './types';

export class VideoLoader {
    /**
     * 加载视频文件并提取元数据
     */
    async loadVideoMetadata(url: string): Promise<VideoMetadata> {
        return new Promise((resolve, reject) => {
            const video = document.createElement('video');
            video.crossOrigin = 'anonymous';
            video.preload = 'metadata';

            video.addEventListener('loadedmetadata', () => {
                const metadata: VideoMetadata = {
                    duration: video.duration,
                    width: video.videoWidth,
                    height: video.videoHeight,
                    fps: 30, // 默认 30fps，实际需要从视频流中解析
                    codec: 'avc1.42E01E' // 默认 H.264，实际需要检测
                };
                resolve(metadata);
            });

            video.addEventListener('error', () => {
                reject(new Error(`Failed to load video: ${url}`));
            });

            video.src = url;
        });
    }

    /**
     * 使用 fetch 加载视频数据
     */
    async fetchVideo(url: string): Promise<ArrayBuffer> {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to fetch video: ${response.statusText}`);
        }
        return await response.arrayBuffer();
    }

    /**
     * 检测视频编码格式
     */
    detectCodec(_data: ArrayBuffer): string {
        // 简化实现：默认返回 H.264
        // 实际应该解析视频文件头来检测编码格式
        return 'avc1.42E01E';
    }
}
