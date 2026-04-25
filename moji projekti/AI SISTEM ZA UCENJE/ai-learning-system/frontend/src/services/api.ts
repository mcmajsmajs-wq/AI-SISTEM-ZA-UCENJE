import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/stores/authStore'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().token
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = useAuthStore.getState().refreshToken
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          const { access_token, refresh_token } = response.data
          useAuthStore.getState().setTokens(access_token, refresh_token)
          
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`
          }
          return api(originalRequest)
        }
      } catch {
        useAuthStore.getState().logout()
        toast.error('Sesija je istekla. Molimo vas da se ponovo prijavite.')
        window.location.href = '/login'
      }
    }

    const message = (error.response?.data as { detail?: string })?.detail || 
                    error.message || 
                    'Došlo je do greške'
    
    if (error.response?.status !== 401) {
      toast.error(message)
    }

    return Promise.reject(error)
  }
)

export const authApi = {
  login: (username: string, password: string) =>
    api.postForm('/auth/login', { username, password }),
  
  loginJson: (email: string, password: string) =>
    api.post('/auth/login/json', { email, password }),
  
  register: (data: { email: string; password: string; full_name?: string }) =>
    api.post('/auth/register', data),
  
  logout: () =>
    api.post('/auth/logout'),
  
  getMe: () =>
    api.get('/auth/me'),
  
  refreshToken: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
}

export const usersApi = {
  getMe: () =>
    api.get('/users/me'),
  
  updateMe: (data: { full_name?: string; timezone?: string; language?: string }) =>
    api.put('/users/me', data),
  
  changePassword: (currentPassword: string, newPassword: string) =>
    api.put('/users/me/password', { current_password: currentPassword, new_password: newPassword }),
  
  getStats: () =>
    api.get('/users/me/stats'),
  
  deleteMe: () =>
    api.delete('/users/me'),
}

export const filesApi = {
  upload: (file: File, onProgress?: (progress: number) => void) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return api.post('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })
  },
  
  list: (page = 1, size = 20) =>
    api.get(`/files?page=${page}&size=${size}`),
  
  get: (id: number) =>
    api.get(`/files/${id}`),
  
  download: (id: number) =>
    api.get(`/files/${id}/download`, { responseType: 'blob' }),
  
  getPresignedUrl: (id: number) =>
    api.get(`/files/${id}/presigned-url`),
  
  delete: (id: number) =>
    api.delete(`/files/${id}`),
  
  getStatus: (id: number) =>
    api.get(`/files/${id}/status`),
}

export const documentsApi = {
  list: (page = 1, size = 20, status?: string) => {
    const params = new URLSearchParams({ page: String(page), size: String(size) })
    if (status) params.append('status', status)
    return api.get(`/documents?${params}`)
  },
  
  get: (id: number) =>
    api.get(`/documents/${id}`),
  
  create: (fileId: number, title?: string, sourceLanguage?: string, targetLanguage?: string) =>
    api.post('/documents', { file_id: fileId, title, source_language: sourceLanguage, target_language: targetLanguage }),
  
  delete: (id: number) =>
    api.delete(`/documents/${id}`),
  
  process: (id: number) =>
    api.post(`/documents/${id}/process`),
  
  translate: (id: number, provider?: string) =>
    api.post(`/documents/${id}/translate`, { provider }),
  
  getProgress: (id: number) =>
    api.get(`/documents/${id}/progress`),
  
  getChunks: (id: number, page = 1, size = 50) =>
    api.get(`/documents/${id}/chunks?page=${page}&size=${size}`),
  
  updateChunk: (documentId: number, chunkId: number, data: { translated_text: string; status?: string }) =>
    api.put(`/documents/${documentId}/chunks/${chunkId}`, data),
  
  export: (id: number) =>
    api.post(`/documents/${id}/export`),
  
  estimateCost: (id: number, provider: string) =>
    api.post(`/documents/${id}/estimate-cost`, { provider }),
}

export const healthApi = {
  check: () => api.get('/health'),
  ready: () => api.get('/ready'),
  live: () => api.get('/live'),
}

export const quizApi = {
  list: (page = 1, size = 20, status?: string, difficulty?: string) => {
    const params = new URLSearchParams({ page: String(page), size: String(size) })
    if (status) params.append('status', status)
    if (difficulty) params.append('difficulty', difficulty)
    return api.get(`/quizzes?${params}`)
  },
  
  get: (id: string) =>
    api.get(`/quizzes/${id}`),
  
  create: (data: {
    title: string
    description?: string
    document_id?: string
    time_limit?: number
    passing_score?: number
    max_attempts?: number
    difficulty?: string
    question_types?: string[]
    questions?: any[]
  }) => api.post('/quizzes', data),
  
  update: (id: string, data: Partial<{
    title: string
    description: string
    time_limit: number
    passing_score: number
    max_attempts: number
    difficulty: string
    status: string
  }>) => api.put(`/quizzes/${id}`, data),
  
  delete: (id: string) =>
    api.delete(`/quizzes/${id}`),
  
  getQuestions: (quizId: string) =>
    api.get(`/quizzes/${quizId}/questions`),
  
  addQuestion: (quizId: string, data: {
    question_text: string
    question_type: string
    options?: string[]
    correct_answer: string
    correct_answers?: string[]
    explanation?: string
    hint?: string
    points?: number
    difficulty?: string
  }) => api.post(`/quizzes/${quizId}/questions`, data),
  
  updateQuestion: (questionId: string, data: Partial<{
    question_text: string
    options: string[]
    correct_answer: string
    correct_answers: string[]
    explanation: string
    hint: string
    points: number
    difficulty: string
  }>) => api.put(`/quizzes/questions/${questionId}`, data),
  
  deleteQuestion: (questionId: string) =>
    api.delete(`/quizzes/questions/${questionId}`),
  
  startAttempt: (quizId: string) =>
    api.post(`/quizzes/${quizId}/attempts`),
  
  getAttempt: (attemptId: string) =>
    api.get(`/quizzes/attempts/${attemptId}`),
  
  submitAnswer: (attemptId: string, data: {
    question_id: string
    selected_answer?: string
    selected_answers?: string[]
    text_answer?: string
    time_spent: number
  }) => api.post(`/quizzes/attempts/${attemptId}/answers`, data),
  
  completeAttempt: (attemptId: string) =>
    api.post(`/quizzes/attempts/${attemptId}/complete`),
  
  listAttempts: (quizId?: string) => {
    const params = quizId ? `?quiz_id=${quizId}` : ''
    return api.get(`/quizzes/attempts${params}`)
  },
  
  getStats: () =>
    api.get('/quizzes/stats'),
  
  generate: (data: {
    document_id: string
    title?: string
    num_questions: number
    question_types?: string[]
    difficulty: string
    time_limit: number
    passing_score: number
  }) => api.post('/quizzes/generate', data),
}

export default api
