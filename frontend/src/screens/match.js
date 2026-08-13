// Pantalla de partida: fases de turno, votación, resultados y marcador.
// Se sincroniza con el backend real por polling (la API es REST, sin WebSocket).
import { h } from '../ui/dom.js';
import { navigate } from '../router.js';
import { api } from '../api.js';
import { store, currentUser } from '../store.js';
import { avatar, codeTiles, progressBar, scoreCard, scoreSelector, spinner } from '../ui/components.js';
import { toast } from '../ui/toast.js';

const POLL_MS = 1200;
const RESULT_SHOW_MS = 4500;

let view;
let M = null;
let tickTimer = null;
let progress = null;
let pollTimer = null;
let finishTimer = null;

export function match(v, { seg }) {
  view = v;
  load(seg[1]);
  return h('div', { class: 'match-loading' }, spinner('Cargando partida…'));
}

async function load(id) {
  try {
    const m = await api.getMatch(id);
    M = normalizeMatch(m, id);
    store.match = M;
    render();
    fetchModality();
    poll();
    pollTimer = setInterval(poll, POLL_MS);
  } catch (err) {
    toast(err.message, 'error');
    navigate('/');
  }
}

function normalizeMatch(raw, id) {
  return {
    id: raw.match_id ?? id,
    room_code: raw.room_code ?? '',
    players: raw.players ?? [],
    order: raw.turn_order ?? [],
    scores: raw.scores ?? {},
    state: raw.state ?? 'initialized',
    turn_id: raw.current_turn ?? null,
    modality: null,
    phase: 'idle',
    author_id: null,
    phrase: null,
    expires_at: null,
    voting_ends_at: null,
    votes: [],
    votes_count: 0,
    result: null,
    winner: null,
    tie: false,
    tie_players: [],
    matchFinished: false,
    turn_index: 0,
    total: 0,
    _iVoted: false,
    _phraseSent: false,
    _lastResultTurn: null,
    _resultUntil: null,
  };
}

// La modalidad no viaja en MatchOut: se toma de la sala (existe mientras la
// partida está en curso). Si la sala ya no está, se usa la plantilla por defecto.
async function fetchModality() {
  if (!M?.room_code) return;
  try {
    const room = await api.getRoom(M.room_code);
    if (room?.modality) M.modality = room.modality;
    render();
  } catch {
    /* sala eliminada al terminar la partida: se ignora */
  }
}

// ---- polling ----------------------------------------------------------------

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

function clearTick() {
  if (tickTimer) {
    clearInterval(tickTimer);
    tickTimer = null;
  }
}

function clearFinishTimer() {
  if (finishTimer) {
    clearTimeout(finishTimer);
    finishTimer = null;
  }
}

async function poll() {
  if (!M) return;
  try {
    const m = await api.getMatch(M.id);
    if (m.state === 'finished') return await handleFinished(m);
    const turn = m.current_turn ? await api.getTurn(M.id, m.current_turn) : null;
    return await applyMatch(m, turn);
  } catch (err) {
    if (err.code === 'MATCH_NOT_FOUND') {
      stopPolling();
      toast('La partida ya terminó.', 'info');
      leave();
    }
  }
}

async function handleFinished(m) {
  updateDerived(m);
  // Mostrar el resultado del último turno (revelado del puntaje secreto)…
  if (M.turn_id && M._lastResultTurn !== M.turn_id) {
    try {
      const prev = await api.getTurn(M.id, M.turn_id);
      M.result = resultFromTurn(prev);
      M.phrase = prev.phrase ?? M.phrase;
      M._lastResultTurn = M.turn_id;
      M.matchFinished = true;
      M.phase = 'result';
      stopPolling();
      render();
      clearFinishTimer();
      finishTimer = setTimeout(showFinish, 12000);
      return;
    } catch {
      /* si el turno no existe, se muestra el podio directamente */
    }
  }
  await showFinish();
}

async function showFinish() {
  stopPolling();
  clearFinishTimer();
  try {
    const r = await api.result(M.id);
    M.winner = r.winner_id;
    M.tie = r.tied;
    M.scores = r.scores;
    const top = Math.max(...Object.values(r.scores));
    M.tie_players = Object.entries(r.scores).filter(([, s]) => s === top).map(([id]) => id);
  } catch {
    /* sin red: se muestra el marcador local */
  }
  M.phase = 'finished';
  confetti();
  render();
}

async function applyMatch(m, turn) {
  const now = Date.now();

  // ¿Estamos mostrando un resultado y todavía no se agotó el tiempo de muestra?
  if (M.phase === 'result' && M._resultUntil && now < M._resultUntil) {
    updateDerived(m);
    render();
    return;
  }
  M._resultUntil = null;

  const prevId = M.turn_id;
  const newId = m.current_turn;

  if (newId && newId !== prevId) {
    // Cambió el turno → revelar el resultado del turno anterior.
    if (prevId && M._lastResultTurn !== prevId) {
      try {
        const prev = await api.getTurn(M.id, prevId);
        M.result = resultFromTurn(prev);
        M.phrase = prev.phrase ?? M.phrase;
        M.author_id = prev.author_id;
        M._lastResultTurn = prevId;
        M._resultUntil = Date.now() + RESULT_SHOW_MS;
        M.matchFinished = false;
        M.phase = 'result';
        updateDerived(m);
        render();
        return;
      } catch {
        /* si no se puede revelar, se sigue al turno actual */
      }
    }
    M.turn_id = newId;
    M._iVoted = false;
    M._phraseSent = false;
    M.result = null;
    M.phrase = null;
  }

  if (turn) {
    M.author_id = turn.author_id;
    M.expires_at = turn.expires_at;
    M.voting_ends_at = turn.voting_ends_at;
    M.votes_count = turn.votes_count;
    if (turn.state === 'active') {
      M.phase = 'authoring';
      M.phrase = null;
    } else if (turn.state === 'voting') {
      M.phase = 'voting';
      M.phrase = turn.phrase;
    } else {
      M.phase = 'result';
      M.result = resultFromTurn(turn);
    }
  } else {
    M.phase = 'idle';
  }

  updateDerived(m);
  render();
}

function updateDerived(m) {
  M.players = m.players ?? M.players;
  M.order = m.turn_order ?? M.order;
  M.scores = m.scores ?? M.scores;
  M.state = m.state ?? M.state;
  M.room_code = m.room_code ?? M.room_code;
  M.turn_index = Math.max(0, M.order.indexOf(M.author_id));
  M.total = M.order.length;
}

function resultFromTurn(turn) {
  return {
    secret_score: turn.secret_score ?? null,
    votes: (turn.votes || []).map((v) => ({ voter: v.voter_id, value: v.value })),
    points: turn.points ?? 0,
    skipped: turn.state === 'discarded',
  };
}

// ---- temporizador ------------------------------------------------------------

function countdownBar(label, deadlineMs, key) {
  const now = Date.now();
  if (key !== M._cdKey) {
    M._cdKey = key;
    M._deadline = deadlineMs && deadlineMs > now ? deadlineMs : now + 60_000;
  }
  const deadline = M._deadline;
  const seconds = Math.max(1, Math.round((deadline - now) / 1000));
  const bar = progressBar();
  progress = bar;
  clearTick();
  const update = () => {
    const left = Math.max(0, deadline - Date.now());
    bar.set(left / (seconds * 1000));
    if (left <= 0) clearTick();
  };
  update();
  tickTimer = setInterval(update, 200);
  return h('div', { class: 'stage-countdown' },
    h('span', { class: 'stage-countdown-label', text: label }),
    bar.node
  );
}

// ---- render ------------------------------------------------------------------

function render() {
  if (!view || !M) return;
  if (!['authoring', 'voting'].includes(M.phase)) clearTick();
  const me = currentUser();

  const stage = h('div', { class: 'match-stage' }, renderStage(me));

  const main = h('div', { class: 'match-main' },
    h('div', { class: 'match-top' },
      h('div', { class: 'match-top-info' },
        h('h1', { class: 'match-title' }, 'Partida'),
        M.modality?.template ? h('span', { class: 'match-modality' }, M.modality.template) : null
      ),
      h('div', { class: 'match-top-right' },
        h('span', { class: 'match-round' }, `Ronda · Turno ${Math.min(M.turn_index + 1, Math.max(1, M.total))} de ${M.total}`),
        h('button', { class: 'btn btn--ghost btn--sm', type: 'button', text: 'Salir', onclick: leave })
      )
    ),
    turnPills(),
    stage
  );

  view.replaceChildren(
    h('div', { class: 'match' },
      main,
      h('aside', { class: 'scoreboard' }, renderScoreboard())
    )
  );
}

function leave() {
  stopPolling();
  clearTick();
  clearFinishTimer();
  store.match = null;
  navigate('/');
}

function playerName(id) {
  return M.players.find((p) => p.id === id)?.username ?? '?';
}

function playerById(id) {
  return M.players.find((p) => p.id === id);
}

// ---- píldoras de progreso de ronda -------------------------------------------

function turnPills() {
  const me = currentUser();
  return h('div', { class: 'turn-pills' },
    M.order.map((id, i) => {
      const p = M.players.find((x) => x.id === id);
      let state = 'done';
      if (i === M.turn_index && M.phase !== 'finished') state = 'current';
      else if (i > M.turn_index) state = 'pending';
      const isMe = id === me?.id;
      return h('div', { class: `turn-pill turn-pill--${state}` + (isMe ? ' is-me' : '') },
        avatar(p || { id, username: '?' }, 34),
        h('span', { class: 'turn-pill-name', text: p?.username ?? '?' }),
        state === 'current' ? h('span', { class: 'turn-pill-state', text: 'autor' }) : null
      );
    })
  );
}

// ---- etapa principal -----------------------------------------------------------

function renderStage(me) {
  const isAuthor = M.author_id === me?.id;

  if (M.phase === 'finished') return finishStage();

  if (M.phase === 'idle') {
    return h('div', { class: 'stage-idle' }, spinner('Preparando la partida…'));
  }

  if (M.phase === 'authoring') {
    if (isAuthor && M._phraseSent) {
      clearTick();
      return h('div', { class: 'stage' },
        h('div', { class: 'stage-check', text: '✓' }),
        h('p', { class: 'stage-title' }, '¡Frase enviada!'),
        h('p', { class: 'stage-sub' }, 'Comienza la votación…')
      );
    }
    if (isAuthor) return authorForm(me);
    return h('div', { class: 'stage' },
      h('div', { class: 'stage-author-avatar' }, avatar(playerById(M.author_id) || { username: '?' }, 64)),
      h('p', { class: 'stage-title' }, `${playerName(M.author_id)} está escribiendo su frase…`),
      h('p', { class: 'stage-sub' }, 'El puntaje se mantiene en secreto hasta que todos voten.'),
      countdownBar('Tiempo del autor', M.expires_at, `author:${M.turn_id}`)
    );
  }

  if (M.phase === 'voting') {
    if (isAuthor) {
      return h('div', { class: 'stage' },
        h('p', { class: 'stage-title' }, 'Votación en curso'),
        h('p', { class: 'stage-sub' }, `${M.votes_count}/${Math.max(1, M.order.length - 1)} jugadores votaron`),
        voteProgress(),
        countdownBar('Tiempo de votación', M.voting_ends_at, `vote:${M.turn_id}`)
      );
    }
    if (M._iVoted) {
      return h('div', { class: 'stage' },
        h('div', { class: 'stage-check', text: '✓' }),
        h('p', { class: 'stage-title' }, '¡Voto registrado!'),
        h('p', { class: 'stage-sub' }, `${M.votes_count}/${Math.max(1, M.order.length - 1)} jugadores votaron`),
        voteProgress(),
        countdownBar('Tiempo de votación', M.voting_ends_at, `vote:${M.turn_id}`)
      );
    }
    return votingForm(me);
  }

  // result
  return resultStage(me);
}

function voteProgress() {
  const total = Math.max(1, M.order.length - 1);
  const pct = Math.round((M.votes_count / total) * 100);
  return h('div', { class: 'vote-progress' },
    h('div', { class: 'vote-progress-track' },
      h('div', { class: 'vote-progress-fill', style: { width: `${pct}%` } })
    )
  );
}

function authorForm(me) {
  const input = h('input', {
    class: 'input input--inline',
    type: 'text',
    placeholder: 'completá la frase…',
    maxlength: '80',
    autofocus: true,
  });
  const base = String(M.modality?.template || 'Es un 10 pero…').replace(/…\s*$/, '').trim();
  const selector = scoreSelector({});
  let selected = null;
  selector.node.setAttribute('role', 'radiogroup');
  selector.node.addEventListener('click', (e) => {
    const btn = e.target.closest('.score-chip');
    if (btn) {
      selected = Number(btn.textContent);
      selector.setValue(selected);
      submitBtn.disabled = false;
    }
  });

  const submitBtn = h('button', { class: 'btn btn--primary btn--lg btn--block', type: 'button', disabled: true, text: 'Enviar frase' });
  submitBtn.addEventListener('click', () => {
    const phrase = `${base} ${input.value.trim()}`.trim();
    if (!input.value.trim()) return toast('Escribí cómo completás la frase.', 'info');
    if (!selected) return toast('Elegí tu puntaje secreto del 1 al 10.', 'info');
    submitBtn.disabled = true;
    api.submitPhrase(M.id, phrase, selected)
      .then(() => {
        M._phraseSent = true;
        M.secret = selected;
        render();
      })
      .catch((err) => {
        toast(err.message, 'error');
        submitBtn.disabled = false;
      });
  });

  return h('div', { class: 'stage' },
    h('p', { class: 'stage-label' }, 'Tu turno de autor'),
    h('h2', { class: 'stage-phrase' },
      h('span', { text: base }),
      h('span', { class: 'stage-phrase-sep', text: ' ' }), '…'
    ),
    input,
    h('p', { class: 'stage-field-hint' }, 'Ahora elegí en secreto el puntaje que le pondrías a tu frase (1 a 10):'),
    selector.node,
    submitBtn,
    countdownBar('Tiempo del autor', M.expires_at, `author-form:${M.turn_id}`)
  );
}

function votingForm(me) {
  const selector = scoreSelector({});
  let selected = null;
  selector.node.addEventListener('click', (e) => {
    const btn = e.target.closest('.score-chip');
    if (btn) {
      selected = Number(btn.textContent);
      selector.setValue(selected);
      submitBtn.disabled = false;
    }
  });

  const submitBtn = h('button', { class: 'btn btn--primary btn--lg btn--block', type: 'button', disabled: true, text: 'Enviar voto' });
  submitBtn.addEventListener('click', () => {
    if (!selected) return toast('Elegí un puntaje del 1 al 10.', 'info');
    submitBtn.disabled = true;
    api.submitVote(M.id, selected)
      .then(() => {
        M._iVoted = true;
        render();
      })
      .catch((err) => {
        if (err.code === 'ALREADY_VOTED') {
          M._iVoted = true;
          toast('Ya emitiste tu voto.', 'info');
          render();
          return;
        }
        toast(err.message, 'error');
        submitBtn.disabled = false;
      });
  });

  return h('div', { class: 'stage' },
    h('p', { class: 'stage-label' }, 'Tu voto'),
    h('h2', { class: 'stage-phrase stage-phrase--vote' }, '¿Cuánto apostó ', h('span', { class: 'stage-author-name', text: playerName(M.author_id) }), '?'),
    M.phrase ? h('p', { class: 'stage-quote' }, `“${M.phrase}”`) : h('p', { class: 'stage-quote' }, 'La frase aún no se publica…'),
    selector.node,
    submitBtn,
    countdownBar('Tiempo de votación', M.voting_ends_at, `vote-form:${M.turn_id}`)
  );
}

function resultStage(me) {
  const r = M.result || { secret_score: null, votes: [], points: 0, skipped: false };
  const isAuthor = M.author_id === me?.id;
  const authorName = playerName(M.author_id);

  const votesList = (r.votes || []).map((v) => {
    const hit = r.secret_score != null && v.value === r.secret_score;
    const voterName = playerName(v.voter);
    return h('div', { class: 'vote-result' + (hit ? ' is-hit' : '') },
      avatar(playerById(v.voter) || { username: voterName }, 30),
      h('span', { class: 'vote-result-name', text: voterName }),
      h('span', { class: 'vote-result-value', text: v.value }),
      h('span', { class: 'vote-result-icon', text: hit ? '✓' : '✗' })
    );
  });

  return h('div', { class: 'stage stage--result' },
    h('p', { class: 'stage-label' }, 'Resultado del turno'),
    h('h2', { class: 'stage-author-name' }, authorName),
    r.skipped
      ? h('p', { class: 'stage-quote' }, 'El autor no escribió su frase a tiempo. El turno se descartó.')
      : h('p', { class: 'stage-quote' }, `“${r.secret_score != null ? M.phrase : '—'}”`),
    h('div', { class: 'secret-reveal' },
      h('span', { class: 'secret-reveal-label' }, 'Puntaje secreto'),
      r.secret_score != null ? scoreCard(r.secret_score) : h('span', { class: 'secret-reveal-score secret-reveal-score--none', text: '—' })
    ),
    h('div', { class: 'vote-results' }, votesList.length ? votesList : h('p', { class: 'stage-sub', text: 'No hubo votos.' })),
    h('div', { class: 'points-banner' },
      h('span', { class: 'points-banner-icon', text: '★' }),
      h('span', {}, r.points === 1 ? `${authorName} suma 1 punto` : `${authorName} suma ${r.points} puntos`),
      isAuthor && r.points > 0 ? h('span', { class: 'points-banner-you', text: '¡Sos vos!' }) : null
    ),
    M.matchFinished
      ? h('button', { class: 'btn btn--primary btn--lg btn--block', type: 'button', text: 'Ver podio final', onclick: showFinish })
      : null
  );
}

function finishStage() {
  const winnerName = M.winner ? playerName(M.winner) : null;
  const tieNames = (M.tie_players || []).map(playerName);

  const podium = h('div', { class: 'finish-podium' },
    h('div', { class: 'finish-trophy', text: '🏆' }),
    M.tie
      ? h('h2', { class: 'finish-title' }, '¡Empate!')
      : h('h2', { class: 'finish-title' }, `${winnerName} ganó la partida`),
    M.tie
      ? h('p', { class: 'finish-sub' }, `${tieNames.join(' y ')} compartieron el podio.`)
      : h('p', { class: 'finish-sub' }, `${winnerName} sumó la mayor cantidad de puntos.`)
  );

  return h('div', { class: 'stage stage--finish' },
    podium,
    finalScoreboard(),
    h('button', { class: 'btn btn--primary btn--lg btn--block', type: 'button', text: 'Volver al inicio', onclick: () => { store.match = null; navigate('/'); } })
  );
}

function finalScoreboard() {
  const sorted = sortedScores();
  return h('div', { class: 'final-scoreboard' },
    sorted.map(([id, score], i) => {
      const p = playerById(id);
      const rank = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}º`;
      return h('div', { class: 'final-row' + (M.winner === id || M.tie_players?.includes(id) ? ' is-winner' : '') },
        h('span', { class: 'final-rank', text: rank }),
        avatar(p || { username: '?' }, 40),
        h('span', { class: 'final-name', text: p?.username ?? '?' }),
        h('span', { class: 'final-score', text: score })
      );
    })
  );
}

// ---- marcador ----------------------------------------------------------------

function renderScoreboard() {
  const me = currentUser();
  const rows = sortedScores().map(([id, score], i) => {
    const p = playerById(id);
    const isAuthor = M.author_id === id && M.phase !== 'finished';
    return h('div', { class: 'score-row' + (isAuthor ? ' is-author' : '') + (id === me?.id ? ' is-me' : '') },
      h('span', { class: 'score-rank', text: `${i + 1}` }),
      avatar(p || { username: '?' }, 32),
      h('span', { class: 'score-name', text: p?.username ?? '?' }),
      isAuthor ? h('span', { class: 'score-role', text: 'autor' }) : null,
      h('span', { class: 'score-value', text: score })
    );
  });

  return h('div', { class: 'scoreboard-inner' },
    h('div', { class: 'scoreboard-head' },
      h('h2', { class: 'panel-title' }, 'Marcador'),
      M.room_code ? codeTiles(M.room_code, { size: 'sm' }) : null
    ),
    rows
  );
}

function sortedScores() {
  return Object.entries(M.scores || {}).sort((a, b) => b[1] - a[1]);
}

// ---- confeti -------------------------------------------------------------------

function confetti() {
  const colors = ['#2ea572', '#7fd0a8', '#c9ecd9', '#2faf98', '#5fbf7f', '#eefbf3'];
  const container = h('div', { class: 'confetti' });
  for (let i = 0; i < 90; i++) {
    const piece = h('span', {
      class: 'confetti-piece',
      style: {
        left: `${Math.random() * 100}%`,
        background: colors[i % colors.length],
        animationDelay: `${Math.random() * 0.4}s`,
        transform: `rotate(${Math.random() * 360}deg) scale(${0.6 + Math.random() * 0.8})`,
        '--drift': `${(Math.random() - 0.5) * 200}px`,
      },
    });
    container.append(piece);
  }
  document.body.append(container);
  setTimeout(() => container.remove(), 3500);
}
