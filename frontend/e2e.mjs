// E2E contra el backend real.
//
// Requisitos:
//   - `vite` corriendo en http://localhost:5173 (npm run dev).
//   - Puerto 8000 libre: este script levanta el backend FastAPI y lo detiene al final.
//   - Python con las dependencias instaladas (requirements.txt).
//
// Flujo: registra y verifica dos cuentas (leyendo el código del proveedor
// "console"), las loguea por la UI, crea una sala, el segundo jugador entra,
// inicia la partida y juega la ronda completa hasta el podio.
import { spawn } from 'node:child_process';
import path from 'node:path';
import { mkdirSync } from 'node:fs';
import { chromium } from 'playwright';

const SHOTS = '/tmp/opencode/shots';
mkdirSync(SHOTS, { recursive: true });

const ROOT = path.resolve(new URL('../', import.meta.url).pathname);
const BASE = 'http://localhost:5173';
const API = 'http://localhost:8000/api/v1';
const PASS = 'e2ePass123';

const waitFor = (page, sel, timeout = 15000) =>
  page.waitForSelector(sel, { timeout, state: 'visible' });

// ---- backend propio ----------------------------------------------------------

let backend;
const verifyTokens = [];
let backendFailed = null;

async function startBackend() {
  backend = spawn('python3', ['-m', 'uvicorn', 'app.main:app', '--port', '8000'], {
    cwd: ROOT,
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  backend.stdout.on('data', (buf) => {
    const text = buf.toString();
    for (const m of text.matchAll(/Tu código de verificación es: (\S+)/g)) verifyTokens.push(m[1]);
  });
  backend.stderr.on('data', (buf) => {
    const text = buf.toString();
    if (text.includes('address already in use')) backendFailed = 'El puerto 8000 está ocupado. Detené otras instancias del backend y reintentá.';
    if (text.toLowerCase().includes('error')) console.error('[backend]', text.trim());
  });
  backend.on('exit', (code) => {
    if (code && code !== 0 && !backendFailed) backendFailed = `El backend salió con código ${code}.`;
  });
}

async function waitHealth(timeoutMs = 20000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (backendFailed) throw new Error(backendFailed);
    try {
      const res = await fetch('http://localhost:8000/health');
      if (res.ok) return;
    } catch { /* aún no levanta */ }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error('El backend no respondió en /health a tiempo.');
}

async function waitToken(timeoutMs = 10000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (verifyTokens.length) return verifyTokens.shift();
    if (backendFailed) throw new Error(backendFailed);
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error('No se recibió el código de verificación por el console.');
}

async function registerVerified(username) {
  const email = `${username}@example.com`;
  const reg = await fetch(`${API}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password: PASS }),
  });
  if (!reg.ok) throw new Error(`Registro ${username} falló: ${reg.status}`);
  const token = await waitToken();
  const ver = await fetch(`${API}/auth/verify-email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token }),
  });
  if (!ver.ok) throw new Error(`Verificación ${username} falló: ${ver.status}`);
  console.log(`  ok  cuenta ${username} registrada y verificada`);
}

// ---- helpers de UI -----------------------------------------------------------

async function login(page, identifier) {
  await page.goto(BASE + '/#/login', { waitUntil: 'networkidle' });
  await waitFor(page, '.auth-card');
  await page.fill('.auth-card input[type="text"]', identifier);
  await page.fill('.auth-card input[type="password"]', PASS);
  await page.click('button:has-text("Iniciar sesión")');
  await waitFor(page, '.dash');
}

let ok = 0;
const check = (cond, msg) => { console.log((cond ? '  ok  ' : '  FAIL ') + msg); if (!cond) process.exitCode = 1; else ok++; };
const shot = (page, name) => page.screenshot({ path: `${SHOTS}/${name}.png`, fullPage: false });

// ------------------------------------------------------------------------------

const browser = await chromium.launch();
const errorsA = [];
const errorsB = [];
const watch = (page, errors) => {
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push('console.error: ' + m.text()); });
};

try {
  await startBackend();
  await waitHealth();
  console.log('  ok  backend levantado en :8000');

  await registerVerified('e2e_alpha');
  await registerVerified('e2e_beta');

  const ctxA = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const ctxB = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const pageA = await ctxA.newPage();
  const pageB = await ctxB.newPage();
  watch(pageA, errorsA);
  watch(pageB, errorsB);

  // ---- login de los dos jugadores ----
  await login(pageA, 'e2e_alpha');
  check(true, 'login creador, dashboard visible');
  await login(pageB, 'e2e_beta');
  check(true, 'login jugador 2, dashboard visible');

  // ---- crear sala y unirse ----
  await pageA.click('button:has-text("Crear sala")');
  await waitFor(pageA, '.modal-choice');
  await pageA.click('.modal-choice');
  await waitFor(pageA, '.room');
  const code = (await pageA.textContent('.code-tiles')).replace(/\s+/g, '');
  check(/^[A-Z0-9]{6}$/.test(code), `sala creada con código ${code}`);

  await pageB.fill('.join-input', code);
  await pageB.click('button:has-text("Unirse")');
  await waitFor(pageB, '.room');
  await waitFor(pageA, '.player-card >> nth=1');
  check(true, 'ambos jugadores en la sala');
  await shot(pageA, '04-room');

  // ---- iniciar partida; el resto entra solo con el código de la sala ----
  await pageA.click('button:has-text("Iniciar partida")');
  await waitFor(pageA, '.match', 20000);
  await waitFor(pageB, '.match', 20000);
  check(true, 'ambos jugadores en la partida sin compartir enlace');

  // ---- jugar hasta finalizar ----
  const deadline = Date.now() + 240000;
  let finished = false;
  let acted = 0;
  while (Date.now() < deadline && !finished) {
    if (await pageA.isVisible('.stage--finish')) { finished = true; break; }

    for (const page of [pageA, pageB]) {
      if (await page.isVisible('input.input--inline')) {
        const phrase = `frase e2e ${Math.floor(Math.random() * 1000)}`;
        await page.fill('input.input--inline', phrase);
        await page.click('.score-chip >> nth=6');
        await page.click('button:has-text("Enviar frase")');
        acted++;
        await page.waitForTimeout(600);
        continue;
      }
      if ((await page.isVisible('.stage-phrase--vote')) && (await page.isVisible('text=Enviar voto'))) {
        await page.click('.score-chip >> nth=3');
        await page.click('button:has-text("Enviar voto")');
        acted++;
        await page.waitForTimeout(600);
      }
    }
    await pageA.waitForTimeout(400);
  }

  check(finished, `partida finalizada en la UI (acciones de juego: ${acted})`);
  await shot(pageA, '05-finish');

  const finishTitle = await pageA.textContent('.finish-title').catch(() => null);
  check(finishTitle !== null, 'pantalla de resultado visible: ' + (finishTitle || '?'));
  check((await pageA.textContent('.final-scoreboard')).includes('e2e'), 'marcador final con jugadores reales');

  const realErrors = [...errorsA, ...errorsB].filter((e) => !e.includes('favicon'));
  check(realErrors.length === 0, `sin errores de consola inesperados (${realErrors.length})`);
  if (realErrors.length) console.log(realErrors.slice(0, 5));

  console.log(`\nRESULTADO: ${ok} OK`);
} catch (e) {
  console.error('E2E FALLÓ:', e.message);
  process.exitCode = 1;
} finally {
  if (backend) backend.kill();
  await browser.close();
}
