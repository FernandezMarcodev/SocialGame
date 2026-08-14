// Componentes de UI reutilizables.
import { h } from './dom.js';
import { avatarHue } from '../store.js';

// --- Avatar automático (RN-005): inicial sobre gradiente por hash del id. ---
export function avatar(user, size = 44, { crown = false } = {}) {
  const url = user?.profile_image_url;
  if (url && !url.startsWith('/avatars/')) {
    const style = {
      width: `${size}px`,
      height: `${size}px`,
      fontSize: `${Math.round(size * 0.44)}px`,
    };
    return h('div', { class: 'avatar avatar--img', style, title: user?.username },
      h('img', { class: 'avatar-img', src: url, alt: user?.username || '' }),
      crown ? h('span', { class: 'avatar-crown', text: '♛' }) : null
    );
  }
  const initial = String(user?.username || '?').charAt(0).toUpperCase();
  const hue = avatarHue(user?.id || user?.username || '?');
  const style = {
    width: `${size}px`,
    height: `${size}px`,
    fontSize: `${Math.round(size * 0.44)}px`,
    background: `linear-gradient(135deg, hsl(${hue} 82% 62%), hsl(${(hue + 46) % 360} 80% 52%))`,
  };
  return h('div', { class: 'avatar', style, title: user?.username }, initial, crown ? h('span', { class: 'avatar-crown', text: '♛' }) : null);
}

// --- Selector de puntaje 1-10 (RN-012 / RN-015) como cartas de baraja inglesa ---
const CARD_SUITS = ['♠', '♥', '♣', '♦'];
const CARD_RED = ['♥', '♦'];

export function scoreSelector({ selected = null, onSelect, disabled = false } = {}) {
  const node = h('div', { class: 'score-selector score-selector--cards' });
  const buttons = [];
  for (let v = 1; v <= 10; v++) {
    const btn = h(
      'button',
      {
        type: 'button',
        class: 'score-chip card' + (v === selected ? ' is-selected' : ''),
        disabled,
        'aria-label': `Puntaje ${v}`,
        onclick: () => {
          if (disabled) return;
          buttons.forEach((b) => b.classList.remove('is-selected'));
          btn.classList.add('is-selected');
          onSelect?.(v);
        },
      },
      cardFace(v)
    );
    buttons.push(btn);
    node.append(btn);
  }
  return {
    node,
    setValue(v) {
      buttons.forEach((b, i) => b.classList.toggle('is-selected', i + 1 === v));
    },
  };
}

// --- Carta de baraja inglesa estática (revelado de puntaje, etc.) ---
export function scoreCard(v) {
  return h('span', { class: 'card card--static' }, cardFace(v));
}

function cardFace(v) {
  const suit = CARD_SUITS[(v - 1) % CARD_SUITS.length];
  const red = CARD_RED.includes(suit);
  return [
    cardCorner(v, suit),
    h('span', { class: 'card-center card-suit' + (red ? ' is-red' : ''), text: suit }),
    cardCorner(v, suit, true),
  ];
}

function cardCorner(rank, suit, flipped = false) {
  return h(
    'span',
    { class: 'card-corner' + (flipped ? ' card-corner--br' : '') + (CARD_RED.includes(suit) ? ' is-red' : '') },
    h('span', { class: 'card-rank', text: rank }),
    h('span', { class: 'card-suit', text: suit })
  );
}

// --- Código de sala en fichas ---
export function codeTiles(code, { size = 'md' } = {}) {
  return h(
    'div',
    { class: `code-tiles code-tiles--${size}` },
    String(code || '------').split('').map((c) => h('span', { class: 'code-tile' }, c))
  );
}

// --- Píldora / badge ---
export function pill(text, tone = 'neutral') {
  return h('span', { class: `pill pill--${tone}` }, text);
}

// --- Spinner con texto ---
export function spinner(text = 'Cargando…') {
  return h('div', { class: 'spinner-wrap' }, h('span', { class: 'spinner' }), h('span', { class: 'spinner-text', text }));
}

// --- Barra de progreso animada (cuenta regresiva de turno) ---
export function progressBar() {
  const node = h('div', { class: 'progress' }, h('div', { class: 'progress-fill' }));
  const fill = node.querySelector('.progress-fill');
  let raf = null;
  let start = 0;
  let duration = 0;

  const stop = () => {
    if (raf) cancelAnimationFrame(raf);
    raf = null;
  };

  const tick = (now) => {
    const elapsed = now - start;
    const frac = Math.max(0, 1 - elapsed / duration);
    fill.style.width = `${frac * 100}%`;
    if (elapsed < duration) raf = requestAnimationFrame(tick);
  };

  return {
    node,
    start(seconds) {
      stop();
      duration = Math.max(1, seconds) * 1000;
      start = performance.now();
      raf = requestAnimationFrame(tick);
    },
    pause() {
      stop();
      const frac = parseFloat(fill.style.width || '100') / 100;
      start = performance.now();
      duration = duration * frac;
      raf = requestAnimationFrame(tick);
    },
    stop,
    set(frac) {
      stop();
      fill.style.width = `${Math.max(0, Math.min(1, frac)) * 100}%`;
    },
  };
}


