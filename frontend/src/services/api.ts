import axios from 'axios'
import type { 
  Video, 
  VideoCreate, 
  VideoEdit, 
  DownloadResult, 
  VideoInfo,
  PaginationParams,
  PaginationResult,
  ApiResponse
} from '@/types'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// 视频相关API
export const videoApi = {
  // 从URL处理视频
  async processFromUrl(url: string, autoAnalyze: boolean = true): Promise<ApiResponse> {
    return api.post('/videos/process', { url, auto_analyze: autoAnalyze })
  },

  // 使用Cookies下载视频
  async downloadWithCookies(url: string, cookiesContent: string): Promise<DownloadResult> {
    return api.post('/videos/download-with-cookies', { url, cookies_content: cookiesContent })
  },

  // 获取视频列表
  async getVideos(params: PaginationParams): Promise<Video[]> {
    const response = await api.get('/videos', { params })
    return response.data || []
  },

  // 获取单个视频
  async getVideo(id: number): Promise<Video> {
    const response = await api.get(`/videos/${id}`)
    return response.data
  },

  // 上传视频
  uploadVideo: (file: File, data: VideoCreate): Promise<Video> => {
    const formData = new FormData()
    formData.append('file', file)
    if (data.title) formData.append('title', data.title)
    if (data.description) formData.append('description', data.description)
    
    return api.post('/videos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }).then(res => res.data)
  },

  // 获取视频信息
  getVideoInfo: (url: string): Promise<VideoInfo> => {
    return api.post('/videos/url/info', { url }).then(res => res.data.info)
  },

  // 分析视频
  analyzeVideo: (id: number): Promise<ApiResponse> => {
    return api.post(`/videos/${id}/analyze`).then(res => res.data)
  },

  // 生成视频摘要
  generateSummary: (id: number, summaryType: string = 'text'): Promise<ApiResponse> => {
    return api.post(`/videos/${id}/summary`, { summary_type: summaryType }).then(res => res.data)
  },

  // 编辑视频
  async editVideo(id: number, instruction: string): Promise<ApiResponse> {
    return api.post(`/videos/${id}/edit`, { instruction })
  },

  // 下载视频文件
  async downloadVideo(id: number): Promise<Blob> {
    const response = await api.get(`/videos/${id}/download`, {
      responseType: 'blob'
    })
    return response
  },

  // 创建视频编辑任务
  createVideoEdit: (id: number, editData: Partial<VideoEdit>): Promise<VideoEdit> => {
    return api.post(`/videos/${id}/edit`, editData).then(res => res.data)
  }
}

// 平台相关API
export const platformApi = {
  // 获取支持的平台
  getSupportedPlatforms: (): Promise<{ platforms: string[], description: string }> => {
    return api.get('/videos/platforms/supported').then(res => res.data)
  }
}

export default api 