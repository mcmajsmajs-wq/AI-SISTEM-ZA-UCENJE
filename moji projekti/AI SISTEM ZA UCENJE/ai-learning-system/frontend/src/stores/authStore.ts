import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, Token } from '@/types'
import { authApi } from '@/services/api'

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  
  setUser: (user: User | null) => void
  setTokens: (token: string, refreshToken: string) => void
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
  setLoading: (loading: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: true,

      setUser: (user) => set({ user, isAuthenticated: !!user }),
      
      setTokens: (token, refreshToken) => set({ token, refreshToken }),
      
      setLoading: (isLoading) => set({ isLoading }),

      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const response = await authApi.login(email, password)
          const data: Token = response.data
          set({ 
            token: data.access_token, 
            refreshToken: data.refresh_token,
            isAuthenticated: true 
          })
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
        set({ 
          user: null, 
          token: null, 
          refreshToken: null, 
          isAuthenticated: false 
        })
      },

      fetchUser: async () => {
        try {
          const response = await authApi.getMe()
          set({ user: response.data, isAuthenticated: true, isLoading: false })
        } catch {
          set({ user: null, token: null, isAuthenticated: false, isLoading: false })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        token: state.token, 
        refreshToken: state.refreshToken 
      }),
    }
  )
)
