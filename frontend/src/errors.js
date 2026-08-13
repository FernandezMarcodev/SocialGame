// Error de dominio de la API, con formato B.3: {error:{code,message,details}}.
export class ApiError extends Error {
  constructor(message, { code = 'UNKNOWN', status = 0, details = {} } = {}) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}
