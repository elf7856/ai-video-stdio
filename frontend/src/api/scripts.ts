/**
 * 脚本生成API
 */
import apiClient from './client';
import type { ScriptGenerateRequest, ScriptGenerateResponse } from './types';

export const scriptsApi = {
  /**
   * 生成视频脚本和分镜
   */
  generateScript: async (request: ScriptGenerateRequest): Promise<ScriptGenerateResponse> => {
    const response = await apiClient.post<ScriptGenerateResponse>(
      '/api/scripts/generate',
      request
    );
    return response.data;
  },

  /**
   * 优化现有脚本
   */
  optimizeScript: async (script: string): Promise<ScriptGenerateResponse> => {
    const response = await apiClient.post<ScriptGenerateResponse>(
      '/api/scripts/optimize',
      { script }
    );
    return response.data;
  },

  /**
   * 生成分镜提示词
   */
  generateShotPrompts: async (script: string, shotCount: number) => {
    const response = await apiClient.post(
      '/api/scripts/generate-shots',
      { script, shotCount }
    );
    return response.data;
  }
};
