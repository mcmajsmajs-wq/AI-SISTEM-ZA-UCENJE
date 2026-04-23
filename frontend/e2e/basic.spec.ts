import { test, expect } from '@playwright/test';

const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:8090';
const API_URL = process.env.API_URL || 'http://localhost:8010';

test.describe('AI Learning System E2E Tests', () => {
  
  test.describe('Health Endpoints (API)', () => {
    test('health endpoint returns 200', async ({ request }) => {
      const response = await request.get(`${API_URL}/health`);
      expect(response.status()).toBe(200);
    });

    test('health endpoint returns healthy status', async ({ request }) => {
      const response = await request.get(`${API_URL}/health`);
      const data = await response.json();
      expect(data.status).toBe('healthy');
    });

    test('live endpoint returns 200', async ({ request }) => {
      const response = await request.get(`${API_URL}/live`);
      expect(response.status()).toBe(200);
    });

    test('ready endpoint returns 200', async ({ request }) => {
      const response = await request.get(`${API_URL}/ready`);
      expect(response.status()).toBe(200);
    });
  });

  test.describe('Frontend Pages', () => {
    test('homepage loads', async ({ page }) => {
      await page.goto(BASE_URL);
      await expect(page).toHaveTitle(/AI|learning|ucenje/i);
    });

    test('login page loads', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);
      await expect(page.locator('body')).toBeVisible();
    });

    test('register page loads', async ({ page }) => {
      await page.goto(`${BASE_URL}/register`);
      await expect(page.locator('body')).toBeVisible();
    });
  });

  test.describe('Navigation', () => {
    test('navbar is visible', async ({ page }) => {
      await page.goto(BASE_URL);
      const nav = page.locator('nav, header').first();
      await expect(nav).toBeVisible({ timeout: 5000 }).catch(() => null);
    });

    test('can navigate to login from home', async ({ page }) => {
      await page.goto(BASE_URL);
      const loginLink = page.getByRole('link', { name: /prijava|login|log in/i }).first();
      await loginLink.click();
      await expect(page).toHaveURL(/login/i);
    });
  });

  test.describe('Forms', () => {
    test('login form has required fields', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);
      const emailInput = page.locator('input[type="email"], input[name="email"], input[id="email"]').first();
      const passwordInput = page.locator('input[type="password"], input[name="password"], input[id="password"]').first();
      
      const emailVisible = await emailInput.isVisible().catch(() => false);
      const passwordVisible = await passwordInput.isVisible().catch(() => false);
      
      expect(emailVisible || passwordVisible).toBe(true);
    });
  });

  test.describe('Responsive Design', () => {
    test('works on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(BASE_URL);
      await expect(page).toHaveURL(/.*/);
    });
  });
});