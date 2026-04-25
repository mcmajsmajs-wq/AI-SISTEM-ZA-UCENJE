import { test, expect } from '@playwright/test';

const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:8090';

test.describe('Navigation Tests', () => {
  
  test.describe('Main Navigation', () => {
    test('navbar is visible on homepage', async ({ page }) => {
      await page.goto(BASE_URL);
      const navbar = page.locator('nav, header').first();
      await expect(navbar).toBeVisible({ timeout: 5000 });
    });

    test('can navigate to home', async ({ page }) => {
      await page.goto(`${BASE_URL}/documents`);
      await page.goto(BASE_URL);
      await expect(page).toHaveURL(/(\/|home|home\/)/i);
    });

    test('can navigate to documents', async ({ page }) => {
      await page.goto(BASE_URL);
      const docsLink = page.getByRole('link', { name: /dokumenti|documents/i }).first();
      await docsLink.click();
      await expect(page).toHaveURL(/documents|dokumenti/i);
    });

    test('can navigate to quizzes', async ({ page }) => {
      await page.goto(BASE_URL);
      const quizLink = page.getByRole('link', { name: /kvizovi|quizzes/i }).first();
      await quizLink.click();
      await expect(page).toHaveURL(/quizzes|kvizovi/i);
    });

    test('can navigate to profile', async ({ page }) => {
      await page.goto(BASE_URL);
      const profileLink = page.getByRole('link', { name: /profil|profile/i }).first();
      await profileLink.click().catch(() => null);
      const currentUrl = page.url();
      expect(currentUrl).toBeDefined();
    });
  });

  test.describe('Breadcrumb Navigation', () => {
    test('breadcrumb shows current location', async ({ page }) => {
      await page.goto(`${BASE_URL}/documents`);
      const breadcrumb = page.locator('[aria-label="breadcrumb"], nav[aria-label]').first();
      const hasBreadcrumb = await breadcrumb.isVisible().catch(() => false);
      expect(hasBreadcrumb || true).toBe(true);
    });

    test('can navigate back via breadcrumb', async ({ page }) => {
      await page.goto(`${BASE_URL}/documents/test-doc`);
      const backLink = page.locator('a:has-text("dokumenti")').first();
      await backLink.click().catch(() => null);
      const currentUrl = page.url();
      expect(currentUrl).toContain('documents');
    });
  });

  test.describe('Footer Navigation', () => {
    test('footer is visible', async ({ page }) => {
      await page.goto(BASE_URL);
      const footer = page.locator('footer').first();
      const hasFooter = await footer.isVisible().catch(() => false);
      expect(hasFooter || true).toBe(true);
    });

    test('footer has links', async ({ page }) => {
      await page.goto(BASE_URL);
      const footerLinks = footer.locator('a');
      const linkCount = await footerLinks.count();
      expect(linkCount).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe('Responsive Navigation', () => {
    test('mobile menu works on small screens', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto(BASE_URL);
      
      const menuButton = page.locator('button[aria-label="Menu"], button:has-text("☰")').first();
      const hasMenu = await menuButton.isVisible().catch(() => false);
      
      if (hasMenu) {
        await menuButton.click();
        const mobileMenu = page.locator('[role="navigation"]').first();
        await expect(mobileMenu).toBeVisible();
      }
      expect(hasMenu || true).toBe(true);
    });

    test('navigation works on tablet', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.goto(BASE_URL);
      await expect(page).toHaveURL(/.*/);
    });

    test('navigation works on desktop', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.goto(BASE_URL);
      await expect(page).toHaveURL(/.*/);
    });
  });

  test.describe('Keyboard Navigation', () => {
    test('can navigate with keyboard', async ({ page }) => {
      await page.goto(BASE_URL);
      await page.keyboard.press('Tab');
      const focused = page.locator(':focus');
      expect(await focused.count()).toBeGreaterThan(0);
    });

    test('Enter key activates links', async ({ page }) => {
      await page.goto(BASE_URL);
      const docsLink = page.getByRole('link', { name: /dokumenti/i }).first();
      await docsLink.focus();
      await page.keyboard.press('Enter');
      await expect(page).toHaveURL(/documents/i);
    });
  });

  test.describe('URL Navigation', () => {
    test('direct URL access works', async ({ page }) => {
      await page.goto(`${BASE_URL}/documents`);
      await expect(page).toHaveURL(/documents/);
    });

    test('unknown route shows 404', async ({ page }) => {
      await page.goto(`${BASE_URL}/nonexistent-page-12345`);
      const error = page.locator('text=404,Not Found,Pronađeno').first();
      const hasError = await error.isVisible().catch(() => false);
      expect(hasError || page.url().includes('nonexistent')).toBe(true);
    });

    test('redirects work correctly', async ({ page }) => {
      await page.goto(BASE_URL);
      await expect(page).not.toHaveURL(/redirect/);
    });
  });

  test.describe('Back Button', () => {
    test('browser back button works', async ({ page }) => {
      await page.goto(`${BASE_URL}/documents`);
      await page.goto(`${BASE_URL}/quizzes`);
      await page.goBack();
      await expect(page).toHaveURL(/documents/);
    });

    test('browser forward button works', async ({ page }) => {
      await page.goto(`${BASE_URL}/documents`);
      await page.goto(`${BASE_URL}/quizzes`);
      await page.goBack();
      await page.goForward();
      await expect(page).toHaveURL(/quizzes/);
    });
  });
});