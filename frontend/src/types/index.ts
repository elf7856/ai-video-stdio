// API 响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
  edit_type?: string
  instruction_analysis?: string
  content_description?: string
}

// 视频相关类型
export interface Video {
  id: number
  filename?: string
  original_path: string
  title: string
  description?: string
  duration?: number
  resolution?: string
  file_size?: number
  format: string
  analysis?: any
  tags?: string[]
  created_at?: string
  updated_at: string
  platform?: string
  file_path?: string
}

export interface VideoCreate {
  title?: string
  description?: string
}

export interface VideoEdit {
  id: number
  video_id: number
  instruction: string
  edit_type: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  start_time?: number
  end_time?: number
  duration?: number
  generated_content?: any
  output_path?: string
  created_at: string
  completed_at?: string
}

// 下载相关类型
export interface DownloadResult {
  success: boolean
  title?: string
  platform?: string
  duration?: number
  file_path?: string
  error?: string
}

export interface VideoInfo {
  success: boolean
  title?: string
  duration?: number
  description?: string
  uploader?: string
  view_count?: number
  platform?: string
  thumbnail?: string
  formats?: string[]
  error?: string
}

// 表单类型
export interface UrlDownloadForm {
  url: string
  autoAnalyze: boolean
}

export interface CookiesDownloadForm {
  url: string
}

export interface EditForm {
  instruction: string
}

// 分页类型
export interface PaginationParams {
  skip: number
  limit: number
}

export interface PaginationResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
} 