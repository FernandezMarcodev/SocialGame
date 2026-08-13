// Notificaciones tipo "toast" (estilo Material snackbar).
import { h } from './dom.js';

export function toast(message, type = 'info', ms = 3800) {
  const root = document.getElementById('toasts');
  if (!root) return;

  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const node = h('div', { class: `toast toast--${type}` }, h('span', { class: 'toast-icon' }, icons[type] || '•'), h('span', { class: 'toast-msg' }, message));

  root.append(node);
  requestAnimationFrame(() => node.classList.add('toast--show'));

  setTimeout(() => {
    node.classList.remove('toast--show');
    setTimeout(() => node.remove(), 350);
  }, ms);
}
