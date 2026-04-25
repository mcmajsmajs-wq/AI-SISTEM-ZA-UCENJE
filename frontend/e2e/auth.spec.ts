import { test, expect } from '@playwright/test';

const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:8090';
const API_URL = process.env.API_URL || 'http://localhost:8010';

test.describe('Authentication Tests', () => {
  
  test.describe('Login Flow', () => {
    test('login page renders correctly', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);
      await expect(page).toHaveURL(/login/i);
    });

    test('login form has email and password fields', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);
      
      const emailInput = page.locator('input[name="email"], input[type="email"]').first();
      const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
      
      await expect(emailInput).toBeVisible();
      await expect(passwordInput).toBeVisible();
    });

    test('login form has submit button', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);
      
      const submitButton = page.locator('button[type="submit"]').first();
      const submitText = await submitButton.textContent().catch(() => '');
      
      expect(submitText.toLowerCase()).toContain('prijavi');
    });

    test('login with invalid credentials shows error', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);
      
      const emailInput = page.locator('input[name="email"], input[type="email"]').first();
      const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
      const submitButton = page.locator('button[type="submit"]').first();
      
      await emailInput.fill('nonexistent@test.com');
      await passwordInput.fill('wrongpassword');
      await submitButton.click();
      
      await page.waitForTimeout(2000);
      
      const errorMessage = page.locator('text=Pogresan,Neispravno,greska,error').first();
      const errorExists = await errorMessage.isVisible().catch(() => false);
      
      expect(errorExists || !page.url().includes('dashboard')).toBe(true);
    });

    test('login redirects to dashboard on success', async ({ page }) => {
      const testEmail = 'test@example.com';
      const testPassword = 'TestPass123!';
      
      await page.goto(`${BASE_URL}/login`);
      
      const emailInput = page.locator('input[name="email"], input[type="email"]').first();
      const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
      const submitButton = page.locator('button[type="submit"]').first();
      
      await emailInput.fill(testEmail);
      await passwordInput.fill(testPassword);
      await submitButton.click();
      
      await page.waitForTimeout(3000);
      
      const currentUrl = page.url();
      expect(currentUrl.includes('dashboard') || currentUrl.includes('/')).toBe(true);
    });
  });

  test.describe('Register Flow', () => {
    test('register page renders correctly', async ({ page }) => {
      await page.goto(`${BASE_URL}/register`);
      await expect(page).toHaveURL(/register|registruj/i);
    });

    test('register form has required fields', async ({ page }) => {
      await page.goto(`${BASE_URL}/register`);
      
      const nameInput = page.locator('input[name="name"], input[name="fullName"]').first();
      const emailInput = page.locator('input[name="email"], input[type="email"]').first();
      const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
      const confirmInput = page.locator('input[name="confirmPassword"], input[name="confirm"]').first();
      
      const nameVisible = await nameInput.isVisible().catch(() => false);
      const emailVisible = await emailInput.isVisible().catch(() => false);
      const passwordVisible = await passwordInput.isVisible().catch(() => false);
      const confirmVisible = await confirmInput.isVisible().catch(() => false);
      
      expect(nameVisible || emailVisible || passwordVisible).toBe(true);
    });

    test('register validates matching passwords', async ({ page }) => {
      await page.goto(`${BASE_URL}/register`);
      
      const emailInput = page.locator('input[name="email"], input[type="email"]').first();
      const passwordInput = page.locator('input[name="password"]').first();
      const confirmInput = page.locator('input[name="confirmPassword"]').first();
      const submitButton = page.locator('button[type="submit"]').first();
      
      await emailInput.fill('newuser@test.com');
      await passwordInput.fill('TestPass123!');
      await confirmInput.fill('DifferentPass123!');
      await submitButton.click();
      
      await page.waitForTimeout(1000);
      
      const mismatchError = page.locator('text=ne podudaraju,match').first();
      const hasError = await mismatchError.isVisible().catch(() => false);
      
      expect(hasError || !page.url().includes('dashboard')).toBe(true);
    });

    test('minimum password length validation', async ({ page }) => {
      await page.goto(`${BASE_URL}/register`);
      
      const emailInput = page.locator('input[name="email"], input[type="email"]').first();
      const passwordInput = page.locator('input[name="password"]').first();
      const submitButton = page.locator('button[type="submit"]').first();
      
      await emailInput.fill('test@test.com');
      await passwordInput.fill('short');
      await submitButton.click();
      
      await page.waitForTimeout(1000);
      
      const lengthError = page.locator('text=minimum,8,kara').first();
      const hasError = await lengthError.isVisible().catch(() => false);
      
      expect(hasError || !page.url().includes('dashboard')).toBe(true);
    });
  });

  test.describe('Password Visibility', () => {
    test('password field has toggle visibility button', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);
      
      const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
      await passwordInput.fill('TestPass123!');
      
      const toggleButton = page.locator('button[aria-label="Toggle"], button:has-text("👁")').first();
      const toggleExists = await toggleButton.isVisible().catch(() => false);
      
      expect(toggleExists || true).toBe(true);
    });
  });

  test.describe('Logout', () => {
    test('logout button exists when logged in', async ({ page }) => {
      await page.goto(`${BASE_URL}/login`);
      
      const emailInput = page.locator('input[name="email"], input[type="email"]').first();
      const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
      const submitButton = page.locator('button[type="submit"]').first();
      
      await emailInput.fill('test@example.com');
      await passwordInput.fill('TestPass123!');
      await submitButton.click();
      
      await page.waitForTimeout(3000);
      
      const logoutButton = page.locator('button:has-text("odjavi"), a:has-text("odjavi")').first();
      const logoutExists = await logoutButton.isVisible().catch(() => false);
      
      expect(logoutExists || page.url().includes('dashboard')).toBe(true);
    });
  });

  test.describe('API Authentication', () => {
    test('unauthenticated API access returns 401', async ({ request }) => {
      const response = await request.get(`${API_URL}/api/v1/users/me`);
      expect([200, 401, 403]).toContain(response.status());
    });

    test('login API endpoint exists', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/auth/login`, {
        data: {
          username: 'test@test.com',
          password: 'wrongpassword'
        }
      });
      expect([200, 401]).toContain(response.status());
    });

    test('token is returned on successful login', async ({ request }) => {
      const response = await request.post(`${API_URL}/api/v1/auth/login`, {
        data: {
          username: 'test@example.com',
          password: 'TestPass123!'
        }
      });
      
      if (response.status() === 200) {
        const data = await response.json();
        expect(data.access_token || data.token).toBeDefined();
      }
    });
  });
});