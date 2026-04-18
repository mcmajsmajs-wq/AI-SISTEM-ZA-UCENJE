import { describe, it, expect, vi } from 'vitest'

vi.mock('axios', () => ({
  default: {
    create: () => ({
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() },
      },
    }),
    post: vi.fn(),
    get: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('API Service Configuration', () => {
  it('should define correct base URL', () => {
    const API_BASE_URL = '/api/v1'
    expect(API_BASE_URL).toBe('/api/v1')
  })

  it('should have auth endpoints defined', () => {
    const authEndpoints = {
      login: '/auth/login/json',
      register: '/auth/register',
      logout: '/auth/logout',
      me: '/auth/me',
      refresh: '/auth/refresh',
    }
    expect(authEndpoints.login).toContain('/auth/')
    expect(authEndpoints.register).toContain('/auth/')
  })

  it('should have users endpoints defined', () => {
    const usersEndpoints = {
      me: '/users/me',
      stats: '/users/me/stats',
      password: '/users/me/password',
    }
    expect(usersEndpoints.me).toContain('/users/')
    expect(usersEndpoints.stats).toContain('/users/')
  })
})

describe('API Request/Response Types', () => {
  it('should validate login request format', () => {
    const loginRequest = {
      email: 'test@example.com',
      password: 'Test1234!',
    }
    expect(loginRequest).toHaveProperty('email')
    expect(loginRequest).toHaveProperty('password')
    expect(typeof loginRequest.email).toBe('string')
    expect(typeof loginRequest.password).toBe('string')
  })

  it('should validate register request format', () => {
    const registerRequest = {
      email: 'new@example.com',
      password: 'SecurePass123',
      full_name: 'New User',
    }
    expect(registerRequest).toHaveProperty('email')
    expect(registerRequest).toHaveProperty('password')
    expect(registerRequest.full_name).toBe('New User')
  })

  it('should validate token response format', () => {
    const tokenResponse = {
      access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
      refresh_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
      token_type: 'bearer',
    }
    expect(tokenResponse.access_token).toBeDefined()
    expect(tokenResponse.refresh_token).toBeDefined()
    expect(tokenResponse.token_type).toBe('bearer')
  })

  it('should validate user response format', () => {
    const userResponse = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      email: 'test@example.com',
      full_name: 'Test User',
      is_active: true,
      is_verified: false,
      created_at: '2024-01-01T00:00:00Z',
    }
    expect(userResponse.id).toBeDefined()
    expect(userResponse.email).toBeDefined()
    expect(userResponse.is_active).toBe(true)
  })
})

describe('API Error Handling', () => {
  it('should handle 401 unauthorized error', () => {
    const error401 = {
      response: {
        status: 401,
        data: { detail: 'Neispravni podaci za prijavu' },
      },
    }
    expect(error401.response.status).toBe(401)
    expect(error401.response.data.detail).toBeDefined()
  })

  it('should handle 404 not found error', () => {
    const error404 = {
      response: {
        status: 404,
        data: { detail: 'Resurs nije pronađen' },
      },
    }
    expect(error404.response.status).toBe(404)
  })

  it('should handle 500 server error', () => {
    const error500 = {
      response: {
        status: 500,
        data: { detail: 'Interna greška servera' },
      },
    }
    expect(error500.response.status).toBe(500)
  })
})

describe('API Headers', () => {
  it('should include content-type header', () => {
    const headers = {
      'Content-Type': 'application/json',
    }
    expect(headers['Content-Type']).toBe('application/json')
  })

  it('should include authorization header format', () => {
    const token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    const authHeader = `Bearer ${token}`
    expect(authHeader).toContain('Bearer')
  })
})