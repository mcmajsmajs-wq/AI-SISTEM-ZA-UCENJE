import { test, expect, type Page, type Locator } from '@playwright/test';

export const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:8090';
export const API_URL = process.env.API_URL || 'http://localhost:8010';

export async function login(page: Page, email: string = 'test@example.com', password: string = 'TestPass123!') {
  await page.goto(`${BASE_URL}/login`);
  const emailInput = page.locator('input[name="email"], input[type="email"]').first();
  const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
  const submitButton = page.locator('button[type="submit"]').first();
  
  await emailInput.fill(email);
  await passwordInput.fill(password);
  await submitButton.click();
  await page.waitForTimeout(3000);
}

export async function logout(page: Page) {
  const logoutButton = page.locator('button:has-text("odjavi"), a:has-text("odjavi")').first();
  const hasLogout = await logoutButton.isVisible().catch(() => false);
  if (hasLogout) {
    await logoutButton.click();
    await page.waitForTimeout(1000);
  }
}

export async function goToDocuments(page: Page) {
  await page.goto(`${BASE_URL}/documents`);
  await page.waitForTimeout(2000);
}

export async function goToQuizzes(page: Page) {
  await page.goto(`${BASE_URL}/quizzes`);
  await page.waitForTimeout(2000);
}

export async function goToProfile(page: Page) {
  await page.goto(`${BASE_URL}/profile`);
  await page.waitForTimeout(2000);
}

export async function waitForPageReady(page: Page, timeout: number = 5000) {
  await page.waitForLoadState('networkidle', { timeout });
}

export async function getAuthToken(page: Page, email: string, password: string): Promise<string | null> {
  const response = await page.request.post(`${API_URL}/api/v1/auth/login`, {
    data: { username: email, password }
  });
  
  if (response.status() === 200) {
    const data = await response.json();
    return data.access_token || null;
  }
  return null;
}

export function getApiHeaders(token?: string): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export const testUser = {
  email: 'test@example.com',
  password: 'TestPass123!',
  fullName: 'Test User'
};

export const testDocument = {
  title: 'Test Document',
  content: 'This is a test document for E2E testing.'
};

export const testQuiz = {
  numQuestions: 5,
  difficulty: 'medium'
};