const puppeteer = require('./frontend/node_modules/puppeteer-core');
const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

(async () => {
  console.log('Starting headless browser verification of all role views...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });
  const page = await browser.newPage();

  const errors = [];
  page.on('pageerror', err => {
    console.error('Page error captured:', err.message);
    errors.push(err.message);
  });
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.error('Console error captured:', msg.text());
      errors.push(msg.text());
    }
  });

  const views = ['landing', 'deals', 'customer', 'donor', 'ngo', 'volunteer', 'admin'];

  for (const role of views) {
    const url = `http://localhost:3000/?role=${role}`;
    console.log(`Checking view: ${role} (${url})...`);
    await page.goto(url, { waitUntil: 'networkidle2', timeout: 20000 });
    await new Promise(r => setTimeout(r, 1500));
    const title = await page.title();
    console.log(`[PASS] ${role} loaded successfully (Title: "${title}")`);
  }

  await browser.close();

  if (errors.length > 0) {
    console.error(`FAILED: ${errors.length} runtime errors captured:`, errors);
    process.exit(1);
  } else {
    console.log('\n================================================================');
    console.log('ALL ROLE VIEWS RENDERED CLEANLY WITH ZERO RUNTIME ERRORS!');
    console.log('================================================================');
    process.exit(0);
  }
})();
