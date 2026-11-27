// Requires a running simulator and Playwright with Chromium.
// Gamepad input is synthetic; no physical controller qualification is implied.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

(async () => {
  const output = process.env.SKALA_TEST_OUTPUT || '/tmp/skala-controls';
  fs.mkdirSync(output, {recursive: true});
  const browser = await chromium.launch({executablePath: process.env.CHROME_BIN || '/usr/bin/google-chrome',
    headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage']});
  const page = await browser.newPage({viewport: {width: 1340, height: 1000}});
  const errors = [], commands = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {
    if (request.url().endsWith('/control') && request.method() === 'POST') commands.push(request.postDataJSON());
  });
  const report = {status: 'failed', gamepad_hardware_tested: false, checks: {}};
  try {
    await page.goto('http://localhost:18765');
    await page.getByText('Simulation live', {exact: true}).waitFor({timeout: 30000});
    const status = async () => (await page.request.get('http://localhost:18765/status')).json();
    const mode = async expected => {
      for (let i=0; i<30; i++) {if ((await status()).mode === expected) return; await page.waitForTimeout(100);}
      throw Error('Control mode did not become '+expected);
    };
    const before = (await status()).pose;
    await page.locator('#enable').click();
    await mode('manual');
    await page.keyboard.down('w');
    await page.waitForTimeout(1200);
    await page.keyboard.up('w');
    await page.waitForTimeout(600);
    const after = (await status()).pose;
    const distance = Math.hypot(after.x-before.x, after.y-before.y);
    assert(distance > .04, `WASD did not move the SLAM pose (${distance})`);
    assert(commands.some(c => c.linear > .1));
    assert(commands.at(-1).linear === 0);
    report.checks.wasd_forward_and_release = {distance_m: distance};
    await page.keyboard.down('a');
    await page.waitForTimeout(400);
    await page.keyboard.up('a');
    assert(commands.some(c => c.angular > .5));
    await page.keyboard.press('Space');
    await mode('stopped');
    report.checks.space_stop = true;
    await page.locator('#enable').click();
    await mode('manual');
    await page.evaluate(() => window.dispatchEvent(new Event('blur')));
    await mode('stopped');
    report.checks.focus_loss_stop = true;

    await page.addInitScript(() => {
      window.testPad = {index: 0, id: 'Synthetic standard gamepad', mapping: 'standard', connected: true,
        axes: [0, -1, 0, 0], buttons: Array.from({length: 17}, () => ({pressed: false, value: 0}))};
      Object.defineProperty(navigator, 'getGamepads', {value: () => window.testPad ? [window.testPad] : []});
    });
    await page.reload();
    await page.locator('#gamepad').click();
    await page.locator('#enable').click();
    await mode('manual');
    await page.waitForTimeout(300);
    assert.equal(commands.at(-1).linear, 0, 'Controller drove without the hold button');
    await page.evaluate(() => {window.testPad.buttons[4] = {pressed: true, value: 1};});
    await page.waitForTimeout(400);
    assert(commands.at(-1).linear > .1, 'Held controller stick did not command forward');
    await page.evaluate(() => {window.testPad.axes = [.6, 0, 0, 0];});
    await page.waitForTimeout(200);
    assert(commands.at(-1).angular < -.2, 'Controller steering direction is wrong');
    await page.evaluate(() => {window.testPad.buttons[4] = {pressed: false, value: 0};});
    await page.waitForTimeout(200);
    assert.equal(commands.at(-1).linear, 0);
    assert.equal(commands.at(-1).angular, 0);
    report.checks.gamepad_hold_steer_release = true;
    await page.evaluate(() => {window.testPad.buttons[1] = {pressed: true, value: 1};});
    await mode('stopped');
    report.checks.gamepad_stop_button = true;
    await page.evaluate(() => {window.testPad.buttons[1] = {pressed: false, value: 0};});
    await page.locator('#enable').click();
    await mode('manual');
    await page.evaluate(() => {window.testPad = null;});
    await mode('stopped');
    report.checks.gamepad_disconnect_stop = true;

    const token = await page.locator('meta[name="skala-token"]').getAttribute('content');
    const h = {'X-Skala-Token': token};
    const first = await page.request.post('http://localhost:18765/control', {headers:h,
      data:{client:'stale-request-test', sequence:10, mode:'stopped'}});
    assert.equal(first.status(),200);
    const stale = await page.request.post('http://localhost:18765/control', {headers:h,
      data:{client:'stale-request-test', sequence:9, mode:'manual', linear:.25}});
    assert.equal(stale.status(),409);
    await mode('stopped');
    const unauthorized = await page.request.post('http://localhost:18765/control',
      {data:{client:'no-token', sequence:1, mode:'manual'}});
    assert.equal(unauthorized.status(),403);
    report.checks.stale_command_rejected = true;
    report.checks.missing_token_rejected = true;
    await page.locator('#keyboard').click();
    await page.waitForTimeout(1200);
    await page.screenshot({path: path.join(output, 'controls.png'), fullPage: true});
    assert.deepEqual(errors, []);
    report.checks.browser_errors = errors;
    report.status = 'passed';
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    report.error = error.stack;
    throw error;
  } finally {
    fs.writeFileSync(path.join(output, 'controls-validation.json'), JSON.stringify(report,null,2)+'\n');
    await browser.close();
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
