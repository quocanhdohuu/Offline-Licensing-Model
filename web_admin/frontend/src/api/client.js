import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request Interceptor: Tự động đính kèm Bearer Token nếu có
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('olm_access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response Interceptor: Xử lý hết hạn phiên
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Hết hạn token hoặc không hợp lệ -> xóa storage
      localStorage.removeItem('olm_access_token')
      localStorage.removeItem('olm_user_info')
      // Bắn event để AuthContext bắt được nếu cần
      window.dispatchEvent(new Event('auth:unauthorized'))
    }
    return Promise.reject(error)
  }
)

export default client

