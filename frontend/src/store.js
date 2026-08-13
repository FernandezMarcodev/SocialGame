// Estado global de la aplicación con persistencia en localStorage.
import { emit } from './events.js';

const LS_KEY = 'es10p.session';

function loadSession() {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    /* ignore */
  }
  return null;
}

export const store = {
  session: loadSession(), // { token, user }
  room: null,
  match: null,
};

export function saveSession(session) {
  store.session = session;
  if (session) localStorage.setItem(LS_KEY, JSON.stringify(session));
  else localStorage.removeItem(LS_KEY);
  emit('session.changed', session);
}

export function setUser(user) {
  if (!store.session) return;
  store.session = { ...store.session, user };
  localStorage.setItem(LS_KEY, JSON.stringify(store.session));
  emit('session.changed', store.session);
}

export function uid() {
  return 'u-' + Math.random().toString(36).slice(2, 10);
}

export function currentUser() {
  return store.session?.user ?? null;
}

export function isAuthed() {
  return Boolean(store.session?.token && store.session?.user);
}

export function avatarHue(seed) {
  let h = 0;
  for (const c of String(seed)) h = (h * 31 + c.charCodeAt(0)) % 360;
  return h;
}
