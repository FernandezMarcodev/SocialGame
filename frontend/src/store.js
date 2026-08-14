// Estado global de la aplicación con persistencia en localStorage.
import { emit } from './events.js';

// Todas las cuentas persistidas (sobrevive a reinicios del navegador).
const LS_SESSIONS = 'es10p.sessions'; // { [userId]: { token, user } }

// Cuenta activa DE ESTA PESTAÑA (sessionStorage → por pestaña, no compartido).
const SS_ACTIVE = 'es10p.active'; // userId

function loadSessions() {
  try {
    const raw = localStorage.getItem(LS_SESSIONS);
    if (raw) return JSON.parse(raw);
  } catch {
    /* ignore */
  }
  return {};
}

function persistSessions(map) {
  localStorage.setItem(LS_SESSIONS, JSON.stringify(map));
}

function activeUserId() {
  try {
    return sessionStorage.getItem(SS_ACTIVE) || null;
  } catch {
    return null;
  }
}

function activeSession() {
  const id = activeUserId();
  if (!id) return null;
  return loadSessions()[id] ?? null;
}

export const store = {
  // Sesión activa de esta pestaña (puede ser null).
  session: activeSession(),
  room: null,
  match: null,
};

export function saveSession(session) {
  const map = loadSessions();
  if (session && session.user?.id) {
    map[session.user.id] = session;
    try {
      sessionStorage.setItem(SS_ACTIVE, session.user.id);
    } catch {
      /* ignore */
    }
    store.session = session;
  } else {
    // Logout solo de la cuenta activa en esta pestaña.
    const id = activeUserId();
    if (id) delete map[id];
    try {
      sessionStorage.removeItem(SS_ACTIVE);
    } catch {
      /* ignore */
    }
    store.session = null;
  }
  persistSessions(map);
  emit('session.changed', store.session);
}

export function setUser(user) {
  const session = store.session;
  if (!session || !user?.id) return;
  const updated = { ...session, user };
  const map = loadSessions();
  map[user.id] = updated;
  persistSessions(map);
  store.session = updated;
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

// Sincroniza cambios hechos en OTRAS pestañas sobre la cuenta activa de esta.
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (e) => {
    if (e.key !== LS_SESSIONS) return;
    const next = activeSession();
    const changed = JSON.stringify(store.session) !== JSON.stringify(next);
    if (changed) {
      store.session = next;
      emit('session.changed', next);
    }
  });
}
