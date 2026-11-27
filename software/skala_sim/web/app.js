'use strict';
const $ = id => document.getElementById(id);
const token = document.querySelector('meta[name="skala-token"]').content;
const keys = new Set();
let enabled = false, device = 'keyboard', busy = false, lastSent = 0, hadPad = false;
let requestGeneration = 0;
const client = crypto.randomUUID();
let sequence = 0, enabledAt = 0;
const headers = {'Content-Type': 'application/json', 'X-Skala-Token': token};

async function send(command, force = false) {
  if (busy && !force) return;
  const generation = ++requestGeneration;
  busy = true;
  try {
    const response = await fetch('/control', {method: 'POST', headers, body: JSON.stringify({...command, client, sequence: ++sequence}), keepalive: true});
    if (!response.ok) throw new Error('Control request rejected');
    lastSent = performance.now();
  } catch {
    enabled = false;
    $('mode').textContent = 'Connection lost — controls disabled';
  } finally {
    if (generation === requestGeneration) busy = false;
  }
}

function stop() {
  enabled = false;
  keys.clear();
  paintKeys();
  $('mode').textContent = 'Controls stopped';
  $('enable').textContent = 'Enable manual controls';
  send({mode: 'stopped', linear: 0, angular: 0}, true);
}

$('enable').onclick = () => {
  keys.clear();
  enabled = true;
  enabledAt = performance.now();
  $('enable').textContent = 'Manual controls enabled';
  $('mode').textContent = device === 'keyboard' ? 'Hold WASD to drive' : 'Hold LB / L1 to drive';
  send({mode: 'manual', linear: 0, angular: 0}, true);
};
$('stop').onclick = stop;
for (const input of ['keyboard', 'gamepad']) $(input).onclick = () => {
  stop(); device = input;
  $('keyboardHelp').hidden = input !== 'keyboard';
  $('gamepadHelp').hidden = input !== 'gamepad';
  $('keyboard').classList.toggle('selected', input === 'keyboard');
  $('gamepad').classList.toggle('selected', input === 'gamepad');
};
function paintKeys() {
  for (const key of document.querySelectorAll('[data-key]')) key.classList.toggle('active', keys.has(key.dataset.key));
}
document.addEventListener('keydown', event => {
  if (event.code === 'Space') {event.preventDefault(); stop(); return;}
  if (['INPUT', 'SELECT'].includes(event.target.tagName)) return;
  const key = event.key.toLowerCase();
  if ('wasd'.includes(key) && key.length === 1) {event.preventDefault(); keys.add(key); paintKeys();}
});
document.addEventListener('keyup', event => {keys.delete(event.key.toLowerCase()); paintKeys();});
window.addEventListener('blur', () => {if (enabled) stop();});
document.addEventListener('visibilitychange', () => {if (document.hidden && enabled) stop();});
window.addEventListener('pagehide', () => {if (enabled) stop();});
window.addEventListener('gamepaddisconnected', () => {if (device === 'gamepad') stop();});
$('speed').oninput = () => {$('speedLabel').value = `${Number($('speed').value).toFixed(2)} m/s`;};

function pads() {
  return navigator.getGamepads ? Array.from(navigator.getGamepads()).filter(Boolean) : [];
}
function refreshPads() {
  const connected = pads(), previous = $('padSelect').value;
  const signature = connected.map(p => `${p.index}:${p.id}`).join('|');
  if ($('padSelect').dataset.signature !== signature) {
    $('padSelect').dataset.signature = signature;
    $('padSelect').replaceChildren();
    for (const pad of connected) $('padSelect').add(new Option(pad.id, pad.index));
    if (!connected.length) $('padSelect').add(new Option('No controller detected', ''));
    if (connected.some(p => String(p.index) === previous)) $('padSelect').value = previous;
  }
  const pad = connected.find(p => String(p.index) === $('padSelect').value);
  $('padStatus').textContent = pad ? `${pad.mapping === 'standard' ? 'Standard mapping' : 'Custom mapping — check axes below'} · ${pad.axes.length} axes · ${pad.buttons.length} buttons` : 'Press a button on a connected controller';
  return pad;
}
function deadzone(v) {return Math.abs(v) < .12 ? 0 : Math.sign(v)*(Math.abs(v)-.12)/.88;}
function controlTick() {
  let linear = 0, angular = 0;
  const speed = Number($('speed').value);
  if (device === 'keyboard' && enabled) {
    linear = ((keys.has('w') ? 1 : 0)-(keys.has('s') ? 1 : 0))*speed;
    angular = ((keys.has('a') ? 1 : 0)-(keys.has('d') ? 1 : 0))*.6;
  }
  if (device === 'gamepad') {
    const pad = refreshPads();
    if (!pad && hadPad) stop();
    hadPad = Boolean(pad);
    if (pad) {
      $('rawPad').textContent = `Axes: ${pad.axes.map(v => v.toFixed(2)).join(', ')}\nButtons: ${pad.buttons.map((b,i) => b.pressed ? i : null).filter(v => v !== null).join(', ') || 'none'}`;
      if (pad.buttons[Number($('stopButton').value)]?.pressed) stop();
      if (enabled && pad.buttons[Number($('holdButton').value)]?.pressed) {
        linear = deadzone(pad.axes[Number($('forwardAxis').value)] || 0)*speed*($('invertForward').checked ? -1 : 1);
        angular = deadzone(pad.axes[Number($('turnAxis').value)] || 0)*.6*($('invertTurn').checked ? -1 : 1);
      }
    }
  }
  $('linear').textContent = `${linear.toFixed(2)} m/s`;
  $('angular').textContent = `${angular.toFixed(2)} rad/s`;
  if (enabled) send({linear, angular});
}
setInterval(controlTick, 80);
setInterval(async () => {
  try {
    const response = await fetch('/status');
    if (!response.ok) throw new Error('Unavailable');
    const state = await response.json();
    const floorplan = state.scenario === 'floorplan';
    $('scenario').textContent = floorplan ? 'Multi-room floorplan · 12 × 10 m · five rooms and connecting doorways' : 'Lab · 6 × 6 m practice room';
    $('floorplanReference').hidden = !floorplan;
    $('connection').textContent = state.scan_live ? 'Simulation live' : 'Waiting for simulation';
    $('connection').classList.toggle('live', state.scan_live);
    if (!state.scan_live && enabled) stop();
    if (state.mode !== 'manual' && enabled && performance.now()-enabledAt > 1000) {
      enabled = false; keys.clear(); paintKeys(); $('enable').textContent = 'Enable manual controls';
    }
    if (!enabled) $('mode').textContent = state.mode === 'demo' ? 'Automatic route has control' : 'Controls stopped';
    if (state.pose) $('pose').textContent = `SLAM pose · x ${state.pose.x.toFixed(2)} m · y ${state.pose.y.toFixed(2)} m · heading ${(state.pose.yaw*180/Math.PI).toFixed(0)}°`;
    if (state.camera_available) $('cameraImage').src = `/camera.png?t=${Date.now()}`;
    if (state.map_available) $('mapImage').src = `/map.png?t=${Date.now()}`;
  } catch {
    $('connection').textContent = 'Disconnected'; $('connection').classList.remove('live');
    if (enabled) stop();
  }
}, 1000);
