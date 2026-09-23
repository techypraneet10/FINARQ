/**
 * Frontend Observability & Privacy-Preserving Telemetry.
 * Tracks navigation performance, API errors, and user workflow latencies without collecting sensitive document data.
 */

export interface TelemetryEvent {
  eventName: string;
  durationMs?: number;
  timestamp: string;
  metadata?: Record<string, any>;
}

class FrontendObservability {
  private events: TelemetryEvent[] = [];
  private readonly MAX_BUFFER = 100;

  public recordEvent(eventName: string, durationMs?: number, metadata?: Record<string, any>): void {
    const ev: TelemetryEvent = {
      eventName,
      durationMs,
      timestamp: new Date().toISOString(),
      metadata,
    };
    this.events.push(ev);
    if (this.events.length > this.MAX_BUFFER) {
      this.events.shift();
    }
  }

  public recordError(action: string, error: Error | any): void {
    this.recordEvent('frontend_error', undefined, {
      action,
      errorName: error.name || 'Error',
      errorMessage: error.message || String(error),
      code: error.code,
      status: error.status,
    });
  }

  public getEvents(): TelemetryEvent[] {
    return [...this.events];
  }

  public clear(): void {
    this.events = [];
  }
}

export const telemetry = new FrontendObservability();
