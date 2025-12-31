/**
 * 视频编辑器API客户端
 */
import apiClient from './client';

export interface SubtitleSegment {
  start_time: number;
  end_time: number;
  text: string;
  font_size?: number;
  color?: string;
  position?: string;
}

export interface SubtitleFile {
  id: string;
  project_id: string;
  language: string;
  segments: SubtitleSegment[];
  default_font_size: number;
  default_color: string;
  default_font_family: string;
  default_position: string;
  created_at: string;
  updated_at: string;
}

export interface TimelineElement {
  id: string;
  name: string;
  duration: number;
  start_time: number;
  trim_start?: number;
  trim_end?: number;
}

export interface MediaElement extends TimelineElement {
  type: 'media';
  media_id: string;
  muted?: boolean;
  volume?: number;
  speed?: number;
}

export interface TextElement extends TimelineElement {
  type: 'text';
  content: string;
  font_size?: number;
  font_family?: string;
  color?: string;
  x?: number;
  y?: number;
  opacity?: number;
}

export interface TimelineTrack {
  id: string;
  name: string;
  type: 'media' | 'text' | 'audio';
  elements: (MediaElement | TextElement)[];
  muted?: boolean;
  locked?: boolean;
}

export interface Timeline {
  id: string;
  name?: string;
  tracks: TimelineTrack[];
  canvas_width?: number;
  canvas_height?: number;
  fps?: number;
  background_color?: string;
  created_at?: string;
  updated_at?: string;
}

export interface EditorProject {
  id: string;
  name: string;
  description?: string;
  timeline?: Timeline;
  status: 'draft' | 'editing' | 'rendering' | 'completed' | 'failed';
  output_path?: string;
  output_format: string;
  output_quality: string;
  render_progress: number;
  render_error?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateRequest {
  name: string;
  description?: string;
  timeline?: Timeline;
}

export interface RenderRequest {
  project_id: string;
  quality?: string;
}

export interface SubtitleGenerateRequest {
  project_id: string;
  video_path: string;
  language?: string;
}

/**
 * 编辑器API
 */
export const editorApi = {
  /**
   * 创建新项目
   */
  async createProject(request: ProjectCreateRequest): Promise<EditorProject> {
    const response = await apiClient.post('/api/editor/projects', request);
    return response.data;
  },

  /**
   * 获取项目详情
   */
  async getProject(projectId: string): Promise<EditorProject> {
    const response = await apiClient.get(`/api/editor/projects/${projectId}`);
    return response.data;
  },

  /**
   * 获取项目列表
   */
  async listProjects(params?: {
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<EditorProject[]> {
    const response = await apiClient.get('/api/editor/projects', { params });
    return response.data;
  },

  /**
   * 更新项目时间轴
   */
  async updateProject(projectId: string, timeline: Timeline): Promise<EditorProject> {
    const response = await apiClient.put(`/api/editor/projects/${projectId}`, timeline);
    return response.data;
  },

  /**
   * 删除项目
   */
  async deleteProject(projectId: string): Promise<{ message: string; project_id: string }> {
    const response = await apiClient.delete(`/api/editor/projects/${projectId}`);
    return response.data;
  },

  /**
   * 渲染视频
   */
  async renderVideo(request: RenderRequest): Promise<{
    message: string;
    project_id: string;
    output_path: string;
  }> {
    const response = await apiClient.post('/api/editor/render', request);
    return response.data;
  },

  /**
   * 生成字幕
   */
  async generateSubtitle(request: SubtitleGenerateRequest): Promise<SubtitleFile> {
    const response = await apiClient.post('/api/editor/subtitle/generate', request);
    return response.data;
  },

  /**
   * 导入字幕
   */
  async importSubtitle(projectId: string, file: File): Promise<SubtitleFile> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post(
      `/api/editor/subtitle/import?project_id=${projectId}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  /**
   * 渲染预览
   */
  async renderPreview(projectId: string, maxDuration: number = 10): Promise<{
    success: boolean;
    preview_path: string;
    duration: number;
  }> {
    const response = await apiClient.post('/api/editor/preview', null, {
      params: { project_id: projectId, max_duration: maxDuration },
    });
    return response.data;
  },
};

export default editorApi;
