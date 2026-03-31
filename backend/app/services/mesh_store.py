"""In-memory mesh network state management with event emission"""

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Optional

from app.models import Message, Node, Thread


class MeshStore:
    """
    In-memory store for mesh network state with CRUD operations
    and event emission hooks for WebSocket updates
    """

    def __init__(self):
        """Initialize the mesh store with empty state"""
        self._nodes: dict[str, Node] = {}
        self._threads: dict[str, Thread] = {}
        self._messages: dict[str, Message] = {}
        self._event_handlers: list[Callable] = []

    # Event emission
    def on_event(self, handler: Callable):
        """
        Register an event handler for state changes

        Args:
            handler: Callable that receives (event_type: str, data: dict)
        """
        self._event_handlers.append(handler)

    def _emit_event(self, event_type: str, data: dict):
        """
        Emit an event to all registered handlers

        Args:
            event_type: Type of event (e.g., "node_added", "node_update")
            data: Event data payload
        """
        for handler in self._event_handlers:
            try:
                handler(event_type, data)
            except Exception as e:
                # Log error but don't stop other handlers
                print(f"Error in event handler: {e}")

    # Node CRUD operations
    def add_node(self, node: Node) -> Node:
        """
        Add a new node to the store

        Args:
            node: Node to add

        Returns:
            The added node

        Raises:
            ValueError: If node with same ID already exists
        """
        if node.id in self._nodes:
            raise ValueError(f"Node with ID {node.id} already exists")

        self._nodes[node.id] = node
        self._emit_event("node_added", node.model_dump())
        return node

    def get_node(self, node_id: str) -> Optional[Node]:
        """
        Get a node by ID

        Args:
            node_id: ID of the node to retrieve

        Returns:
            The node if found, None otherwise
        """
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> list[Node]:
        """
        Get all nodes

        Returns:
            List of all nodes
        """
        return list(self._nodes.values())

    def update_node(self, node_id: str, **updates) -> Optional[Node]:
        """
        Update a node's fields

        Args:
            node_id: ID of the node to update
            **updates: Fields to update

        Returns:
            Updated node if found, None otherwise
        """
        node = self._nodes.get(node_id)
        if not node:
            return None

        # Create updated node with new values
        updated_data = node.model_dump()
        updated_data.update(updates)
        updated_node = Node(**updated_data)

        self._nodes[node_id] = updated_node
        self._emit_event("node_update", updated_node.model_dump())
        return updated_node

    def remove_node(self, node_id: str) -> bool:
        """
        Remove a node from the store

        Args:
            node_id: ID of the node to remove

        Returns:
            True if node was removed, False if not found
        """
        if node_id in self._nodes:
            self._nodes.pop(node_id)
            self._emit_event("node_removed", {"id": node_id})

            # Also remove threads involving this node
            threads_to_remove = [
                thread_id
                for thread_id, thread in self._threads.items()
                if thread.source_id == node_id or thread.target_id == node_id
            ]
            for thread_id in threads_to_remove:
                self.remove_thread(thread_id)

            return True
        return False

    # Thread CRUD operations
    def add_thread(self, thread: Thread) -> Thread:
        """
        Add a new thread (connection) to the store

        Args:
            thread: Thread to add

        Returns:
            The added thread

        Raises:
            ValueError: If thread with same ID already exists
        """
        if thread.id in self._threads:
            raise ValueError(f"Thread with ID {thread.id} already exists")

        # Verify that both nodes exist
        if thread.source_id not in self._nodes:
            raise ValueError(f"Source node {thread.source_id} does not exist")
        if thread.target_id not in self._nodes:
            raise ValueError(f"Target node {thread.target_id} does not exist")

        self._threads[thread.id] = thread
        self._emit_event("thread_added", thread.model_dump())
        return thread

    def get_thread(self, thread_id: str) -> Optional[Thread]:
        """
        Get a thread by ID

        Args:
            thread_id: ID of the thread to retrieve

        Returns:
            The thread if found, None otherwise
        """
        return self._threads.get(thread_id)

    def get_all_threads(self) -> list[Thread]:
        """
        Get all threads

        Returns:
            List of all threads
        """
        return list(self._threads.values())

    def get_threads_for_node(self, node_id: str) -> list[Thread]:
        """
        Get all threads connected to a specific node

        Args:
            node_id: ID of the node

        Returns:
            List of threads involving this node
        """
        return [
            thread
            for thread in self._threads.values()
            if thread.source_id == node_id or thread.target_id == node_id
        ]

    def update_thread(self, thread_id: str, **updates) -> Optional[Thread]:
        """
        Update a thread's fields

        Args:
            thread_id: ID of the thread to update
            **updates: Fields to update

        Returns:
            Updated thread if found, None otherwise
        """
        thread = self._threads.get(thread_id)
        if not thread:
            return None

        # Create updated thread with new values
        updated_data = thread.model_dump()
        updated_data.update(updates)
        updated_thread = Thread(**updated_data)

        self._threads[thread_id] = updated_thread
        self._emit_event("thread_update", updated_thread.model_dump())
        return updated_thread

    def remove_thread(self, thread_id: str) -> bool:
        """
        Remove a thread from the store

        Args:
            thread_id: ID of the thread to remove

        Returns:
            True if thread was removed, False if not found
        """
        if thread_id in self._threads:
            self._threads.pop(thread_id)
            self._emit_event("thread_removed", {"id": thread_id})
            return True
        return False

    # Message CRUD operations
    def add_message(self, message: Message) -> Message:
        """
        Add a new message to the store

        Args:
            message: Message to add

        Returns:
            The added message

        Raises:
            ValueError: If message with same ID already exists
        """
        if message.id in self._messages:
            raise ValueError(f"Message with ID {message.id} already exists")

        # Verify sender exists
        if message.sender_id not in self._nodes:
            raise ValueError(f"Sender node {message.sender_id} does not exist")

        # Verify recipient exists (if not broadcast)
        if message.recipient_id is not None and message.recipient_id not in self._nodes:
            raise ValueError(f"Recipient node {message.recipient_id} does not exist")

        self._messages[message.id] = message
        self._emit_event("message_added", message.model_dump())
        return message

    def get_message(self, message_id: str) -> Optional[Message]:
        """
        Get a message by ID

        Args:
            message_id: ID of the message to retrieve

        Returns:
            The message if found, None otherwise
        """
        return self._messages.get(message_id)

    def get_all_messages(self) -> list[Message]:
        """
        Get all messages

        Returns:
            List of all messages sorted by timestamp (newest first)
        """
        messages = list(self._messages.values())
        messages.sort(key=lambda m: m.timestamp, reverse=True)
        return messages

    def get_messages_for_node(self, node_id: str) -> list[Message]:
        """
        Get all messages sent to or from a specific node

        Args:
            node_id: ID of the node

        Returns:
            List of messages involving this node (sorted by timestamp, newest first)
        """
        messages = [
            msg
            for msg in self._messages.values()
            if msg.sender_id == node_id or msg.recipient_id == node_id
        ]
        messages.sort(key=lambda m: m.timestamp, reverse=True)
        return messages

    def remove_message(self, message_id: str) -> bool:
        """
        Remove a message from the store

        Args:
            message_id: ID of the message to remove

        Returns:
            True if message was removed, False if not found
        """
        if message_id in self._messages:
            self._messages.pop(message_id)
            self._emit_event("message_removed", {"id": message_id})
            return True
        return False

    # Utility methods
    def clear(self):
        """Clear all data from the store"""
        self._nodes.clear()
        self._threads.clear()
        self._messages.clear()
        self._emit_event("store_cleared", {})

    def get_stats(self) -> dict:
        """
        Get store statistics

        Returns:
            Dictionary with node, thread, and message counts
        """
        online_nodes = sum(
            1 for node in self._nodes.values() if node.status == "online"
        )
        return {
            "node_count": len(self._nodes),
            "active_node_count": online_nodes,
            "thread_count": len(self._threads),
            "message_count": len(self._messages),
            "last_update": datetime.now(timezone.utc),
        }

    def load_from_source(
        self, nodes: list[Node], threads: list[Thread], messages: list[Message]
    ):
        """
        Bulk load data from a source (useful for initialization)

        Args:
            nodes: List of nodes to load
            threads: List of threads to load
            messages: List of messages to load
        """
        self.clear()

        # Load nodes first
        for node in nodes:
            self._nodes[node.id] = node

        # Then threads (requires nodes to exist)
        for thread in threads:
            self._threads[thread.id] = thread

        # Finally messages (requires nodes to exist)
        for message in messages:
            self._messages[message.id] = message

        self._emit_event("store_loaded", self.get_stats())

    def merge_from_source(
        self, nodes: list[Node], threads: list[Thread], messages: list[Message]
    ):
        """
        Merge BATMAN data into the store without clearing Meshtastic-bridged nodes.

        Removes stale BATMAN nodes (not prefixed with 'mesh_') and replaces them
        with the new data, while preserving Meshtastic-bridged entries.

        Args:
            nodes: BATMAN nodes to merge
            threads: BATMAN threads to merge
            messages: BATMAN messages to merge
        """
        # Remove old BATMAN nodes/threads/messages (keep Meshtastic-bridged ones)
        self._nodes = {k: v for k, v in self._nodes.items() if k.startswith("mesh_")}
        self._threads = {
            k: v for k, v in self._threads.items() if k.startswith("thread_mesh_")
        }
        # Messages don't have a mesh_ prefix convention — clear all and reload
        self._messages.clear()

        # Merge in BATMAN data
        for node in nodes:
            self._nodes[node.id] = node
        for thread in threads:
            self._threads[thread.id] = thread
        for message in messages:
            self._messages[message.id] = message
