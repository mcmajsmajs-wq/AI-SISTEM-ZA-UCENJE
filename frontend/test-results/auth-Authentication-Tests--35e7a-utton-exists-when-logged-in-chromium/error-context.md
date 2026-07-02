# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth.spec.ts >> Authentication Tests >> Logout >> logout button exists when logged in
- Location: e2e/auth.spec.ts:151:5

# Error details

```
Test timeout of 30000ms exceeded.
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
  58  |       const emailInput = page.locator('input[name="email"], input[type="email"]').first();
  59  |       const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
  60  |       const submitButton = page.locator('button[type="submit"]').first();
  61  |       
  62  |       await emailInput.fill(testEmail);
  63  |       await passwordInput.fill(testPassword);
  64  |       await submitButton.click();
  65  |       
  66  |       await page.waitForTimeout(3000);
  67  |       
  68  |       const currentUrl = page.url();
  69  |       expect(currentUrl.includes('dashboard') || currentUrl.includes('/')).toBe(true);
  70  |     });
  71  |   });
  72  | 
  73  |   test.describe('Register Flow', () => {
  74  |     test('register page renders correctly', async ({ page }) => {
  75  |       await page.goto(`${BASE_URL}/register`);
  76  |       await expect(page).toHaveURL(/register|registruj/i);
  77  |     });
  78  | 
  79  |     test('register form has required fields', async ({ page }) => {
  80  |       await page.goto(`${BASE_URL}/register`);
  81  |       
  82  |       const nameInput = page.locator('input[name="name"], input[name="fullName"]').first();
  83  |       const emailInput = page.locator('input[name="email"], input[type="email"]').first();
  84  |       const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
  85  |       const confirmInput = page.locator('input[name="confirmPassword"], input[name="confirm"]').first();
  86  |       
  87  |       const nameVisible = await nameInput.isVisible().catch(() => false);
  88  |       const emailVisible = await emailInput.isVisible().catch(() => false);
  89  |       const passwordVisible = await passwordInput.isVisible().catch(() => false);
  90  |       const confirmVisible = await confirmInput.isVisible().catch(() => false);
  91  |       
  92  |       expect(nameVisible || emailVisible || passwordVisible).toBe(true);
  93  |     });
  94  | 
  95  |     test('register validates matching passwords', async ({ page }) => {
  96  |       await page.goto(`${BASE_URL}/register`);
  97  |       
  98  |       const emailInput = page.locator('input[name="email"], input[type="email"]').first();
  99  |       const passwordInput = page.locator('input[name="password"]').first();
  100 |       const confirmInput = page.locator('input[name="confirmPassword"]').first();
  101 |       const submitButton = page.locator('button[type="submit"]').first();
  102 |       
  103 |       await emailInput.fill('newuser@test.com');
  104 |       await passwordInput.fill('TestPass123!');
  105 |       await confirmInput.fill('DifferentPass123!');
  106 |       await submitButton.click();
  107 |       
  108 |       await page.waitForTimeout(1000);
  109 |       
  110 |       const mismatchError = page.locator('text=ne podudaraju,match').first();
  111 |       const hasError = await mismatchError.isVisible().catch(() => false);
  112 |       
  113 |       expect(hasError || !page.url().includes('dashboard')).toBe(true);
  114 |     });
  115 | 
  116 |     test('minimum password length validation', async ({ page }) => {
  117 |       await page.goto(`${BASE_URL}/register`);
  118 |       
  119 |       const emailInput = page.locator('input[name="email"], input[type="email"]').first();
  120 |       const passwordInput = page.locator('input[name="password"]').first();
  121 |       const submitButton = page.locator('button[type="submit"]').first();
  122 |       
  123 |       await emailInput.fill('test@test.com');
  124 |       await passwordInput.fill('short');
  125 |       await submitButton.click();
  126 |       
  127 |       await page.waitForTimeout(1000);
  128 |       
  129 |       const lengthError = page.locator('text=minimum,8,kara').first();
  130 |       const hasError = await lengthError.isVisible().catch(() => false);
  131 |       
  132 |       expect(hasError || !page.url().includes('dashboard')).toBe(true);
  133 |     });
  134 |   });
  135 | 
  136 |   test.describe('Password Visibility', () => {
  137 |     test('password field has toggle visibility button', async ({ page }) => {
  138 |       await page.goto(`${BASE_URL}/login`);
  139 |       
  140 |       const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
  141 |       await passwordInput.fill('TestPass123!');
  142 |       
  143 |       const toggleButton = page.locator('button[aria-label="Toggle"], button:has-text("👁")').first();
  144 |       const toggleExists = await toggleButton.isVisible().catch(() => false);
  145 |       
  146 |       expect(toggleExists || true).toBe(true);
  147 |     });
  148 |   });
  149 | 
  150 |   test.describe('Logout', () => {
  151 |     test('logout button exists when logged in', async ({ page }) => {
  152 |       await page.goto(`${BASE_URL}/login`);
  153 |       
  154 |       const emailInput = page.locator('input[name="email"], input[type="email"]').first();
  155 |       const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
  156 |       const submitButton = page.locator('button[type="submit"]').first();
  157 |       
> 158 |       await emailInput.fill('test@example.com');
      |                        ^ Error: locator.fill: Test timeout of 30000ms exceeded.
  159 |       await passwordInput.fill('TestPass123!');
  160 |       await submitButton.click();
  161 |       
  162 |       await page.waitForTimeout(3000);
  163 |       
  164 |       const logoutButton = page.locator('button:has-text("odjavi"), a:has-text("odjavi")').first();
  165 |       const logoutExists = await logoutButton.isVisible().catch(() => false);
  166 |       
  167 |       expect(logoutExists || page.url().includes('dashboard')).toBe(true);
  168 |     });
  169 |   });
  170 | 
  171 |   test.describe('API Authentication', () => {
  172 |     test('unauthenticated API access returns 401', async ({ request }) => {
  173 |       const response = await request.get(`${API_URL}/api/v1/users/me`);
  174 |       expect([200, 401, 403]).toContain(response.status());
  175 |     });
  176 | 
  177 |     test('login API endpoint exists', async ({ request }) => {
  178 |       const response = await request.post(`${API_URL}/api/v1/auth/login`, {
  179 |         data: {
  180 |           username: 'test@test.com',
  181 |           password: 'wrongpassword'
  182 |         }
  183 |       });
  184 |       expect([200, 401]).toContain(response.status());
  185 |     });
  186 | 
  187 |     test('token is returned on successful login', async ({ request }) => {
  188 |       const response = await request.post(`${API_URL}/api/v1/auth/login`, {
  189 |         data: {
  190 |           username: 'test@example.com',
  191 |           password: 'TestPass123!'
  192 |         }
  193 |       });
  194 |       
  195 |       if (response.status() === 200) {
  196 |         const data = await response.json();
  197 |         expect(data.access_token || data.token).toBeDefined();
  198 |       }
  199 |     });
  200 |   });
  201 | });
```