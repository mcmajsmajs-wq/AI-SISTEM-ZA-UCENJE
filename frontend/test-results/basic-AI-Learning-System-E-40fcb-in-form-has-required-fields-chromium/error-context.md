# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: basic.spec.ts >> AI Learning System E2E Tests >> Forms >> login form has required fields
- Location: e2e/basic.spec.ts:64:5

# Error details

```
Error: expect(received).toBe(expected) // Object.is equality

Expected: true
Received: false
```

# Page snapshot

```yaml
- main [ref=e7]:
  - generic [ref=e10]:
    - generic [ref=e12]:
      - generic [ref=e13]:
        - img "Grafana" [ref=e14]
        - heading "Welcome to Grafana" [level=1] [ref=e16]
      - generic [ref=e20]:
        - generic [ref=e21]:
          - generic [ref=e24]: Email or username
          - textbox "Email or username" [active] [ref=e29]:
            - /placeholder: email or username
        - generic [ref=e30]:
          - generic [ref=e33]: Password
          - generic [ref=e37]:
            - textbox "Password" [ref=e38]:
              - /placeholder: password
            - switch "Show password" [ref=e40] [cursor=pointer]:
              - img [ref=e41]
        - button "Log in" [ref=e43] [cursor=pointer]:
          - generic [ref=e44]: Log in
        - link "Forgot your password?" [ref=e46] [cursor=pointer]:
          - /url: /user/password/send-reset-email
          - generic [ref=e47]: Forgot your password?
    - list [ref=e50]:
      - listitem [ref=e51]:
        - img [ref=e52]
        - link "Documentation" [ref=e54] [cursor=pointer]:
          - /url: https://grafana.com/docs/grafana/latest/?utm_source=grafana_footer
        - text: "|"
      - listitem [ref=e55]:
        - img [ref=e56]
        - link "Support" [ref=e58] [cursor=pointer]:
          - /url: https://grafana.com/products/enterprise/?utm_source=grafana_footer
        - text: "|"
      - listitem [ref=e59]:
        - img [ref=e60]
        - link "Community" [ref=e62] [cursor=pointer]:
          - /url: https://community.grafana.com/?utm_source=grafana_footer
        - text: "|"
      - listitem [ref=e63]:
        - link "Open Source" [ref=e64] [cursor=pointer]:
          - /url: https://grafana.com/oss/grafana?utm_source=grafana_footer
        - text: "|"
      - listitem [ref=e65]:
        - link "Grafana v12.4.0 (d1729c53a7)" [ref=e66] [cursor=pointer]:
          - /url: https://github.com/grafana/grafana/blob/main/CHANGELOG.md
        - text: "|"
      - listitem [ref=e67]:
        - img [ref=e68]
        - link "New version available!" [ref=e70] [cursor=pointer]:
          - /url: https://grafana.com/grafana/download?utm_source=grafana_footer
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:8090';
  4  | const API_URL = process.env.API_URL || 'http://localhost:8010';
  5  | 
  6  | test.describe('AI Learning System E2E Tests', () => {
  7  |   
  8  |   test.describe('Health Endpoints (API)', () => {
  9  |     test('health endpoint returns 200', async ({ request }) => {
  10 |       const response = await request.get(`${API_URL}/health`);
  11 |       expect(response.status()).toBe(200);
  12 |     });
  13 | 
  14 |     test('health endpoint returns healthy status', async ({ request }) => {
  15 |       const response = await request.get(`${API_URL}/health`);
  16 |       const data = await response.json();
  17 |       expect(data.status).toBe('healthy');
  18 |     });
  19 | 
  20 |     test('live endpoint returns 200', async ({ request }) => {
  21 |       const response = await request.get(`${API_URL}/live`);
  22 |       expect(response.status()).toBe(200);
  23 |     });
  24 | 
  25 |     test('ready endpoint returns 200', async ({ request }) => {
  26 |       const response = await request.get(`${API_URL}/ready`);
  27 |       expect(response.status()).toBe(200);
  28 |     });
  29 |   });
  30 | 
  31 |   test.describe('Frontend Pages', () => {
  32 |     test('homepage loads', async ({ page }) => {
  33 |       await page.goto(BASE_URL);
  34 |       await expect(page).toHaveTitle(/AI|learning|ucenje/i);
  35 |     });
  36 | 
  37 |     test('login page loads', async ({ page }) => {
  38 |       await page.goto(`${BASE_URL}/login`);
  39 |       await expect(page.locator('body')).toBeVisible();
  40 |     });
  41 | 
  42 |     test('register page loads', async ({ page }) => {
  43 |       await page.goto(`${BASE_URL}/register`);
  44 |       await expect(page.locator('body')).toBeVisible();
  45 |     });
  46 |   });
  47 | 
  48 |   test.describe('Navigation', () => {
  49 |     test('navbar is visible', async ({ page }) => {
  50 |       await page.goto(BASE_URL);
  51 |       const nav = page.locator('nav, header').first();
  52 |       await expect(nav).toBeVisible({ timeout: 5000 }).catch(() => null);
  53 |     });
  54 | 
  55 |     test('can navigate to login from home', async ({ page }) => {
  56 |       await page.goto(BASE_URL);
  57 |       const loginLink = page.getByRole('link', { name: /prijava|login|log in/i }).first();
  58 |       await loginLink.click();
  59 |       await expect(page).toHaveURL(/login/i);
  60 |     });
  61 |   });
  62 | 
  63 |   test.describe('Forms', () => {
  64 |     test('login form has required fields', async ({ page }) => {
  65 |       await page.goto(`${BASE_URL}/login`);
  66 |       const emailInput = page.locator('input[type="email"], input[name="email"], input[id="email"]').first();
  67 |       const passwordInput = page.locator('input[type="password"], input[name="password"], input[id="password"]').first();
  68 |       
  69 |       const emailVisible = await emailInput.isVisible().catch(() => false);
  70 |       const passwordVisible = await passwordInput.isVisible().catch(() => false);
  71 |       
> 72 |       expect(emailVisible || passwordVisible).toBe(true);
     |                                               ^ Error: expect(received).toBe(expected) // Object.is equality
  73 |     });
  74 |   });
  75 | 
  76 |   test.describe('Responsive Design', () => {
  77 |     test('works on mobile viewport', async ({ page }) => {
  78 |       await page.setViewportSize({ width: 375, height: 667 });
  79 |       await page.goto(BASE_URL);
  80 |       await expect(page).toHaveURL(/.*/);
  81 |     });
  82 |   });
  83 | });
```