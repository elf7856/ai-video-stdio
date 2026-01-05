/**
 * API客户端配置
 * 使用axios进行HTTP请求
 */
import axios from 'axios';

// 创建axios实例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000', // 优先使用环境变量
  timeout: 120000, // 2分钟超时（AI生成需要较长时间）
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等认证信息
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 统一错误处理
    console.error('API Error:', error);

    if (error.response) {
      // 服务器返回错误
      const { status, data } = error.response;

      switch (status) {
        case 400:
          console.error('请求参数错误:', data);
          break;
        case 401:
          console.error('未授权，请登录');
          break;
        case 404:
          console.error('请求的资源不存在');
          break;
        case 500:
          console.error('服务器错误:', data);
          break;
        default:
          console.error('请求失败:', data);
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      console.error('网络错误，请检查连接');
    } else {
      // 其他错误
      console.error('请求配置错误:', error.message);
    }

    return Promise.reject(error);
  }
);

export default apiClient;
