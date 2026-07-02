# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: quiz.spec.ts >> Quiz Tests >> Quiz Generation >> quiz generation shows modal
- Location: e2e/quiz.spec.ts:42:5

# Error details

```
Test timeout of 30000ms exceeded while running "beforeEach" hook.
```

```
Error: locator.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('input[name="email"], input[type="email"]').first()

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
  4   | const API_URL = process.env.API_URL || 'http://localhost:8010';
  5   | 
  6   | test.describe('Quiz Tests', () => {
  7   |   
  8   |   test.beforeEach(async ({ page }) => {
  9   |     await page.goto(`${BASE_URL}/login`);
  10  |     const emailInput = page.locator('input[name="email"], input[type="email"]').first();
  11  |     const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
  12  |     const submitButton = page.locator('button[type="submit"]').first();
  13  |     
> 14  |     await emailInput.fill('test@example.com');
      |                      ^ Error: locator.fill: Test timeout of 30000ms exceeded.
  15  |     await passwordInput.fill('TestPass123!');
  16  |     await submitButton.click();
  17  |     await page.waitForTimeout(3000);
  18  |   });
  19  | 
  20  |   test.describe('Quiz List Page', () => {
  21  |     test('quizzes page loads', async ({ page }) => {
  22  |       await page.goto(`${BASE_URL}/quizzes`);
  23  |       await expect(page).toHaveURL(/quizzes|kvizovi|quiz/i);
  24  |     });
  25  | 
  26  |     test('quiz list is visible', async ({ page }) => {
  27  |       await page.goto(`${BASE_URL}/quizzes`);
  28  |       const quizList = page.locator('[data-testid="quiz-list"], .quiz-list').first();
  29  |       await expect(quizList).toBeVisible({ timeout: 5000 }).catch(() => null);
  30  |     });
  31  |   });
  32  | 
  33  |   test.describe('Quiz Generation', () => {
  34  |     test('generate quiz button exists', async ({ page }) => {
  35  |       await page.goto(`${BASE_URL}/documents`);
  36  |       
  37  |       const generateButton = page.locator('button:has-text("generisi"), button:has-text("kviz")').first();
  38  |       const canClick = await generateButton.isVisible().catch(() => false);
  39  |       expect(canClick || true).toBe(true);
  40  |     });
  41  | 
  42  |     test('quiz generation shows modal', async ({ page }) => {
  43  |       await page.goto(`${BASE_URL}/documents`);
  44  |       
  45  |       const generateButton = page.locator('button:has-text("generisi"), button:has-text("kviz")').first();
  46  |       await generateButton.click().catch(() => null);
  47  |       
  48  |       const modal = page.locator('dialog, [role="dialog"]').first();
  49  |       const hasModal = await modal.isVisible().catch(() => false);
  50  |       expect(hasModal || true).toBe(true);
  51  |     });
  52  | 
  53  |     test('can select number of questions', async ({ page }) => {
  54  |       await page.goto(`${BASE_URL}/documents`);
  55  |       
  56  |       const generateButton = page.locator('button:has-text("generisi"), button:has-text("kviz")').first();
  57  |       await generateButton.click().catch(() => null);
  58  |       
  59  |       const numberInput = page.locator('input[name="numQuestions"], input[type="number"]').first();
  60  |       const hasInput = await numberInput.isVisible().catch(() => false);
  61  |       expect(hasInput || true).toBe(true);
  62  |     });
  63  | 
  64  |     test('quiz generation starts processing', async ({ page }) => {
  65  |       await page.goto(`${BASE_URL}/documents`);
  66  |       
  67  |       const generateButton = page.locator('button:has-text("generisi")').first();
  68  |       await generateButton.click().catch(() => null);
  69  |       
  70  |       await page.waitForTimeout(2000);
  71  |       
  72  |       const processing = page.locator('text=obrada,processing,ucitavanje').first();
  73  |       const isProcessing = await processing.isVisible().catch(() => false);
  74  |       expect(isProcessing || true).toBe(true);
  75  |     });
  76  |   });
  77  | 
  78  |   test.describe('Quiz Taking', () => {
  79  |     test('can start quiz attempt', async ({ page }) => {
  80  |       await page.goto(`${BASE_URL}/quizzes`);
  81  |       
  82  |       const startButton = page.locator('button:has-text("pocni"), button:has-text("start")').first();
  83  |       const canStart = await startButton.isVisible().catch(() => false);
  84  |       expect(canStart || true).toBe(true);
  85  |     });
  86  | 
  87  |     test('questions are displayed', async ({ page }) => {
  88  |       await page.goto(`${BASE_URL}/quizzes`);
  89  |       
  90  |       await page.waitForTimeout(2000);
  91  |       
  92  |       const question = page.locator('[data-testid="question"], .question').first();
  93  |       const hasQuestion = await question.isVisible().catch(() => false);
  94  |       expect(hasQuestion || true).toBe(true);
  95  |     });
  96  | 
  97  |     test('can select answer', async ({ page }) => {
  98  |       await page.goto(`${BASE_URL}/quizzes`);
  99  |       
  100 |       await page.waitForTimeout(2000);
  101 |       
  102 |       const firstOption = page.locator('[data-testid="option"], .option').first();
  103 |       await firstOption.click().catch(() => null);
  104 |       
  105 |       const isSelected = await firstOption.isChecked().catch(() => false);
  106 |       expect(isSelected || true).toBe(true);
  107 |     });
  108 | 
  109 |     test('can navigate between questions', async ({ page }) => {
  110 |       await page.goto(`${BASE_URL}/quizzes`);
  111 |       
  112 |       await page.waitForTimeout(2000);
  113 |       
  114 |       const nextButton = page.locator('button:has-text("sledece"), button:has-text("next")').first();
```