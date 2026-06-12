/**
 * 视频生成API
 */
import apiClient from './client';
import type {
  VideoGenerationRequest,
  VideoGenerationTask,
  Shot,
  ProductionBible,
  StrategyDecision,
  IntentGenerationRequest,
  IntentGenerationResponse,
  SourceMaterial
} from './types';
import { getFullUrl } from '../utils/url';

export const videosApi = {
  /**
   * 创建视频生成任务（默认只生成脚本）
   */
  createTask: async (request: VideoGenerationRequest): Promise<{ taskId: string }> => {
    const isAutopilot = request.generationMode === 'autopilot';
    const response = await apiClient.post<{ success: boolean; taskId: string }>(
      '/api/video-generation/create',
      {
        ...request,
        autoGenerate: isAutopilot,
        generateScriptOnly: !isAutopilot
      }
    );
    // 返回任务ID
    return { taskId: response.data.taskId };
  },

  /**
   * 自然语言生成入口：用户输入可包含 URL，后端会先拉取来源并判断是否需要追问。
   */
  createFromIntent: async (request: IntentGenerationRequest): Promise<IntentGenerationResponse> => {
    const response = await apiClient.post<IntentGenerationResponse>(
      '/api/video-generation/intent',
      request
    );
    return response.data;
  },

  /**
   * 确认脚本并开始生成视频
   */
  confirmAndGenerate: async (
    taskId: string,
    script: string,
    shots: Shot[],
    options?: any
  ): Promise<VideoGenerationTask> => {
    const response = await apiClient.post<VideoGenerationTask>(
      `/api/video-generation/task/${taskId}/confirm`,
      {
        script,
        shots,
        options
      }
    );
    return response.data;
  },

  /**
   * 重新生成单个分镜的图片
   */
  regenerateShot: async (
    taskId: string,
    sequence: number,
    prompt: string,
    duration: number
  ): Promise<any> => {
    const response = await apiClient.post(
      `/api/video-generation/task/${taskId}/regenerate-shot`,
      { sequence, prompt, duration }
    );
    return response.data;
  },

  /**
   * 获取任务状态
   */
  getTaskStatus: async (taskId: string): Promise<VideoGenerationTask> => {
    const response = await apiClient.get<{
      success: boolean;
      taskId: string;
      status: string;
      progress: number;
      message?: string;
      data?: {
        taskId: string;
        status: string;
        progress: number;
        script?: string;
        shots?: Shot[];
        generatedVideos?: any[];
        finalVideo?: string;
        narrationAudioPath?: string;
        config?: { topic: string; style: string; target_duration?: number; shot_count?: number };
        logs?: any[];
        error?: string;
        createdAt?: string;
        completedAt?: string;
        bible?: ProductionBible | null;
        strategyDecision?: StrategyDecision | null;
        sourceMaterial?: SourceMaterial | null;
      };
    }>(`/api/video-generation/task/${taskId}`);

    // 从后端响应中提取任务数据
    const taskData = response.data.data;
    return {
      taskId: response.data.taskId,
      topic: taskData?.config?.topic,
      style: taskData?.config?.style,
      targetDuration: taskData?.config?.target_duration,
      shotCount: taskData?.config?.shot_count,
      message: response.data.message, // Map message
      status: response.data.status as VideoGenerationTask['status'],
      progress: response.data.progress,
      script: taskData?.script,
      shots: taskData?.shots,
      generatedVideos: taskData?.generatedVideos,
      finalVideo: taskData?.finalVideo,
      narrationAudioPath: taskData?.narrationAudioPath,
      logs: taskData?.logs,  // Map logs
      error: taskData?.error,
      createdAt: taskData?.createdAt || new Date().toISOString(),
      bible: taskData?.bible ?? null,
      strategyDecision: taskData?.strategyDecision ?? null,
      sourceMaterial: taskData?.sourceMaterial ?? null,
    };
  },

  /**
   * 轮询任务状态（带超时）
   */
  pollTaskStatus: async (
    taskId: string,
    onProgress?: (task: VideoGenerationTask) => void,
    maxWaitTime: number = 600000 // 10分钟
  ): Promise<VideoGenerationTask> => {
    const startTime = Date.now();
    const pollInterval = 3000; // 3秒轮询一次

    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const task = await videosApi.getTaskStatus(taskId);

          // 调用进度回调
          if (onProgress) {
            onProgress(task);
          }

          // 检查是否完成
          if (task.status === 'completed' || task.status === 'partial_success') {
            resolve(task);
            return;
          }

          // 检查是否失败
          if (task.status === 'failed') {
            reject(new Error(task.error || '视频生成失败'));
            return;
          }

          // 检查是否在等待确认（不算失败，停止轮询）
          if (task.status === 'waiting_confirmation') {
            resolve(task);
            return;
          }

          // 检查超时
          if (Date.now() - startTime > maxWaitTime) {
            reject(new Error('视频生成超时'));
            return;
          }

          // 继续轮询
          setTimeout(poll, pollInterval);
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  },

  /**
   * 下载视频
   */
  downloadVideo: (videoPath: string): string => {
    // 返回视频文件的URL
    return getFullUrl(videoPath);
  }
};
