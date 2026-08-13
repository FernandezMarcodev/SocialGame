// Pantalla 404.
import { h } from '../ui/dom.js';
import { navigate } from '../router.js';

export function notFound(view) {
  return h('div', { class: 'nf' },
    h('div', { class: 'nf-code', text: '4' }),
    h('div', { class: 'nf-code nf-code--mid', text: '0' }),
    h('div', { class: 'nf-code', text: '4' }),
    h('p', { class: 'nf-sub' }, 'Esta pantalla no existe…'),
    h('button', { class: 'btn btn--primary btn--lg', type: 'button', onclick: () => navigate('/'), text: 'Volver al inicio' })
  );
}
