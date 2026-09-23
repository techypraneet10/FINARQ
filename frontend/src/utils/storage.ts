/**
 * Tenant-scoped Local Storage helper.
 * Prevents cross-tenant state leakage and ensures complete cache purging upon tenant switch or logout.
 */

export class TenantStorage {
  private static getPrefix(tenantId: string): string {
    return `fin_tenant_${tenantId}_`;
  }

  public static setItem(tenantId: string, key: string, value: any): void {
    if (!tenantId) return;
    try {
      const serialized = JSON.stringify(value);
      localStorage.setItem(`${this.getPrefix(tenantId)}${key}`, serialized);
    } catch {
      // Ignore quota exceeded errors
    }
  }

  public static getItem<T>(tenantId: string, key: string, defaultValue: T): T {
    if (!tenantId) return defaultValue;
    try {
      const raw = localStorage.getItem(`${this.getPrefix(tenantId)}${key}`);
      if (!raw) return defaultValue;
      return JSON.parse(raw) as T;
    } catch {
      return defaultValue;
    }
  }

  public static removeItem(tenantId: string, key: string): void {
    if (!tenantId) return;
    localStorage.removeItem(`${this.getPrefix(tenantId)}${key}`);
  }

  public static clearTenant(tenantId: string): void {
    if (!tenantId) return;
    const prefix = this.getPrefix(tenantId);
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.startsWith(prefix)) {
        keysToRemove.push(k);
      }
    }
    keysToRemove.forEach((k) => localStorage.removeItem(k));
  }

  public static purgeAll(): void {
    localStorage.clear();
  }
}
