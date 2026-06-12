"""
视频质量检查服务

提供视频质量的全面检查，包括：
- 视觉一致性检查
- 内容匹配度评估
- 技术质量检查
- 综合质量评分
"""

import os
import json
import logging
import tempfile
import base64
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

try:
    import cv2
    import numpy as np
    CV_QUALITY_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    CV_QUALITY_AVAILABLE = False

from .models import (
    QualityCheckConfig,
    QualityReport,
    ShotQualityResult,
    VisualConsistencyResult,
    ContentMatchResult,
    TechnicalQualityResult,
    FrameAnalysis,
    QualityLevel,
    RegenerationRequest
)
from app.services.llm.service import LLMService, ProviderType

logger = logging.getLogger(__name__)


class VideoQualityChecker:
    """
    视频质量检查器

    提供完整的视频质量检查功能，包括：
    1. 关键帧提取和分析
    2. 视觉一致性检查（色彩、风格、光照）
    3. 内容匹配度检查（prompt与生成内容的匹配）
    4. 技术质量检查（分辨率、清晰度、编码）
    5. 综合质量评分和建议
    """

    def __init__(
        self,
        config: Optional[QualityCheckConfig] = None,
        llm_service: Optional[LLMService] = None
    ):
        """
        初始化质量检查器

        Args:
            config: 质量检查配置
            llm_service: LLM服务实例
        """
        self.config = config or QualityCheckConfig()
        self.llm = llm_service or LLMService(provider=ProviderType.GOOGLE)
        self._temp_dir = tempfile.mkdtemp(prefix="quality_check_")

        logger.info(f"质量检查器初始化完成，临时目录: {self._temp_dir}")

    def check_video(
        self,
        video_path: str,
        prompt: str,
        shot_index: int = 0,
        shot_id: str = ""
    ) -> ShotQualityResult:
        """
        检查单个视频的质量

        Args:
            video_path: 视频文件路径
            prompt: 生成该视频的提示词
            shot_index: 镜头索引
            shot_id: 镜头ID

        Returns:
            ShotQualityResult: 质量检查结果
        """
        logger.info(f"开始检查视频质量: {video_path}")

        result = ShotQualityResult(
            shot_index=shot_index,
            shot_id=shot_id or f"shot_{shot_index}",
            video_path=video_path,
            prompt=prompt
        )

        if not os.path.exists(video_path):
            logger.error(f"视频文件不存在: {video_path}")
            result.overall_score = 0
            result.overall_level = QualityLevel.UNACCEPTABLE
            result.needs_regeneration = True
            result.regeneration_reason = "视频文件不存在"
            return result

        try:
            # 1. 技术质量检查
            if self.config.check_technical_quality:
                result.technical_quality = self._check_technical_quality(video_path)

            # 2. 提取关键帧
            keyframes = self._extract_keyframes(video_path)

            # 3. 视觉一致性检查
            if self.config.check_visual_consistency and keyframes:
                result.visual_consistency = self._check_visual_consistency(keyframes)

            # 4. 内容匹配度检查
            if self.config.check_content_match and keyframes:
                result.content_match = self._check_content_match(keyframes, prompt)

            # 5. 计算综合分数
            self._calculate_overall_score(result)

            # 6. 判断是否需要重新生成
            self._evaluate_regeneration_need(result)

        except Exception as e:
            logger.error(f"质量检查失败: {e}", exc_info=True)
            result.overall_score = 0
            result.overall_level = QualityLevel.UNACCEPTABLE
            result.needs_regeneration = True
            result.regeneration_reason = f"检查过程出错: {str(e)}"

        return result

    def check_multiple_videos(
        self,
        videos: List[Dict[str, Any]],
        project_id: str = ""
    ) -> QualityReport:
        """
        检查多个视频的质量（完整项目）

        Args:
            videos: 视频列表，每个元素包含 {path, prompt, shot_index, shot_id}
            project_id: 项目ID

        Returns:
            QualityReport: 完整质量报告
        """
        logger.info(f"开始批量质量检查，共 {len(videos)} 个视频")

        report = QualityReport(
            project_id=project_id,
            config=self.config
        )

        for i, video in enumerate(videos):
            video_path = video.get("path", "")
            prompt = video.get("prompt", "")
            shot_index = video.get("shot_index", i)
            shot_id = video.get("shot_id", f"shot_{i}")

            shot_result = self.check_video(
                video_path=video_path,
                prompt=prompt,
                shot_index=shot_index,
                shot_id=shot_id
            )
            report.shots.append(shot_result)

        # 计算整体分数
        report.calculate_overall_scores()

        # 生成总结和建议
        self._generate_report_summary(report)

        logger.info(f"批量质量检查完成，整体分数: {report.overall_score:.2f}")

        return report

    def _extract_keyframes(self, video_path: str) -> List[str]:
        """
        提取视频关键帧

        Args:
            video_path: 视频路径

        Returns:
            关键帧图像路径列表
        """
        keyframes = []

        if not CV_QUALITY_AVAILABLE:
            logger.info("OpenCV/Numpy 未安装，跳过关键帧提取")
            return keyframes

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"无法打开视频: {video_path}")
                return keyframes

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            if total_frames == 0:
                logger.warning("视频帧数为0")
                cap.release()
                return keyframes

            # 均匀提取关键帧
            frame_indices = np.linspace(
                0, total_frames - 1,
                min(self.config.keyframe_count, total_frames),
                dtype=int
            )

            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    frame_path = os.path.join(
                        self._temp_dir,
                        f"keyframe_{idx:06d}.jpg"
                    )
                    cv2.imwrite(frame_path, frame)
                    keyframes.append(frame_path)

            cap.release()
            logger.info(f"提取了 {len(keyframes)} 个关键帧")

        except Exception as e:
            logger.error(f"提取关键帧失败: {e}")

        return keyframes

    def _check_technical_quality(self, video_path: str) -> TechnicalQualityResult:
        """检查技术质量"""
        result = TechnicalQualityResult()

        try:
            metadata = self._probe_video_metadata(video_path)
            width = metadata["width"]
            height = metadata["height"]
            result.resolution = f"{width}x{height}"
            result.fps = metadata["fps"]
            result.duration = metadata["duration"]
            result.file_size = os.path.getsize(video_path)

            # 计算比特率 (kbps)
            if result.duration > 0:
                result.bitrate = (result.file_size * 8) / (result.duration * 1000)

            # 评估各项指标

            # 分辨率评分
            if width >= 1920 or height >= 1080:
                resolution_score = 1.0
            elif width >= 1280 or height >= 720:
                resolution_score = 0.8
            elif width >= 854 or height >= 480:
                resolution_score = 0.6
            else:
                resolution_score = 0.4

            # 帧率评分
            if result.fps >= 30:
                fps_score = 1.0
            elif result.fps >= 24:
                fps_score = 0.8
            elif result.fps >= 15:
                fps_score = 0.6
            else:
                fps_score = 0.4

            # 文件大小/比特率评分 (太小可能质量差)
            if result.bitrate >= 5000:
                bitrate_score = 1.0
            elif result.bitrate >= 2000:
                bitrate_score = 0.8
            elif result.bitrate >= 1000:
                bitrate_score = 0.6
            else:
                bitrate_score = 0.5

            # 综合技术质量分数
            result.clarity_score = resolution_score
            result.encoding_quality = bitrate_score
            result.stability_score = fps_score

            result.score = (
                resolution_score * 0.4 +
                fps_score * 0.3 +
                bitrate_score * 0.3
            )

            # 识别问题
            if width < 720:
                result.issues.append(f"分辨率较低: {result.resolution}")
            if result.fps < 24:
                result.issues.append(f"帧率较低: {result.fps}fps")
            if result.bitrate < 1000:
                result.issues.append(f"比特率较低: {result.bitrate:.0f}kbps")

            result.level = QualityReport._score_to_level(result.score)

        except Exception as e:
            logger.error(f"技术质量检查失败: {e}")
            result.score = 0
            result.issues.append(f"检查失败: {str(e)}")
            result.level = QualityLevel.UNACCEPTABLE

        return result

    def _probe_video_metadata(self, video_path: str) -> Dict[str, float]:
        """使用 ffprobe 获取视频基础元数据，避免依赖 moviepy。"""
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,avg_frame_rate,duration",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            video_path,
        ]
        completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(completed.stdout)
        stream = (data.get("streams") or [{}])[0]
        fmt = data.get("format") or {}

        fps = self._parse_frame_rate(stream.get("avg_frame_rate", "0/1"))
        duration = float(stream.get("duration") or fmt.get("duration") or 0)

        return {
            "width": int(stream.get("width") or 0),
            "height": int(stream.get("height") or 0),
            "fps": fps,
            "duration": duration,
        }

    def _parse_frame_rate(self, value: str) -> float:
        if not value:
            return 0
        if "/" not in value:
            return float(value)
        numerator, denominator = value.split("/", 1)
        denominator_value = float(denominator)
        if denominator_value == 0:
            return 0
        return float(numerator) / denominator_value

    def _check_visual_consistency(
        self,
        keyframes: List[str]
    ) -> VisualConsistencyResult:
        """检查视觉一致性"""
        result = VisualConsistencyResult()

        if not CV_QUALITY_AVAILABLE:
            result.score = 0.5
            result.level = QualityLevel.ACCEPTABLE
            result.suggestions.append("OpenCV/Numpy 未安装，已跳过视觉一致性检查")
            return result

        if len(keyframes) < 2:
            result.score = 1.0
            result.level = QualityLevel.EXCELLENT
            return result

        try:
            # 分析每个关键帧
            frame_analyses = []
            for i, frame_path in enumerate(keyframes):
                analysis = self._analyze_frame(frame_path, i)
                frame_analyses.append(analysis)
            result.frame_analyses = frame_analyses

            # 计算色彩一致性
            result.color_consistency = self._calculate_color_consistency(frame_analyses)

            # 计算亮度一致性
            brightness_values = [f.brightness for f in frame_analyses]
            result.lighting_consistency = 1.0 - np.std(brightness_values) * 2
            result.lighting_consistency = max(0, min(1, result.lighting_consistency))

            # 使用LLM分析风格一致性
            if self.config.use_llm_analysis and len(keyframes) >= 2:
                style_result = self._llm_check_style_consistency(keyframes)
                result.style_consistency = style_result.get("score", 0.5)
                result.inconsistencies.extend(style_result.get("issues", []))
                result.suggestions.extend(style_result.get("suggestions", []))
            else:
                result.style_consistency = (result.color_consistency + result.lighting_consistency) / 2

            # 综合分数
            result.score = (
                result.color_consistency * 0.35 +
                result.style_consistency * 0.4 +
                result.lighting_consistency * 0.25
            )

            result.level = QualityReport._score_to_level(result.score)

        except Exception as e:
            logger.error(f"视觉一致性检查失败: {e}")
            result.score = 0.5
            result.level = QualityLevel.ACCEPTABLE

        return result

    def _analyze_frame(self, frame_path: str, index: int) -> FrameAnalysis:
        """分析单个帧"""
        analysis = FrameAnalysis(
            frame_index=index,
            timestamp=0,
            frame_path=frame_path
        )

        try:
            if not CV_QUALITY_AVAILABLE:
                return analysis

            img = cv2.imread(frame_path)
            if img is None:
                return analysis

            # 计算亮度
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            analysis.brightness = np.mean(gray) / 255.0

            # 计算对比度
            analysis.contrast = np.std(gray) / 128.0
            analysis.contrast = min(1.0, analysis.contrast)

            # 计算清晰度 (Laplacian variance)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            analysis.sharpness = min(1.0, np.var(laplacian) / 500.0)

            # 提取主要颜色
            analysis.dominant_colors = self._extract_dominant_colors(img)

            # 检测问题
            if analysis.sharpness < 0.3:
                analysis.issues.append("图像模糊")
            if analysis.brightness < 0.2:
                analysis.issues.append("图像过暗")
            elif analysis.brightness > 0.8:
                analysis.issues.append("图像过亮")

        except Exception as e:
            logger.error(f"帧分析失败: {e}")

        return analysis

    def _extract_dominant_colors(self, img: Any, n_colors: int = 3) -> List[str]:
        """提取主要颜色"""
        try:
            # 缩小图像以加速处理
            small = cv2.resize(img, (50, 50))
            pixels = small.reshape(-1, 3)

            # 使用K-means聚类
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
            kmeans.fit(pixels)

            colors = []
            for center in kmeans.cluster_centers_:
                b, g, r = int(center[0]), int(center[1]), int(center[2])
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                colors.append(hex_color)

            return colors

        except ImportError:
            # 如果没有sklearn，返回简单的平均颜色
            mean_color = np.mean(img.reshape(-1, 3), axis=0)
            b, g, r = int(mean_color[0]), int(mean_color[1]), int(mean_color[2])
            return [f"#{r:02x}{g:02x}{b:02x}"]

        except Exception as e:
            logger.warning(f"提取主要颜色失败: {e}")
            return []

    def _calculate_color_consistency(self, frame_analyses: List[FrameAnalysis]) -> float:
        """计算色彩一致性"""
        if len(frame_analyses) < 2:
            return 1.0

        try:
            # 收集所有主要颜色
            all_colors = []
            for analysis in frame_analyses:
                for color_hex in analysis.dominant_colors:
                    # 转换hex到RGB
                    r = int(color_hex[1:3], 16)
                    g = int(color_hex[3:5], 16)
                    b = int(color_hex[5:7], 16)
                    all_colors.append([r, g, b])

            if len(all_colors) < 2:
                return 1.0

            # 计算颜色的标准差
            colors_array = np.array(all_colors)
            color_std = np.mean(np.std(colors_array, axis=0))

            # 归一化到0-1（标准差越小，一致性越高）
            consistency = 1.0 - (color_std / 128.0)
            return max(0, min(1, consistency))

        except Exception as e:
            logger.warning(f"计算色彩一致性失败: {e}")
            return 0.5

    def _llm_check_style_consistency(self, keyframes: List[str]) -> Dict[str, Any]:
        """使用LLM检查风格一致性"""
        try:
            # 选择几个关键帧进行分析
            frames_to_analyze = keyframes[:min(3, len(keyframes))]

            # 编码图像为base64
            encoded_frames = []
            for frame_path in frames_to_analyze:
                with open(frame_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                    encoded_frames.append(encoded)

            # 构建多模态消息
            prompt = """分析以下视频帧的视觉一致性。评估：
1. 色彩风格是否统一
2. 画面风格是否一致（如卡通、写实、复古等）
3. 光照条件是否协调
4. 是否存在明显的风格跳跃

请返回JSON格式：
{
    "score": 0.0-1.0的一致性分数,
    "style_description": "整体风格描述",
    "issues": ["发现的不一致问题列表"],
    "suggestions": ["改进建议列表"]
}

只返回JSON，不要其他文字。"""

            # 构建带图像的消息
            content = [{"type": "text", "text": prompt}]
            for i, encoded in enumerate(encoded_frames):
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": encoded
                    }
                })

            messages = [{"role": "user", "content": content}]

            # 调用LLM
            response = self.llm.call(messages, max_tokens=1000)

            if response.get("success"):
                content = response.get("content", "{}")
                # 尝试解析JSON
                try:
                    # 清理可能的markdown代码块
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]

                    result = json.loads(content.strip())
                    return {
                        "score": float(result.get("score", 0.5)),
                        "issues": result.get("issues", []),
                        "suggestions": result.get("suggestions", [])
                    }
                except json.JSONDecodeError:
                    logger.warning("LLM返回的JSON解析失败")

        except Exception as e:
            logger.error(f"LLM风格一致性检查失败: {e}")

        return {"score": 0.5, "issues": [], "suggestions": []}

    def _check_content_match(
        self,
        keyframes: List[str],
        prompt: str
    ) -> ContentMatchResult:
        """检查内容匹配度"""
        result = ContentMatchResult(original_prompt=prompt)

        if not prompt or not keyframes:
            result.score = 0.5
            result.level = QualityLevel.ACCEPTABLE
            return result

        try:
            if self.config.use_llm_analysis:
                llm_result = self._llm_check_content_match(keyframes, prompt)
                result.semantic_match = llm_result.get("semantic_match", 0.5)
                result.visual_match = llm_result.get("visual_match", 0.5)
                result.style_match = llm_result.get("style_match", 0.5)
                result.matched_elements = llm_result.get("matched_elements", [])
                result.missing_elements = llm_result.get("missing_elements", [])
                result.unexpected_elements = llm_result.get("unexpected_elements", [])
                result.suggestions = llm_result.get("suggestions", [])

                # 计算综合分数
                result.score = (
                    result.semantic_match * 0.4 +
                    result.visual_match * 0.4 +
                    result.style_match * 0.2
                )
            else:
                result.score = 0.5

            result.level = QualityReport._score_to_level(result.score)

        except Exception as e:
            logger.error(f"内容匹配检查失败: {e}")
            result.score = 0.5
            result.level = QualityLevel.ACCEPTABLE

        return result

    def _llm_check_content_match(
        self,
        keyframes: List[str],
        prompt: str
    ) -> Dict[str, Any]:
        """使用LLM检查内容匹配度"""
        try:
            # 选择关键帧
            frames_to_analyze = keyframes[:min(3, len(keyframes))]

            # 编码图像
            encoded_frames = []
            for frame_path in frames_to_analyze:
                with open(frame_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                    encoded_frames.append(encoded)

            analysis_prompt = f"""分析视频帧与原始提示词的匹配程度。

原始提示词：
"{prompt}"

请评估：
1. 语义匹配度：视频内容是否符合提示词描述的含义
2. 视觉匹配度：画面元素是否与提示词要求一致
3. 风格匹配度：视觉风格是否符合提示词暗示的风格

返回JSON格式：
{{
    "semantic_match": 0.0-1.0的语义匹配分数,
    "visual_match": 0.0-1.0的视觉匹配分数,
    "style_match": 0.0-1.0的风格匹配分数,
    "matched_elements": ["提示词中正确呈现的元素"],
    "missing_elements": ["提示词要求但缺失的元素"],
    "unexpected_elements": ["出现但提示词未要求的元素"],
    "suggestions": ["如何改进prompt以获得更好结果"]
}}

只返回JSON，不要其他文字。"""

            content = [{"type": "text", "text": analysis_prompt}]
            for encoded in encoded_frames:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": encoded
                    }
                })

            messages = [{"role": "user", "content": content}]
            response = self.llm.call(messages, max_tokens=1500)

            if response.get("success"):
                content = response.get("content", "{}")
                try:
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]

                    return json.loads(content.strip())
                except json.JSONDecodeError:
                    logger.warning("内容匹配JSON解析失败")

        except Exception as e:
            logger.error(f"LLM内容匹配检查失败: {e}")

        return {
            "semantic_match": 0.5,
            "visual_match": 0.5,
            "style_match": 0.5,
            "matched_elements": [],
            "missing_elements": [],
            "unexpected_elements": [],
            "suggestions": []
        }

    def _calculate_overall_score(self, result: ShotQualityResult) -> None:
        """计算综合分数"""
        weights = self.config.weights

        result.overall_score = (
            result.visual_consistency.score * weights.get("visual_consistency", 0.3) +
            result.content_match.score * weights.get("content_match", 0.4) +
            result.technical_quality.score * weights.get("technical_quality", 0.3)
        )

        result.overall_level = QualityReport._score_to_level(result.overall_score)

    def _evaluate_regeneration_need(self, result: ShotQualityResult) -> None:
        """评估是否需要重新生成"""
        threshold = self.config.regeneration_threshold

        if result.overall_score < threshold:
            result.needs_regeneration = True

            # 确定主要问题
            issues = []
            if result.visual_consistency.score < threshold:
                issues.append("视觉一致性差")
            if result.content_match.score < threshold:
                issues.append("内容不匹配")
            if result.technical_quality.score < threshold:
                issues.append("技术质量低")

            result.regeneration_reason = "，".join(issues) if issues else "综合质量不达标"

            # 收集改进建议
            suggestions = []
            suggestions.extend(result.visual_consistency.suggestions)
            suggestions.extend(result.content_match.suggestions)

            # 去重
            result.regeneration_suggestions = list(set(suggestions))

    def _generate_report_summary(self, report: QualityReport) -> None:
        """生成报告总结"""
        total_shots = len(report.shots)
        need_regen = len(report.shots_to_regenerate)

        # 生成总结
        if report.overall_level == QualityLevel.EXCELLENT:
            report.summary = f"质量优秀！{total_shots}个镜头整体表现出色。"
        elif report.overall_level == QualityLevel.GOOD:
            report.summary = f"质量良好。{total_shots}个镜头中有{need_regen}个建议优化。"
        elif report.overall_level == QualityLevel.ACCEPTABLE:
            report.summary = f"质量可接受。{total_shots}个镜头中有{need_regen}个需要改进。"
        else:
            report.summary = f"质量不足。{total_shots}个镜头中有{need_regen}个需要重新生成。"

        # 收集建议
        recommendations = set()

        if report.overall_visual_consistency < 0.6:
            recommendations.add("建议统一各镜头的视觉风格和色调")
        if report.overall_content_match < 0.6:
            recommendations.add("建议优化提示词，使其更具体和明确")
        if report.overall_technical_quality < 0.6:
            recommendations.add("建议提高视频分辨率和编码质量")

        # 从各镜头收集建议
        for shot in report.shots:
            recommendations.update(shot.regeneration_suggestions[:2])

        report.recommendations = list(recommendations)[:5]

    def get_regeneration_requests(
        self,
        report: QualityReport
    ) -> List[RegenerationRequest]:
        """
        从质量报告中生成重新生成请求列表

        Args:
            report: 质量检查报告

        Returns:
            需要重新生成的请求列表
        """
        requests = []

        for shot in report.shots:
            if shot.needs_regeneration:
                # 尝试改进prompt
                improved_prompt = self._improve_prompt(
                    shot.prompt,
                    shot.content_match.missing_elements,
                    shot.content_match.suggestions
                )

                request = RegenerationRequest(
                    shot_index=shot.shot_index,
                    original_prompt=shot.prompt,
                    improved_prompt=improved_prompt,
                    quality_issues=[shot.regeneration_reason],
                    suggestions=shot.regeneration_suggestions,
                    priority=1 if shot.overall_score < 0.3 else 2
                )
                requests.append(request)

        # 按优先级排序
        requests.sort(key=lambda x: x.priority)

        return requests

    def _improve_prompt(
        self,
        original_prompt: str,
        missing_elements: List[str],
        suggestions: List[str]
    ) -> str:
        """尝试改进提示词"""
        if not missing_elements and not suggestions:
            return original_prompt

        try:
            improvement_prompt = f"""请改进以下视频生成提示词。

原始提示词：
"{original_prompt}"

存在的问题：
- 缺失元素：{', '.join(missing_elements) if missing_elements else '无'}
- 改进建议：{', '.join(suggestions[:3]) if suggestions else '无'}

请生成一个改进后的提示词，要求：
1. 保持原始意图
2. 添加缺失的关键元素
3. 更加具体和清晰
4. 不要超过200字

只返回改进后的提示词，不要其他解释。"""

            response = self.llm.simple_call(improvement_prompt, max_tokens=300)

            if response.get("success"):
                improved = response.get("content", "").strip()
                if improved and len(improved) > 10:
                    return improved

        except Exception as e:
            logger.warning(f"改进提示词失败: {e}")

        return original_prompt

    def cleanup(self) -> None:
        """清理临时文件"""
        try:
            import shutil
            if os.path.exists(self._temp_dir):
                shutil.rmtree(self._temp_dir)
                logger.info(f"清理临时目录: {self._temp_dir}")
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")

    def __del__(self):
        """析构时清理"""
        self.cleanup()


# 便捷函数
def check_video_quality(
    video_path: str,
    prompt: str,
    config: Optional[QualityCheckConfig] = None
) -> ShotQualityResult:
    """
    快速检查单个视频质量

    Args:
        video_path: 视频路径
        prompt: 生成提示词
        config: 检查配置

    Returns:
        质量检查结果
    """
    checker = VideoQualityChecker(config=config)
    try:
        return checker.check_video(video_path, prompt)
    finally:
        checker.cleanup()


def check_project_quality(
    videos: List[Dict[str, Any]],
    project_id: str = "",
    config: Optional[QualityCheckConfig] = None
) -> QualityReport:
    """
    检查整个项目的视频质量

    Args:
        videos: 视频列表
        project_id: 项目ID
        config: 检查配置

    Returns:
        质量报告
    """
    checker = VideoQualityChecker(config=config)
    try:
        return checker.check_multiple_videos(videos, project_id)
    finally:
        checker.cleanup()
