# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: api.spec.ts >> API Endpoints Tests >> Response Headers >> content-type is correct
- Location: e2e/api.spec.ts:262:5

# Error details

```
TypeError: response.headers(...).get is not a function
```

# Test source

```ts
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
  194 |       expect([200, 201, 401]).toContain(response.status());
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
> 264 |       const contentType = response.headers().get('content-type');
      |                                              ^ TypeError: response.headers(...).get is not a function
  265 |       expect(contentType).toContain('application/json');
  266 |     });
  267 |   });
  268 | });
```