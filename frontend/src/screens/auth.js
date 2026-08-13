// Pantallas de autenticación: login, registro, recuperación, verificación.
import { h, mount } from '../ui/dom.js';
import { navigate } from '../router.js';
import { api } from '../api.js';
import { saveSession } from '../store.js';
import { toast } from '../ui/toast.js';

function card(title, subtitle, body) {
  return h('div', { class: 'auth-wrap' },
    h('div', { class: 'auth-card' },
      h('p', { class: 'auth-kicker' }, 'Es un 10 pero…'),
      h('h1', { class: 'auth-title' }, title),
      subtitle ? h('p', { class: 'auth-subtitle' }, subtitle) : null,
      body
    )
  );
}

function field(label, input, hint) {
  return h('label', { class: 'field' },
    h('span', { class: 'field-label' }, label),
    input,
    hint ? h('span', { class: 'field-hint' }, hint) : null
  );
}

function textInput(props = {}) {
  return h('input', { class: 'input', type: 'text', autocomplete: 'off', spellcheck: 'false', ...props });
}

const errBox = (msg) => h('p', { class: 'form-error', text: msg });

function busy(btn, on) {
  btn.disabled = on;
  btn.classList.toggle('btn--loading', on);
}

// ---- Login ------------------------------------------------------------------

export function login(view) {
  const formErr = h('div');
  const identifier = textInput({ placeholder: 'Nombre de usuario o correo', autofocus: true, required: true });
  const password = h('input', { class: 'input', type: 'password', placeholder: 'Contraseña', required: true });
  const submitBtn = h('button', { class: 'btn btn--primary btn--block', type: 'submit', text: 'Iniciar sesión' });

  async function submit() {
    formErr.textContent = '';
    if (!identifier.value || !password.value) {
      formErr.append(errBox('Completá todos los campos.'));
      return;
    }
    busy(submitBtn, true);
    try {
      const res = await api.login(identifier.value.trim(), password.value);
      saveSession({ token: res.access_token, user: res.user });
      toast(`¡Hola de nuevo, ${res.user.username}!`, 'success');
      navigate('/');
    } catch (err) {
      formErr.append(errBox(err.message));
      busy(submitBtn, false);
    }
  }

  return card('Iniciar sesión', null,
    h('form', { onsubmit: (e) => { e.preventDefault(); submit(); } },
      field('Usuario o correo', identifier),
      field('Contraseña', password),
      formErr,
      submitBtn
    ),
    h('div', { class: 'auth-links' },
      h('a', { class: 'auth-link', href: '#/register', text: 'Crear cuenta' }),
      h('a', { class: 'auth-link', href: '#/forgot', text: 'Olvidé mi contraseña' })
    )
  );
}

// ---- Registro ---------------------------------------------------------------

export function register(view) {
  const formErr = h('div');
  const username = textInput({ placeholder: 'Ej: ken2000', autofocus: true, required: true });
  const email = h('input', { class: 'input', type: 'email', placeholder: 'tucorreo@ejemplo.com', required: true });
  const password = h('input', { class: 'input', type: 'password', placeholder: 'Mínimo 8 caracteres con letras y números', required: true });
  const confirm = h('input', { class: 'input', type: 'password', placeholder: 'Repetí la contraseña', required: true });
  const submitBtn = h('button', { class: 'btn btn--primary btn--block', type: 'submit', text: 'Crear cuenta' });

  async function submit() {
    formErr.textContent = '';
    if (!username.value || !email.value || !password.value) {
      formErr.append(errBox('Completá todos los campos.'));
      return;
    }
    if (password.value !== confirm.value) {
      formErr.append(errBox('Las contraseñas no coinciden.'));
      return;
    }
    busy(submitBtn, true);
    try {
      const res = await api.register(username.value.trim(), email.value.trim(), password.value);
      success(view, res);
    } catch (err) {
      formErr.append(errBox(err.message));
      busy(submitBtn, false);
    }
  }

  return card('Crear cuenta', 'Unite a la mesa de juego',
    h('form', { onsubmit: (e) => { e.preventDefault(); submit(); } },
      field('Nombre de usuario', username, 'Será tu identidad en la partida.'),
      field('Correo electrónico', email),
      field('Contraseña', password, 'Mínimo 8 caracteres, con letras y números.'),
      field('Confirmar contraseña', confirm),
      formErr,
      submitBtn
    ),
    h('div', { class: 'auth-links' },
      h('a', { class: 'auth-link', href: '#/login', text: 'Ya tengo una cuenta' })
    )
  );
}

function success(view, res) {
  const body = h('div', { class: 'auth-success' },
    h('div', { class: 'auth-success-icon', text: '✓' }),
    h('h2', { class: 'auth-success-title' }, '¡Casi listo!'),
    h('p', { class: 'auth-success-desc' }, `Te enviamos un correo de verificación a ${res.email ?? 'tu cuenta'}. Confirmalo para poder iniciar sesión.`)
  );

  body.append(
    h('button', { class: 'btn btn--glass btn--block', type: 'button', onclick: () => navigate('/login'), text: 'Ya verifiqué · Iniciar sesión' })
  );

  return mount(view, card('Revisá tu correo', null, body));
}

// ---- Verificación (enlace directo) ------------------------------------------

export function verify(view, { params }) {
  const tokenInput = textInput({ placeholder: 'Código de verificación', value: params.get('token') || '' });
  const formErr = h('div');
  const submitBtn = h('button', { class: 'btn btn--primary btn--block', type: 'submit', text: 'Verificar cuenta' });

  async function submit() {
    formErr.textContent = '';
    if (!tokenInput.value) return formErr.append(errBox('Ingresá el código de verificación.'));
    busy(submitBtn, true);
    try {
      await api.verifyEmail(tokenInput.value.trim());
      toast('¡Cuenta verificada! Ya podés iniciar sesión.', 'success');
      navigate('/login');
    } catch (err) {
      formErr.append(errBox(err.message));
      busy(submitBtn, false);
    }
  }

  return card('Verificar cuenta', 'Ingresá el código que recibiste por correo.',
    h('form', { onsubmit: (e) => { e.preventDefault(); submit(); } },
      field('Código', tokenInput), formErr, submitBtn
    )
  );
}

// ---- Olvidé mi contraseña ----------------------------------------------------

export function forgot(view) {
  const formErr = h('div');
  const email = h('input', { class: 'input', type: 'email', placeholder: 'tucorreo@ejemplo.com', autofocus: true });
  const submitBtn = h('button', { class: 'btn btn--primary btn--block', type: 'submit', text: 'Enviar enlace' });

  async function submit() {
    formErr.textContent = '';
    if (!email.value) return formErr.append(errBox('Ingresá tu correo.'));
    busy(submitBtn, true);
    try {
      await api.forgotPassword(email.value.trim());
      const body = h('div', { class: 'auth-success' },
        h('div', { class: 'auth-success-icon', text: '✉' }),
        h('p', { class: 'auth-success-desc' }, 'Si existe una cuenta con ese correo, recibís un enlace para restablecer tu contraseña.')
      );
      return card('Correo enviado', null, body);
    } catch (err) {
      formErr.append(errBox(err.message));
      busy(submitBtn, false);
    }
  }

  return card('Recuperar contraseña', null,
    h('form', { onsubmit: (e) => { e.preventDefault(); submit(); } },
      field('Correo electrónico', email), formErr, submitBtn
    ),
    h('div', { class: 'auth-links' },
      h('a', { class: 'auth-link', href: '#/login', text: 'Volver al inicio de sesión' })
    )
  );
}

// ---- Restablecer contraseña --------------------------------------------------

export function reset(view, { params }) {
  const tokenInput = textInput({ placeholder: 'Código de restablecimiento', value: params.get('token') || '' });
  const password = h('input', { class: 'input', type: 'password', placeholder: 'Nueva contraseña' });
  const confirm = h('input', { class: 'input', type: 'password', placeholder: 'Repetir nueva contraseña' });
  const formErr = h('div');
  const submitBtn = h('button', { class: 'btn btn--primary btn--block', type: 'submit', text: 'Restablecer contraseña' });

  async function submit() {
    formErr.textContent = '';
    if (!tokenInput.value) return formErr.append(errBox('Ingresá el código.'));
    if (password.value !== confirm.value) return formErr.append(errBox('Las contraseñas no coinciden.'));
    busy(submitBtn, true);
    try {
      await api.resetPassword(tokenInput.value.trim(), password.value);
      toast('Contraseña actualizada. Ya podés iniciar sesión.', 'success');
      navigate('/login');
    } catch (err) {
      formErr.append(errBox(err.message));
      busy(submitBtn, false);
    }
  }

  return card('Restablecer contraseña', null,
    h('form', { onsubmit: (e) => { e.preventDefault(); submit(); } },
      field('Código', tokenInput),
      field('Nueva contraseña', password, 'Mínimo 8 caracteres, con letras y números.'),
      field('Confirmar contraseña', confirm),
      formErr, submitBtn
    )
  );
}
