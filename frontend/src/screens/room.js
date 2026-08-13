// Pantalla de sala: código privado, jugadores y botón de inicio.
// Se sincroniza por el canal de tiempo real (RF-COM-004/005): los eventos
// room.updated / match.started / room.cancelled llegan por WebSocket.
import { h } from '../ui/dom.js';
import { navigate } from '../router.js';
import { api } from '../api.js';
import { store, currentUser } from '../store.js';
import { avatar, codeTiles, pill, spinner } from '../ui/components.js';
import { toast } from '../ui/toast.js';
import { confirmSheet } from '../ui/sheet.js';
import { on, off } from '../events.js';

let node;
let code = null;
let joining = false;
let joinAttempts = 0;
let subs = [];

export function room(v, { seg }) {
  teardown();
  node = h('div', { class: 'room' }, h('div', { class: 'room-loading' }, 'Cargando sala…'));
  code = seg[1];
  load(code);
  return node;
}

function teardown() {
  subs.forEach(({ type, cb }) => off(type, cb));
  subs = [];
  joining = false;
  joinAttempts = 0;
}

function onWs(event, cb) {
  on(event, cb);
  subs.push({ type: event, cb });
}

async function load(roomCode) {
  try {
    const room = await api.getRoom(roomCode);
    store.room = room;
    subscribe(roomCode);
    if (room.state === 'in_match') {
      joinMatch(roomCode);
      return renderInMatch(room);
    }
    render();
  } catch (err) {
    if (err.code === 'ROOM_NOT_FOUND') {
      toast('La sala ya no existe.', 'info');
      store.room = null;
      navigate('/');
      return;
    }
    toast(err.message, 'error');
    navigate('/');
  }
}

function subscribe(roomCode) {
  onWs('rt:match.started', (data) => {
    toast('La partida comenzó.', 'success');
    store.room = null;
    navigate(`/match/${data.match_id}`);
  });

  onWs('rt:room.updated', (data) => {
    if (!location.hash.startsWith('#/room')) return;
    store.room = data;
    render();
  });

  onWs('rt:room.cancelled', () => {
    teardown();
    toast('La sala fue cancelada.', 'info');
    store.room = null;
    navigate('/');
  });

  // Re-sincronización tras una reconexión del canal.
  onWs('rt:open', () => {
    if (location.hash.startsWith('#/room')) load(roomCode);
  });
}

function render() {
  if (!node) return;
  const room = store.room;
  if (!room) return;

  if (room.state === 'in_match') return renderInMatch(room);

  const me = currentUser();
  const isCreator = room.creator_id === me?.id || room.creator === me?.username;
  const minPlayersMet = room.players.length >= room.min_players;

  const actionBtn = h(
    'button',
    {
      class: 'btn btn--primary btn--lg btn--block',
      type: 'button',
      disabled: !isCreator || !minPlayersMet,
      text: isCreator ? (minPlayersMet ? 'Iniciar partida' : 'Esperando jugadores…') : 'Esperando al creador…',
    },
  );
  actionBtn.addEventListener('click', async () => {
    actionBtn.disabled = true;
    actionBtn.classList.add('btn--loading');
    try {
      const res = await api.startMatch(room.code);
      store.room = { ...store.room, state: 'in_match' };
      navigate(`/match/${res.match_id}`);
    } catch (err) {
      toast(err.message, 'error');
      actionBtn.disabled = false;
      actionBtn.classList.remove('btn--loading');
    }
  });

  const secondary = h('button', { class: 'btn btn--ghost', type: 'button', text: isCreator ? 'Cancelar sala' : 'Abandonar sala' });
  secondary.addEventListener('click', () => {
    confirmSheet({
      title: isCreator ? '¿Cancelar la sala?' : '¿Abandonar la sala?',
      message: isCreator ? 'Se eliminará la sala y nadie podrá ingresar.' : 'Perderás el código de esta sala.',
      confirmLabel: 'Sí, continuar',
      danger: true,
      onConfirm: async () => {
        try {
          if (isCreator) await api.cancelRoom(room.code);
          else await api.leaveRoom(room.code);
        } catch (err) {
          toast(err.message, 'error');
        }
        store.room = null;
        navigate('/');
      },
    });
  });

  node.replaceChildren(
    h('div', { class: 'room-hero' },
      h('div', { class: 'room-code-copy' },
        codeTiles(room.code, { size: 'lg' }),
        h('button', { class: 'btn btn--ghost btn--copy', type: 'button', text: 'Copiar' })
      ),
      h('p', { class: 'room-hint' }, 'Compartí este código con tus amigos (máx. 6 jugadores).')
    ),
    h('div', { class: 'room-meta' },
      pill(room.modality?.template || 'Modalidad', 'primary'),
      pill('Esperando jugadores', 'success')
    ),
    h('div', { class: 'room-panel' },
      h('div', { class: 'room-panel-head' },
        h('h2', { class: 'panel-title' }, 'Jugadores'),
        h('span', { class: 'panel-count' }, `${room.players.length}/${room.max_players}`)
      ),
      h('div', { class: 'players-grid' }, room.players.map((p) => playerCard(p, me, isCreator))),
      !minPlayersMet && isCreator
        ? h('p', { class: 'room-waiting' }, `Necesitás al menos ${room.min_players} jugadores para empezar.`)
        : null
    ),
    h('div', { class: 'room-actions' },
      actionBtn,
      secondary
    )
  );
}

function renderInMatch(room) {
  node.replaceChildren(
    h('div', { class: 'room-hero' },
      codeTiles(room.code, { size: 'lg' }),
      h('p', { class: 'room-hint' }, room.modality?.template ? `Modalidad: ${room.modality.template}` : '')
    ),
    h('div', { class: 'match-started' },
      h('div', { class: 'stage-check', text: '🏁' }),
      h('h2', { class: 'match-started-title' }, 'La partida comenzó'),
      h('p', { class: 'match-started-desc' }, 'Te estás uniendo a la partida…'),
      spinner('Ingresando')
    )
  );
}

async function joinMatch(roomCode) {
  if (joining) return;
  if (joinAttempts >= 5) return;
  joining = true;
  joinAttempts += 1;
  try {
    const m = await api.getMatchByRoom(roomCode);
    store.room = null;
    navigate(`/match/${m.match_id}`);
  } catch (err) {
    toast(err.message, 'error');
    joining = false;
    if (location.hash.startsWith('#/room')) {
      setTimeout(() => load(roomCode), 2000);
    }
  }
}

function playerCard(p, me, isCreator) {
  const isMe = p.id === me?.id;
  return h('div', { class: 'player-card' + (isMe ? ' is-me' : '') },
    avatar(p, 56, { crown: isCreator && p.id === (store.room?.creator_id ?? p.id) }),
    h('span', { class: 'player-name', text: p.username }),
    h('div', { class: 'player-tags' },
      isMe ? pill('TÚ', 'accent') : null,
      isCreator ? pill('Creador', 'gold') : null
    )
  );
}
