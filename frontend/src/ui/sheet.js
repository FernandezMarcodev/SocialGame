// Hojas / modales de confirmación con estética Apple (sheet).
import { h, clear } from './dom.js';

let active = null;

export function openSheet({ title, body, actions = [], dismissable = true }) {
  const root = document.getElementById('sheet-root');
  if (active) closeSheet();

  const overlay = h('div', { class: 'sheet-overlay', onclick: (e) => e.target === overlay && dismissable && closeSheet() });
  const sheet = h(
    'div',
    { class: 'sheet' },
    h('div', { class: 'sheet-grabber' }),
    title ? h('div', { class: 'sheet-title' }, title) : null,
    h('div', { class: 'sheet-body' }, body),
    actions.length
      ? h('div', { class: 'sheet-actions' }, actions.map((a) => a.button))
      : null
  );
  overlay.append(sheet);
  root.append(overlay);
  requestAnimationFrame(() => overlay.classList.add('sheet-overlay--open'));
  active = { overlay, actions };

  const close = () => closeSheet();
  return { close, overlay, sheet };
}

export function closeSheet() {
  if (!active) return;
  const { overlay } = active;
  active = null;
  overlay.classList.remove('sheet-overlay--open');
  setTimeout(() => overlay.remove(), 300);
}

export function confirmSheet({ title, message, confirmLabel = 'Confirmar', cancelLabel = 'Cancelar', danger = false, onConfirm }) {
  const state = { confirmed: false };
  const okBtn = h('button', { class: `btn btn--${danger ? 'danger' : 'primary'}`, type: 'button' }, confirmLabel);
  const cancelBtn = h('button', { class: 'btn btn--ghost', type: 'button' }, cancelLabel);
  const sheet = openSheet({
    title,
    body: h('p', { class: 'sheet-message' }, message),
    actions: [
      { button: cancelBtn },
      {
        button: okBtn,
      },
    ],
  });
  cancelBtn.addEventListener('click', () => {
    state.confirmed = false;
    sheet.close();
  });
  okBtn.addEventListener('click', async () => {
    state.confirmed = true;
    okBtn.disabled = true;
    okBtn.classList.add('btn--loading');
    try {
      await onConfirm();
      sheet.close();
    } catch (e) {
      okBtn.disabled = false;
      okBtn.classList.remove('btn--loading');
      throw e;
    }
  });
  return state;
}
