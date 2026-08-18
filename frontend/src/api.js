// Cliente de la API REST.
//
// Se comunica exclusivamente con el backend real (proxy Vite -> localhost:8000).
// Los errores de dominio ({error:{code,message}}) se propagan tal cual.

import { ApiError } from './errors.js';
import { store } from './store.js';

function getToken() {
  return store.session?.token ?? null;
}

function headersFor(opts) {
  const headers = {};
  if (!(opts.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  if (opts.auth !== false) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function restCall(path, opts = {}) {
  let res;
  try {
    res = await fetch(path, {
      method: opts.method ?? 'GET',
      headers: opts.headers,
      body: opts.body instanceof FormData ? opts.body : (opts.body !== undefined ? JSON.stringify(opts.body) : undefined),
    });
  } catch {
    throw new ApiError('No se pudo conectar con el servidor.', { code: 'NETWORK', status: 0 });
  }

  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (res.status === 204 || res.status === 205) return null;

  // Formato de error estándar del sistema (B.3): es un error de dominio.
  if (data && typeof data === 'object' && data.error && typeof data.error.message === 'string') {
    const { code = 'REQUEST_FAILED', message, details = {} } = data.error;
    if (res.status === 401) {
      sessionStorage.setItem('es10p.redirect', 'auth');
      window.dispatchEvent(new CustomEvent('app:logout'));
    }
    throw new ApiError(message, { code, status: res.status, details });
  }

  if (!res.ok) {
    const detail = data?.detail ?? res.statusText ?? 'Error del servidor';
    const msg = Array.isArray(detail) ? detail.map((d) => d.msg ?? JSON.stringify(d)).join('. ') : String(detail);
    throw new ApiError(msg, { code: 'HTTP_' + res.status, status: res.status, details: data });
  }

  return data;
}

export async function call(path, opts = {}) {
  return restCall(path, { ...opts, headers: headersFor(opts) });
}

// ---- Endpoints del Apéndice B.1 -------------------------------------------------

export const api = {
  // Health / info
  root: () => call('/', { auth: false }),
  health: () => call('/health', { auth: false }),

  // Auth
  register: (username, email, password) =>
    call('/api/v1/auth/register', { method: 'POST', body: { username, email, password }, auth: false }),
  login: (identifier, password) => call('/api/v1/auth/login', { method: 'POST', body: { identifier, password }, auth: false }),
  logout: () => call('/api/v1/auth/logout', { method: 'POST' }),
  changePassword: (current_password, new_password) =>
    call('/api/v1/auth/change-password', { method: 'POST', body: { current_password, new_password } }),
  forgotPassword: (email) => call('/api/v1/auth/forgot-password', { method: 'POST', body: { email }, auth: false }),
  resetPassword: (token, new_password) => call('/api/v1/auth/reset-password', { method: 'POST', body: { token, new_password }, auth: false }),

  // Usuarios
   me: () => call('/api/v1/users/me'),
   updateMe: (fields) => call('/api/v1/users/me', { method: 'PATCH', body: fields }),
   updateAvatar: (file) => {
     const form = new FormData();
     form.append('file', file);
     return call('/api/v1/users/me/avatar', { method: 'PUT', body: form });
   },
   updateAvatarPredefined: (avatar_id) => call('/api/v1/users/me/avatar/predefined', { method: 'PUT', body: { avatar_id } }),
   getAvatars: () => call('/api/v1/users/avatars').then((d) => d?.items ?? []),
   forceLeaveGhosts: () => call('/api/v1/users/me/rooms/force-leave', { method: 'POST' }),

  // Modalidades
  modalities: () => call('/api/v1/modalities').then((d) => d?.items ?? []),

  // Salas
  createRoom: (modality_id) => call('/api/v1/rooms', { method: 'POST', body: { modality_id } }),
  getRoom: (code) => call(`/api/v1/rooms/${encodeURIComponent(code)}`),
  joinRoom: (code) => call(`/api/v1/rooms/${encodeURIComponent(code)}/join`, { method: 'POST' }),
  leaveRoom: (code) => call(`/api/v1/rooms/${encodeURIComponent(code)}/leave`, { method: 'POST' }),
  startMatch: (code) => call(`/api/v1/rooms/${encodeURIComponent(code)}/start`, { method: 'POST' }),
  cancelRoom: (code) => call(`/api/v1/rooms/${encodeURIComponent(code)}`, { method: 'DELETE' }),

  // Partidas
  getMatch: (id) => call(`/api/v1/matches/${encodeURIComponent(id)}`),
  getMatchByRoom: (code) => call(`/api/v1/matches/by-room/${encodeURIComponent(code)}`),
  getTurn: (matchId, turnId) => call(`/api/v1/matches/${encodeURIComponent(matchId)}/turns/${encodeURIComponent(turnId)}`),
  submitPhrase: (id, phrase, secret_score) =>
    call(`/api/v1/matches/${encodeURIComponent(id)}/phrase`, { method: 'POST', body: { phrase, secret_score } }),
  submitVote: (id, score) => call(`/api/v1/matches/${encodeURIComponent(id)}/votes`, { method: 'POST', body: { score } }),
  scoreboard: (id) => call(`/api/v1/matches/${encodeURIComponent(id)}/scoreboard`),
  result: (id) => call(`/api/v1/matches/${encodeURIComponent(id)}/result`),
};
