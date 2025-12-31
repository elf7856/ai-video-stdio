/**
 * 图像生成API
 */
import apiClient from './client';
import type { ImageGenerationRequest, ImageGenerationResponse, ImageProvider } from './types';
import { getFullUrl } from '../utils/url';

export const imagesApi = {
  /**
   * 生成图像
   */
  generateImage: async (request: ImageGenerationRequest): Promise<ImageGenerationResponse> => {
    const response = await apiClient.post<ImageGenerationResponse>(
      '/api/images/generate',
      request
    );
    return response.data;
  },

  /**
   * 获取可用的图像生成器列表
   */
  getAvailableProviders: async (): Promise<string[]> => {
    const response = await apiClient.get<{ providers: string[] }>(
      '/api/images/providers'
    );
    return response.data.providers;
  },

  /**
   * 获取生成器详细信息
   */
  getProviderInfo: async (): Promise<Record<string, ImageProvider>> => {
    const response = await apiClient.get<Record<string, ImageProvider>>(
      '/api/images/providers/info'
    );
    return response.data;
  },

  /**
   * 下载图像
   */
  downloadImage: (imagePath: string): string => {
    return getFullUrl(imagePath);
  },

  /**
   * 获取图像URL（用于预览）
   */
  getImageUrl: (imagePath: string): string => {
    return getFullUrl(imagePath);
  }
};
