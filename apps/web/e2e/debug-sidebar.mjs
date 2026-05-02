import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
await page.goto('http://localhost:3001/login');
await page.getByRole('button', { name: /development bypass/i }).click();
await page.waitForURL(/\/home/);
await page.waitForTimeout(2000);

const hasAside = await page.locator('aside').count() > 0;
const hasNav = await page.locator('nav').count() > 0;
const asideText = await page.locator('aside').first().textContent().catch(() => 'NO ASIDE');

console.log('Has aside:', hasAside);
console.log('Has nav:', hasNav);
console.log('Aside text preview:', asideText.substring(0, 300));

await browser.close();
