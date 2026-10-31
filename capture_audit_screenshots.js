const puppeteer = require('./frontend/node_modules/puppeteer-core');
const path = require('path');
const fs = require('fs');

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const SCREENSHOT_DIR = path.resolve(__dirname, 'screenshots');

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

const PAGES_TO_TEST = [
  { name: '01_landing_desktop', url: 'http://localhost:3000/?role=landing', viewport: { width: 1920, height: 1080 } },
  { name: '02_landing_mobile', url: 'http://localhost:3000/?role=landing', viewport: { width: 390, height: 844 }, isMobile: true },
  { name: '03_rescue_deals_marketplace', url: 'http://localhost:3000/?role=deals', viewport: { width: 1920, height: 1080 } },
  { name: '04_customer_dashboard_orders', url: 'http://localhost:3000/?role=customer', viewport: { width: 1920, height: 1080 } },
  { name: '05_donor_restaurant_dashboard', url: 'http://localhost:3000/?role=donor', viewport: { width: 1920, height: 1080 } },
  { name: '06_ngo_distribution_portal', url: 'http://localhost:3000/?role=ngo', viewport: { width: 1920, height: 1080 } },
  { name: '07_volunteer_logistics_control', url: 'http://localhost:3000/?role=volunteer', viewport: { width: 1920, height: 1080 } },
  { name: '08_admin_control_safety_centre', url: 'http://localhost:3000/?role=admin', viewport: { width: 1920, height: 1080 } },
  { name: '09_jaipur_demo_simulation_modal', url: 'http://localhost:3000/?modal=demo', viewport: { width: 1920, height: 1080 } },
  { name: '10_auth_portal_modal', url: 'http://localhost:3000/?modal=auth', viewport: { width: 1920, height: 1080 } },
  { name: '11_profile_settings_modal', url: 'http://localhost:3000/?modal=profile', viewport: { width: 1920, height: 1080 } },
  { name: '12_marketplace_tablet_view', url: 'http://localhost:3000/?role=deals', viewport: { width: 768, height: 1024 } }
];

async function run() {
  console.log('Launching Chrome via puppeteer-core...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });

  const page = await browser.newPage();
  const results = [];
  const consoleErrors = [];

  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(`[Console Error] ${msg.text()}`);
    }
  });

  page.on('response', resp => {
    if (resp.status() >= 400) {
      consoleErrors.push(`[HTTP Error ${resp.status()}] ${resp.url()}`);
    }
  });

  for (const item of PAGES_TO_TEST) {
    try {
      console.log(`Visiting: ${item.name} (${item.url})...`);
      await page.setViewport(item.viewport);
      await page.goto(item.url, { waitUntil: 'networkidle2', timeout: 30000 });
      // Allow animations and client state to settle
      await new Promise(r => setTimeout(r, 1200));

      const screenshotPath = path.join(SCREENSHOT_DIR, `${item.name}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: false });
      console.log(`  ✓ Saved: ${screenshotPath}`);

      results.push({ name: item.name, status: 'PASS', path: screenshotPath });
    } catch (err) {
      console.error(`  ✗ Error visiting ${item.name}:`, err.message);
      results.push({ name: item.name, status: 'FAIL', error: err.message });
    }
  }

  await browser.close();
  console.log('\n--- Screenshot Audit Summary ---');
  console.table(results);
  console.log('\n--- Intercepted Console & HTTP Errors ---');
  if (consoleErrors.length === 0) {
    console.log('Zero console or HTTP errors intercepted!');
  } else {
    consoleErrors.forEach(e => console.log(e));
  }
}

run().catch(console.error);
