/**
 * FrameBuffer - 帧缓冲管理器
 *
 * 职责：
 * - 缓存解码后的 VideoFrame
 * - 提供帧级精确的 seek
 * - 管理内存使用
 */

import type { DecodedVideoFrame } from './WebCodecsDecoder';

export class FrameBuffer {
    private frames: Map<number, DecodedVideoFrame> = new Map();
    private maxFrames: number = 300; // 最多缓存 300 帧（约 10 秒 @ 30fps）
    private sortedTimestamps: number[] = [];

    constructor(maxFrames: number = 300) {
        this.maxFrames = maxFrames;
    }

    /**
     * 添加一帧
     */
    addFrame(frame: DecodedVideoFrame): void {
        const timestamp = frame.timestamp;

        // 如果已存在，先释放旧帧
        if (this.frames.has(timestamp)) {
            const oldFrame = this.frames.get(timestamp)!;
            oldFrame.frame.close();
        }

        // 添加新帧
        this.frames.set(timestamp, frame);
        this.sortedTimestamps.push(timestamp);
        this.sortedTimestamps.sort((a, b) => a - b);

        // 检查是否超过最大缓存
        if (this.frames.size > this.maxFrames) {
            this.evictOldestFrame();
        }
    }

    /**
     * 移除最旧的帧
     */
    private evictOldestFrame(): void {
        if (this.sortedTimestamps.length === 0) return;

        const oldestTimestamp = this.sortedTimestamps.shift()!;
        const frame = this.frames.get(oldestTimestamp);

        if (frame) {
            frame.frame.close();
            this.frames.delete(oldestTimestamp);
        }
    }

    /**
     * 获取指定时间的帧（精确匹配）
     */
    getFrameAt(timestamp: number): DecodedVideoFrame | null {
        return this.frames.get(timestamp) || null;
    }

    /**
     * 获取最接近指定时间的帧
     */
    getClosestFrame(timestamp: number): DecodedVideoFrame | null {
        if (this.sortedTimestamps.length === 0) return null;

        // 二分查找最接近的时间戳
        let left = 0;
        let right = this.sortedTimestamps.length - 1;
        let closest = this.sortedTimestamps[0];
        let minDiff = Math.abs(timestamp - closest);

        while (left <= right) {
            const mid = Math.floor((left + right) / 2);
            const midTimestamp = this.sortedTimestamps[mid];
            const diff = Math.abs(timestamp - midTimestamp);

            if (diff < minDiff) {
                minDiff = diff;
                closest = midTimestamp;
            }

            if (midTimestamp < timestamp) {
                left = mid + 1;
            } else if (midTimestamp > timestamp) {
                right = mid - 1;
            } else {
                // 精确匹配
                return this.frames.get(midTimestamp) || null;
            }
        }

        return this.frames.get(closest) || null;
    }

    /**
     * 获取时间范围内的所有帧
     */
    getFramesInRange(startTime: number, endTime: number): DecodedVideoFrame[] {
        const frames: DecodedVideoFrame[] = [];

        for (const timestamp of this.sortedTimestamps) {
            if (timestamp >= startTime && timestamp <= endTime) {
                const frame = this.frames.get(timestamp);
                if (frame) {
                    frames.push(frame);
                }
            }
        }

        return frames;
    }

    /**
     * 清空缓冲区
     */
    clear(): void {
        // 释放所有帧
        for (const frame of this.frames.values()) {
            frame.frame.close();
        }

        this.frames.clear();
        this.sortedTimestamps = [];
    }

    /**
     * 获取缓存的帧数
     */
    getFrameCount(): number {
        return this.frames.size;
    }

    /**
     * 获取时间范围
     */
    getTimeRange(): { start: number; end: number } | null {
        if (this.sortedTimestamps.length === 0) return null;

        return {
            start: this.sortedTimestamps[0],
            end: this.sortedTimestamps[this.sortedTimestamps.length - 1]
        };
    }

    /**
     * 检查是否有指定时间的帧
     */
    hasFrameAt(timestamp: number, tolerance: number = 16666): boolean {
        // tolerance 默认为 16.666ms（60fps 的一帧）
        for (const ts of this.sortedTimestamps) {
            if (Math.abs(ts - timestamp) <= tolerance) {
                return true;
            }
        }
        return false;
    }
}
