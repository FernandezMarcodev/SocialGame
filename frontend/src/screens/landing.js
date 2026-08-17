// Pantalla de inicio: hero + dashboard (crear / unirse a sala).
import { h } from '../ui/dom.js';
import { navigate } from '../router.js';
import { api } from '../api.js';
import { currentUser, store } from '../store.js';
import { avatar, pill } from '../ui/components.js';
import { openSheet } from '../ui/sheet.js';
import { toast } from '../ui/toast.js';

export function landing(view) {
  if (store.session) return dashboard(view);
  return hero(view);
}

function hero(view) {
  const node = h('div', { class: 'landing' },
    h('section', { class: 'hero' },
      h('p', { class: 'hero-kicker' }, 'Videojuego multijugador · por turnos'),
      h('h1', { class: 'hero-title' }, 'Es un ', h('span', { class: 'hero-title--gradient', text: '10' }), ' pero…'),
      h('p', { class: 'hero-sub' },
        'Completá la frase, asignale un puntaje secreto del 1 al 10 y adiviná el de tus amigos.',
        ' El que acierte exacto, suma.'
      ),
      h('div', { class: 'hero-chips' },
        pill('2 a 6 jugadores'),
        pill('Ronda por turnos'),
        pill('Puntaje secreto 1–10'),
        pill('Partidas privadas')
      ),
      h('div', { class: 'hero-cta' },
        h('button', { class: 'btn btn--primary btn--lg', type: 'button', onclick: () => navigate('/register') },
          h('span', { class: 'btn-icon', text: '▶' }), 'Jugar ahora'),
        h('button', { class: 'btn btn--glass btn--lg', type: 'button', onclick: () => navigate('/login') }, 'Ya tengo cuenta')
      )
    ),
    h('section', { class: 'howto' },
      h('div', { class: 'howto-head' },
        h('h2', { class: 'howto-title' }, 'Cómo se juega'),
        h('a', { class: 'howto-link', href: '#/howto', text: 'Ver guía completa', onclick: (e) => { e.preventDefault(); navigate('/howto'); } })
      ),
      h('div', { class: 'howto-grid' },
        step('1', 'Creá o uníte a una sala', 'Con un código privado compartís la sala con hasta 6 jugadores.'),
        step('2', 'Completá la frase', 'Cuando es tu turno, terminás la frase y elegís un puntaje secreto del 1 al 10.'),
        step('3', 'Adiviná a tus amigos', 'En los turnos de los demás, votás cuánto creés que apostó cada uno.'),
        step('4', 'Sumá y ganá', 'El autor suma un punto por cada acierto exacto. El máximo al final de la ronda, gana.')
      )
    )
  );
  return node;
}

function step(num, title, desc) {
  return h('div', { class: 'howto-card' },
    h('span', { class: 'howto-num', text: num }),
    h('h3', { class: 'howto-card-title' }, title),
    h('p', { class: 'howto-card-desc' }, desc)
  );
}

function dashboard(view) {
  const user = currentUser();
  return h('div', { class: 'dash' },
    h('section', { class: 'dash-hero' },
      h('div', { class: 'dash-avatar-wrap' }, avatar(user, 72)),
      h('div',
        h('p', { class: 'dash-greeting' }, 'Hola, '),
        h('h1', { class: 'dash-name' }, user?.username),
        h('p', { class: 'dash-hint' }, '¿Con quién jugamos hoy?')
      )
    ),
    h('section', { class: 'dash-grid' },
      createCard(),
      joinCard()
    ),
    h('section', { class: 'dash-ghost' },
      ghostCard(),
      devInfoCard()
    )
  );
}

function createCard() {
  return h('div', { class: 'dash-card' },
    h('div', { class: 'dash-card-icon dash-card-icon--create', text: '+' }),
    h('h2', { class: 'dash-card-title' }, 'Crear una sala'),
    h('p', { class: 'dash-card-desc' }, 'Elegí una modalidad y compartí el código con tus amigos.'),
    h('button', { class: 'btn btn--primary btn--block', type: 'button', onclick: pickModality }, 'Crear sala')
  );
}

function joinCard() {
  const input = h('input', {
    class: 'join-input',
    type: 'text',
    maxlength: '6',
    placeholder: 'Código · AB12CD',
    autocapitalize: 'characters',
    autocomplete: 'off',
    spellcheck: 'false',
  });
  input.addEventListener('input', () => {
    input.value = input.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 6);
  });
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') submit(); });

  const submit = async () => {
    const code = input.value.trim();
    if (code.length < 4) return toast('Ingresá el código de la sala.', 'info');
    input.disabled = true;
    try {
      const room = await api.joinRoom(code);
      store.room = room;
      navigate(`/room/${room.code}`);
    } catch (err) {
      toast(err.message, 'error');
      input.disabled = false;
    }
  };

  return h('div', { class: 'dash-card' },
    h('div', { class: 'dash-card-icon dash-card-icon--join', text: '⌁' }),
    h('h2', { class: 'dash-card-title' }, 'Unirse a una sala'),
    h('p', { class: 'dash-card-desc' }, '¿Te pasaron un código? Entrá directo a la partida.'),
    input,
    h('button', { class: 'btn btn--glass btn--block', type: 'button', onclick: submit }, 'Unirse')
  );
}

function ghostCard() {
  const btn = h(
    'button',
    { class: 'btn btn--glass btn--block', type: 'button', text: 'Desconectar sala fantasma' }
  );
  btn.addEventListener('click', async () => {
    btn.disabled = true;
    btn.classList.add('btn--loading');
    try {
      const result = await api.forceLeaveGhosts();
      if (result.disconnected) {
        toast('Sala fantasma limpiada. Ya podés crear o unirte a una sala.', 'success');
      } else {
        toast(result.message || 'No estabas en ninguna sala.', 'info');
      }
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.classList.remove('btn--loading');
    }
  });

  return h('div', { class: 'dash-card' },
    h('div', { class: 'dash-card-icon dash-card-icon--ghost', text: '👻' }),
    h('h2', { class: 'dash-card-title' }, 'Sala fantasma'),
    h('p', { class: 'dash-card-desc' }, 'Si te desconectaste sin salir de una sala, usalo para liberar tu cupo.'),
    btn
  );
}

function devInfoCard() {
  return h('div', { class: 'dash-card dash-card--dev' },
    h('div', { class: 'dash-card-icon dash-card-icon--dev', text: '👨‍💻' }),
    h('h2', { class: 'dash-card-title' }, 'Desarrollado por'),
    h('p', { class: 'dash-card-desc' }, 'FernandezMarcodev'),
    h('p', { class: 'dash-card-desc' }, 'Desarrollador Backend · Analista en Informática'),
    h('div', { class: 'dev-links' },
      h('a', { class: 'dev-link', href: 'https://github.com/FernandezMarcodev', target: '_blank', rel: 'noopener', text: 'GitHub' }),
      h('span', { class: 'dev-separator', text: '·' }),
      h('a', { class: 'dev-link', href: 'https://linkedin.com/in/fernandezmarcodev', target: '_blank', rel: 'noopener', text: 'LinkedIn' })
    )
  );
}

async function pickModality() {
  let modalities;
  try {
    modalities = await api.modalities();
  } catch (err) {
    return toast(err.message, 'error');
  }

  const list = h('div', { class: 'modal-choice-list' });
  modalities.forEach((m) => {
    list.append(
      h('button', { class: 'modal-choice', type: 'button', onclick: () => createWith(m) },
        h('span', { class: 'modal-choice-template' }, m.template),
        h('span', { class: 'modal-choice-meta' }, m.code)
      )
    );
  });

  const sheet = openSheet({
    title: 'Elegí la modalidad',
    body: list,
  });

  async function createWith(modality) {
    sheet.close();
    try {
      const room = await api.createRoom(modality.id);
      store.room = room;
      navigate(`/room/${room.code}`);
    } catch (err) {
      toast(err.message, 'error');
    }
  }
}
