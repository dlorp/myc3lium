/**
 * API Service for MYC3LIUM Backend
 * 
 * Handles REST API calls to the FastAPI backend.
 * Base URL defaults to localhost for development.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * Generic fetch wrapper with error handling and auth token injection
 */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  // Inject auth token from localStorage
  const token = localStorage.getItem('myc3_token');
  const authHeaders: Record<string, string> = {};
  if (token) {
    authHeaders['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));

    // Auth required: redirect to login
    if (response.status === 401) {
      localStorage.removeItem('myc3_token');
      window.location.href = '/login';
      throw new Error('Authentication required');
    }

    // Setup gate: redirect to setup wizard if setup isn't complete
    if (response.status === 403 && response.headers.get('X-Setup-Required') === 'true') {
      window.location.href = '/setup';
      throw new Error('Setup required');
    }

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
  await apiFetch<void>(`/api/threads/${threadId}`, { method: 'DELETE' });
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
  await apiFetch<void>(`/api/messages/${messageId}`, { method: 'DELETE' });
}

// ============================================================================
// Mesh Status API
// ============================================================================

export interface MeshStatus {
  batman: {
    available: boolean;
    originators: number;
    neighbors: number;
  };
  reticulum: {
    available: boolean;
    status: string;
    interfaces: string[];
  } | null;
}

export interface RadioStatus {
  radios: Array<{
    name: string;
    type: string;
    status: string;
    throughput: number | null;
    neighbors: number;
  }>;
}

export interface MeshTopology {
  nodes: Node[];
  edges: Thread[];
}

export interface MeshStatistics {
  available: boolean;
  data: Record<string, number | string>;
}

/**
 * Get overall mesh status (BATMAN + Reticulum)
 */
export async function fetchMeshStatus(): Promise<MeshStatus> {
  return apiFetch<MeshStatus>('/api/mesh/status');
}

/**
 * Get per-radio interface status
 */
export async function fetchRadioStatus(): Promise<RadioStatus> {
  return apiFetch<RadioStatus>('/api/mesh/radios');
}

/**
 * Get full mesh topology (nodes + edges)
 */
export async function fetchMeshTopology(): Promise<MeshTopology> {
  return apiFetch<MeshTopology>('/api/mesh/topology');
}

/**
 * Get BATMAN network statistics
 */
export async function fetchMeshStatistics(): Promise<MeshStatistics> {
  return apiFetch<MeshStatistics>('/api/mesh/statistics');
}

// ============================================================================
// Meshtastic API
// ============================================================================

export interface MeshtasticStatus {
  connected: boolean;
  device: string;
  node_id: string;
  short_name: string;
  long_name: string;
  battery_level: number;
  voltage: number;
  channel_utilization: number;
  air_util_tx: number;
  nodes_count: number;
}

export interface MeshtasticNode {
  node_id: string;
  short_name: string;
  long_name: string;
  last_heard: number;
  snr: number | null;
  position: { lat: number; lon: number; alt: number } | null;
}

/**
 * Get Meshtastic device status
 */
export async function fetchMeshtasticStatus(): Promise<MeshtasticStatus> {
  return apiFetch<MeshtasticStatus>('/api/meshtastic/status');
}

/**
 * Get all Meshtastic mesh nodes
 */
export async function fetchMeshtasticNodes(): Promise<MeshtasticNode[]> {
  return apiFetch<MeshtasticNode[]>('/api/meshtastic/nodes');
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

// ============================================================================
// Config API
// ============================================================================

export async function fetchConfig(): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>('/api/config');
}

export async function fetchConfigSection(section: string): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/api/config/${section}`);
}

export async function updateConfigSection(
  section: string,
  data: Record<string, unknown>
): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/api/config/${section}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function checkFirstBoot(): Promise<{ first_boot: boolean }> {
  return apiFetch<{ first_boot: boolean }>('/api/config/first-boot');
}

export async function saveConfigDefaults(): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>('/api/config/save-defaults', {
    method: 'POST',
  });
}

export async function restartService(name: string): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>(`/api/config/restart-service/${name}`, {
    method: 'POST',
  });
}

// ============================================================================
// Backhaul / Network Apply API
// ============================================================================

export interface BackhaulAdapter {
  name: string;
  driver: string;
  mac: string;
  usb_id: string;
}

export async function fetchBackhaulAdapters(): Promise<{ adapters: BackhaulAdapter[] }> {
  return apiFetch<{ adapters: BackhaulAdapter[] }>('/api/config/backhaul/adapters');
}

export async function fetchBackhaulStatus(): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>('/api/config/backhaul/status');
}

export async function applyBackhaul(): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>('/api/config/apply-backhaul', {
    method: 'POST',
  });
}

export async function applyNetwork(): Promise<Record<string, unknown>> {
  return apiFetch<Record<string, unknown>>('/api/config/apply-network', {
    method: 'POST',
  });
}
