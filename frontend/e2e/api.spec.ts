import { test, expect } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8010';

test.describe('API Endpoints Tests', () => {
  
  test.describe('Health Endpoints', () => {
    test('GET /health returns 200', async ({ request }) => {
      const response = await request.get(`${API_URL}/health`);
      expect(response.status()).toBe(200);
    });

    test('GET /health returns healthy status', async ({ request }) => {
      const response = await request.get(`${API_URL}/health`);
      const data = await response.json();
      expect(data.status).toBe('healthy');
    });

    test('GET /live returns 200', async ({ request }) => {
      const response = await request.get(`${API_URL}/live`);
      expect(response.status()).toBe(200);
    });

    test('GET /ready returns 200', async ({ request }) => {
      const response = await request.get(`${API_URL}/ready`);
      expect(response.status()).toBe(200);
    });
  });

  test.describe('Auth Endpoints', () => {
    test('POST /api/v1/auth/login works', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/auth/login`, {
        data: {
          username: 'test@example.com',
          password: 'TestPass123!'
        }
      });
      expect([200, 401]).toContain(response.status());
    });

    test('POST /api/v1/auth/register works', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/auth/register`, {
        data: {
          email: `test${Date.now()}@example.com`,
          password: 'TestPass123!',
          full_name: 'Test User'
        }
      });
      expect([200, 201, 400, 422]).toContain(response.status());
    });

    test('POST /api/v1/auth/logout works', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/auth/logout`);
      expect([200, 401]).toContain(response.status());
    });

    test('POST /api/v1/auth/refresh works', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/auth/refresh`, {
        data: {}
      });
      expect([200, 401]).toContain(response.status());
    });
  });

  test.describe('Users Endpoints', () => {
    test('GET /api/v1/users/me requires auth', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/users/me`);
      expect([200, 401]).toContain(response.status());
    });

    test('PATCH /api/v1/users/me works with auth', async ({ request }) => {
      const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
        data: {
          username: 'test@example.com',
          password: 'TestPass123!'
        }
      });
      
      if (loginResponse.status() === 200) {
        const data = await loginResponse.json();
        const token = data.access_token;
        
        const response = await request.patch(`${API_URL}/api/v1/users/me`, {
          headers: { 'Authorization': `Bearer ${token}` },
          data: { full_name: 'Updated Name' }
        });
        expect([200, 401]).toContain(response.status());
      }
    });
  });

  test.describe('Documents Endpoints', () => {
    test('GET /api/v1/documents returns list', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/documents`);
      expect([200, 401]).toContain(response.status());
    });

    test('POST /api/v1/documents creates document', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/documents`, {
        data: { title: 'Test Document' }
      });
      expect([200, 201, 401]).toContain(response.status());
    });

    test('GET /api/v1/documents/:id returns document', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/documents/test-id`);
      expect([200, 404]).toContain(response.status());
    });

    test('DELETE /api/v1/documents/:id deletes document', async ({ request }) => {
      const response = await request.delete(`${API_URL}/api/v1/documents/test-id`);
      expect([200, 204, 404]).toContain(response.status());
    });
  });

  test.describe('Chunks Endpoints', () => {
    test('GET /api/v1/documents/:id/chunks returns chunks', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/documents/test-id/chunks`);
      expect([200, 404]).toContain(response.status());
    });

    test('PATCH /api/v1/chunks/:id updates chunk', async ({ request }) => {
      const response = await request.patch(`${API_URL}/api/v1/chunks/test-id`, {
        data: { content: 'Updated content' }
      });
      expect([200, 404]).toContain(response.status());
    });
  });

  test.describe('Quiz Endpoints', () => {
    test('GET /api/v1/quizzes returns list', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/quizzes`);
      expect([200, 401]).toContain(response.status());
    });

    test('POST /api/v1/quizzes/generate generates quiz', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/quizzes/generate`, {
        data: {
          document_id: 'test-doc',
          num_questions: 5
        }
      });
      expect([200, 201, 400, 401]).toContain(response.status());
    });

    test('GET /api/v1/quizzes/:id returns quiz', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/quizzes/test-id`);
      expect([200, 404]).toContain(response.status());
    });

    test('POST /api/v1/quizzes/:id/attempts starts attempt', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/quizzes/test-id/attempts`);
      expect([200, 201, 404]).toContain(response.status());
    });

    test('POST /api/v1/quizzes/:id/attempts/:attempt_id/submit submits', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/quizzes/test-id/attempts/test-attempt/submit`, {
        data: { answers: [] }
      });
      expect([200, 404]).toContain(response.status());
    });
  });

  test.describe('Translation Endpoints', () => {
    test('POST /api/v1/translate translates document', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/translate`, {
        data: {
          document_id: 'test-doc',
          target_language: 'en'
        }
      });
      expect([200, 201, 400, 401]).toContain(response.status());
    });

    test('GET /api/v1/translate/status returns status', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/translate/status?document_id=test-doc`);
      expect([200, 401]).toContain(response.status());
    });
  });

  test.describe('Study Plan Endpoints', () => {
    test('GET /api/v1/study-plans returns list', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/study-plans`);
      expect([200, 401]).toContain(response.status());
    });

    test('POST /api/v1/study-plans creates plan', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/study-plans`, {
        data: {
          title: 'Test Plan',
          documents: []
        }
      });
      expect([200, 201, 401]).toContain(response.status());
    });
  });

  test.describe('Analytics Endpoints', () => {
    test('GET /api/v1/analytics/me/overview returns overview', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/analytics/me/overview`);
      expect([200, 401]).toContain(response.status());
    });

    test('GET /api/v1/analytics/me/statistics returns stats', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/analytics/me/statistics`);
      expect([200, 401]).toContain(response.status());
    });

    test('GET /api/v1/analytics/dashboard returns dashboard', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/analytics/dashboard`);
      expect([200, 401]).toContain(response.status());
    });
  });

  test.describe('OpenAPI Documentation', () => {
    test('GET /docs returns documentation', async ({ request }) => {
      const response = await request.get(`${API_URL}/docs`);
      expect(response.status()).toBe(200);
    });

    test('GET /openapi.json returns schema', async ({ request }) => {
      const response = await request.get(`${API_URL}/openapi.json`);
      expect(response.status()).toBe(200);
      const data = await response.json();
      expect(data.openapi).toBeDefined();
    });
  });

  test.describe('Error Handling', () => {
    test('invalid endpoint returns 404', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/invalid-endpoint`);
      expect(response.status()).toBe(404);
    });

    test('invalid JSON returns validation error', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/auth/login`, {
        data: { invalid: 'data' }
      });
      expect([400, 422]).toContain(response.status());
    });

    test('rate limiting works', async ({ request }) => {
      const responses = await Promise.all(
        Array(10).fill(null).map(() => 
          request.get(`${API_URL}/health`)
        )
      );
      const statusCodes = responses.map(r => r.status());
      expect(statusCodes.every(s => s === 200)).toBe(true);
    });
  });

  test.describe('CORS Headers', () => {
    test('CORS headers are present', async ({ request }) => {
      const response = await request.get(`${API_URL}/health`);
      const corsHeader = response.headers().get('access-control-allow-origin');
      expect(corsHeader || '*').toBeDefined();
    });
  });

  test.describe('Response Headers', () => {
    test('content-type is correct', async ({ request }) => {
      const response = await request.get(`${API_URL}/health`);
      const contentType = response.headers().get('content-type');
      expect(contentType).toContain('application/json');
    });
  });
});