const { chromium } = require('playwright');
const path = require('path');

const BASE = 'http://localhost:3006';
const OUT = 'd:/桌面/毕业设计/screenshots-phase1';

async function snap(page, name) {
  await page.goto(`${BASE}${name}`, { waitUntil: 'load', timeout: 30000 });
  await page.waitForTimeout(500);
  await page.screenshot({ path: `${OUT}${name === '/' ? '/home' : name}.png`, fullPage: true });
  console.log(`  OK: ${name}`);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });

  // Ensure output dir
  const fs = require('fs');
  if (!fs.existsSync(OUT)) fs.mkdirSync(OUT, { recursive: true });

  console.log('Taking screenshots at 390x844 (mobile)...');
  const page = await context.newPage();

  // Main pages
  await snap(page, '/');
  await snap(page, '/ai');
  await snap(page, '/content');
  await snap(page, '/activities');
  await snap(page, '/discussions');
  await snap(page, '/profile');

  await browser.close();
  console.log('Done.');
})().catch(e => { console.error(e.message); process.exit(1); });
