import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, Token } from '@/types'
import { authApi } from '@/services/api'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  tokenObtainedAt: number | null
  isAuthenticated: boolean
  isLoading: boolean
  refreshTimer: ReturnType<typeof setTimeout> | null
  
  setUser: (user: User | null) => void
  setTokens: (token: string, refreshToken: string) => void
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
  setLoading: (loading: boolean) => void
  refreshAccessToken: () => Promise<void>
  scheduleTokenRefresh: () => void
  clearRefreshTimer: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      tokenObtainedAt: null,
      isAuthenticated: false,
      isLoading: true,
      refreshTimer: null,

      setUser: (user) => set({ user, isAuthenticated: !!user }),
      
      setTokens: (token, refreshToken) => {
        set({ token, refreshToken, tokenObtainedAt: Date.now() })
        get().scheduleTokenRefresh()
      },
      
      setLoading: (isLoading) => set({ isLoading }),

      scheduleTokenRefresh: () => {
        const state = get()
        state.clearRefreshTimer()
        
        if (!state.refreshToken) return
        
        const refreshAt = 14 * 60 * 1000
        const timer = setTimeout(async () => {
          try {
            await get().refreshAccessToken()
          } catch {
            get().logout()
          }
        }, refreshAt)
        
        set({ refreshTimer: timer })
      },

      clearRefreshTimer: () => {
        const { refreshTimer } = get()
        if (refreshTimer) {
          clearTimeout(refreshTimer)
          set({ refreshTimer: null })
        }
      },

      refreshAccessToken: async () => {
        const { refreshToken } = get()
        if (!refreshToken) throw new Error('No refresh token')
        
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        })
        const { access_token, refresh_token } = response.data
        set({ token: access_token, refreshToken: refresh_token, tokenObtainedAt: Date.now() })
        get().scheduleTokenRefresh()
      },

      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const response = await authApi.login(email, password)
          const data: Token = response.data
          set({ 
            token: data.access_token, 
            refreshToken: data.refresh_token,
            tokenObtainedAt: Date.now(),
            isAuthenticated: true,
            isLoading: false
          })
          get().scheduleTokenRefresh()
          await get().fetchUser()
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      register: async (email, password, fullName) => {
        set({ isLoading: true })
        try {
          await authApi.register({ email, password, full_name: fullName })
          await get().login(email, password)
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      logout: () => {
        get().clearRefreshTimer()
        set({ 
          user: null, 
          token: null, 
          refreshToken: null,
          tokenObtainedAt: null,
          isAuthenticated: false 
        })
      },

      fetchUser: async () => {
        try {
          const response = await authApi.getMe()
          set({ user: response.data, isLoading: false })
        } catch (error) {
          console.error('fetchUser failed:', error)
          set({ isLoading: false })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        token: state.token, 
        refreshToken: state.refreshToken,
        tokenObtainedAt: state.tokenObtainedAt,
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.token && state?.refreshToken) {
          state.scheduleTokenRefresh()
        }
      }
    }
  )
)
