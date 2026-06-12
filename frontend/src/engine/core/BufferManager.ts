/**
 * BufferManager - 视频缓冲管理器
 *
 * 职责：
 * - 管理双缓冲的两个 video 元素
 * - 预加载下一个片段
 * - 处理视频元素的切换
 */

import type { VideoClipData, BufferState } from '../types';

export class BufferManager {
    private primaryVideo: HTMLVideoElement | null = null;
    private secondaryVideo: HTMLVideoElement | null = null;
    private activePrimary: boolean = true;
    private preloadedClipId: string | null = null;
    private urlHelper: (path: string) => string;

    constructor(urlHelper: (path: string) => string) {
        this.urlHelper = urlHelper;
    }

    /**
     * 初始化视频元素
     */
    initialize(primaryVideo: HTMLVideoElement, secondaryVideo: HTMLVideoElement): void {
        this.primaryVideo = primaryVideo;
        this.secondaryVideo = secondaryVideo;
        this.activePrimary = true;
        this.preloadedClipId = null;

        // 设置视频元素的基本属性
        [primaryVideo, secondaryVideo].forEach(video => {
            video.crossOrigin = 'anonymous';
            video.preload = 'auto';
        });
    }

    /**
     * 获取当前活跃的视频元素
     */
    getActiveVideo(): HTMLVideoElement | null {
        return this.activePrimary ? this.primaryVideo : this.secondaryVideo;
    }

    /**
     * 获取当前非活跃的视频元素
     */
    getInactiveVideo(): HTMLVideoElement | null {
        return this.activePrimary ? this.secondaryVideo : this.primaryVideo;
    }

    /**
     * 获取缓冲状态
     */
    getState(): BufferState {
        return {
            primaryVideoElement: this.primaryVideo,
            secondaryVideoElement: this.secondaryVideo,
            activePrimary: this.activePrimary,
            preloadedClipId: this.preloadedClipId
        };
    }

    /**
     * 加载并播放指定片段到活跃的视频元素
     */
    async loadAndPlay(clip: VideoClipData, localTime: number = 0, autoPlay: boolean = true): Promise<void> {
        const activeVideo = this.getActiveVideo();
        if (!activeVideo) {
            throw new Error('No active video element');
        }

        return new Promise((resolve, reject) => {
            const videoUrl = this.urlHelper(clip.videoPath);

            const handleLoadedData = () => {
                activeVideo.currentTime = localTime;

                if (autoPlay) {
                    activeVideo.play()
                        .then(() => resolve())
                        .catch(reject);
                } else {
                    resolve();
                }

                cleanup();
            };

            const handleError = () => {
                cleanup();
                reject(new Error(`Failed to load clip ${clip.id}`));
            };

            const cleanup = () => {
                activeVideo.removeEventListener('loadeddata', handleLoadedData);
                activeVideo.removeEventListener('error', handleError);
            };

            activeVideo.addEventListener('loadeddata', handleLoadedData, { once: true });
            activeVideo.addEventListener('error', handleError, { once: true });

            activeVideo.src = videoUrl;
            activeVideo.load();
        });
    }

    /**
     * 预加载下一个片段到非活跃的视频元素
     */
    async preloadClip(clip: VideoClipData): Promise<void> {
        const inactiveVideo = this.getInactiveVideo();
        if (!inactiveVideo) {
            console.warn('No inactive video element available for preloading');
            return;
        }

        return new Promise((resolve, reject) => {
            const videoUrl = this.urlHelper(clip.videoPath);

            const handleLoadedData = () => {
                this.preloadedClipId = clip.id;
                console.log(`[BufferManager] Preloaded clip ${clip.id}`);
                cleanup();
                resolve();
            };

            const handleError = () => {
                console.error(`[BufferManager] Failed to preload clip ${clip.id}`);
                cleanup();
                reject(new Error(`Failed to preload clip ${clip.id}`));
            };

            const cleanup = () => {
                inactiveVideo.removeEventListener('loadeddata', handleLoadedData);
                inactiveVideo.removeEventListener('error', handleError);
            };

            inactiveVideo.addEventListener('loadeddata', handleLoadedData, { once: true });
            inactiveVideo.addEventListener('error', handleError, { once: true });

            inactiveVideo.src = videoUrl;
            inactiveVideo.currentTime = 0;
            inactiveVideo.load();
        });
    }

    /**
     * 切换到预加载的片段（无缝切换）
     */
    async switchToPreloadedClip(clip: VideoClipData, localTime: number = 0): Promise<boolean> {
        // 检查是否已预加载了正确的片段
        if (this.preloadedClipId !== clip.id) {
            console.warn(`[BufferManager] Expected preloaded clip ${clip.id}, but got ${this.preloadedClipId}`);
            return false;
        }

        const currentActiveVideo = this.getActiveVideo();
        const currentInactiveVideo = this.getInactiveVideo();

        if (!currentInactiveVideo) {
            return false;
        }

        // 检查预加载的视频是否准备好
        if (currentInactiveVideo.readyState < 2) {
            console.warn(`[BufferManager] Preloaded video not ready, readyState: ${currentInactiveVideo.readyState}`);
            return false;
        }

        try {
            // 暂停当前视频
            if (currentActiveVideo) {
                currentActiveVideo.pause();
            }

            // 设置新视频的播放位置
            currentInactiveVideo.currentTime = localTime;

            // 播放新视频
            await currentInactiveVideo.play();

            // 切换活跃标志
            this.activePrimary = !this.activePrimary;
            this.preloadedClipId = null;

            console.log(`[BufferManager] Successfully switched to clip ${clip.id}, now active: ${this.activePrimary ? 'primary' : 'secondary'}`);

            return true;
        } catch (error) {
            console.error('[BufferManager] Failed to switch to preloaded clip:', error);
            return false;
        }
    }

    /**
     * 设置音量
     */
    setVolume(volume: number): void {
        if (this.primaryVideo) this.primaryVideo.volume = volume;
        if (this.secondaryVideo) this.secondaryVideo.volume = volume;
    }

    /**
     * 设置静音
     */
    setMuted(muted: boolean): void {
        if (this.primaryVideo) this.primaryVideo.muted = muted;
        if (this.secondaryVideo) this.secondaryVideo.muted = muted;
    }

    /**
     * 清理资源
     */
    dispose(): void {
        if (this.primaryVideo) {
            this.primaryVideo.pause();
            this.primaryVideo.src = '';
        }
        if (this.secondaryVideo) {
            this.secondaryVideo.pause();
            this.secondaryVideo.src = '';
        }
        this.preloadedClipId = null;
    }
}
