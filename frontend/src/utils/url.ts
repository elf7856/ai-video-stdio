import apiClient from '../api/client';

/**
 * 将后端返回的路径转换为完整的可访问 URL
 * 处理 ./, /, outputs/ 前缀等各种情况
 */
export const getFullUrl = (path?: string): string => {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  if (path.startsWith('/assets/') || path.startsWith('assets/')) return path; // Frontend asset
  
  const baseUrl = apiClient.defaults.baseURL?.replace(/\/$/, '') || 'http://localhost:8000';
  
  // 1. 先移除开头的 ./ 或 /
  let cleanPath = path.replace(/^(\.\/|\/)/, '');
  
  // 2. 如果路径里没有 outputs/，补上挂载点
  if (!cleanPath.startsWith('outputs/')) {
    cleanPath = `outputs/${cleanPath}`;
  }
  
  // 3. 再次兜底，防止出现 outputs/outputs/
  cleanPath = cleanPath.replace(/^outputs\/outputs\//, 'outputs/');
  
  const finalUrl = `${baseUrl}/${cleanPath}`;
  return finalUrl;
};
