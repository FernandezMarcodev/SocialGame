// Punto de entrada de la SPA.
import './styles/main.css';
import { navigate, handleRoute } from './router.js';
import { store, saveSession, isAuthed } from './store.js';
import { api } from './api.js';
import { toast } from './ui/toast.js';
import { on } from './events.js';
import { connectRT, disconnectRT } from './realtime.js';

// Sesión vencida: cualquier 401 dispara logout global.
window.addEventListener('app:logout', () => {
  saveSession(null);
  toast('Tu sesión expiró. Volvé a iniciar sesión.', 'info');
  navigate('/login');
});

// Mantiene el canal de tiempo real alineado con la sesión.
on('session.changed', (session) => {
  if (session?.token) connectRT();
  else disconnectRT();
});

function boot() {
  if (isAuthed()) connectRT();
  // Si había una redirección pendiente (ruta protegida), se respeta.
  const redirect = sessionStorage.getItem('es10p.redirect');
  if (redirect && redirect !== 'auth') {
    sessionStorage.removeItem('es10p.redirect');
    navigate(redirect);
  } else if (redirect === 'auth') {
    sessionStorage.removeItem('es10p.redirect');
    navigate('/login');
  }

  // Primer render explícito: en la carga inicial no se dispara `hashchange`
  // si ya había un hash en la URL.
  handleRoute();
}

boot();

// Para depuración desde consola.
window.__app = { store, api };
