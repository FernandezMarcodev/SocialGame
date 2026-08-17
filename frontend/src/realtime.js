// Cliente WebSocket del módulo de tiempo real (RF-COM-001, AD-004).
//
// Conexión persistente autenticada con el token de sesión. Los eventos
// recibidos se despachan en el bus global como `rt:<evento>` (p. ej.
// `rt:match.started`), con reconexión automática con backoff.
// Incluye heartbeat (ping/pong) para mantener la conexión viva a través
// de NATs, firewalls y balanceadores de carga en Internet.
import { store } from './store.js';
import { emit } from './events.js';

let ws = null;
let shouldReconnect = false;
let retries = 0
let reconnectTimer = null;
let pongTimeout = null;
const PONG_TIMEOUT_MS = 10000;

export function connectRT() {
  if (!store.session?.token || ws) return;
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/api/v1/ws?token=${encodeURIComponent(store.session.token)}`);
  shouldReconnect = true;

  ws.onopen = () => {
    retries = 0;
    emit('rt:open');
    startPongMonitor();
  };

  ws.onmessage = (e) => {
    let msg;
    try {
      msg = JSON.parse(e.data);
    } catch {
      return;
    }
    if (msg?.type === 'ping') {
      sendPong();
      return;
    }
    if (msg?.type === 'pong') {
      clearTimeout(pongTimeout);
      startPongMonitor();
      return;
    }
    if (msg?.event) emit(`rt:${msg.event}`, msg.data);
  };

  ws.onclose = () => {
    ws = null;
    clearTimeout(pongTimeout);
    scheduleReconnect();
  };

  ws.onerror = () => {
    // El cierre real llega por `onclose`.
  };
}

function sendPong() {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: 'pong' }));
  }
}

function startPongMonitor() {
  clearTimeout(pongTimeout);
  pongTimeout = setTimeout(() => {
    if (ws) {
      ws.close();
    }
  }, PONG_TIMEOUT_MS);
}

export function disconnectRT() {
  shouldReconnect = false;
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  clearTimeout(pongTimeout);
  if (ws) {
    ws.onclose = null;
    ws.close();
    ws = null;
  }
}

function scheduleReconnect() {
  if (!shouldReconnect || reconnectTimer) return;
  const delay = Math.min(1000 * 2 ** retries, 15000);
  retries += 1;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    ws = null;
    connectRT();
  }, delay);
}
