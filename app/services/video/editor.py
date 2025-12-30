from app.services.video.manager import VideoProcessingManager

class VideoEditor:
    def __init__(self):
        self.manager = VideoProcessingManager()

    async def process_natural_language_edit(self, video_path: str, instruction: str):
        """
        用自然语言编辑视频
        :param video_path: 视频文件路径
        :param instruction: 编辑指令（自然语言）
        :return: 编辑结果字典
        """
        return await self.manager.process_natural_language_edit(video_path, instruction)