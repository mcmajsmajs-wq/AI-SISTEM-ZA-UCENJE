# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: api.spec.ts >> API Endpoints Tests >> Study Plan Endpoints >> POST /api/v1/study-plans creates plan
- Location: e2e/api.spec.ts:187:5

# Error details

```
Error: expect(received).toContain(expected) // indexOf

Expected value: 404
Received array: [200, 201, 401]
```

# Test source

```ts
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
  162 |   });
  163 | 
  164 |   test.describe('Translation Endpoints', () => {
  165 |     test('POST /api/v1/translate translates document', async ({ request }) => {
  166 |       const response = await request.post(`${API_URL}/api/v1/translate`, {
  167 |         data: {
  168 |           document_id: 'test-doc',
  169 |           target_language: 'en'
  170 |         }
  171 |       });
  172 |       expect([200, 201, 400, 401]).toContain(response.status());
  173 |     });
  174 | 
  175 |     test('GET /api/v1/translate/status returns status', async ({ request }) => {
  176 |       const response = await request.get(`${API_URL}/api/v1/translate/status?document_id=test-doc`);
  177 |       expect([200, 401]).toContain(response.status());
  178 |     });
  179 |   });
  180 | 
  181 |   test.describe('Study Plan Endpoints', () => {
  182 |     test('GET /api/v1/study-plans returns list', async ({ request }) => {
  183 |       const response = await request.get(`${API_URL}/api/v1/study-plans`);
  184 |       expect([200, 401]).toContain(response.status());
  185 |     });
  186 | 
  187 |     test('POST /api/v1/study-plans creates plan', async ({ request }) => {
  188 |       const response = await request.post(`${API_URL}/api/v1/study-plans`, {
  189 |         data: {
  190 |           title: 'Test Plan',
  191 |           documents: []
  192 |         }
  193 |       });
> 194 |       expect([200, 201, 401]).toContain(response.status());
      |                               ^ Error: expect(received).toContain(expected) // indexOf
  195 |     });
  196 |   });
  197 | 
  198 |   test.describe('Analytics Endpoints', () => {
  199 |     test('GET /api/v1/analytics/me/overview returns overview', async ({ request }) => {
  200 |       const response = await request.get(`${API_URL}/api/v1/analytics/me/overview`);
  201 |       expect([200, 401]).toContain(response.status());
  202 |     });
  203 | 
  204 |     test('GET /api/v1/analytics/me/statistics returns stats', async ({ request }) => {
  205 |       const response = await request.get(`${API_URL}/api/v1/analytics/me/statistics`);
  206 |       expect([200, 401]).toContain(response.status());
  207 |     });
  208 | 
  209 |     test('GET /api/v1/analytics/dashboard returns dashboard', async ({ request }) => {
  210 |       const response = await request.get(`${API_URL}/api/v1/analytics/dashboard`);
  211 |       expect([200, 401]).toContain(response.status());
  212 |     });
  213 |   });
  214 | 
  215 |   test.describe('OpenAPI Documentation', () => {
  216 |     test('GET /docs returns documentation', async ({ request }) => {
  217 |       const response = await request.get(`${API_URL}/docs`);
  218 |       expect(response.status()).toBe(200);
  219 |     });
  220 | 
  221 |     test('GET /openapi.json returns schema', async ({ request }) => {
  222 |       const response = await request.get(`${API_URL}/openapi.json`);
  223 |       expect(response.status()).toBe(200);
  224 |       const data = await response.json();
  225 |       expect(data.openapi).toBeDefined();
  226 |     });
  227 |   });
  228 | 
  229 |   test.describe('Error Handling', () => {
  230 |     test('invalid endpoint returns 404', async ({ request }) => {
  231 |       const response = await request.get(`${API_URL}/api/v1/invalid-endpoint`);
  232 |       expect(response.status()).toBe(404);
  233 |     });
  234 | 
  235 |     test('invalid JSON returns validation error', async ({ request }) => {
  236 |       const response = await request.post(`${API_URL}/api/v1/auth/login`, {
  237 |         data: { invalid: 'data' }
  238 |       });
  239 |       expect([400, 422]).toContain(response.status());
  240 |     });
  241 | 
  242 |     test('rate limiting works', async ({ request }) => {
  243 |       const responses = await Promise.all(
  244 |         Array(10).fill(null).map(() => 
  245 |           request.get(`${API_URL}/health`)
  246 |         )
  247 |       );
  248 |       const statusCodes = responses.map(r => r.status());
  249 |       expect(statusCodes.every(s => s === 200)).toBe(true);
  250 |     });
  251 |   });
  252 | 
  253 |   test.describe('CORS Headers', () => {
  254 |     test('CORS headers are present', async ({ request }) => {
  255 |       const response = await request.get(`${API_URL}/health`);
  256 |       const corsHeader = response.headers().get('access-control-allow-origin');
  257 |       expect(corsHeader || '*').toBeDefined();
  258 |     });
  259 |   });
  260 | 
  261 |   test.describe('Response Headers', () => {
  262 |     test('content-type is correct', async ({ request }) => {
  263 |       const response = await request.get(`${API_URL}/health`);
  264 |       const contentType = response.headers().get('content-type');
  265 |       expect(contentType).toContain('application/json');
  266 |     });
  267 |   });
  268 | });
```