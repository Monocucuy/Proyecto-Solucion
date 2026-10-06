export class RateLimitError extends Error {
  constructor(retryAfterMs) { super('rate_limited'); this.retryAfterMs = retryAfterMs; }
}
export class AuthError extends Error {
  constructor() { super('auth'); }
}
export class TransientError extends Error {
  constructor(msg = 'transient') { super(msg); }
}
