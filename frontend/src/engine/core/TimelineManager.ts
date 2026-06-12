/**
 * TimelineManager - 时间轴管理器
 *
 * 职责：
 * - 管理所有视频片段的时间轴布局
 * - 计算全局时间和片段本地时间的转换
 * - 查找指定时间点应该播放的片段
 */

import type { VideoClipData } from '../types';

export class TimelineManager {
    private clips: VideoClipData[] = [];
    private totalDuration: number = 0;

    constructor(clips: VideoClipData[] = []) {
        this.setClips(clips);
    }

    /**
     * 设置时间轴上的所有片段
     */
    setClips(clips: VideoClipData[]): void {
        // 按开始时间排序
        this.clips = [...clips].sort((a, b) => a.startTime - b.startTime);
        this.calculateTotalDuration();
    }

    /**
     * 获取所有片段
     */
    getClips(): VideoClipData[] {
        return [...this.clips];
    }

    /**
     * 计算总时长
     */
    private calculateTotalDuration(): void {
        if (this.clips.length === 0) {
            this.totalDuration = 0;
            return;
        }
        const lastClip = this.clips[this.clips.length - 1];
        this.totalDuration = lastClip.endTime;
    }

    /**
     * 获取总时长
     */
    getTotalDuration(): number {
        return this.totalDuration;
    }

    /**
     * 根据全局时间查找当前应该播放的片段
     */
    getClipAtTime(globalTime: number): { clip: VideoClipData; index: number; localTime: number } | null {
        for (let i = 0; i < this.clips.length; i++) {
            const clip = this.clips[i];
            if (globalTime >= clip.startTime && globalTime < clip.endTime) {
                const localTime = globalTime - clip.startTime + (clip.trimStart || 0);
                return { clip, index: i, localTime };
            }
        }
        return null;
    }

    /**
     * 获取指定索引的片段
     */
    getClipByIndex(index: number): VideoClipData | null {
        return this.clips[index] || null;
    }

    /**
     * 获取片段数量
     */
    getClipCount(): number {
        return this.clips.length;
    }

    /**
     * 将全局时间转换为片段索引和本地时间
     */
    globalTimeToClipTime(globalTime: number): { clipIndex: number; localTime: number } | null {
        const result = this.getClipAtTime(globalTime);
        if (!result) return null;
        return { clipIndex: result.index, localTime: result.localTime };
    }

    /**
     * 将片段索引和本地时间转换为全局时间
     */
    clipTimeToGlobalTime(clipIndex: number, localTime: number): number | null {
        const clip = this.getClipByIndex(clipIndex);
        if (!clip) return null;
        return clip.startTime + localTime - (clip.trimStart || 0);
    }
}
