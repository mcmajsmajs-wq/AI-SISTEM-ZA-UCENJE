# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: api.spec.ts >> API Endpoints Tests >> Auth Endpoints >> POST /api/v1/auth/refresh works
- Location: e2e/api.spec.ts:57:5

# Error details

```
Error: expect(received).toContain(expected) // indexOf

Expected value: 422
Received array: [200, 401]
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | const API_URL = process.env.API_URL || 'http://localhost:8010';
  4   | 
  5   | test.describe('API Endpoints Tests', () => {
  6   |   
  7   |   test.describe('Health Endpoints', () => {
  8   |     test('GET /health returns 200', async ({ request }) => {
  9   |       const response = await request.get(`${API_URL}/health`);
  10  |       expect(response.status()).toBe(200);
  11  |     });
  12  | 
  13  |     test('GET /health returns healthy status', async ({ request }) => {
  14  |       const response = await request.get(`${API_URL}/health`);
  15  |       const data = await response.json();
  16  |       expect(data.status).toBe('healthy');
  17  |     });
  18  | 
  19  |     test('GET /live returns 200', async ({ request }) => {
  20  |       const response = await request.get(`${API_URL}/live`);
  21  |       expect(response.status()).toBe(200);
  22  |     });
  23  | 
  24  |     test('GET /ready returns 200', async ({ request }) => {
  25  |       const response = await request.get(`${API_URL}/ready`);
  26  |       expect(response.status()).toBe(200);
  27  |     });
  28  |   });
  29  | 
  30  |   test.describe('Auth Endpoints', () => {
  31  |     test('POST /api/v1/auth/login works', async ({ request }) => {
  32  |       const response = await request.post(`${API_URL}/api/v1/auth/login`, {
  33  |         data: {
  34  |           username: 'test@example.com',
  35  |           password: 'TestPass123!'
  36  |         }
  37  |       });
  38  |       expect([200, 401]).toContain(response.status());
  39  |     });
  40  | 
  41  |     test('POST /api/v1/auth/register works', async ({ request }) => {
  42  |       const response = await request.post(`${API_URL}/api/v1/auth/register`, {
  43  |         data: {
  44  |           email: `test${Date.now()}@example.com`,
  45  |           password: 'TestPass123!',
  46  |           full_name: 'Test User'
  47  |         }
  48  |       });
  49  |       expect([200, 201, 400, 422]).toContain(response.status());
  50  |     });
  51  | 
  52  |     test('POST /api/v1/auth/logout works', async ({ request }) => {
  53  |       const response = await request.post(`${API_URL}/api/v1/auth/logout`);
  54  |       expect([200, 401]).toContain(response.status());
  55  |     });
  56  | 
  57  |     test('POST /api/v1/auth/refresh works', async ({ request }) => {
  58  |       const response = await request.post(`${API_URL}/api/v1/auth/refresh`, {
  59  |         data: {}
  60  |       });
> 61  |       expect([200, 401]).toContain(response.status());
      |                          ^ Error: expect(received).toContain(expected) // indexOf
  62  |     });
  63  |   });
  64  | 
  65  |   test.describe('Users Endpoints', () => {
  66  |     test('GET /api/v1/users/me requires auth', async ({ request }) => {
  67  |       const response = await request.get(`${API_URL}/api/v1/users/me`);
  68  |       expect([200, 401]).toContain(response.status());
  69  |     });
  70  | 
  71  |     test('PATCH /api/v1/users/me works with auth', async ({ request }) => {
  72  |       const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
  73  |         data: {
  74  |           username: 'test@example.com',
  75  |           password: 'TestPass123!'
  76  |         }
  77  |       });
  78  |       
  79  |       if (loginResponse.status() === 200) {
  80  |         const data = await loginResponse.json();
  81  |         const token = data.access_token;
  82  |         
  83  |         const response = await request.patch(`${API_URL}/api/v1/users/me`, {
  84  |           headers: { 'Authorization': `Bearer ${token}` },
  85  |           data: { full_name: 'Updated Name' }
  86  |         });
  87  |         expect([200, 401]).toContain(response.status());
  88  |       }
  89  |     });
  90  |   });
  91  | 
  92  |   test.describe('Documents Endpoints', () => {
  93  |     test('GET /api/v1/documents returns list', async ({ request }) => {
  94  |       const response = await request.get(`${API_URL}/api/v1/documents`);
  95  |       expect([200, 401]).toContain(response.status());
  96  |     });
  97  | 
  98  |     test('POST /api/v1/documents creates document', async ({ request }) => {
  99  |       const response = await request.post(`${API_URL}/api/v1/documents`, {
  100 |         data: { title: 'Test Document' }
  101 |       });
  102 |       expect([200, 201, 401]).toContain(response.status());
  103 |     });
  104 | 
  105 |     test('GET /api/v1/documents/:id returns document', async ({ request }) => {
  106 |       const response = await request.get(`${API_URL}/api/v1/documents/test-id`);
  107 |       expect([200, 404]).toContain(response.status());
  108 |     });
  109 | 
  110 |     test('DELETE /api/v1/documents/:id deletes document', async ({ request }) => {
  111 |       const response = await request.delete(`${API_URL}/api/v1/documents/test-id`);
  112 |       expect([200, 204, 404]).toContain(response.status());
  113 |     });
  114 |   });
  115 | 
  116 |   test.describe('Chunks Endpoints', () => {
  117 |     test('GET /api/v1/documents/:id/chunks returns chunks', async ({ request }) => {
  118 |       const response = await request.get(`${API_URL}/api/v1/documents/test-id/chunks`);
  119 |       expect([200, 404]).toContain(response.status());
  120 |     });
  121 | 
  122 |     test('PATCH /api/v1/chunks/:id updates chunk', async ({ request }) => {
  123 |       const response = await request.patch(`${API_URL}/api/v1/chunks/test-id`, {
  124 |         data: { content: 'Updated content' }
  125 |       });
  126 |       expect([200, 404]).toContain(response.status());
  127 |     });
  128 |   });
  129 | 
  130 |   test.describe('Quiz Endpoints', () => {
  131 |     test('GET /api/v1/quizzes returns list', async ({ request }) => {
  132 |       const response = await request.get(`${API_URL}/api/v1/quizzes`);
  133 |       expect([200, 401]).toContain(response.status());
  134 |     });
  135 | 
  136 |     test('POST /api/v1/quizzes/generate generates quiz', async ({ request }) => {
  137 |       const response = await request.post(`${API_URL}/api/v1/quizzes/generate`, {
  138 |         data: {
  139 |           document_id: 'test-doc',
  140 |           num_questions: 5
  141 |         }
  142 |       });
  143 |       expect([200, 201, 400, 401]).toContain(response.status());
  144 |     });
  145 | 
  146 |     test('GET /api/v1/quizzes/:id returns quiz', async ({ request }) => {
  147 |       const response = await request.get(`${API_URL}/api/v1/quizzes/test-id`);
  148 |       expect([200, 404]).toContain(response.status());
  149 |     });
  150 | 
  151 |     test('POST /api/v1/quizzes/:id/attempts starts attempt', async ({ request }) => {
  152 |       const response = await request.post(`${API_URL}/api/v1/quizzes/test-id/attempts`);
  153 |       expect([200, 201, 404]).toContain(response.status());
  154 |     });
  155 | 
  156 |     test('POST /api/v1/quizzes/:id/attempts/:attempt_id/submit submits', async ({ request }) => {
  157 |       const response = await request.post(`${API_URL}/api/v1/quizzes/test-id/attempts/test-attempt/submit`, {
  158 |         data: { answers: [] }
  159 |       });
  160 |       expect([200, 404]).toContain(response.status());
  161 |     });
```