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
  maxRedirects: 5,
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
  login: (email: string, password: string) =>
    api.post('/auth/login/json', { email, password }),
  
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

export const studyPlanApi = {
  getPlan: () => api.get('/study-plan/me'),
  updatePlan: (data: {
    daily_quiz_goal?: number
    weekly_quiz_goal?: number
    session_duration_min?: number
    study_days?: number[]
    reminder_enabled?: boolean
    reminder_time?: string
    notes?: string
  }) => api.put('/study-plan/me', data),
  getProgress: () => api.get('/study-plan/me/progress'),
  listItems: (fromDate?: string, toDate?: string, onlyPending?: boolean) => {
    const p = new URLSearchParams()
    if (fromDate) p.append('from_date', fromDate)
    if (toDate) p.append('to_date', toDate)
    if (onlyPending) p.append('only_pending', 'true')
    return api.get(`/study-plan/me/items?${p}`)
  },
  addItem: (data: { quiz_id: string; scheduled_for: string; priority?: number; notes?: string }) =>
    api.post('/study-plan/me/items', data),
  updateItem: (id: string, data: { scheduled_for?: string; priority?: number; notes?: string }) =>
    api.put(`/study-plan/me/items/${id}`, data),
  completeItem: (id: string, attemptId?: string) =>
    api.post(`/study-plan/me/items/${id}/complete`, { attempt_id: attemptId }),
  deleteItem: (id: string) =>
    api.delete(`/study-plan/me/items/${id}`),
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
  
  list: (skip = 0, limit = 20) =>
    api.get(`/files?skip=${skip}&limit=${limit}`),
  
  get: (id: string) =>
    api.get(`/files/${id}`),
  
  download: (id: string) =>
    api.get(`/files/${id}/download`, { responseType: 'blob' }),
  
  getPresignedUrl: (id: string) =>
    api.get(`/files/${id}/presigned-url`),
  
  delete: (id: string) =>
    api.delete(`/files/${id}`),
  
  getStatus: (id: string) =>
    api.get(`/files/${id}/status`),
}

export const documentsApi = {
  list: (skip = 0, limit = 20, status?: string) => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) })
    if (status) params.append('status_filter', status)
    return api.get(`/documents/?${params}`)
  },

  get: (id: string) =>
    api.get(`/documents/${id}`),

  create: (fileId: string, title?: string, sourceLanguage?: string, targetLanguage?: string) =>
    api.post('/documents/', { file_id: fileId, title, source_language: sourceLanguage, target_language: targetLanguage }),

  delete: (id: string) =>
    api.delete(`/documents/${id}`),

  process: (id: string) =>
    api.post(`/documents/${id}/process`),
  
  translate: (id: string, provider?: string) =>
    api.post(`/documents/${id}/translate`, { provider }),

  // Prekini prevod i sačuvaj checkpoint
  stopTranslation: (id: string) =>
    api.delete(`/documents/${id}/translation`),
  
  // Nastavi prevod od checkpoint-a
  resumeTranslation: (id: string) =>
    api.post(`/documents/${id}/translation/resume`),
  
  getProgress: (id: string) =>
    api.get(`/documents/${id}/progress`),
  
  getChunks: (id: string, skip = 0, limit = 50) =>
    api.get(`/documents/${id}/chunks?skip=${skip}&limit=${limit}`),
  
  updateChunk: (documentId: string, chunkId: string, data: { translated_content?: string; is_reviewed?: boolean }) => {
    const params = new URLSearchParams()
    if (data.translated_content !== undefined) params.append('translated_content', data.translated_content)
    if (data.is_reviewed !== undefined) params.append('is_reviewed', String(data.is_reviewed))
    return api.put(`/documents/${documentId}/chunks/${chunkId}?${params}`)
  },
  
  export: (id: string) =>
    api.post(`/documents/${id}/export`),
  
  estimateCost: (id: string, provider: string) =>
    api.post(`/documents/${id}/estimate-translation`, { provider }),

  startPipeline: (id: string, options: {
    source_language?: string
    target_language?: string
    translation_provider?: string | null
    quiz_provider?: string | null
    num_questions?: number
    skip_translation?: boolean
    passing_score?: number
  }) => api.post(`/documents/${id}/pipeline`, options),

  getPipelineProviders: () =>
    api.get('/documents/pipeline/providers'),

  exportPdf: (id: string, includeOriginal = false) =>
    api.post(`/documents/${id}/export-pdf?include_original=${includeOriginal}`),

  exportPdfStatus: (taskId: string) =>
    api.get(`/documents/pdf-status/${taskId}`),

  exportPdfDownload: (id: string, taskId: string) =>
    api.get(`/documents/${id}/pdf-download?task_id=${taskId}`, {
      responseType: 'blob',
    }),

  exportDocx: (id: string, includeOriginal = false) =>
    api.post(`/documents/${id}/export-docx?include_original=${includeOriginal}`),

  exportDocxStatus: (taskId: string) =>
    api.get(`/documents/docx-status/${taskId}`),

  exportDocxDownload: (id: string, taskId: string) =>
    api.get(`/documents/${id}/docx-download?task_id=${taskId}`, {
      responseType: 'blob',
    }),

  exportXlsx: (id: string) =>
    api.get(`/documents/${id}/export/xlsx`, {
      responseType: 'blob',
    }),

  exportPptx: (id: string) =>
    api.get(`/documents/${id}/export/pptx`, {
      responseType: 'blob',
    }),

  getQuizAvailability: (id: string) =>
    api.get(`/documents/${id}/quiz-availability`),

  validateTranslationProvider: (provider?: string) =>
    api.get(`/documents/translation/validate${provider ? `?provider=${provider}` : ''}`),
}

export const quizzesApi = {
  create: (documentId: string, numQuestions = 5, timeLimit?: number, passingScore = 60, shuffleQuestions = false, sourceContent?: string) =>
    api.post('/quizzes', { 
      document_id: documentId, 
      num_questions: numQuestions, 
      time_limit: timeLimit, 
      passing_score: passingScore, 
      shuffle_questions: shuffleQuestions,
      source_content: sourceContent,
    }),

  validateProvider: (provider?: string) =>
    api.get(`/quizzes/validate${provider ? `?provider=${provider}` : ''}`),

  list: (skip = 0, limit = 20, documentId?: string) => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) })
    if (documentId) params.append('document_id', documentId)
    return api.get(`/quizzes?${params}`)
  },

  get: (id: string) =>
    api.get(`/quizzes/${id}`),

  getStatus: (id: string) =>
    api.get(`/quizzes/${id}/status`),

  delete: (id: string) =>
    api.delete(`/quizzes/${id}`),

  startAttempt: (quizId: string) =>
    api.post(`/quizzes/${quizId}/attempts`),

  submitAttempt: (quizId: string, attemptId: string, answers: { question_id: string; user_answer: string }[]) =>
    api.post(`/quizzes/${quizId}/attempts/${attemptId}/submit`, { answers }),

  listAttempts: (quizId: string, skip = 0, limit = 10) =>
    api.get(`/quizzes/${quizId}/attempts?skip=${skip}&limit=${limit}`),

  getAttemptResult: (quizId: string, attemptId: string) =>
    api.get(`/quizzes/${quizId}/attempts/${attemptId}/result`),
  getLatestAttemptResult: (quizId: string) =>
    api.get(`/quizzes/${quizId}/attempts/latest/result`),

  chat: (
    quizId: string,
    data: {
      message: string
      question_id: string
      user_answer: string
      history: { role: string; content: string }[]
      provider?: string
    }
  ) => api.post(`/quizzes/${quizId}/chat`, data),
}

export const healthApi = {
  check: () => api.get('/health'),
  ready: () => api.get('/ready'),
  live: () => api.get('/live'),
}

export const analyticsApi = {
  getOverview: () => api.get('/analytics/me/overview'),
  getActivity: (days = 30) => api.get(`/analytics/me/activity?days=${days}`),
  getQuizPerformance: (limit = 10) => api.get(`/analytics/me/quizzes?limit=${limit}`),
  getDocumentStats: () => api.get('/analytics/me/documents'),
  getStreakHistory: (weeks = 8) => api.get(`/analytics/me/streak-history?weeks=${weeks}`),
}

export const aiSettingsApi = {
  get: () => api.get('/users/me/ai-settings'),
  update: (data: {
    ai_provider: string
    ai_api_key_openai?: string | null
    ai_api_key_claude?: string | null
    ai_api_key_gemini?: string | null
    ai_api_key_groq?: string | null
    ai_api_key_mistral?: string | null
    ai_api_key_deepseek?: string | null
    ai_custom_base_url?: string | null
    ai_api_key_custom?: string | null
  }) => api.put('/users/me/ai-settings', data),
}



export const knowledgeApi = {
  query: (query: string, top_k = 5, provider?: string) =>
    api.post('/knowledge/query', { query, top_k, provider }),
  sources: () =>
    api.get('/knowledge/sources'),
  stats: () =>
    api.get('/knowledge/stats'),
  ingestUrl: (url: string, options?: { name?: string; recursive?: boolean; max_depth?: number; max_pages?: number }) =>
    api.post('/knowledge/ingest/url', { url, ...options }),
  ingestText: (content: string, name: string, source_type = 'manual') =>
    api.post('/knowledge/ingest/text', { content, name, source_type }),
  deleteSource: (id: string) =>
    api.delete(`/knowledge/sources/${id}`),
  reindex: () =>
    api.post('/knowledge/reindex', {}),
}

export const intelligenceTestApi = {
  saveResult: (result: {
    total_questions: number
    correct_answers: number
    time_spent: number
    category_scores: Record<string, number>
  }) => api.post('/intelligence-test/results', result),
  
  getResults: () => api.get('/intelligence-test/results'),
}

export const providersHealthApi = {
  check: () => api.get('/providers/health'),
}

export const gamificationApi = {
  profile: () => api.get('/gamification/profile'),
  badges: () => api.get('/gamification/badges'),
}

export default api
