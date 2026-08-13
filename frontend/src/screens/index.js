// Registro de pantallas + shell (barra superior persistente).
import { h, mount, clear } from '../ui/dom.js';
import { avatar } from '../ui/components.js';
import { isAuthed } from '../store.js';
import { navigate } from '../router.js';
import { on } from '../events.js';

import { landing } from './landing.js';
import { login, register, forgot, reset, verify } from './auth.js';
import { room } from './room.js';
import { match } from './match.js';
import { profile } from './profile.js';
import { notFound } from './notfound.js';

export { landing, login, register, forgot, reset, verify, room, match, profile, notFound };

let listenersAttached = false;

export function shell(root, ctx) {
  if (!root.querySelector('#view')) {
    const header = h(
      'header',
      { class: 'topbar' },
      h(
        'a',
        { class: 'brand', href: '#/', onclick: (e) => { e.preventDefault(); navigate('/'); } },
        h('span', { class: 'brand-badge', text: '10' }),
        h('span', { class: 'brand-name' }, 'Es un 10 pero…')
      ),
      h('div', { class: 'topbar-right' }, isAuthed() ? avatarBtn() : null)
    );
    const view = h('main', { id: 'view', class: 'view' });
    mount(root, h('div', { class: 'app-shell' }, header, view));

    if (!listenersAttached) {
      listenersAttached = true;
      on('session.changed', () => refreshTopbar(root));
    }
  }
}

function refreshTopbar(root) {
  const right = root.querySelector('.topbar-right');
  if (!right) return;
  clear(right);
  if (isAuthed()) right.append(avatarBtn());
}

function avatarBtn() {
  return h(
    'button',
    { class: 'topbar-avatar', title: 'Mi perfil', onclick: () => navigate('/profile') },
    avatar(store.session?.user, 36)
  );
}
