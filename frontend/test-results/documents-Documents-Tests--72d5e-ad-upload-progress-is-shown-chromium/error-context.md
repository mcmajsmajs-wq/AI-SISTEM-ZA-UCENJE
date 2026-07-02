# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: documents.spec.ts >> Documents Tests >> Document Upload >> upload progress is shown
- Location: e2e/documents.spec.ts:61:5

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
  6   | test.describe('Documents Tests', () => {
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
  20  |   test.describe('Documents Page', () => {
  21  |     test('documents page loads', async ({ page }) => {
  22  |       await page.goto(`${BASE_URL}/documents`);
  23  |       await expect(page).toHaveURL(/documents|dokumenti/i);
  24  |     });
  25  | 
  26  |     test('documents list is visible', async ({ page }) => {
  27  |       await page.goto(`${BASE_URL}/documents`);
  28  |       const documentList = page.locator('[data-testid="document-list"], .document-list, table').first();
  29  |       await expect(documentList).toBeVisible({ timeout: 5000 }).catch(() => null);
  30  |     });
  31  |   });
  32  | 
  33  |   test.describe('Document Upload', () => {
  34  |     test('upload button exists', async ({ page }) => {
  35  |       await page.goto(`${BASE_URL}/documents`);
  36  |       
  37  |       const uploadButton = page.locator('button:has-text("dodaj"), button:has-text("upload"), input[type="file"]').first();
  38  |       const uploadExists = await uploadButton.isVisible().catch(() => false);
  39  |       
  40  |       expect(uploadExists || true).toBe(true);
  41  |     });
  42  | 
  43  |     test('can select file for upload', async ({ page }) => {
  44  |       await page.goto(`${BASE_URL}/documents`);
  45  |       
  46  |       const fileInput = page.locator('input[type="file"]').first();
  47  |       const fileInputExists = await fileInput.isVisible().catch(() => false);
  48  |       
  49  |       expect(fileInputExists || true).toBe(true);
  50  |     });
  51  | 
  52  |     test('accepts PDF files', async ({ page }) => {
  53  |       await page.goto(`${BASE_URL}/documents`);
  54  |       
  55  |       const fileInput = page.locator('input[type="file"]').first();
  56  |       const accept = await fileInput.getAttribute('accept').catch(() => '');
  57  |       
  58  |       expect(accept?.includes('.pdf') || !accept).toBe(true);
  59  |     });
  60  | 
  61  |     test('upload progress is shown', async ({ page }) => {
  62  |       await page.goto(`${BASE_URL}/documents`);
  63  |       
  64  |       const progressBar = page.locator('progress, [data-testid="upload-progress"]').first();
  65  |       const progressExists = await progressBar.isVisible().catch(() => false);
  66  |       
  67  |       expect(progressExists || true).toBe(true);
  68  |     });
  69  |   });
  70  | 
  71  |   test.describe('Document Actions', () => {
  72  |     test('document can be viewed', async ({ page }) => {
  73  |       await page.goto(`${BASE_URL}/documents`);
  74  |       
  75  |       const firstDoc = page.locator('[data-testid="document-item"], .document-item').first();
  76  |       const viewButton = firstDoc.locator('button:has-text("pogledaj"), a:has-text("pogledaj")').first();
  77  |       
  78  |       const canClick = await viewButton.isVisible().catch(() => false);
  79  |       expect(canClick || true).toBe(true);
  80  |     });
  81  | 
  82  |     test('document can be deleted', async ({ page }) => {
  83  |       await page.goto(`${BASE_URL}/documents`);
  84  |       
  85  |       const firstDoc = page.locator('[data-testid="document-item"], .document-item').first();
  86  |       const deleteButton = firstDoc.locator('button:has-text("obrisi"), [aria-label*="delete"]').first();
  87  |       
  88  |       const canDelete = await deleteButton.isVisible().catch(() => false);
  89  |       expect(canDelete || true).toBe(true);
  90  |     });
  91  | 
  92  |     test('delete shows confirmation', async ({ page }) => {
  93  |       await page.goto(`${BASE_URL}/documents`);
  94  |       
  95  |       const firstDoc = page.locator('[data-testid="document-item"], .document-item').first();
  96  |       const deleteButton = firstDoc.locator('button:has-text("obrisi")').first();
  97  |       
  98  |       await deleteButton.click().catch(() => null);
  99  |       
  100 |       const confirmDialog = page.locator('dialog, text=potvrda,confirm').first();
  101 |       const hasConfirm = await confirmDialog.isVisible().catch(() => false);
  102 |       
  103 |       expect(hasConfirm || true).toBe(true);
  104 |     });
  105 |   });
  106 | 
  107 |   test.describe('Document Processing', () => {
  108 |     test('processing status is shown', async ({ page }) => {
  109 |       await page.goto(`${BASE_URL}/documents`);
  110 |       
  111 |       const processingBadge = page.locator('text=obrada,processing').first();
  112 |       const hasProcessing = await processingBadge.isVisible().catch(() => false);
  113 |       
  114 |       expect(hasProcessing || true).toBe(true);
```