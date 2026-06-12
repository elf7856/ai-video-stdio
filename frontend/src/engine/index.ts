/**
 * NLE Engine - 非线性编辑引擎
 *
 * 这是一个借鉴 MLT Framework 设计理念的 Web-based NLE 引擎
 *
 * 主要模块：
 * - NLEEngine: 主引擎类，提供统一的 API
 * - TimelineManager: 时间轴管理，处理片段布局和时间转换
 * - PlaybackController: 播放控制，管理播放状态和进度
 * - BufferManager: 缓冲管理，实现双缓冲和预加载
 *
 * 使用示例：
 * ```typescript
 * const engine = createNLEEngine({
 *   primaryVideoElement: video1,
 *   secondaryVideoElement: video2,
 *   urlHelper: (path) => `http://localhost:8000${path}`
 * });
 *
 * // 加载时间轴
 * await engine.loadTimeline(clips);
 *
 * // 监听事件
 * engine.on('timeupdate', (event) => {
 *   console.log('Current time:', event.data.time);
 * });
 *
 * // 播放控制
 * await engine.play();
 * engine.pause();
 * await engine.seek(10);
 * ```
 */

export { NLEEngine, createNLEEngine } from './core/NLEEngine';
export { TimelineManager } from './core/TimelineManager';
export { PlaybackController } from './core/PlaybackController';
export { BufferManager } from './core/BufferManager';
export type {
    VideoClipData,
    PlaybackState,
    BufferState,
    PlaybackEvent,
    PlaybackEventType,
    EventCallback
} from './types';
