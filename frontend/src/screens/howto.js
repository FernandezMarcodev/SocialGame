// Pantalla: Guía completa de "Cómo se juega".
import { h } from '../ui/dom.js';
import { navigate } from '../router.js';
import { pill } from '../ui/components.js';

export function howto(view) {
  return h('div', { class: 'howto-page' },
    heroSection(),
    h('section', { class: 'howto-section' },
      h('h2', { class: 'howto-section-title' }, '1. ¿De qué se trata?'),
      h('p', { class: 'howto-text' },
        '"Es un 10 pero…" es un juego multijugador por turnos donde deberás completar una frase con un premio o castigo, ' +
        'asignarle un puntaje secreto del 1 al 10, y luego adivinar el puntaje que elegieron tus amigos en sus propias frases. ' +
        'Quien acierbe el puntaje exacto del autor, le cuesta un punto.'
      ),
      h('div', { class: 'howto-chip-row' },
        pill('2 a 6 jugadores', 'neutral'),
        pill('3 rondas por partida', 'neutral'),
        pill('Puntaje 1–10', 'neutral')
      )
    ),
    h('section', { class: 'howto-section' },
      h('h2', { class: 'howto-section-title' }, '2. Empezar a jugar'),
      h('p', { class: 'howto-text' },
        'Creá una cuenta o iniciá sesión. No necesitás verificar el correo para jugar.'
      ),
      h('ol', { class: 'howto-steps' },
        h('li', {}, h('strong', {}, 'Registrate'), h('span', { class: 'howto-step-desc' }, 'Elegí nombre de usuario, correo y contraseña (mín. 8 caracteres con letras y números).')),
        h('li', {}, h('strong', {}, 'Iniciá sesión'), h('span', { class: 'howto-step-desc' }, 'Ingresá con tu nombre de usuario o correo y tu contraseña.'))
      )
    ),
    h('section', { class: 'howto-section' },
      h('h2', { class: 'howto-section-title' }, '3. Crear o unirte a una sala'),
      h('ol', { class: 'howto-steps' },
        step('Crear una sala', 'Soleado podés crear una sala nueva. Elegís una modalidad ("Es un 10 pero…" o "Es un 1 pero…") y compartís el código de 6 caracteres con tus amigos.'),
        step('Unirse a una sala', 'Si ya tenés un código, ingresalo en el campo correspondiente y uniros a la partida del creador.'),
        hint('Se necesitan entre 2 y 6 jugadores para iniciar. El creador es quien pulsa "Iniciar partida".')
      )
    ),
    h('section', { class: 'howto-section' },
      h('h2', { class: 'howto-section-title' }, '4. Modalidades'),
      h('p', { class: 'howto-text' },
        'La modalidad define la plantilla de la frase que completarás. El creador la elige al crear la sala y no se puede cambiar durante la partida.'
      ),
      h('div', { class: 'howto-modality-list' },
        modalityCard('Es un 10 pero…', 'Es un 10 pero ...', 'El clásico: buscá el puntaje más alto (o el más creativo) para la frase.'),
        modalityCard('Es un 1 pero…', 'Es un 1 pero ...', 'Una variante: buscá el puntaje más bajo. ¡El secreto está en saber qué buscás!')
      )
    ),
    h('section', { class: 'howto-section' },
      h('h2', { class: 'howto-section-title' }, '5. Desarrollo de la partida'),
      h('p', { class: 'howto-text' },
        'Una partida consta de 3 rondas. Cada ronda, todos los jugadores pasan por el turno de autor una vez, en un orden aleatorio.'
      ),
      h('div', { class: 'howto-phases' },
        phaseStep('1. Tu turno como autor', 'Completá la frase (3-200 caracteres) y asignale un puntaje secreto del 1 al 10. Tu puntaje se mantiene oculto hasta que terminue la votación.', 'accent'),
        phaseStep('2. Turno de los demás', 'Cuando otro jugador es autor, vos vota vas a ver su frase y deberás adivinar su puntaje secreto con un voto del 1 al 10. ¡Solo podés votar una vez por turno!', 'amber'),
        phaseStep('3. Resultado del turno', 'Una vez que todos votaron (o se agotó el tiempo), se revela el puntaje secreto, los votos y los puntos obtenidos. El autor suma un punto por cada acierto exacto.', 'primary')
      ),
      hint('Tenés 60 segundos para redactar y 30 segundos para votar. Si se acaba el tiempo, el turno se descarta automáticamente.')
    ),
    h('section', { class: 'howto-section' },
      h('h2', { class: 'howto-section-title' }, '6. Sistema de puntaje'),
      h('table', { class: 'howto-scoring' },
        h('thead', {},
          h('tr', {},
            h('th', {}, 'Situación'),
            h('th', {}, 'Puntos para el autor')
          )
        ),
        h('tbody', {},
          h('tr', {}, h('td', {}, 'Un jugador adivina el puntaje exacto'), h('td', {}, '+1')),
          h('tr', {}, h('td', {}, 'Dos jugadores adivinan exacto'), h('td', {}, '+2')),
          h('tr', {}, h('td', {}, 'Nadie adivina exacto'), h('td', {}, '+0'))
        )
      ),
      h('p', { class: 'howto-text' },
        'Sólo el autor suma puntos. Los votantes no obtienen puntos por acertar; su objetivo es adivinar correctamente para "robar" puntos al autor.'
      )
    ),
    h('section', { class: 'howto-section' },
      h('h2', { class: 'howto-section-title' }, '7. Ganar la partida'),
      h('p', { class: 'howto-text' },
        'Al finalizar las 3 rondas, el jugador con más puntos es el ganador. Si hay empate, el sistema lo declara.'
      ),
      h('p', { class: 'howto-text' },
        'Recuerd: la clave es redactar frases que lleven a tu puntaje secreto a la mente de los demás, o viceversa: adivinar con precisión.'
      )
    ),
    credits()
  );
}

function heroSection() {
  return h('section', { class: 'howto-hero' },
    h('div', { class: 'howto-hero-kicker' },
      h('span', { class: 'howto-hero-kicker-num', text: '?' }),
      h('span', { class: 'howto-hero-kicker-label' }, 'GUÍA DEL JUEGO')
    ),
    h('h1', { class: 'howto-hero-title' },
      'Cómo se juega ',
      h('span', { class: 'howto-hero-title--gradient' }, 'Es un 10 pero…')
    ),
    h('p', { class: 'howto-hero-sub' },
      'Una guía completa para empezar a jugar y dominar el juego.'
    ),
    h('button', { class: 'btn btn--primary btn--lg', type: 'button', onclick: () => navigate('/register') },
      h('span', { class: 'btn-icon', text: '▶' }), 'Jugar ahora'
    )
  );
}

function step(title, desc) {
  return h('li', {},
    h('strong', { class: 'howto-step-title' }, title),
    h('span', { class: 'howto-step-desc' }, desc)
  );
}

function hint(text) {
  return h('li', { class: 'howto-hint' }, h('span', { class: 'howto-hint-icon', text: '💡' }), h('span', {}, text));
}

function modalityCard(name, template, desc) {
  return h('div', { class: 'howto-modality' },
    h('div', { class: 'howto-modality-template' }, template),
    h('h3', { class: 'howto-modality-name' }, name),
    h('p', { class: 'howto-modality-desc' }, desc)
  );
}

function phaseStep(title, desc, tone) {
  return h('div', { class: `howto-phase howto-phase--${tone}` },
    h('div', { class: 'howto-phase-num', text: title.charAt(0) }),
    h('div', { class: 'howto-phase-body' },
      h('h3', { class: 'howto-phase-title' }, title),
      h('p', { class: 'howto-phase-desc' }, desc)
    )
  );
}

function credits() {
  return h('footer', { class: 'howto-footer' },
    h('div', { class: 'howto-credits' },
      h('div', { class: 'howto-credits-inner' },
        h('div', { class: 'howto-credits-main' },
          h('span', { class: 'howto-credits-label' }, 'Desarrollado por'),
          h('span', { class: 'howto-developer-name' }, 'FernandezMarcodev')
        ),
        h('div', { class: 'howto-credits-sub' },
          h('span', { text: 'Desarrollador Backend' }),
          h('span', { class: 'howto-credits-separator' }, '·'),
          h('span', { text: 'Analista en Informática' }),
          h('span', { class: 'howto-credits-separator' }, '·'),
          h('span', { text: '2026' })
        ),
        h('div', { class: 'howto-credits-links' },
          h('a', { class: 'howto-credit-link', href: 'https://github.com/FernandezMarcodev', target: '_blank', rel: 'noopener noreferrer' }, 'GitHub'),
          h('a', { class: 'howto-credit-link', href: 'mailto:fernandezmarcovalentin@gmail.com', target: '_blank', rel: 'noopener noreferrer' }, 'Email'),
          h('a', { class: 'howto-credit-link', href: 'https://www.linkedin.com/in/fernandezmarcodev', target: '_blank', rel: 'noopener noreferrer' }, 'LinkedIn')
        )
      )
    )
  );
}
