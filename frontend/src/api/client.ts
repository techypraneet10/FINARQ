/**
 * Typed API Client for Financial RAG Platform.
 * Enforces centralized token lifecycle, request correlation, error envelope parsing, and retry policies.
 */

import {
  AnswerPackageResponse,
  AnswerQueryRequest,
  AnswerQueryResponse,
  AuditEventResponse,
  CreateUserRequest,
  DocumentChunkResponse,
  DocumentPageResponse,
  DocumentResponse,
  DocumentUploadResponse,
  DocumentVersionResponse,
  HealthResponse,
  IngestionJobResponse,
  MetricsResponse,
  ReadyResponse,
  RetrievalSearchRequest,
  RetrievalSearchResponse,
  TokenResponse,
  UserResponse,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export class ApiClientError extends Error {
  public code: string;
  public status: number;
  public details: Record<string, any>;
  public requestId?: string;

  constructor(message: string, status: number, code: string = 'API_ERROR', details: Record<string, any> = {}, requestId?: string) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.code = code;
    this.details = details;
    this.requestId = requestId;
  }
}

class ApiClient {
  private accessToken: string | null = null;
  private refreshTokenValue: string | null = null;
  private isRefreshing: boolean = false;
  private refreshSubscribers: Array<(token: string) => void> = [];
  private onUnauthorizedCallback: (() => void) | null = null;

  constructor() {
    this.accessToken = localStorage.getItem('fin_access_token');
    this.refreshTokenValue = localStorage.getItem('fin_refresh_token');
  }

  public setTokens(accessToken: string | null, refreshToken: string | null): void {
    this.accessToken = accessToken;
    this.refreshTokenValue = refreshToken;
    if (accessToken) {
      localStorage.setItem('fin_access_token', accessToken);
    } else {
      localStorage.removeItem('fin_access_token');
    }
    if (refreshToken) {
      localStorage.setItem('fin_refresh_token', refreshToken);
    } else {
      localStorage.removeItem('fin_refresh_token');
    }
  }

  public clearTokens(): void {
    this.setTokens(null, null);
    localStorage.removeItem('fin_active_tenant');
    localStorage.removeItem('fin_user_profile');
  }

  public setOnUnauthorized(callback: () => void): void {
    this.onUnauthorizedCallback = callback;
  }

  private generateRequestId(): string {
    return 'req-' + Math.random().toString(36).substring(2, 11) + '-' + Date.now();
  }

  private onTokenRefreshed(token: string) {
    this.refreshSubscribers.forEach((callback) => callback(token));
    this.refreshSubscribers = [];
  }

  private addRefreshSubscriber(callback: (token: string) => void) {
    this.refreshSubscribers.push(callback);
  }

  private async refreshAccessToken(): Promise<string | null> {
    if (!this.refreshTokenValue) {
      this.clearTokens();
      if (this.onUnauthorizedCallback) this.onUnauthorizedCallback();
      return null;
    }

    try {
      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Request-ID': this.generateRequestId(),
        },
        body: JSON.stringify({ refresh_token: this.refreshTokenValue }),
      });

      if (!response.ok) {
        throw new Error('Token refresh rejected');
      }

      const data: TokenResponse = await response.json();
      this.setTokens(data.access_token, data.refresh_token);
      return data.access_token;
    } catch {
      this.clearTokens();
      if (this.onUnauthorizedCallback) this.onUnauthorizedCallback();
      return null;
    }
  }

  public async request<T>(
    endpoint: string,
    options: RequestInit = {},
    requiresAuth: boolean = true,
    retryCount: number = 0
  ): Promise<T> {
    const url = endpoint.startsWith('http') || endpoint.startsWith('/') ? endpoint : `${API_BASE}/${endpoint}`;
    const requestId = this.generateRequestId();

    const headers: Record<string, string> = {
      'X-Request-ID': requestId,
      ...(options.headers as Record<string, string>),
    };

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    if (requiresAuth && this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle 401 with transparent token refresh
      if (response.status === 401 && requiresAuth && retryCount === 0 && this.refreshTokenValue) {
        if (!this.isRefreshing) {
          this.isRefreshing = true;
          const newToken = await this.refreshAccessToken();
          this.isRefreshing = false;
          if (newToken) {
            this.onTokenRefreshed(newToken);
            return this.request<T>(endpoint, options, requiresAuth, retryCount + 1);
          }
        } else {
          return new Promise<T>((resolve, reject) => {
            this.addRefreshSubscriber(async () => {
              try {
                const res = await this.request<T>(endpoint, options, requiresAuth, retryCount + 1);
                resolve(res);
              } catch (err) {
                reject(err);
              }
            });
          });
        }
      }

      if (!response.ok) {
        let errorData: any = {};
        try {
          errorData = await response.json();
        } catch {
          errorData = { message: response.statusText };
        }

        let message =
          errorData.detail ||
          errorData.error?.message ||
          errorData.message;

        if (!message || message === 'Internal Server Error') {
          if (response.status === 500) {
            message = 'The authentication or backend service is temporarily unavailable.';
          } else if (response.status === 502 || response.status === 503 || response.status === 504) {
            message = 'Upstream gateway or service is unreachable. Please retry shortly.';
          } else if (response.status === 401) {
            message = 'Invalid corporate email or password. Please check your credentials.';
          } else {
            message = `HTTP ${response.status}: Request failed`;
          }
        }

        const code = errorData.error?.code || `HTTP_${response.status}`;
        const details = errorData.error?.details || errorData.details || {};

        if (response.status === 401 && this.onUnauthorizedCallback && requiresAuth) {
          this.onUnauthorizedCallback();
        }

        throw new ApiClientError(message, response.status, code, details, response.headers.get('X-Request-ID') || requestId);
      }

      if (response.status === 204) {
        return {} as T;
      }

      return (await response.json()) as T;
    } catch (err: any) {
      if (err instanceof ApiClientError) {
        throw err;
      }
      throw new ApiClientError(
        'Unable to connect to Financial RAG server. Please ensure backend is running.',
        0,
        'NETWORK_ERROR',
        {},
        requestId
      );
    }
  }

  // ============================================================================
  // Authentication & User Identity APIs
  // ============================================================================

  public async login(email: string, password: string): Promise<TokenResponse> {
    const data = await this.request<TokenResponse>(
      `${API_BASE}/auth/login`,
      {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      },
      false
    );
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  public async register(email: string, password: string, tenantName?: string): Promise<TokenResponse> {
    const data = await this.request<TokenResponse>(
      `${API_BASE}/auth/register`,
      {
        method: 'POST',
        body: JSON.stringify({
          email,
          password,
          tenant_name: tenantName,
          role: 'owner',
        }),
      },
      false
    );
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  public async logout(): Promise<void> {
    try {
      if (this.accessToken) {
        await this.request(`${API_BASE}/auth/logout`, { method: 'POST' });
      }
    } finally {
      this.clearTokens();
    }
  }

  public async getMe(): Promise<UserResponse> {
    return this.request<UserResponse>(`${API_BASE}/auth/me`);
  }

  public async listUsers(): Promise<UserResponse[]> {
    return this.request<UserResponse[]>(`${API_BASE}/users`);
  }

  public async createUser(req: CreateUserRequest): Promise<UserResponse> {
    return this.request<UserResponse>(`${API_BASE}/users`, {
      method: 'POST',
      body: JSON.stringify(req),
    });
  }

  public async updateUserStatus(userId: string, status: string): Promise<UserResponse> {
    return this.request<UserResponse>(`${API_BASE}/users/${userId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  }

  public async listAuditEvents(limit: number = 50, offset: number = 0): Promise<AuditEventResponse[]> {
    return this.request<AuditEventResponse[]>(`${API_BASE}/audit-events?limit=${limit}&offset=${offset}`);
  }

  // ============================================================================
  // Documents & Ingestion Lifecycle APIs
  // ============================================================================

  public async listDocuments(limit: number = 50, offset: number = 0, ticker?: string): Promise<DocumentResponse[]> {
    let url = `${API_BASE}/documents?limit=${limit}&offset=${offset}`;
    if (ticker) url += `&ticker_symbol=${encodeURIComponent(ticker)}`;
    return this.request<DocumentResponse[]>(url);
  }

  public async getDocument(documentId: string): Promise<DocumentResponse> {
    return this.request<DocumentResponse>(`${API_BASE}/documents/${documentId}`);
  }

  public async uploadDocument(
    file: File,
    meta: {
      title?: string;
      document_type?: string;
      ticker_symbol?: string;
      fiscal_year?: number;
      fiscal_period?: string;
    } = {}
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (meta.title) formData.append('title', meta.title);
    if (meta.document_type) formData.append('document_type', meta.document_type);
    if (meta.ticker_symbol) formData.append('ticker_symbol', meta.ticker_symbol);
    if (meta.fiscal_year) formData.append('fiscal_year', meta.fiscal_year.toString());
    if (meta.fiscal_period) formData.append('fiscal_period', meta.fiscal_period);

    return this.request<DocumentUploadResponse>(`${API_BASE}/documents`, {
      method: 'POST',
      body: formData,
    });
  }

  public async deleteDocument(documentId: string): Promise<{ message: string; deleted: boolean }> {
    return this.request<{ message: string; deleted: boolean }>(`${API_BASE}/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  public async getDocumentVersions(documentId: string): Promise<DocumentVersionResponse[]> {
    return this.request<DocumentVersionResponse[]>(`${API_BASE}/documents/${documentId}/versions`);
  }

  public async getDocumentChunks(documentId: string): Promise<DocumentChunkResponse[]> {
    return this.request<DocumentChunkResponse[]>(`${API_BASE}/documents/${documentId}/chunks`);
  }

  public async getDocumentPages(documentId: string): Promise<DocumentPageResponse[]> {
    return this.request<DocumentPageResponse[]>(`${API_BASE}/documents/${documentId}/pages`);
  }

  public async getDocumentPage(documentId: string, pageNumber: number): Promise<DocumentPageResponse> {
    return this.request<DocumentPageResponse>(`${API_BASE}/documents/${documentId}/pages/${pageNumber}`);
  }

  public getDocumentFileUrl(documentId: string): string {
    return `${API_BASE}/documents/${documentId}/file`;
  }

  public async listIngestionJobs(limit: number = 50, offset: number = 0): Promise<IngestionJobResponse[]> {
    return this.request<IngestionJobResponse[]>(`${API_BASE}/ingestion-jobs?limit=${limit}&offset=${offset}`);
  }

  public async getIngestionJob(jobId: string): Promise<IngestionJobResponse> {
    return this.request<IngestionJobResponse>(`${API_BASE}/ingestion-jobs/${jobId}`);
  }

  public async retryIngestionJob(jobId: string): Promise<IngestionJobResponse> {
    return this.request<IngestionJobResponse>(`${API_BASE}/ingestion-jobs/${jobId}/retry`, {
      method: 'POST',
    });
  }

  // ============================================================================
  // Retrieval, Reasoning & Verified Answers APIs
  // ============================================================================

  public async searchEvidence(request: RetrievalSearchRequest): Promise<RetrievalSearchResponse> {
    return this.request<RetrievalSearchResponse>(`${API_BASE}/retrieval/search`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  public async generateAnswerPackage(query: string, filters?: any, topK: number = 10): Promise<AnswerPackageResponse> {
    return this.request<AnswerPackageResponse>(`${API_BASE}/reasoning/answer-package`, {
      method: 'POST',
      body: JSON.stringify({ query, filters, top_k: topK }),
    });
  }

  public async generateVerifiedAnswer(request: AnswerQueryRequest): Promise<AnswerQueryResponse> {
    return this.request<AnswerQueryResponse>(`${API_BASE}/answers`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // ============================================================================
  // Health & Observability APIs
  // ============================================================================

  public async getHealth(): Promise<HealthResponse> {
    try {
      return await this.request<HealthResponse>('/health', {}, false);
    } catch {
      return this.request<HealthResponse>(`${API_BASE}/health`, {}, false);
    }
  }

  public async getReadiness(): Promise<ReadyResponse> {
    try {
      return await this.request<ReadyResponse>('/ready', {}, false);
    } catch {
      return this.request<ReadyResponse>(`${API_BASE}/ready`, {}, false);
    }
  }

  public async getMetrics(): Promise<MetricsResponse> {
    try {
      return await this.request<MetricsResponse>('/metrics', {}, false);
    } catch {
      return this.request<MetricsResponse>(`${API_BASE}/metrics`, {}, false);
    }
  }
}

export const api = new ApiClient();
