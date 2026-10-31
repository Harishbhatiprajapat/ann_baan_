const puppeteer = require('./frontend/node_modules/puppeteer-core');
const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('PAGE CONSOLE:', msg.type(), msg.text()));
  page.on('request', req => {
    if (req.url().includes('/marketplace/listings')) {
      console.log('REQUEST TO LISTINGS:', req.method(), req.url());
      if (req.method() === 'POST') {
        console.log('POST DATA:', req.postData());
      }
    }
  });
  page.on('requestfailed', req => console.log('REQ FAILED:', req.method(), req.url(), req.failure().errorText));
  page.on('response', res => {
    if (res.url().includes('/marketplace/listings')) {
      console.log('RESPONSE FROM LISTINGS:', res.status(), res.url());
    }
  });
  page.on('dialog', async dialog => {
    console.log('DIALOG DETECTED:', dialog.type(), dialog.message());
    await dialog.accept();
  });

  console.log('Navigating to http://localhost:3000/?role=donor...');
  await page.goto('http://localhost:3000/?role=donor', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 2000));

  console.log('Waiting for button...');
  // Find button with exact text
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const btn = btns.find(b => b.textContent && b.textContent.includes('List Commercial Deal'));
    if (btn) {
      console.log('Triggering click on button in page context:', btn.textContent);
      btn.click();
    } else {
      console.log('Button not found in page context');
    }
  });

  await new Promise(r => setTimeout(r, 1500));

  console.log('Checking for modal form...');
  const submitted = await page.evaluate(async () => {
    const form = document.querySelector('form');
    if (form && form.innerHTML.includes('Deal Title / Dish')) {
      console.log('Found commercial deal form, submitting via submit button...');
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.click();
        return true;
      }
    }
    return false;
  });

  console.log('Form submission triggered:', submitted);
  await new Promise(r => setTimeout(r, 3500));

  await browser.close();
  console.log('Finished browser test.');
})().catch(console.error);
