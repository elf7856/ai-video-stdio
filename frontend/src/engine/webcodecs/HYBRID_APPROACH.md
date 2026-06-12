/**
 * 实用的 WebCodecs 混合引擎
 *
 * 方案说明：
 * 由于完整的 WebCodecs + MP4 解复用实现非常复杂（需要处理 MP4 容器格式、编码配置等），
 * 我们采用一个更实用的混合方案：
 *
 * **Video Element + Canvas + RequestVideoFrameCallback**
 *
 * 核心思路：
 * 1. 使用 video 元素进行解码（利用浏览器原生能力）
 * 2. 使用 requestVideoFrameCallback 获取帧
 * 3. 将帧绘制到 Canvas（实现无缝切换）
 * 4. 双 video 预加载下一个片段
 *
 * 优势：
 * - ✅ 真正的无缝切换（Canvas 上渲染，无闪烁）
 * - ✅ 利用浏览器原生解码（无需手动解复用）
 * - ✅ 实现相对简单
 * - ✅ 兼容性好（Chrome 83+）
 * - ✅ 可以添加转场效果
 *
 * 与之前方案的区别：
 * - 之前：直接切换 video 元素的 z-index（有闪烁）
 * - 现在：在 Canvas 上绘制 video 帧（完全无缝）
 *
 * 架构：
 * VideoSource (video 元素) → FrameExtractor (rVFC) → Canvas Renderer → UI
 *
 * 注意：如果将来需要更高级的功能（如实时特效、复杂转场），
 * 可以升级到完整的 WebCodecs 方案。
 */
