"""
Plugin Event Bus for IrintAI Assistant
Enables inter-plugin communication through a publish/subscribe pattern
"""
import threading
import time
import uuid
import queue
from typing import Dict, List, Any, Callable, Set, Optional, Tuple, Union

class EventBus:
    """
    Event bus for inter-plugin communication
    Implements a publish/subscribe pattern with support for wildcards
    """
    
    def __init__(self, logger=None):
        """
        Initialize the event bus
        
        Args:
            logger: Optional logger for event logging
        """
        self.logger = logger
        self.subscribers = {}
        self.wildcard_subscribers = {}
        self.one_time_subscribers = {}
        self.subscriptions = {}  # Track subscriptions by subscriber ID
        self.lock = threading.RLock()
        self.event_history = {}
        self.history_limit = 100
        self.event_queue = queue.Queue()
        self.running = False
        self.async_thread = None
        
    def start(self):
        """Start the async event processing thread"""
        if self.running:
            return
            
        self.running = True
        self.async_thread = threading.Thread(target=self._process_event_queue, daemon=True)
        self.async_thread.start()
        self._log("Event Bus started")
        
    def stop(self):
        """Stop the async event processing thread"""
        self.running = False
        if self.async_thread:
            self.async_thread.join(timeout=2.0)
            self.async_thread = None
        self._log("Event Bus stopped")
        
    def _log(self, message, level="INFO"):
        """Log a message if logger is available"""
        if self.logger:
            if hasattr(self.logger, 'log'):
                self.logger.log(f"[EventBus] {message}", level)
            else:
                print(f"[EventBus] {message}")
        
    def subscribe(self, event_pattern: str, callback: Callable, subscriber_id: str = None, 
                  one_time: bool = False) -> str:
        """
        Subscribe to events matching the given pattern
        
        Args:
            event_pattern: Event pattern to subscribe to (can include wildcards *)
            callback: Function to call when event occurs
            subscriber_id: Optional ID of the subscriber (used for unsubscribing)
            one_time: Whether this is a one-time subscription
            
        Returns:
            Subscription ID
        """
        if not callable(callback):
            raise ValueError("Callback must be callable")
            
        # Generate subscriber ID if not provided
        if subscriber_id is None:
            subscriber_id = str(uuid.uuid4())
            
        # Generate a unique subscription ID
        subscription_id = str(uuid.uuid4())
        
        with self.lock:
            # Handle wildcard patterns
            if '*' in event_pattern:
                if event_pattern not in self.wildcard_subscribers:
                    self.wildcard_subscribers[event_pattern] = {}
                self.wildcard_subscribers[event_pattern][subscription_id] = callback
            else:
                if event_pattern not in self.subscribers:
                    self.subscribers[event_pattern] = {}
                self.subscribers[event_pattern][subscription_id] = callback
                
            # Store one-time subscriptions separately
            if one_time:
                self.one_time_subscribers[subscription_id] = event_pattern
                
            # Track subscription by subscriber ID
            if subscriber_id not in self.subscriptions:
                self.subscriptions[subscriber_id] = set()
            self.subscriptions[subscriber_id].add(subscription_id)
            
        self._log(f"Subscriber {subscriber_id} subscribed to {event_pattern} (ID: {subscription_id})")
        return subscription_id
        
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from an event using the subscription ID
        
        Args:
            subscription_id: ID returned from subscribe()
            
        Returns:
            True if unsubscribed successfully, False otherwise
        """
        with self.lock:
            # Check if this is a one-time subscription
            one_time = False
            if subscription_id in self.one_time_subscribers:
                event_pattern = self.one_time_subscribers.pop(subscription_id)
                one_time = True
            else:
                # Search for the subscription ID in all event patterns
                event_pattern = None
                for pattern, subscribers in self.subscribers.items():
                    if subscription_id in subscribers:
                        event_pattern = pattern
                        break
                        
                if event_pattern is None:
                    # Check wildcard patterns
                    for pattern, subscribers in self.wildcard_subscribers.items():
                        if subscription_id in subscribers:
                            event_pattern = pattern
                            break
            
            if not event_pattern:
                return False
                
            # Remove the subscription
            removed = False
            if '*' in event_pattern:
                if event_pattern in self.wildcard_subscribers:
                    if subscription_id in self.wildcard_subscribers[event_pattern]:
                        del self.wildcard_subscribers[event_pattern][subscription_id]
                        removed = True
            else:
                if event_pattern in self.subscribers:
                    if subscription_id in self.subscribers[event_pattern]:
                        del self.subscribers[event_pattern][subscription_id]
                        removed = True
                        
            # Remove from subscriber's list
            for subscriber_id, subscriptions in self.subscriptions.items():
                if subscription_id in subscriptions:
                    subscriptions.remove(subscription_id)
                    if not subscriptions:
                        del self.subscriptions[subscriber_id]
                    break
                    
            if removed:
                self._log(f"Unsubscribed from {event_pattern} (ID: {subscription_id})")
            return removed
            
    def unsubscribe_all(self, subscriber_id: str) -> int:
        """
        Unsubscribe from all events for a given subscriber ID
        
        Args:
            subscriber_id: Subscriber ID
            
        Returns:
            Number of subscriptions removed
        """
        with self.lock:
            if subscriber_id not in self.subscriptions:
                return 0
                
            subscriptions = list(self.subscriptions[subscriber_id])
            count = 0
            
            for subscription_id in subscriptions:
                if self.unsubscribe(subscription_id):
                    count += 1
                    
            return count
            
    def publish(self, event_name: str, data: Any = None, 
                async_mode: bool = False, publisher_id: str = None) -> None:
        """
        Publish an event
        
        Args:
            event_name: Name of the event
            data: Data to include with the event
            async_mode: Whether to process the event asynchronously
            publisher_id: Optional ID of the publisher
        """
        event = {
            'name': event_name,
            'data': data,
            'timestamp': time.time(),
            'publisher_id': publisher_id
        }
        
        # Add to event history
        with self.lock:
            if event_name not in self.event_history:
                self.event_history[event_name] = []
            self.event_history[event_name].append(event)
            
            # Trim history if needed
            if len(self.event_history[event_name]) > self.history_limit:
                self.event_history[event_name] = self.event_history[event_name][-self.history_limit:]
        
        if async_mode and self.running:
            # Add to the event queue for async processing
            self.event_queue.put(event)
        else:
            # Process synchronously
            self._process_event(event)
            
    def _process_event_queue(self):
        """Process events from the queue asynchronously"""
        while self.running:
            try:
                # Wait for an event with timeout to allow checking running status
                try:
                    event = self.event_queue.get(timeout=0.5)
                    self._process_event(event)
                    self.event_queue.task_done()
                except queue.Empty:
                    continue
            except Exception as e:
                self._log(f"Error processing event queue: {e}", "ERROR")
                time.sleep(1)  # Avoid tight loop in case of persistent error
    
    def _process_event(self, event):
        """Process a single event"""
        event_name = event['name']
        
        # Get all matching subscribers
        matching_subscribers = {}
        one_time_ids = set()
        
        with self.lock:
            # Direct subscribers
            if event_name in self.subscribers:
                for sub_id, callback in self.subscribers[event_name].items():
                    matching_subscribers[sub_id] = callback
                    # Check if this is a one-time subscription
                    if sub_id in self.one_time_subscribers:
                        one_time_ids.add(sub_id)
                        
            # Wildcard subscribers
            for pattern, subscribers in self.wildcard_subscribers.items():
                if self._matches_pattern(event_name, pattern):
                    for sub_id, callback in subscribers.items():
                        matching_subscribers[sub_id] = callback
                        # Check if this is a one-time subscription
                        if sub_id in self.one_time_subscribers:
                            one_time_ids.add(sub_id)
        
        # Call the subscribers
        for sub_id, callback in matching_subscribers.items():
            try:
                callback(event_name, event['data'], event)
            except Exception as e:
                self._log(f"Error in event callback for {event_name}: {e}", "ERROR")
                
        # Remove one-time subscribers
        if one_time_ids:
            with self.lock:
                for sub_id in one_time_ids:
                    self.unsubscribe(sub_id)
    
    def _matches_pattern(self, event_name: str, pattern: str) -> bool:
        """
        Check if an event name matches a pattern
        
        Args:
            event_name: Event name to check
            pattern: Pattern to match against
            
        Returns:
            True if the event name matches the pattern, False otherwise
        """
        # Simple wildcard matching
        if pattern == '*':
            return True
            
        if pattern.endswith('.*'):
            prefix = pattern[:-2]
            return event_name.startswith(prefix + '.')
            
        if pattern.startswith('*.'):
            suffix = pattern[2:]
            return event_name.endswith('.' + suffix)
            
        # Handle patterns with * in the middle
        parts = pattern.split('*')
        if len(parts) == 1:
            return pattern == event_name
            
        # Check start
        if not event_name.startswith(parts[0]):
            return False
        
        # Check end
        if not event_name.endswith(parts[-1]):
            return False
        
        # Check middle parts
        current_pos = len(parts[0])
        for part in parts[1:-1]:
            if part:
                part_pos = event_name.find(part, current_pos)
                if part_pos == -1:
                    return False
                current_pos = part_pos + len(part)
                
        return True
        
    def get_event_history(self, event_name: str = None, limit: int = None) -> List[Dict]:
        """
        Get event history for a specific event or all events
        
        Args:
            event_name: Optional event name to filter by
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        with self.lock:
            result = []
            
            if event_name:
                # Get history for specific event
                events = self.event_history.get(event_name, [])
                result = events.copy()
            else:
                # Get all events, flattened
                for event_list in self.event_history.values():
                    result.extend(event_list)
                    
                # Sort by timestamp
                result.sort(key=lambda e: e['timestamp'])
                
            # Apply limit
            if limit and len(result) > limit:
                result = result[-limit:]
                
            return result
            
    def clear_event_history(self, event_name: str = None) -> None:
        """
        Clear event history
        
        Args:
            event_name: Optional event name to clear history for
        """
        with self.lock:
            if event_name:
                if event_name in self.event_history:
                    self.event_history[event_name] = []
            else:
                self.event_history = {}
                
    def wait_for_event(self, event_name: str, timeout: float = None, 
                       condition: Callable = None) -> Optional[Dict]:
        """
        Wait for an event to occur
        
        Args:
            event_name: Event name to wait for
            timeout: Maximum time to wait in seconds
            condition: Optional condition function to check event data
            
        Returns:
            Event data or None if timeout
        """
        result = [None]
        event = threading.Event()
        
        def callback(name, data, event_data):
            if condition and not condition(data):
                return
                
            result[0] = event_data
            event.set()
            
        # Subscribe to the event
        sub_id = self.subscribe(event_name, callback, one_time=True)
        
        # Wait for the event or timeout
        if not event.wait(timeout):
            # Timeout, unsubscribe
            self.unsubscribe(sub_id)
            
        return result[0]
        
    def list_subscribers(self, event_pattern: str = None) -> Dict:
        """
        List subscribers
        
        Args:
            event_pattern: Optional event pattern to filter by
            
        Returns:
            Dictionary of event patterns and subscriber counts
        """
        with self.lock:
            result = {}
            
            if event_pattern:
                # Count subscribers for specific pattern
                if '*' in event_pattern:
                    if event_pattern in self.wildcard_subscribers:
                        result[event_pattern] = len(self.wildcard_subscribers[event_pattern])
                else:
                    if event_pattern in self.subscribers:
                        result[event_pattern] = len(self.subscribers[event_pattern])
            else:
                # Count all subscribers
                for pattern, subscribers in self.subscribers.items():
                    result[pattern] = len(subscribers)
                    
                for pattern, subscribers in self.wildcard_subscribers.items():
                    result[pattern] = len(subscribers)
                    
            return result
            
    def get_subscriber_info(self, subscriber_id: str) -> Dict:
        """
        Get information about a subscriber
        
        Args:
            subscriber_id: Subscriber ID
            
        Returns:
            Dictionary of subscriber information
        """
        with self.lock:
            if subscriber_id not in self.subscriptions:
                return {'subscriber_id': subscriber_id, 'subscriptions': []}
                
            subscriptions = []
            for subscription_id in self.subscriptions[subscriber_id]:
                # Find the event pattern for this subscription
                event_pattern = None
                one_time = subscription_id in self.one_time_subscribers
                
                # Check direct subscribers
                for pattern, subs in self.subscribers.items():
                    if subscription_id in subs:
                        event_pattern = pattern
                        break
                        
                # Check wildcard subscribers
                if not event_pattern:
                    for pattern, subs in self.wildcard_subscribers.items():
                        if subscription_id in subs:
                            event_pattern = pattern
                            break
                            
                if event_pattern:
                    subscriptions.append({
                        'id': subscription_id,
                        'event_pattern': event_pattern,
                        'one_time': one_time
                    })
                    
            return {
                'subscriber_id': subscriber_id,
                'subscriptions': subscriptions
            }