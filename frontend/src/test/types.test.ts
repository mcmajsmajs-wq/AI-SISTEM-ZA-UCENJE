import { describe, it, expect } from 'vitest'

describe('Types', () => {
  describe('User', () => {
    it('should have correct user interface structure', () => {
      const user = {
        id: '123',
        email: 'test@test.com',
        full_name: 'Test User',
        is_active: true,
        is_verified: false,
        created_at: '2024-01-01',
      }
      expect(user.id).toBe('123')
      expect(user.email).toBe('test@test.com')
    })

    it('should allow optional fields', () => {
      const user = {
        id: '456',
        email: 'minimal@test.com',
        full_name: null,
        is_active: true,
        is_verified: true,
        created_at: '2024-01-01',
      }
      expect(user.full_name).toBeNull()
    })
  })

  describe('Token', () => {
    it('should have correct token interface', () => {
      const token = {
        access_token: 'access-token-123',
        refresh_token: 'refresh-token-456',
        token_type: 'bearer',
      }
      expect(token.access_token).toContain('access-token')
      expect(token.refresh_token).toContain('refresh-token')
    })
  })

  describe('LoginCredentials', () => {
    it('should have correct login credentials interface', () => {
      const credentials = {
        username: 'test@example.com',
        password: 'password123',
      }
      expect(credentials.username).toBe('test@example.com')
      expect(credentials.password).toBe('password123')
    })
  })

  describe('RegisterData', () => {
    it('should have correct register data interface', () => {
      const data = {
        email: 'new@example.com',
        password: 'password123',
        full_name: 'New User',
      }
      expect(data.email).toBe('new@example.com')
      expect(data.full_name).toBe('New User')
    })

    it('should allow optional full_name', () => {
      const data: { email: string; password: string; full_name?: string } = {
        email: 'minimal@example.com',
        password: 'pass123',
      }
      expect(data.full_name).toBeUndefined()
    })
  })

  describe('UserStats', () => {
    it('should have correct user stats interface', () => {
      const stats = {
        total_documents: 10,
        total_chunks: 500,
        translated_chunks: 250,
        total_quizzes: 5,
        average_score: 85.5,
        study_streak: 3,
      }
      expect(stats.total_documents).toBe(10)
      expect(stats.study_streak).toBe(3)
    })
  })
})

describe('Utility Functions', () => {
  describe('Email validation', () => {
    const isValidEmail = (email: string): boolean => {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      return emailRegex.test(email)
    }

    it('should validate correct email', () => {
      expect(isValidEmail('test@example.com')).toBe(true)
      expect(isValidEmail('user@domain.org')).toBe(true)
    })

    it('should reject invalid email', () => {
      expect(isValidEmail('invalid')).toBe(false)
      expect(isValidEmail('no@domain')).toBe(false)
      expect(isValidEmail('')).toBe(false)
    })
  })

  describe('Password strength', () => {
    const isStrongPassword = (password: string): boolean => {
      return password.length >= 8 && 
             /[A-Z]/.test(password) && 
             /[0-9]/.test(password)
    }

    it('should validate strong passwords', () => {
      expect(isStrongPassword('Password123')).toBe(true)
      expect(isStrongPassword('Secure1234')).toBe(true)
    })

    it('should reject weak passwords', () => {
      expect(isStrongPassword('short')).toBe(false)
      expect(isStrongPassword('alllowercase')).toBe(false)
      expect(isStrongPassword('ALLUPPERCASE')).toBe(false)
    })
  })

  describe('Date formatting', () => {
    const formatDate = (date: string): string => {
      return new Date(date).toLocaleDateString('sr-RS').replace(/\.$/, '')
    }

    it('should format date correctly', () => {
      expect(formatDate('2024-01-01')).toBe('1. 1. 2024')
    })
  })
})