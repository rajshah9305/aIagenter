import uuid
import json
import threading
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from collections import defaultdict, deque

class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"

class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class MessageStatus(Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    EXPIRED = "expired"

class IAMessage:
    """Inter-Agent Message structure."""
    
    def __init__(self, from_agent_id: str, to_agent_id: str, message_type: MessageType,
                 content: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL,
                 ttl_seconds: int = 300, requires_ack: bool = False):
        self.id = str(uuid.uuid4())
        self.from_agent_id = from_agent_id
        self.to_agent_id = to_agent_id
        self.message_type = message_type
        self.content = content
        self.priority = priority
        self.ttl_seconds = ttl_seconds
        self.requires_ack = requires_ack
        self.created_at = datetime.utcnow()
        self.delivered_at = None
        self.acknowledged_at = None
        self.status = MessageStatus.PENDING
        self.retry_count = 0
        self.max_retries = 3
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'from_agent_id': self.from_agent_id,
            'to_agent_id': self.to_agent_id,
            'message_type': self.message_type.value,
            'content': self.content,
            'priority': self.priority.value,
            'ttl_seconds': self.ttl_seconds,
            'requires_ack': self.requires_ack,
            'created_at': self.created_at.isoformat(),
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'status': self.status.value,
            'retry_count': self.retry_count
        }
    
    def is_expired(self) -> bool:
        """Check if message has expired."""
        if self.ttl_seconds <= 0:
            return False
        return (datetime.utcnow() - self.created_at).total_seconds() > self.ttl_seconds

class InterAgentCommunicationProtocol:
    """
    Inter-Agent Communication Protocol (IACP) implementation.
    Provides standardized messaging between agents across different frameworks.
    """
    
    def __init__(self):
        self.message_queue: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.message_history: Dict[str, IAMessage] = {}
        self.agent_subscriptions: Dict[str, List[str]] = defaultdict(list)  # topic -> [agent_ids]
        self.agent_handlers: Dict[str, Callable] = {}  # agent_id -> message_handler
        self.delivery_callbacks: Dict[str, Callable] = {}  # message_id -> callback
        self.is_running = False
        self.processor_thread = None
        self.cleanup_thread = None
        self.lock = threading.RLock()
        
    def start(self):
        """Start the IACP service."""
        if self.is_running:
            return
            
        self.is_running = True
        self.processor_thread = threading.Thread(target=self._message_processor_loop, daemon=True)
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        
        self.processor_thread.start()
        self.cleanup_thread.start()
        
        print("Inter-Agent Communication Protocol started")
    
    def stop(self):
        """Stop the IACP service."""
        self.is_running = False
        
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
            
        print("Inter-Agent Communication Protocol stopped")
    
    def register_agent(self, agent_id: str, message_handler: Callable = None):
        """
        Register an agent with the communication protocol.
        
        Args:
            agent_id: Unique agent identifier
            message_handler: Function to handle incoming messages
        """
        with self.lock:
            if message_handler:
                self.agent_handlers[agent_id] = message_handler
            
            # Initialize message queue for agent
            if agent_id not in self.message_queue:
                self.message_queue[agent_id] = deque(maxlen=1000)
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from the communication protocol."""
        with self.lock:
            # Remove from handlers
            if agent_id in self.agent_handlers:
                del self.agent_handlers[agent_id]
            
            # Remove from subscriptions
            for topic, subscribers in self.agent_subscriptions.items():
                if agent_id in subscribers:
                    subscribers.remove(agent_id)
            
            # Clear message queue
            if agent_id in self.message_queue:
                del self.message_queue[agent_id]
    
    def send_message(self, from_agent_id: str, to_agent_id: str, content: Dict[str, Any],
                    message_type: MessageType = MessageType.REQUEST,
                    priority: MessagePriority = MessagePriority.NORMAL,
                    ttl_seconds: int = 300, requires_ack: bool = False,
                    delivery_callback: Callable = None) -> str:
        """
        Send a message from one agent to another.
        
        Args:
            from_agent_id: Sender agent ID
            to_agent_id: Recipient agent ID
            content: Message content
            message_type: Type of message
            priority: Message priority
            ttl_seconds: Time to live in seconds
            requires_ack: Whether acknowledgment is required
            delivery_callback: Callback function for delivery confirmation
            
        Returns:
            message_id: Unique identifier for the sent message
        """
        message = IAMessage(
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            message_type=message_type,
            content=content,
            priority=priority,
            ttl_seconds=ttl_seconds,
            requires_ack=requires_ack
        )
        
        with self.lock:
            # Store message in history
            self.message_history[message.id] = message
            
            # Add to recipient's queue
            self.message_queue[to_agent_id].append(message)
            
            # Sort queue by priority
            self.message_queue[to_agent_id] = deque(
                sorted(self.message_queue[to_agent_id], 
                      key=lambda m: m.priority.value, reverse=True),
                maxlen=1000
            )
            
            # Register delivery callback
            if delivery_callback:
                self.delivery_callbacks[message.id] = delivery_callback
        
        return message.id
    
    def send_broadcast(self, from_agent_id: str, topic: str, content: Dict[str, Any],
                      priority: MessagePriority = MessagePriority.NORMAL) -> List[str]:
        """
        Send a broadcast message to all agents subscribed to a topic.
        
        Args:
            from_agent_id: Sender agent ID
            topic: Topic to broadcast to
            content: Message content
            priority: Message priority
            
        Returns:
            message_ids: List of message IDs for each recipient
        """
        message_ids = []
        
        with self.lock:
            subscribers = self.agent_subscriptions.get(topic, [])
            
            for subscriber_id in subscribers:
                if subscriber_id != from_agent_id:  # Don't send to self
                    message_id = self.send_message(
                        from_agent_id=from_agent_id,
                        to_agent_id=subscriber_id,
                        content={**content, 'topic': topic},
                        message_type=MessageType.BROADCAST,
                        priority=priority
                    )
                    message_ids.append(message_id)
        
        return message_ids
    
    def subscribe_to_topic(self, agent_id: str, topic: str):
        """Subscribe an agent to a topic for broadcast messages."""
        with self.lock:
            if agent_id not in self.agent_subscriptions[topic]:
                self.agent_subscriptions[topic].append(agent_id)
    
    def unsubscribe_from_topic(self, agent_id: str, topic: str):
        """Unsubscribe an agent from a topic."""
        with self.lock:
            if agent_id in self.agent_subscriptions[topic]:
                self.agent_subscriptions[topic].remove(agent_id)
    
    def get_messages(self, agent_id: str, limit: int = 10) -> List[IAMessage]:
        """
        Get pending messages for an agent.
        
        Args:
            agent_id: Agent identifier
            limit: Maximum number of messages to return
            
        Returns:
            messages: List of pending messages
        """
        with self.lock:
            messages = []
            agent_queue = self.message_queue.get(agent_id, deque())
            
            for _ in range(min(limit, len(agent_queue))):
                if agent_queue:
                    message = agent_queue.popleft()
                    if not message.is_expired():
                        message.status = MessageStatus.DELIVERED
                        message.delivered_at = datetime.utcnow()
                        messages.append(message)
                    else:
                        message.status = MessageStatus.EXPIRED
            
            return messages
    
    def acknowledge_message(self, message_id: str, agent_id: str) -> bool:
        """
        Acknowledge receipt of a message.
        
        Args:
            message_id: Message identifier
            agent_id: Agent acknowledging the message
            
        Returns:
            success: True if acknowledgment was successful
        """
        with self.lock:
            if message_id in self.message_history:
                message = self.message_history[message_id]
                
                if message.to_agent_id == agent_id and message.requires_ack:
                    message.status = MessageStatus.ACKNOWLEDGED
                    message.acknowledged_at = datetime.utcnow()
                    
                    # Call delivery callback if registered
                    if message_id in self.delivery_callbacks:
                        callback = self.delivery_callbacks[message_id]
                        try:
                            callback(message)
                        except Exception as e:
                            print(f"Error calling delivery callback: {e}")
                        finally:
                            del self.delivery_callbacks[message_id]
                    
                    return True
            
            return False
    
    def get_message_status(self, message_id: str) -> Optional[MessageStatus]:
        """Get the status of a message."""
        with self.lock:
            if message_id in self.message_history:
                return self.message_history[message_id].status
            return None
    
    def get_communication_stats(self) -> Dict[str, Any]:
        """Get communication statistics."""
        with self.lock:
            total_messages = len(self.message_history)
            pending_messages = sum(len(queue) for queue in self.message_queue.values())
            
            status_counts = defaultdict(int)
            for message in self.message_history.values():
                status_counts[message.status.value] += 1
            
            return {
                'total_messages': total_messages,
                'pending_messages': pending_messages,
                'registered_agents': len(self.agent_handlers),
                'active_topics': len(self.agent_subscriptions),
                'status_breakdown': dict(status_counts),
                'delivery_callbacks_pending': len(self.delivery_callbacks)
            }
    
    def _message_processor_loop(self):
        """Main message processing loop."""
        while self.is_running:
            try:
                self._process_pending_messages()
                self._retry_failed_messages()
                time.sleep(1)  # Process messages every second
                
            except Exception as e:
                print(f"Error in message processor loop: {e}")
                time.sleep(5)
    
    def _process_pending_messages(self):
        """Process pending messages by calling agent handlers."""
        with self.lock:
            for agent_id, handler in self.agent_handlers.items():
                if agent_id in self.message_queue:
                    queue = self.message_queue[agent_id]
                    
                    # Process up to 5 messages per agent per cycle
                    for _ in range(min(5, len(queue))):
                        if queue:
                            message = queue.popleft()
                            
                            if not message.is_expired():
                                try:
                                    # Call agent's message handler
                                    handler(message)
                                    message.status = MessageStatus.DELIVERED
                                    message.delivered_at = datetime.utcnow()
                                    
                                except Exception as e:
                                    print(f"Error delivering message {message.id} to {agent_id}: {e}")
                                    message.status = MessageStatus.FAILED
                                    message.retry_count += 1
                                    
                                    # Re-queue for retry if under max retries
                                    if message.retry_count < message.max_retries:
                                        queue.append(message)
                            else:
                                message.status = MessageStatus.EXPIRED
    
    def _retry_failed_messages(self):
        """Retry failed messages that haven't exceeded max retries."""
        # This is handled in _process_pending_messages by re-queuing failed messages
        pass
    
    def _cleanup_loop(self):
        """Cleanup loop for removing old messages and expired data."""
        while self.is_running:
            try:
                self._cleanup_expired_messages()
                time.sleep(300)  # Cleanup every 5 minutes
                
            except Exception as e:
                print(f"Error in cleanup loop: {e}")
                time.sleep(60)
    
    def _cleanup_expired_messages(self):
        """Remove expired messages from history and queues."""
        with self.lock:
            # Clean up message history (keep messages for 1 hour after expiry)
            cutoff_time = datetime.utcnow()
            expired_message_ids = []
            
            for message_id, message in self.message_history.items():
                if message.is_expired():
                    # Keep for additional hour after expiry for debugging
                    if (cutoff_time - message.created_at).total_seconds() > (message.ttl_seconds + 3600):
                        expired_message_ids.append(message_id)
            
            for message_id in expired_message_ids:
                del self.message_history[message_id]
                # Also remove any pending delivery callbacks
                if message_id in self.delivery_callbacks:
                    del self.delivery_callbacks[message_id]
            
            # Clean up expired messages from queues
            for agent_id, queue in self.message_queue.items():
                # Convert to list, filter, and convert back to deque
                valid_messages = [msg for msg in queue if not msg.is_expired()]
                self.message_queue[agent_id] = deque(valid_messages, maxlen=1000)

class WebSocketManager:
    """
    WebSocket manager for real-time communication with frontend clients.
    """
    
    def __init__(self):
        self.clients: Dict[str, Any] = {}  # client_id -> websocket_connection
        self.client_subscriptions: Dict[str, List[str]] = defaultdict(list)  # topic -> [client_ids]
        self.is_running = False
        
    def start(self):
        """Start the WebSocket manager."""
        self.is_running = True
        print("WebSocket manager started")
    
    def stop(self):
        """Stop the WebSocket manager."""
        self.is_running = False
        print("WebSocket manager stopped")
    
    def add_client(self, client_id: str, websocket_connection):
        """Add a WebSocket client."""
        self.clients[client_id] = websocket_connection
    
    def remove_client(self, client_id: str):
        """Remove a WebSocket client."""
        if client_id in self.clients:
            del self.clients[client_id]
        
        # Remove from all subscriptions
        for topic, subscribers in self.client_subscriptions.items():
            if client_id in subscribers:
                subscribers.remove(client_id)
    
    def subscribe_client(self, client_id: str, topic: str):
        """Subscribe a client to a topic."""
        if client_id not in self.client_subscriptions[topic]:
            self.client_subscriptions[topic].append(client_id)
    
    def unsubscribe_client(self, client_id: str, topic: str):
        """Unsubscribe a client from a topic."""
        if client_id in self.client_subscriptions[topic]:
            self.client_subscriptions[topic].remove(client_id)
    
    def broadcast_to_topic(self, topic: str, data: Dict[str, Any]):
        """Broadcast data to all clients subscribed to a topic."""
        subscribers = self.client_subscriptions.get(topic, [])
        
        for client_id in subscribers:
            if client_id in self.clients:
                try:
                    # In a real implementation, this would send via WebSocket
                    # For now, we'll just log the broadcast
                    print(f"Broadcasting to client {client_id} on topic {topic}: {data}")
                except Exception as e:
                    print(f"Error broadcasting to client {client_id}: {e}")
    
    def send_to_client(self, client_id: str, data: Dict[str, Any]):
        """Send data to a specific client."""
        if client_id in self.clients:
            try:
                # In a real implementation, this would send via WebSocket
                print(f"Sending to client {client_id}: {data}")
            except Exception as e:
                print(f"Error sending to client {client_id}: {e}")

