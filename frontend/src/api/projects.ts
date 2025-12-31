/**
 * 项目管理API
 */
import apiClient from './client';
import type { Project, ProjectCreateRequest } from './types';

export const projectsApi = {
  /**
   * 创建新项目
   */
  createProject: async (request: ProjectCreateRequest): Promise<{ message: string; projectId: string }> => {
    const response = await apiClient.post('/api/projects', request);
    return response.data;
  },

  /**
   * 获取项目列表
   */
  listProjects: async (params?: { status?: string; limit?: number; offset?: number }): Promise<Project[]> => {
    const response = await apiClient.get('/api/projects', { params });
    return response.data;
  },

  /**
   * 获取项目详情
   */
  getProject: async (projectId: string): Promise<Project> => {
    const response = await apiClient.get(`/api/projects/${projectId}`);
    return response.data;
  },

  /**
   * 删除项目
   */
  deleteProject: async (projectId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/api/projects/${projectId}`);
    return response.data;
  }
};
