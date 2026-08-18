// Pantalla de perfil: edicion de datos, cambio de contraseña y logout.
import { h } from '../ui/dom.js';
import { navigate } from '../router.js';
import { api } from '../api.js';
import { store, currentUser, saveSession, setUser } from '../store.js';
import { avatar } from '../ui/components.js';
import { toast } from '../ui/toast.js';
import { confirmSheet } from '../ui/sheet.js';

function field(label, input) {
  return h('label', { class: 'field' },
    h('span', { class: 'field-label' }, label),
    input
  );
}

export function profile(view) {
  const user = currentUser();

  const username = h('input', { class: 'input', type: 'text', value: user?.username || '' });
  const email = h('input', { class: 'input', type: 'email', value: user?.email || '' });

  const saveBtn = h('button', { class: 'btn btn--primary btn--block', type: 'submit', text: 'Guardar cambios' });

  async function save() {
    if (!username.value.trim()) return toast('El nombre de usuario no puede quedar vacio.', 'info');
    saveBtn.disabled = true;
    saveBtn.classList.add('btn--loading');
    try {
      const updated = await api.updateMe({
        username: username.value.trim(),
        ...(email.value.trim() !== user?.email ? { email: email.value.trim() } : {}),
      });
      setUser(updated);
      toast('Perfil actualizado.', 'success');
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      saveBtn.disabled = false;
      saveBtn.classList.remove('btn--loading');
    }
  }


  // Contraseña
  const cur = h('input', { class: 'input', type: 'password', placeholder: 'Contraseña actual' });
  const pw = h('input', { class: 'input', type: 'password', placeholder: 'Nueva contraseña' });
  const pw2 = h('input', { class: 'input', type: 'password', placeholder: 'Repetir nueva contraseña' });
  const pwBtn = h('button', { class: 'btn btn--glass btn--block', type: 'submit', text: 'Cambiar contraseña' });
  const pwMsg = h('p', { class: 'form-success' });

  async function changePw() {
    pwMsg.textContent = '';
    if (!cur.value || !pw.value) return toast('Completa los campos de contraseña.', 'info');
    if (pw.value !== pw2.value) return toast('Las contraseñas no coinciden.', 'error');
    pwBtn.disabled = true;
    pwBtn.classList.add('btn--loading');
    try {
      await api.changePassword(cur.value, pw.value);
      cur.value = pw.value = pw2.value = '';
      pwMsg.textContent = 'Contraseña actualizada.';
      toast('Contraseña actualizada.', 'success');
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      pwBtn.disabled = false;
      pwBtn.classList.remove('btn--loading');
    }
  }

  // Desconectar salas fantasmas (RF-COM-010)
  const ghostBtn = h(
    'button',
    { class: 'btn btn--glass btn--block', type: 'button', text: 'Desconectarme de salas fantasmas' }
  );
  ghostBtn.addEventListener('click', async () => {
    ghostBtn.disabled = true;
    ghostBtn.classList.add('btn--loading');
    try {
      const result = await api.forceLeaveGhosts();
      if (result.disconnected) {
        toast('Te has desconectado de la sala.', 'success');
      } else {
        toast(result.message || 'No estabas en ninguna sala.', 'info');
      }
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      ghostBtn.disabled = false;
      ghostBtn.classList.remove('btn--loading');
    }
  });

  const logoutBtn = h('button', { class: 'btn btn--danger btn--block', type: 'button', text: 'Cerrar sesion' });
  logoutBtn.addEventListener('click', () => {
    confirmSheet({
      title: '¿Cerrar sesion?',
      message: 'Necesitaras volver a iniciar sesion para jugar.',
      confirmLabel: 'Cerrar sesion',
      danger: true,
      onConfirm: async () => {
        try {
          await api.logout();
        } catch {
          /* sin red: igual se limpia la sesion local */
        }
        saveSession(null);
        toast('Sesion cerrada.', 'info');
        navigate('/login');
      },
    });
  });

  return h('div', { class: 'profile' },
    h('section', { class: 'profile-hero' },
      avatar(user, 88),
      h('div',
        h('h1', { class: 'profile-name' }, user?.username),
        h('p', { class: 'profile-email' }, user?.email)
      )
    ),
    h('section', { class: 'profile-card' },
      h('h2', { class: 'panel-title' }, 'Datos del perfil'),
      h('form', { onsubmit: (e) => { e.preventDefault(); save(); } },
        field('Nombre de usuario', username),
        field('Correo electronico', email),
        saveBtn
      )
    ),
    h('section', { class: 'profile-card' },
      h('h2', { class: 'panel-title' }, 'Cambiar contraseña'),
      h('form', { onsubmit: (e) => { e.preventDefault(); changePw(); } },
        field('Contraseña actual', cur),
        field('Nueva contraseña', pw),
        field('Confirmar nueva contraseña', pw2),
        pwMsg,
        pwBtn
      )
    ),
    h('section', { class: 'profile-card' },
      h('h2', { class: 'panel-title' }, 'Sesion activa'),
      h('p', { class: 'form-hint', text: 'Si un jugador se desconecto sin salir de una sala, queda como sala fantasma.' }),
      ghostBtn
    ),
    h('section', { class: 'profile-card' },
      logoutBtn
    )
  );
}
