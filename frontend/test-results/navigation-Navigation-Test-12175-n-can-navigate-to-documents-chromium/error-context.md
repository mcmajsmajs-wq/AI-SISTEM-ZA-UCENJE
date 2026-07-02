# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: navigation.spec.ts >> Navigation Tests >> Main Navigation >> can navigate to documents
- Location: e2e/navigation.spec.ts:20:5

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByRole('link', { name: /dokumenti|documents/i }).first()

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
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:8090';
  4   | 
  5   | test.describe('Navigation Tests', () => {
  6   |   
  7   |   test.describe('Main Navigation', () => {
  8   |     test('navbar is visible on homepage', async ({ page }) => {
  9   |       await page.goto(BASE_URL);
  10  |       const navbar = page.locator('nav, header').first();
  11  |       await expect(navbar).toBeVisible({ timeout: 5000 });
  12  |     });
  13  | 
  14  |     test('can navigate to home', async ({ page }) => {
  15  |       await page.goto(`${BASE_URL}/documents`);
  16  |       await page.goto(BASE_URL);
  17  |       await expect(page).toHaveURL(/(\/|home|home\/)/i);
  18  |     });
  19  | 
  20  |     test('can navigate to documents', async ({ page }) => {
  21  |       await page.goto(BASE_URL);
  22  |       const docsLink = page.getByRole('link', { name: /dokumenti|documents/i }).first();
> 23  |       await docsLink.click();
      |                      ^ Error: locator.click: Test timeout of 30000ms exceeded.
  24  |       await expect(page).toHaveURL(/documents|dokumenti/i);
  25  |     });
  26  | 
  27  |     test('can navigate to quizzes', async ({ page }) => {
  28  |       await page.goto(BASE_URL);
  29  |       const quizLink = page.getByRole('link', { name: /kvizovi|quizzes/i }).first();
  30  |       await quizLink.click();
  31  |       await expect(page).toHaveURL(/quizzes|kvizovi/i);
  32  |     });
  33  | 
  34  |     test('can navigate to profile', async ({ page }) => {
  35  |       await page.goto(BASE_URL);
  36  |       const profileLink = page.getByRole('link', { name: /profil|profile/i }).first();
  37  |       await profileLink.click().catch(() => null);
  38  |       const currentUrl = page.url();
  39  |       expect(currentUrl).toBeDefined();
  40  |     });
  41  |   });
  42  | 
  43  |   test.describe('Breadcrumb Navigation', () => {
  44  |     test('breadcrumb shows current location', async ({ page }) => {
  45  |       await page.goto(`${BASE_URL}/documents`);
  46  |       const breadcrumb = page.locator('[aria-label="breadcrumb"], nav[aria-label]').first();
  47  |       const hasBreadcrumb = await breadcrumb.isVisible().catch(() => false);
  48  |       expect(hasBreadcrumb || true).toBe(true);
  49  |     });
  50  | 
  51  |     test('can navigate back via breadcrumb', async ({ page }) => {
  52  |       await page.goto(`${BASE_URL}/documents/test-doc`);
  53  |       const backLink = page.locator('a:has-text("dokumenti")').first();
  54  |       await backLink.click().catch(() => null);
  55  |       const currentUrl = page.url();
  56  |       expect(currentUrl).toContain('documents');
  57  |     });
  58  |   });
  59  | 
  60  |   test.describe('Footer Navigation', () => {
  61  |     test('footer is visible', async ({ page }) => {
  62  |       await page.goto(BASE_URL);
  63  |       const footer = page.locator('footer').first();
  64  |       const hasFooter = await footer.isVisible().catch(() => false);
  65  |       expect(hasFooter || true).toBe(true);
  66  |     });
  67  | 
  68  |     test('footer has links', async ({ page }) => {
  69  |       await page.goto(BASE_URL);
  70  |       const footerLinks = footer.locator('a');
  71  |       const linkCount = await footerLinks.count();
  72  |       expect(linkCount).toBeGreaterThanOrEqual(0);
  73  |     });
  74  |   });
  75  | 
  76  |   test.describe('Responsive Navigation', () => {
  77  |     test('mobile menu works on small screens', async ({ page }) => {
  78  |       await page.setViewportSize({ width: 375, height: 667 });
  79  |       await page.goto(BASE_URL);
  80  |       
  81  |       const menuButton = page.locator('button[aria-label="Menu"], button:has-text("☰")').first();
  82  |       const hasMenu = await menuButton.isVisible().catch(() => false);
  83  |       
  84  |       if (hasMenu) {
  85  |         await menuButton.click();
  86  |         const mobileMenu = page.locator('[role="navigation"]').first();
  87  |         await expect(mobileMenu).toBeVisible();
  88  |       }
  89  |       expect(hasMenu || true).toBe(true);
  90  |     });
  91  | 
  92  |     test('navigation works on tablet', async ({ page }) => {
  93  |       await page.setViewportSize({ width: 768, height: 1024 });
  94  |       await page.goto(BASE_URL);
  95  |       await expect(page).toHaveURL(/.*/);
  96  |     });
  97  | 
  98  |     test('navigation works on desktop', async ({ page }) => {
  99  |       await page.setViewportSize({ width: 1920, height: 1080 });
  100 |       await page.goto(BASE_URL);
  101 |       await expect(page).toHaveURL(/.*/);
  102 |     });
  103 |   });
  104 | 
  105 |   test.describe('Keyboard Navigation', () => {
  106 |     test('can navigate with keyboard', async ({ page }) => {
  107 |       await page.goto(BASE_URL);
  108 |       await page.keyboard.press('Tab');
  109 |       const focused = page.locator(':focus');
  110 |       expect(await focused.count()).toBeGreaterThan(0);
  111 |     });
  112 | 
  113 |     test('Enter key activates links', async ({ page }) => {
  114 |       await page.goto(BASE_URL);
  115 |       const docsLink = page.getByRole('link', { name: /dokumenti/i }).first();
  116 |       await docsLink.focus();
  117 |       await page.keyboard.press('Enter');
  118 |       await expect(page).toHaveURL(/documents/i);
  119 |     });
  120 |   });
  121 | 
  122 |   test.describe('URL Navigation', () => {
  123 |     test('direct URL access works', async ({ page }) => {
```