/**
 * Mesh Network Store
 * 
 * Zustand store for managing mesh network state with live API and WebSocket updates.
 * Combines REST API fetching with real-time WebSocket events.
 */

import { create } from 'zustand';
import {
  fetchNodes,
  fetchThreads,
  fetchMessages,
  fetchMeshStatus,
  type Node,
  type Thread,
  type Message,
  type MeshStatus,
} from '../services/api';
import {
  connectWebSocket,
  disconnectWebSocket,
  getWebSocketClient,
  type WebSocketMessage,
} from '../services/ws';

interface MeshStore {
  // Data
  nodes: Node[];
  threads: Thread[];
  messages: Message[];
  meshStatus: MeshStatus | null;

  // Loading states
  nodesLoading: boolean;
  threadsLoading: boolean;
  messagesLoading: boolean;
  meshStatusLoading: boolean;

  // Error states
  nodesError: string | null;
  threadsError: string | null;
  messagesError: string | null;
  meshStatusError: string | null;

  // WebSocket connection
  wsConnected: boolean;

  // Actions
  loadNodes: () => Promise<void>;
  loadThreads: () => Promise<void>;
  loadMessages: () => Promise<void>;
  loadMeshStatus: () => Promise<void>;
  loadAll: () => Promise<void>;
  
  connectWS: () => void;
  disconnectWS: () => void;

  // Internal update handlers
  updateNode: (_node: Node) => void;
  addNode: (_node: Node) => void;
  removeNode: (_nodeId: string) => void;
  
  updateThread: (_thread: Thread) => void;
  addThread: (_thread: Thread) => void;
  removeThread: (_threadId: string) => void;
  
  addMessage: (_message: Message) => void;
  removeMessage: (_messageId: string) => void;
}

const useMeshStore = create<MeshStore>((set, get) => ({
  // Initial state
  nodes: [],
  threads: [],
  messages: [],
  meshStatus: null,

  nodesLoading: false,
  threadsLoading: false,
  messagesLoading: false,
  meshStatusLoading: false,

  nodesError: null,
  threadsError: null,
  messagesError: null,
  meshStatusError: null,

  wsConnected: false,

  // ========================================================================
  // REST API Actions
  // ========================================================================

  /**
   * Load all nodes from the API
   */
  loadNodes: async () => {
    set({ nodesLoading: true, nodesError: null });
    try {
      const nodes = await fetchNodes();
      set({ nodes, nodesLoading: false });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load nodes';
      set({ nodesError: errorMessage, nodesLoading: false });
      console.error('[MeshStore] Failed to load nodes:', error);
    }
  },

  /**
   * Load all threads from the API
   */
  loadThreads: async () => {
    set({ threadsLoading: true, threadsError: null });
    try {
      const threads = await fetchThreads();
      set({ threads, threadsLoading: false });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load threads';
      set({ threadsError: errorMessage, threadsLoading: false });
      console.error('[MeshStore] Failed to load threads:', error);
    }
  },

  /**
   * Load recent messages from the API
   */
  loadMessages: async () => {
    set({ messagesLoading: true, messagesError: null });
    try {
      const messages = await fetchMessages({ limit: 100 });
      set({ messages, messagesLoading: false });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load messages';
      set({ messagesError: errorMessage, messagesLoading: false });
      console.error('[MeshStore] Failed to load messages:', error);
    }
  },

  /**
   * Load mesh status (BATMAN + Reticulum availability)
   */
  loadMeshStatus: async () => {
    set({ meshStatusLoading: true, meshStatusError: null });
    try {
      const status = await fetchMeshStatus();
      set({ meshStatus: status, meshStatusLoading: false });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load mesh status';
      set({ meshStatusError: errorMessage, meshStatusLoading: false });
      console.error('[MeshStore] Failed to load mesh status:', error);
    }
  },

  /**
   * Load all data (nodes, threads, messages, mesh status)
   */
  loadAll: async () => {
    await Promise.all([
      get().loadNodes(),
      get().loadThreads(),
      get().loadMessages(),
      get().loadMeshStatus(),
    ]);
  },

  // ========================================================================
  // WebSocket Actions
  // ========================================================================

  /**
   * Connect to WebSocket and subscribe to events
   */
  connectWS: () => {
    const client = connectWebSocket();

    // Subscribe to connection status
    client.on('connected', () => {
      set({ wsConnected: true });
      console.log('[MeshStore] WebSocket connected');
    });

    // Subscribe to node events
    client.on('node_added', (msg: WebSocketMessage) => {
      if (msg.data) {
        get().addNode(msg.data as Node);
      }
    });

    client.on('node_updated', (msg: WebSocketMessage) => {
      if (msg.data) {
        get().updateNode(msg.data as Node);
      }
    });

    client.on('node_removed', (msg: WebSocketMessage) => {
      if (msg.data?.id) {
        get().removeNode(msg.data.id);
      }
    });

    // Subscribe to thread events
    client.on('thread_added', (msg: WebSocketMessage) => {
      if (msg.data) {
        get().addThread(msg.data as Thread);
      }
    });

    client.on('thread_updated', (msg: WebSocketMessage) => {
      if (msg.data) {
        get().updateThread(msg.data as Thread);
      }
    });

    client.on('thread_removed', (msg: WebSocketMessage) => {
      if (msg.data?.id) {
        get().removeThread(msg.data.id);
      }
    });

    // Subscribe to message events
    client.on('message_added', (msg: WebSocketMessage) => {
      if (msg.data) {
        get().addMessage(msg.data as Message);
      }
    });

    client.on('message_removed', (msg: WebSocketMessage) => {
      if (msg.data?.id) {
        get().removeMessage(msg.data.id);
      }
    });

    // Subscribe to store events
    client.on('store_loaded', () => {
      console.log('[MeshStore] Store reloaded on backend, fetching fresh data');
      get().loadAll();
    });

    client.on('store_cleared', () => {
      console.log('[MeshStore] Store cleared on backend');
      set({ nodes: [], threads: [], messages: [] });
    });

    // Subscribe to mesh_update events (Phase 3: real-time mesh monitoring)
    client.on('mesh_update', (msg: WebSocketMessage) => {
      if (msg.data) {
        console.log('[MeshStore] Mesh topology changed, refreshing data');
        // Refresh all data from REST API to get the updated state
        get().loadAll();
      }
    });

    // Track disconnection
    const ws = getWebSocketClient();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const wsInstance = (ws as any)['ws'] as WebSocket | null;
    if (wsInstance) {
      const originalOnClose = wsInstance.onclose;
      wsInstance.onclose = (event) => {
        set({ wsConnected: false });
        if (originalOnClose) {
          originalOnClose.call(wsInstance, event);
        }
      };
    }
  },

  /**
   * Disconnect from WebSocket
   */
  disconnectWS: () => {
    disconnectWebSocket();
    set({ wsConnected: false });
  },

  // ========================================================================
  // Internal Update Handlers
  // ========================================================================

  /**
   * Update an existing node or add if not found
   */
  updateNode: (updatedNode: Node) => {
    set((state) => {
      const index = state.nodes.findIndex((n) => n.id === updatedNode.id);
      if (index === -1) {
        // Not found, add it
        return { nodes: [...state.nodes, updatedNode] };
      }
      // Update existing
      const nodes = [...state.nodes];
      nodes[index] = updatedNode;
      return { nodes };
    });
  },

  /**
   * Add a new node
   */
  addNode: (node: Node) => {
    set((state) => {
      // Avoid duplicates
      if (state.nodes.some((n) => n.id === node.id)) {
        return state;
      }
      return { nodes: [...state.nodes, node] };
    });
  },

  /**
   * Remove a node by ID
   */
  removeNode: (nodeId: string) => {
    set((state) => ({
      nodes: state.nodes.filter((n) => n.id !== nodeId),
    }));
  },

  /**
   * Update an existing thread or add if not found
   */
  updateThread: (updatedThread: Thread) => {
    set((state) => {
      const index = state.threads.findIndex((t) => t.id === updatedThread.id);
      if (index === -1) {
        return { threads: [...state.threads, updatedThread] };
      }
      const threads = [...state.threads];
      threads[index] = updatedThread;
      return { threads };
    });
  },

  /**
   * Add a new thread
   */
  addThread: (thread: Thread) => {
    set((state) => {
      if (state.threads.some((t) => t.id === thread.id)) {
        return state;
      }
      return { threads: [...state.threads, thread] };
    });
  },

  /**
   * Remove a thread by ID
   */
  removeThread: (threadId: string) => {
    set((state) => ({
      threads: state.threads.filter((t) => t.id !== threadId),
    }));
  },

  /**
   * Add a new message (prepend to list for newest-first order)
   */
  addMessage: (message: Message) => {
    set((state) => {
      if (state.messages.some((m) => m.id === message.id)) {
        return state;
      }
      return { messages: [message, ...state.messages] };
    });
  },

  /**
   * Remove a message by ID
   */
  removeMessage: (messageId: string) => {
    set((state) => ({
      messages: state.messages.filter((m) => m.id !== messageId),
    }));
  },
}));

export default useMeshStore;
= messageId),
    }));
  },
}));

export default useMeshStore;
