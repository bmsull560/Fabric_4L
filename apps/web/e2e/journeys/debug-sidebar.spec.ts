import { test, expect } from '../fixtures/contract-test';

test('debug sidebar @debug', async ({ page }) => {
  const consoleLogs: string[] = [];
  page.on('console', msg => consoleLogs.push(`[${msg.type()}] ${msg.text()}`));
  page.on('pageerror', err => consoleLogs.push(`[PAGE_ERROR] ${err.message}`));

  await page.goto('http://localhost:3001/login');
  await page.getByRole('button', { name: /development bypass/i }).click();
  await page.waitForURL(/\/home/);
  await page.waitForTimeout(3000);

  const title = await page.title();
  const html = await page.content();
  console.log('Page title:', title);
  console.log('URL:', page.url());
  console.log('HTML has root div:', html.includes('id="root"'));
  console.log('HTML has aside:', html.includes('<aside'));
  console.log('HTML has nav:', html.includes('<nav'));

  // Try to find ANY rendered text
  const bodyText = await page.locator('body').innerText();
  console.log('Body innerText preview:', bodyText?.substring(0, 300));

  console.log('Console logs:');
  consoleLogs.forEach(log => console.log(log));
});
