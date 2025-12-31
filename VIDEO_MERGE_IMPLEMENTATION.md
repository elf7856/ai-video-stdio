# 视频合并功能实现 ✅

## 🎯 问题描述

用户发现生成了多个视频片段（每个镜头一个），但没有合并成最终视频：
- ❌ 当前：生成多个单独的 `.mp4` 文件（每个镜头）
- ✅ 期望：合并所有镜头为一个完整的视频

## 📊 实现方案

### 完整流程

```
1. 生成脚本和分镜
   ↓
2. 为每个镜头生成视频片段
   ├─ shot_1.mp4 (8秒)
   ├─ shot_2.mp4 (8秒)
   ├─ shot_3.mp4 (8秒)
   └─ ...
   ↓
3. 合并所有片段 ⬅️ 新增！
   └─ final_video_xxx.mp4 (完整视频)
   ↓
4. 前端播放最终视频 ⬅️ 新增！
```

## 🔧 修改内容

### 1. 后端 - 添加视频合并步骤

**文件**: `app/services/video_generation/google_robust_client.py:176-177`

```python
# 修改视频保存路径
output_dir = "./outputs/videos"  # 从 "./outputs" 改为 "./outputs/videos"
```

**文件**: `app/api/video_generation.py:247-306`

添加阶段3（视频合并）：

```python
# ========== 阶段3: 合并视频 ==========
final_video_path = None
success_count = sum(1 for v in generated_videos if v["status"] == "success")

if success_count > 0:
    logger.info(f"[{task_id}] 阶段3: 开始合并 {success_count} 个视频片段...")
    task["status"] = "merging_videos"
    task["progress"] = 90.0

    try:
        # 获取所有成功生成的视频路径
        video_paths = [v["videoPath"] for v in generated_videos
                      if v["status"] == "success" and v.get("videoPath")]

        if len(video_paths) > 1:
            # 使用 VideoProcessor 合并多个视频
            from app.services.video.processor import VideoProcessor
            processor = VideoProcessor()

            # 生成最终视频文件名
            final_filename = f"final_video_{task_id.split('_')[-1]}_{int(datetime.now().timestamp())}.mp4"
            final_video_path = os.path.join("outputs/videos", final_filename)

            # 合并视频
            merge_success = processor.merge_videos(video_paths, final_video_path)

            if merge_success and os.path.exists(final_video_path):
                logger.info(f"[{task_id}] ✅ 视频合并成功: {final_video_path}")
                task["finalVideo"] = final_video_path
            else:
                logger.warning(f"[{task_id}] ⚠️ 视频合并失败，使用第一个片段")
                final_video_path = video_paths[0]

        elif len(video_paths) == 1:
            # 只有一个视频，直接使用
            final_video_path = video_paths[0]
            task["finalVideo"] = final_video_path
            logger.info(f"[{task_id}] 只有一个视频片段，无需合并")

    except Exception as merge_error:
        logger.error(f"[{task_id}] 视频合并失败: {merge_error}")
        # 降级：使用第一个成功的视频
```

### 2. 前端 - 添加视频播放器

**文件**: `frontend/src/api/types.ts:98-109`

```typescript
export interface VideoGenerationTask {
  // ... 其他字段
  finalVideo?: string;  // 新增：最终合并的视频路径
  status: 'pending' | 'processing' | 'generating' | 'merging_videos' | 'completed' | 'failed';
}
```

**文件**: `frontend/src/pages/Generate.tsx:498-549`

```tsx
{videoTask?.finalVideo ? (
    // 显示最终合并的视频 - 带播放器
    <Box sx={{ width: '100%', height: '100%', position: 'relative', bgcolor: 'black' }}>
        <video
            src={`http://localhost:8000/${videoTask.finalVideo}`}
            controls
            autoPlay
            style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain'
            }}
        />
        <Box sx={{ position: 'absolute', bottom: 16, right: 16 }}>
            <Button
                variant="contained"
                startIcon={<DownloadIcon />}
                onClick={() => {
                    window.open(`http://localhost:8000/${videoTask.finalVideo}`);
                }}
            >
                Download
            </Button>
        </Box>
    </Box>
) : videoTask?.generatedVideos?.some(v => v.status === 'success') ? (
    // 显示合并中状态
    <Box>
        <CircularProgress />
        <Typography>Merging Video Clips...</Typography>
    </Box>
) : (
    // 显示等待状态
    ...
)}
```

## 📁 目录结构

```
outputs/
└── videos/
    ├── google_robust_xxx_1.mp4    ← 镜头1
    ├── google_robust_xxx_2.mp4    ← 镜头2
    ├── google_robust_xxx_3.mp4    ← 镜头3
    └── final_video_xxx.mp4        ← 最终合并视频 ✨
```

## 🎬 用户体验

### 进度显示

```
阶段1: 生成脚本...          [10%]
阶段2: 生成视频片段...      [30% - 90%]
  ├─ 镜头 1/5 生成中...
  ├─ 镜头 2/5 生成中...
  ├─ 镜头 3/5 生成中...
  ├─ 镜头 4/5 生成中...
  └─ 镜头 5/5 生成中...
阶段3: 合并视频片段...      [90%]
  └─ 合并 5 个视频片段...
完成！                      [100%]
```

### 前端显示

**生成中**:
```
┌────────────────────────┐
│   🎬 生成镜头 3/5      │
│   ▓▓▓▓▓▓▓░░░  70%      │
└────────────────────────┘
```

**合并中**:
```
┌────────────────────────┐
│   🔄 Merging Clips...  │
│   Combining 5 clips    │
└────────────────────────┘
```

**完成**:
```
┌────────────────────────┐
│   ▶️ [视频播放器]      │
│   可以直接预览播放      │
│   [Download] 按钮       │
└────────────────────────┘
```

## 🔍 技术细节

### 视频合并使用的工具

使用 `VideoProcessor.merge_videos()` 方法，内部使用 `ffmpeg`：

```python
# app/services/video/processor.py
def merge_videos(self, video_paths: List[str], output_path: str) -> bool:
    """合并多个视频文件"""
    # 使用 ffmpeg concat 协议
    # ffmpeg -i "concat:input1.mp4|input2.mp4|..." -c copy output.mp4
```

### 降级策略

1. **多个视频**: 尝试合并，失败则使用第一个片段
2. **单个视频**: 直接使用，无需合并
3. **合并失败**: 降级到使用第一个成功的片段

### 文件命名规范

- **单个镜头**: `google_robust_{task_id}_{timestamp}.mp4`
- **最终视频**: `final_video_{task_id}_{timestamp}.mp4`

## ✅ 测试验证

### 后端测试
```bash
# 查看视频目录
ls -lh outputs/videos/

# 应该看到:
# - 多个 google_robust_xxx.mp4 (单个镜头)
# - final_video_xxx.mp4 (最终合并视频)
```

### 前端测试
1. 访问: http://localhost:5174
2. 生成视频
3. 等待完成
4. 看到视频播放器，可以直接预览
5. 点击 Download 按钮下载完整视频

## 📊 API 响应示例

```json
{
  "taskId": "task_20251215_123456",
  "status": "completed",
  "progress": 100.0,
  "script": "...",
  "shots": [...],
  "generatedVideos": [
    {
      "sequence": 1,
      "videoPath": "outputs/videos/google_robust_xxx_1.mp4",
      "status": "success"
    },
    {
      "sequence": 2,
      "videoPath": "outputs/videos/google_robust_xxx_2.mp4",
      "status": "success"
    }
  ],
  "finalVideo": "outputs/videos/final_video_123456_1734278945.mp4"  ← 新增
}
```

## 🎉 总结

### 解决的问题
- ✅ 添加视频合并功能
- ✅ 前端显示最终视频
- ✅ 支持直接在线预览播放
- ✅ 提供下载按钮
- ✅ 完整的进度显示

### 用户价值
- 🎬 获得完整的合成视频，不是碎片
- 📺 可以直接在线预览播放
- 💾 一键下载完整视频
- 🎯 清晰的进度反馈

---

**实施日期**: 2025-12-15
**状态**: ✅ 已完成
