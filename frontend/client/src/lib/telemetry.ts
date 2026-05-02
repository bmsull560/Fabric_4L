/**
 * Centralized Telemetry & Error Logging Service
 *
 * Single source of truth for all frontend observability:
 * - Environment-guarded console logging (dev only by default)
 * - Structured error capture with trace IDs
 * - Pluggable backend ready for Sentry/DataDog/etc.
 *
 * Usage:
 *   import { logError, captureException } from '@/lib/telemetry';
 *   logError('Failed to load value packs', { packId, statusCode });
 *   captureException(error, { traceId });
 */

type LogLevel = 'error' | 'warn' | 'info' | 'debug';

export interface LogContext extends Record<string, unknown> {
  traceId?: string | null;
  statusCode?: number;
  errorCode?: string;
}

/** Determine whether console logging should be emitted */
function isLoggingEnabled(): boolean {
  return (
    import.meta.env.DEV === true ||
    (typeof process !== 'undefined' && process.env?.NODE_ENV === 'development')
  );
}

/** Core logger — emits to console in dev, swallows in prod */
function log(level: LogLevel, message: string, context?: LogContext): void {
  if (!isLoggingEnabled()) return;

  const prefix = '[Fabric]';
  const args = context ? [prefix, message, context] : [prefix, message];

  switch (level) {
    case 'error':
      console.error(...args);
      break;
    case 'warn':
      console.warn(...args);
      break;
    case 'info':
      console.info(...args);
      break;
    case 'debug':
      console.debug(...args);
      break;
  }
}

/** Log an error with optional structured context */
export function logError(message: string, context?: LogContext): void {
  log('error', message, context);
}

/** Log a warning with optional structured context */
export function logWarn(message: string, context?: LogContext): void {
  log('warn', message, context);
}

/** Log an info message with optional structured context */
export function logInfo(message: string, context?: LogContext): void {
  log('info', message, context);
}

/** Log a debug message with optional structured context */
export function logDebug(message: string, context?: LogContext): void {
  log('debug', message, context);
}

/**
 * Capture an exception for telemetry.
 * In development: logs to console with stack trace.
 * In production: reserved for Sentry/DataDog/etc.
 */
export function captureException(error: Error, context?: LogContext): void {
  logError(error.message, {
    stack: error.stack,
    name: error.name,
    ...context,
  });

  // TODO: Integrate with Sentry/Datadog in production
  // if (import.meta.env.PROD && typeof window.Sentry !== 'undefined') {
  //   window.Sentry.captureException(error, { extra: context });
  // }
}

/**
 * Capture a structured message for telemetry.
 * In development: logs to console.
 * In production: reserved for Sentry/DataDog/etc.
 */
export function captureMessage(
  message: string,
  level: LogLevel = 'info',
  context?: LogContext
): void {
  log(level, message, context);

  // TODO: Integrate with Sentry/Datadog in production
  // if (import.meta.env.PROD && typeof window.Sentry !== 'undefined') {
  //   window.Sentry.captureMessage(message, level);
  // }
}

/**
 * Create a namespaced logger for a module.
 * Produces messages like `[Fabric][useValuePacks] Deployment failed`.
 */
export function createLogger(module: string) {
  const prefix = `[Fabric][${module}]`;

  return {
    error: (message: string, context?: LogContext) =>
      log('error', `${prefix} ${message}`, context),
    warn: (message: string, context?: LogContext) =>
      log('warn', `${prefix} ${message}`, context),
    info: (message: string, context?: LogContext) =>
      log('info', `${prefix} ${message}`, context),
    debug: (message: string, context?: LogContext) =>
      log('debug', `${prefix} ${message}`, context),
  };
}
