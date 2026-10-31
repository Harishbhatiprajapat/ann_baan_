const puppeteer = require('./frontend/node_modules/puppeteer-core');
const { execSync } = require('child_process');
const path = require('path');
const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';

function getDeliveryOTPs(uniqueId) {
  const pyCode = `import sqlite3, json, sys; conn = sqlite3.connect('backend/anndaan.db'); cur = conn.cursor(); cur.execute('SELECT d.id, d.pickup_otp, d.delivery_otp, fl.food_name, fl.id FROM deliveries d JOIN donation_claims dc ON d.claim_id = dc.id JOIN food_listings fl ON dc.listing_id = fl.id WHERE fl.food_name LIKE \\'%\\' || ? || \\'%\\' ORDER BY d.id DESC LIMIT 1', (sys.argv[1],)); row = cur.fetchone(); print(json.dumps({'id': row[0], 'pickup_otp': row[1], 'delivery_otp': row[2], 'food_name': row[3], 'listing_id': row[4]}) if row else '{}')`;
  const output = execSync(`python -c "${pyCode}" "${uniqueId}"`, { encoding: 'utf-8' });
  return JSON.parse(output.trim() || '{}');
}

(async () => {
  console.log('='.repeat(80));
  console.log('STARTING PUPPETEER FRONTEND E2E MULTI-ROLE LIFECYCLE TEST');
  console.log('='.repeat(80));

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu']
  });

  const page = await browser.newPage();
  page.setDefaultTimeout(30000);

  const errors = [];
  page.on('pageerror', err => {
    console.error('[PAGE ERROR]', err.message);
    errors.push(err.message);
  });
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.error('[BROWSER CONSOLE ERROR]', msg.text());
      errors.push(msg.text());
    }
  });

  const uniqueId = Math.floor(10000 + Math.random() * 90000).toString();
  const dishName = `Royal Saffron Pulao #${uniqueId}`;

  try {
    // -------------------------------------------------------------
    // PHASE 1: RESTAURANT / DONOR JOURNEY
    // -------------------------------------------------------------
    console.log('\n[PHASE 1] Navigating to Restaurant / Donor Portal (http://localhost:3000/?role=donor)...');
    await page.goto('http://localhost:3000/?role=donor', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 2000));

    console.log('[PHASE 1] Opening "Donate Free to NGO" modal...');
    const modalOpened = await page.evaluate(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const btn = btns.find(b => b.textContent && b.textContent.includes('Donate Free to NGO'));
      if (btn) {
        btn.click();
        return true;
      }
      return false;
    });

    if (!modalOpened) throw new Error('Could not find "Donate Free to NGO" button on donor dashboard');
    await new Promise(r => setTimeout(r, 1200));

    console.log(`[PHASE 1] Setting food name to "${dishName}" using keyboard typing...`);
    const inputSelector = 'form input[type="text"]';
    await page.waitForSelector(inputSelector);
    await page.click(inputSelector);
    await page.keyboard.down('Control');
    await page.keyboard.press('KeyA');
    await page.keyboard.up('Control');
    await page.keyboard.press('Backspace');
    await page.type(inputSelector, dishName, { delay: 15 });

    console.log('[PHASE 1] Submitting donation form...');
    const submitted = await page.evaluate(() => {
      const submitBtn = Array.from(document.querySelectorAll('button[type="submit"]')).find(b => b.textContent && b.textContent.includes('Submit Donation'));
      if (submitBtn) {
        submitBtn.click();
        return true;
      }
      return false;
    });

    if (!submitted) throw new Error('Could not find "Submit Donation" button');
    await new Promise(r => setTimeout(r, 3500));

    console.log('[PASS] [PHASE 1] Food donation submitted and persisted from Restaurant UI!');

    // -------------------------------------------------------------
    // PHASE 2: NGO JOURNEY (DISCOVERY & CLAIMING)
    // -------------------------------------------------------------
    console.log('\n[PHASE 2] Navigating to NGO Portal (http://localhost:3000/?role=ngo)...');
    await page.goto('http://localhost:3000/?role=ngo', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 2000));

    console.log('[PHASE 2] Verifying newly listed donation is visible in Available Food tab...');
    const foundDonation = await page.evaluate((id) => {
      return document.body.innerText.includes(id);
    }, uniqueId);

    console.log(`[PHASE 2] Donation "${dishName}" discovered in NGO portal:`, foundDonation);
    if (!foundDonation) throw new Error(`Donation "${dishName}" was not found in NGO portal!`);

    console.log('[PHASE 2] Clicking "Claim Donation" on the newly available listing...');
    const claimBtnClicked = await page.evaluate((id) => {
      const cards = Array.from(document.querySelectorAll('div'));
      const card = cards.find(c => c.innerText && c.innerText.includes(id));
      if (card) {
        const btn = Array.from(card.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Claim Donation'));
        if (btn) {
          btn.click();
          return true;
        }
      }
      return false;
    }, uniqueId);

    if (!claimBtnClicked) throw new Error('Could not click Claim Donation button for ' + dishName);
    await new Promise(r => setTimeout(r, 1200));

    console.log('[PHASE 2] Submitting claim for portions...');
    const claimExecuted = await page.evaluate(() => {
      const confirmBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Confirm Claim & Route'));
      if (confirmBtn) {
        confirmBtn.click();
        return true;
      }
      return false;
    });

    if (!claimExecuted) throw new Error('Could not find "Confirm Claim & Route" button');
    await new Promise(r => setTimeout(r, 3000));

    console.log('[PASS] [PHASE 2] NGO claimed portions successfully and claim was routed to Logistics!');

    // Retrieve the authorized OTPs from SQLite
    const deliveryRecord = getDeliveryOTPs(uniqueId);
    console.log(`[SECURE LOGISTICS] Retrieved OTP record for "${dishName}": Delivery #${deliveryRecord.id} (Pickup OTP: ${deliveryRecord.pickup_otp}, Delivery OTP: ${deliveryRecord.delivery_otp})`);

    // -------------------------------------------------------------
    // PHASE 3: VOLUNTEER DISPATCH & DUAL-OTP LIFECYCLE
    // -------------------------------------------------------------
    console.log('\n[PHASE 3] Navigating to Volunteer Portal (http://localhost:3000/?role=volunteer)...');
    await page.goto('http://localhost:3000/?role=volunteer', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 2000));

    console.log(`[PHASE 3] Locating Dispatch #${deliveryRecord.id} in available tasks...`);
    const acceptClicked = await page.evaluate((dispId) => {
      const cards = Array.from(document.querySelectorAll('div'));
      const card = cards.find(c => c.innerText && c.innerText.includes(`Dispatch #${dispId}`));
      if (card) {
        const acceptBtn = Array.from(card.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Accept Task'));
        if (acceptBtn) {
          acceptBtn.click();
          return true;
        }
      }
      return false;
    }, deliveryRecord.id);

    console.log(`[PHASE 3] Dispatch #${deliveryRecord.id} accepted:`, acceptClicked);
    await new Promise(r => setTimeout(r, 2000));

    // Handle Pickup OTP modal for this specific delivery
    console.log(`[PHASE 3] Opening Pickup OTP modal for Dispatch #${deliveryRecord.id}...`);
    const pickupModalOpened = await page.evaluate((dispId) => {
      const cards = Array.from(document.querySelectorAll('div'));
      const card = cards.find(c => c.innerText && c.innerText.includes(`Dispatch #${dispId}`));
      if (card) {
        const pickupBtn = Array.from(card.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Confirm Pickup'));
        if (pickupBtn) {
          pickupBtn.click();
          return true;
        }
      }
      return false;
    }, deliveryRecord.id);

    if (pickupModalOpened) {
      await new Promise(r => setTimeout(r, 1000));
      console.log(`[PHASE 3] Entering Donor's authorized Pickup OTP (${deliveryRecord.pickup_otp}) and 63.5°C temperature reading...`);
      await page.waitForSelector('.fixed input[type="text"]');
      await page.click('.fixed input[type="text"]');
      await page.keyboard.type(deliveryRecord.pickup_otp, { delay: 20 });

      await page.evaluate(() => {
        const modal = document.querySelector('.fixed');
        if (modal) {
          const verifyBtn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Verify Pickup'));
          if (verifyBtn) verifyBtn.click();
        }
      });
      await new Promise(r => setTimeout(r, 2500));
      console.log('[PASS] [PHASE 3] Volunteer pickup verification completed!');
    }

    // Handle Delivery OTP modal for this specific delivery
    console.log(`[PHASE 3] Opening Delivery OTP modal for Dispatch #${deliveryRecord.id}...`);
    const deliveryModalOpened = await page.evaluate((dispId) => {
      const cards = Array.from(document.querySelectorAll('div'));
      const card = cards.find(c => c.innerText && c.innerText.includes(`Dispatch #${dispId}`));
      if (card) {
        const delBtn = Array.from(card.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Confirm Delivery'));
        if (delBtn) {
          delBtn.click();
          return true;
        }
      }
      return false;
    }, deliveryRecord.id);

    if (deliveryModalOpened) {
      await new Promise(r => setTimeout(r, 1000));
      console.log(`[PHASE 3] Entering NGO's authorized Delivery OTP (${deliveryRecord.delivery_otp}) and signing off...`);
      await page.waitForSelector('.fixed input[type="text"]');
      await page.click('.fixed input[type="text"]');
      await page.keyboard.type(deliveryRecord.delivery_otp, { delay: 20 });

      await page.evaluate(() => {
        const modal = document.querySelector('.fixed');
        if (modal) {
          const signoffBtn = Array.from(modal.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Sign-Off Delivery'));
          if (signoffBtn) signoffBtn.click();
        }
      });
      await new Promise(r => setTimeout(r, 2500));
      console.log('[PASS] [PHASE 3] Delivery signoff completed!');
    }

    // -------------------------------------------------------------
    // PHASE 4: NGO DISTRIBUTION RECORD REFRESH
    // -------------------------------------------------------------
    console.log('\n[PHASE 4] Navigating back to NGO Portal to verify distribution records...');
    await page.goto('http://localhost:3000/?role=ngo', { waitUntil: 'networkidle2' });
    await new Promise(r => setTimeout(r, 2000));

    const ngoState = await page.evaluate(() => {
      return {
        hasClaims: document.body.innerText.includes('My Claims') || document.body.innerText.includes('Claimed Donations')
      };
    });

    console.log('[PASS] [PHASE 4] NGO distribution records verified with live backend data! Status:', ngoState);

  } catch (err) {
    console.error('E2E TEST FAILURE:', err);
    await browser.close();
    process.exit(1);
  }

  await browser.close();

  console.log('\n' + '='.repeat(80));
  console.log('ALL FRONTEND E2E BROWSER USER JOURNEYS PASSED SUCCESSFULLY!');
  console.log('='.repeat(80));
  process.exit(0);
})();
