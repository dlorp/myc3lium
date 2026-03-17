/**
 * API Service for MYC3LIUM Backend
 * 
 * Handles REST API calls to the FastAPI backend.
 * Base URL defaults to localhost for development.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

// ============================================================================
// Node API
// ============================================================================

export interface Node {
  id: string;
  type: 'SPORE' | 'HYPHA' | 'FROND' | 'RHIZOME';
  callsign: string;
  status: 'online' | 'offline' | 'degraded';
  rssi: number | null;
  battery: number | null;
  last_seen: string;
  position: { lat: number; lon: number } | null;
}

export interface NodeFilters {
  status?: 'online' | 'offline' | 'degraded';
  type?: 'SPORE' | 'HYPHA' | 'FROND' | 'RHIZOME';
}

/**
 * Fetch all nodes with optional filters
 */
export async function fetchNodes(filters?: NodeFilters): Promise<Node[]> {
  const params = new URLSearchParams();
  if (filters?.status) params.append('status', filters.status);
  if (filters?.type) params.append('type', filters.type);
  
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<Node[]>(`/api/nodes${query}`);
}

/**
 * Fetch a single node by ID
 */
export async function fetchNode(nodeId: string): Promise<Node> {
  return apiFetch<Node>(`/api/nodes/${nodeId}`);
}

// ============================================================================
// Thread API
// ============================================================================

export interface Thread {
  id: string;
  source_id: string;
  target_id: string;
  radio_type: 'LoRa' | 'HaLow' | 'WiFi';
  rssi: number | null;
  quality: number;
  latency: number | null;
  established: string;
}

export interface ThreadFilters {
  node_id?: string;
  radio_type?: 'LoRa' | 'HaLow' | 'WiFi';
  min_quality?: number;
}

/**
 * Fetch all threads with optional filters
 */
export async function fetchThreads(filters?: ThreadFilters): Promise<Thread[]> {
  const params = new URLSearchParams();
  if (filters?.node_id) params.append('node_id', filters.node_id);
  if (filters?.radio_type) params.append('radio_type', filters.radio_type);
  if (filters?.min_quality !== undefined) {
    params.append('min_quality', filters.min_quality.toString());
  }
  
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<Thread[]>(`/api/threads${query}`);
}

/**
 * Fetch a single thread by ID
 */
export async function fetchThread(threadId: string): Promise<Thread> {
  return apiFetch<Thread>(`/api/threads/${threadId}`);
}

/**
 * Update thread properties (partial update)
 */
export async function updateThread(
  threadId: string,
  data: {
    quality?: number;
    latency?: number;
    rssi?: number;
  }
): Promise<Thread> {
  return apiFetch<Thread>(`/api/threads/${threadId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/**
 * Delete a thread
 */
export async function deleteThread(threadId: string): Promise<void> {
  await fetch(`${API_BASE_URL}/api/threads/${threadId}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// Message API
// ============================================================================

export interface Message {
  id: string;
  sender_id: string;
  recipient_id: string | null;
  content: string;
  timestamp: string;
  hops: number;
}

export interface MessageFilters {
  sender_id?: string;
  recipient_id?: string;
  limit?: number;
  cursor?: string;
}

export interface MessageCreate {
  sender_id: string;
  recipient_id?: string | null;
  content: string;
  hops?: number;
}

/**
 * Fetch messages with optional filters and pagination
 */
export async function fetchMessages(filters?: MessageFilters): Promise<Message[]> {
  const params = new URLSearchParams();
  if (filters?.sender_id) params.append('sender_id', filters.sender_id);
  if (filters?.recipient_id) params.append('recipient_id', filters.recipient_id);
  if (filters?.limit !== undefined) {
    params.append('limit', filters.limit.toString());
  }
  if (filters?.cursor) params.append('cursor', filters.cursor);
  
  const query = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<Message[]>(`/api/messages${query}`);
}

/**
 * Create a new message
 */
export async function postMessage(data: MessageCreate): Promise<Message> {
  return apiFetch<Message>('/api/messages', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Delete a message
 */
export async function deleteMessage(messageId: string): Promise<void> {
  await fetch(`${API_BASE_URL}/api/messages/${messageId}`, {
    method: 'DELETE',
  });
}

// ============================================================================
// Health Check
// ============================================================================

export interface HealthStatus {
  status: string;
}

/**
 * Check API health
 */
export async function checkHealth(): Promise<HealthStatus> {
  return apiFetch<HealthStatus>('/health');
}
