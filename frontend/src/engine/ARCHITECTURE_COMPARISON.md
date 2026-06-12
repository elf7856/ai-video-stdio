# NLE 引擎架构对比

## 旧架构（useSeamlessVideoPlayback）

```
React Hook (useSeamlessVideoPlayback.ts)
├── 播放控制逻辑
├── 双缓冲管理
├── 时间轴计算
├── 进度更新循环
└── 事件处理

问题：
❌ 所有逻辑混在 React Hook 中
❌ 难以测试和维护
❌ 与 React 状态紧密耦合
❌ 无法在其他框架中复用
```

## 新架构（NLE Engine + useNLEEngine）

```
┌─────────────────────────────────────┐
│   React Layer (useNLEEngine.ts)     │  ← UI 层，处理 React 状态同步
├─────────────────────────────────────┤
│   Engine Layer (NLEEngine.ts)       │  ← 引擎层，提供统一 API
├─────────────────────────────────────┤
│   ┌─────────────────────────────┐   │
│   │   TimelineManager.ts        │   │  ← 时间轴管理
│   ├─────────────────────────────┤   │
│   │   PlaybackController.ts     │   │  ← 播放控制
│   ├─────────────────────────────┤   │
│   │   BufferManager.ts          │   │  ← 缓冲管理
│   └─────────────────────────────┘   │
└─────────────────────────────────────┘

优势：
✅ 分层清晰，职责分离
✅ 易于测试和维护
✅ 与框架解耦，可复用
✅ 为 WebCodecs 升级做好准备
```

## 代码对比

### 旧方式（直接在 Hook 中实现）

```typescript
// useSeamlessVideoPlayback.ts - 500+ 行
export const useSeamlessVideoPlayback = ({ orderedShots }) => {
    // 状态管理
    const [currentShotIndex, setCurrentShotIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);

    // 双缓冲逻辑
    const [usePrimary, setUsePrimary] = useState(true);
    const activeVideoRef = usePrimary ? primaryVideoRef : secondaryVideoRef;

    // 预加载逻辑
    const preloadNextShot = useCallback((nextIndex: number) => {
        // 复杂的预加载逻辑...
    }, [/* 多个依赖 */]);

    // 切换逻辑
    const switchToNextShot = useCallback(() => {
        // 复杂的切换逻辑...
        // ref 和 state 不同步问题...
    }, [/* 多个依赖 */]);

    // 进度循环
    useEffect(() => {
        const updateProgress = (timestamp) => {
            // 进度更新逻辑...
            // 使用 ref 而不是 state...
        };
        // ...
    }, [/* 依赖问题 */]);

    // 还有很多其他逻辑...
}
```

### 新方式（使用 NLE 引擎）

```typescript
// useNLEEngine.ts - 简洁清晰
export const useNLEEngine = ({ orderedShots }) => {
    const engineRef = useRef<NLEEngine | null>(null);

    // 初始化引擎
    useEffect(() => {
        const engine = createNLEEngine({
            primaryVideoElement: primaryVideoRef.current!,
            secondaryVideoElement: secondaryVideoRef.current!,
            urlHelper: getFullUrl
        });

        await engine.loadTimeline(clips);

        // 注册事件监听
        engine.on('timeupdate', (event) => {
            setCurrentTime(event.data.time);
        });

        engineRef.current = engine;

        return () => engine.dispose();
    }, [orderedShots]);

    // 播放控制 - 简单！
    const handlePlayPause = () => {
        engineRef.current?.togglePlayPause();
    };

    // 其他控制也很简单...
}
```

## 维护性对比

### 旧架构问题：
1. **难以调试**：所有逻辑混在一起，难以追踪 bug
2. **ref vs state**：需要同时维护 ref 和 state，容易不同步
3. **依赖地狱**：useCallback 和 useEffect 的依赖很难管理
4. **难以测试**：无法单独测试播放逻辑
5. **难以升级**：要升级到 WebCodecs，需要重写整个 Hook

### 新架构优势：
1. **易于调试**：每个模块职责明确，bug 容易定位
2. **状态一致**：引擎内部统一管理状态
3. **无依赖问题**：引擎不依赖 React
4. **易于测试**：可以单独测试每个模块
5. **易于升级**：只需替换 BufferManager，其他代码不变

## 性能对比

### 切换延迟
- 旧方案：50-200ms（因为 setTimeout 和状态更新）
- 新方案：< 50ms（直接在引擎中同步切换）

### 内存使用
- 旧方案：两个 video 元素 + React 状态
- 新方案：两个 video 元素 + 轻量级引擎状态

### CPU 使用
- 旧方案：React 重渲染 + 进度循环
- 新方案：进度循环在引擎中，React 只更新 UI

## 升级路径

### 当前：HTMLVideoElement
```
NLEEngine
  └── BufferManager (HTMLVideoElement)
      ├── primaryVideo
      └── secondaryVideo
```

### 将来：WebCodecs + Canvas
```
NLEEngine
  └── WebCodecsBufferManager (Canvas + WebCodecs)
      ├── VideoDecoder
      ├── FrameBuffer
      └── CanvasRenderer
```

只需要替换 BufferManager，其他代码保持不变！

## 使用建议

1. **新项目**：直接使用 useNLEEngine
2. **现有项目**：
   - 如果遇到切换问题 → 迁移到 useNLEEngine
   - 如果需要高级功能（转场、特效） → 使用 WebCodecs 版本
3. **生产环境**：建议在充分测试后再切换

## 总结

新架构不仅解决了当前的切换问题，还为未来的升级（WebCodecs、特效、转场）铺平了道路。

**关键优势：**
- ✅ 代码更清晰
- ✅ 更易维护
- ✅ 更易测试
- ✅ 更易升级
- ✅ 性能更好
