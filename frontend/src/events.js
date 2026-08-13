// Bus de eventos central de la aplicación (sesión, tiempo real, etc.).

const bus = new EventTarget();
const wrappers = new Map();

export function emit(type, data) {
  bus.dispatchEvent(new CustomEvent(type, { detail: data }));
}

export function on(type, cb) {
  let wrapped = wrappers.get(cb);
  if (!wrapped) {
    wrapped = (e) => cb(e.detail);
    wrappers.set(cb, wrapped);
  }
  bus.addEventListener(type, wrapped);
  return wrapped;
}

export function off(type, cb) {
  const wrapped = wrappers.get(cb);
  if (wrapped) {
    bus.removeEventListener(type, wrapped);
    wrappers.delete(cb);
  }
}

// suscripción única (autoremovible)
export function once(type, cb) {
  const wrapped = (d) => {
    off(type, wrapped);
    cb(d);
  };
  on(type, wrapped);
}
