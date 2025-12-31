/**
 * 多平台上传API
 */
import apiClient from './client';

export type Platform = 'youtube' | 'bilibili' | 'douyin' | 'kuaishou' | 'xiaohongshu' | 'wechat_channels' | 'weibo';

export interface PlatformConfig {
  platform: Platform;
  enabled: boolean;
  api_key?: string;
  api_secret?: string;
  access_token?: string;
  refresh_token?: string;
  client_id?: string;
  client_secret?: string;
  cookies?: Record<string, string>;
  session_data?: Record<string, any>;
}

export interface MultiPlatformUploadRequest {
  video_path: string;
  title: string;
  description: string;
  tags?: string[];
  category?: string;
  thumbnail_path?: string;
  cover_image?: string;
  privacy?: 'public' | 'private' | 'unlisted';
  platforms: Platform[];
  topic?: string;
  allow_comment?: boolean;
  allow_download?: boolean;
  allow_duet?: boolean;
}

export interface UploadResult {
  platform: string;
  status: 'pending' | 'uploading' | 'processing' | 'success' | 'failed';
  video_id?: string;
  video_url?: string;
  error?: string;
  uploaded_at?: string;
}

export interface UploadTask {
  task_id: string;
  status: 'pending' | 'uploading' | 'completed' | 'failed' | 'partial';
  platforms: string[];
  results: UploadResult[];
  created_at: string;
  completed_at?: string;
}

export const uploadApi = {
  /**
   * 配置平台
   */
  configurePlatform: async (config: PlatformConfig): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post('/api/upload/configure-platform', config);
    return response.data;
  },

  /**
   * 获取已配置的平台列表
   */
  getConfiguredPlatforms: async (): Promise<{ platforms: string[]; count: number }> => {
    const response = await apiClient.get('/api/upload/configured-platforms');
    return response.data;
  },

  /**
   * 上传视频到多个平台
   */
  uploadVideo: async (request: MultiPlatformUploadRequest): Promise<{ success: boolean; task_id: string; message: string }> => {
    const response = await apiClient.post('/api/upload/upload', request);
    return response.data;
  },

  /**
   * 获取上传任务状态
   */
  getTask: async (taskId: string): Promise<UploadTask> => {
    const response = await apiClient.get(`/api/upload/task/${taskId}`);
    return response.data;
  },

  /**
   * 获取所有上传任务
   */
  getAllTasks: async (): Promise<{ tasks: UploadTask[]; total: number }> => {
    const response = await apiClient.get('/api/upload/tasks');
    return response.data;
  },

  /**
   * 重试失败的上传
   */
  retryFailedUploads: async (taskId: string): Promise<{ success: boolean; task_id: string; status: string; message: string }> => {
    const response = await apiClient.post(`/api/upload/task/${taskId}/retry`);
    return response.data;
  },

  /**
   * 删除视频
   */
  deleteVideo: async (videoId: string, platforms: Platform[]): Promise<{ success: boolean; results: Record<string, boolean> }> => {
    const response = await apiClient.delete('/api/upload/video', {
      params: { video_id: videoId },
      data: { platforms }
    });
    return response.data;
  },

  /**
   * 获取统计信息
   */
  getStats: async (): Promise<any> => {
    const response = await apiClient.get('/api/upload/stats');
    return response.data;
  },

  /**
   * 获取YouTube OAuth授权URL
   */
  getYouTubeAuthUrl: async (redirectUri: string): Promise<{ authorization_url: string; state: string }> => {
    const response = await apiClient.get('/api/upload/oauth/youtube/authorize-url', {
      params: { redirect_uri: redirectUri }
    });
    return response.data;
  },

  /**
   * 处理YouTube OAuth回调
   */
  handleYouTubeCallback: async (code: string, redirectUri: string): Promise<{ success: boolean; message: string; access_token: string }> => {
    const response = await apiClient.post('/api/upload/oauth/youtube/callback', null, {
      params: { code, redirect_uri: redirectUri }
    });
    return response.data;
  },

  /**
   * 轮询任务状态
   */
  pollTaskStatus: async (
    taskId: string,
    onProgress?: (task: UploadTask) => void,
    maxWaitTime: number = 1800000 // 30分钟
  ): Promise<UploadTask> => {
    const startTime = Date.now();
    const pollInterval = 3000; // 3秒

    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const task = await uploadApi.getTask(taskId);

          if (onProgress) {
            onProgress(task);
          }

          // 检查是否完成
          if (task.status === 'completed' || task.status === 'partial') {
            resolve(task);
            return;
          }

          // 检查是否失败
          if (task.status === 'failed') {
            reject(new Error('All uploads failed'));
            return;
          }

          // 检查超时
          if (Date.now() - startTime > maxWaitTime) {
            reject(new Error('Upload timeout'));
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
  }
};
