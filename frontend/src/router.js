// Router hash-based para la SPA.
import { mount } from './ui/dom.js';
import * as screens from './screens/index.js';
import { isAuthed } from './store.js';

const root = document.getElementById('app');

function parse(hash) {
  const clean = (hash || '').replace(/^#\/?/, '');
  const [path, query] = clean.split('?');
  const params = new URLSearchParams(query || '');
  const seg = path.split('/').filter(Boolean);
  return { seg, params, path };
}

export function navigate(to) {
  if (to === (location.hash || '')) return;
  location.hash = '#' + to;
}

const PUBLIC = ['landing', 'login', 'register', 'forgot', 'reset'];

export function handleRoute() {
  const { seg, params } = parse(location.hash);
  const name = seg[0] || 'landing';

  if (!PUBLIC.includes(name) && !isAuthed()) {
    sessionStorage.setItem('es10p.redirect', name ? `/${seg.join('/')}` : '/');
    return render('login');
  }

  render(name, { seg, params });
}

function render(name, ctx = {}) {
  const def = screens[name] || screens.notFound;
  screens.shell(root, ctx, def);
  const view = root.querySelector('#view');
  mount(view, def(view, ctx));
}

window.addEventListener('hashchange', handleRoute);
