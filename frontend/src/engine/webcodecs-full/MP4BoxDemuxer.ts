/**
 * MP4BoxDemuxer - 基于 mp4box.js 的 MP4 解复用器
 *
 * 职责：
 * - 解析 MP4 文件
 * - 提取视频轨道配置
 * - 提取音频轨道配置
 * - 按需提供 EncodedVideoChunk 和 EncodedAudioChunk
 */

// mp4box.js 使用命名导入
import * as MP4Box from 'mp4box';

export interface VideoTrackInfo {
    id: number;
    codec: string;
    codedWidth: number;
    codedHeight: number;
    duration: number;
    timescale: number;
    description?: Uint8Array;
}

export interface AudioTrackInfo {
    id: number;
    codec: string;
    sampleRate: number;
    numberOfChannels: number;
    description?: Uint8Array;
}

export interface MP4Sample {
    data: Uint8Array;
    timestamp: number; // 微秒
    duration: number;  // 微秒
    isKeyFrame: boolean;
}

export class MP4BoxDemuxer {
    private mp4boxFile: any;
    private videoTrack: VideoTrackInfo | null = null;
    private audioTrack: AudioTrackInfo | null = null;
    private onVideoSample: ((sample: MP4Sample) => void) | null = null;
    private onAudioSample: ((sample: MP4Sample) => void) | null = null;

    constructor() {
        // 不在构造函数中创建，而是在 load 时创建
    }

    /**
     * 设置视频样本回调
     */
    setVideoSampleCallback(callback: (sample: MP4Sample) => void): void {
        this.onVideoSample = callback;
    }

    /**
     * 设置音频样本回调
     */
    setAudioSampleCallback(callback: (sample: MP4Sample) => void): void {
        this.onAudioSample = callback;
    }

    /**
     * 加载 MP4 文件
     */
    async load(url: string): Promise<void> {
        return new Promise(async (resolve, reject) => {
            // 重新创建 mp4boxFile 实例，避免重用问题
            this.mp4boxFile = MP4Box.createFile();

            console.log('[MP4BoxDemuxer] Created MP4Box file instance');

            // 设置样本回调（必须在 onReady 之前设置）
            this.mp4boxFile.onSamples = (id: number, _user: any, samples: any[]) => {
                console.log('[MP4BoxDemuxer] onSamples called! Track:', id, 'Samples:', samples.length);

                for (const sample of samples) {
                    const mp4Sample: MP4Sample = {
                        data: sample.data,
                        timestamp: (sample.cts * 1000000) / sample.timescale,
                        duration: (sample.duration * 1000000) / sample.timescale,
                        isKeyFrame: sample.is_rap
                    };

                    if (id === this.videoTrack?.id && this.onVideoSample) {
                        this.onVideoSample(mp4Sample);
                    } else if (id === this.audioTrack?.id && this.onAudioSample) {
                        this.onAudioSample(mp4Sample);
                    }
                }
            };

            // 设置回调
            this.mp4boxFile.onReady = (info: any) => {
                console.log('[MP4BoxDemuxer] File ready:', info);

                // 提取视频轨道
                const videoTrack = info.videoTracks[0];
                if (videoTrack) {
                    this.videoTrack = {
                        id: videoTrack.id,
                        codec: this.getCodecString(videoTrack.codec),
                        codedWidth: videoTrack.video.width,
                        codedHeight: videoTrack.video.height,
                        duration: videoTrack.duration / videoTrack.timescale,
                        timescale: videoTrack.timescale
                    };
                    console.log('[MP4BoxDemuxer] Video track:', this.videoTrack);
                }

                // 提取音频轨道
                const audioTrack = info.audioTracks[0];
                if (audioTrack) {
                    this.audioTrack = {
                        id: audioTrack.id,
                        codec: this.getCodecString(audioTrack.codec),
                        sampleRate: audioTrack.audio.sample_rate,
                        numberOfChannels: audioTrack.audio.channel_count
                    };
                    console.log('[MP4BoxDemuxer] Audio track:', this.audioTrack);
                }

                resolve();
            };

            this.mp4boxFile.onError = (e: any) => {
                console.error('[MP4BoxDemuxer] Error:', e);
                reject(new Error('Failed to parse MP4 file'));
            };

            // 获取文件
            try {
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`Failed to fetch: ${response.statusText}`);
                }

                console.log('[MP4BoxDemuxer] Fetching file from:', url);

                const reader = response.body!.getReader();
                let offset = 0;

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) {
                        console.log('[MP4BoxDemuxer] File fetch complete, total bytes:', offset);
                        break;
                    }

                    // 转换为 ArrayBuffer
                    const buffer = value.buffer as any;
                    buffer.fileStart = offset;

                    // 追加到 mp4box
                    this.mp4boxFile.appendBuffer(buffer);

                    offset += value.length;
                }

                // 完成
                this.mp4boxFile.flush();
                console.log('[MP4BoxDemuxer] File flushed');

                // 在文件完全加载后，如果设置了回调，自动开始提取
                if (this.videoTrack && this.onVideoSample) {
                    console.log('[MP4BoxDemuxer] Starting video extraction after flush');
                    console.log('[MP4BoxDemuxer] Video track ID:', this.videoTrack.id);

                    this.mp4boxFile.setExtractionOptions(this.videoTrack.id, this, {
                        nbSamples: 100
                    });

                    this.mp4boxFile.start();
                    console.log('[MP4BoxDemuxer] Extraction started');
                }
            } catch (error) {
                console.error('[MP4BoxDemuxer] Load error:', error);
                reject(error);
            }
        });
    }

    /**
     * 获取 codec 字符串
     */
    private getCodecString(codec: string): string {
        // mp4box.js 返回的 codec 格式可能需要转换
        // 例如：'avc1' -> 'avc1.42E01E'
        if (codec.startsWith('avc1')) {
            return 'avc1.42E01E'; // H.264 Baseline
        }
        if (codec.startsWith('hev1') || codec.startsWith('hvc1')) {
            return 'hev1.1.6.L93.B0'; // H.265
        }
        return codec;
    }

    /**
     * 开始提取视频样本
     */
    startVideoExtraction(onSample: (sample: MP4Sample) => void): void {
        this.onVideoSample = onSample;
        if (this.videoTrack) {
            console.log('[MP4BoxDemuxer] Starting video extraction for track', this.videoTrack.id);
            this.mp4boxFile.setExtractionOptions(this.videoTrack.id, null, {
                nbSamples: 100 // 每次提取 100 个样本
            });
            this.mp4boxFile.start();
            console.log('[MP4BoxDemuxer] Extraction started');
        } else {
            console.error('[MP4BoxDemuxer] No video track available');
        }
    }

    /**
     * 开始提取音频样本
     */
    startAudioExtraction(onSample: (sample: MP4Sample) => void): void {
        this.onAudioSample = onSample;
        if (this.audioTrack) {
            this.mp4boxFile.setExtractionOptions(this.audioTrack.id, null, {
                nbSamples: 100
            });
        }
    }

    /**
     * 停止提取
     */
    stop(): void {
        this.mp4boxFile.stop();
    }

    /**
     * Seek 到指定时间
     */
    seek(time: number): void {
        if (this.videoTrack) {
            const seekTime = time * this.videoTrack.timescale;
            this.mp4boxFile.seek(seekTime, true);
        }
    }

    /**
     * 获取视频轨道信息
     */
    getVideoTrack(): VideoTrackInfo | null {
        return this.videoTrack;
    }

    /**
     * 获取音频轨道信息
     */
    getAudioTrack(): AudioTrackInfo | null {
        return this.audioTrack;
    }

    /**
     * 清理资源
     */
    dispose(): void {
        if (this.mp4boxFile) {
            this.stop();
        }
        this.onVideoSample = null;
        this.onAudioSample = null;
        this.videoTrack = null;
        this.audioTrack = null;
        // 不要设置为 null，因为可能会被重用
        // this.mp4boxFile = null;
    }
}
