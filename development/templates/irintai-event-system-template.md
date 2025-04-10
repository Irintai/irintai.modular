# Irintai Event System Development Template

## Event System Architecture

### Design Principles
- Decoupled communication
- Asynchronous event handling
- Flexible subscription model
- Minimal performance overhead
- Thread-safe operations

### Implementation Template

```python
# core/event_system.py
"""
Irintai Event System - Flexible Event Management and Communication

Provides a robust, decoupled event communication mechanism 
for system-wide interactions.
"""

import threading
import queue
import weakref
import logging
from typing import (
    Any, 
    Callable, 
    Dict, 
    List, 
    Optional, 
    Type, 
    TypeVar
)

T = TypeVar('T')

class EventSubscription:
    """
    Represents a single event subscription
    
    Manages subscription lifecycle and provides 
    weak reference handling
    """
    
    def __init__(
        self, 
        event_type: Type[T], 
        callback: Callable[[T], None],
        priority: int = 0
    ):
        """
        Initialize event subscription
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event occurs
            priority: Subscription priority (lower = earlier execution)
        """
        self.event_type = event_type
        self.callback = weakref.WeakMethod(callback)
        self.priority = priority
        self.id = id(self)
    
    def __call__(self, event: T) -> None:
        """
        Execute the callback for this subscription
        
        Args:
            event: Event instance to process
        """
        callback = self.callback()
        if callback:
            callback(event)
        else:
            # Callback has been garbage collected
            return False
        return True

class Event:
    """
    Base event class for system-wide events
    
    Provides a standardized event representation
    """
    
    def __init__(
        self, 
        source: Optional[Any] = None, 
        timestamp: Optional[float] = None
    ):
        """
        Initialize event
        
        Args:
            source: Event source object
            timestamp: Event creation timestamp
        """
        import time
        
        self.source = source
        self.timestamp = timestamp or time.time()
        self.propagation_stopped = False
    
    def stop_propagation(self) -> None:
        """
        Stop further event propagation
        """
        self.propagation_stopped = True

class EventSystem:
    """
    Central event management and dispatching system
    
    Provides publish-subscribe communication mechanism
    with advanced features
    """
    
    def __init__(
        self, 
        logger: Optional[Callable] = None
    ):
        """
        Initialize event system
        
        Args:
            logger: Optional logging function
        """
        # Thread-safe event subscriptions
        self._subscriptions: Dict[Type[Event], List[EventSubscription]] = {}
        
        # Event processing queue
        self._event_queue = queue.Queue()
        
        # Synchronization primitives
        self._lock = threading.Lock()
        
        # Logging setup
        self.log = logger or self._default_logger
        
        # Start event processing thread
        self._stop_event = threading.Event()
        self._event_thread = threading.Thread(
            target=self._process_events, 
            daemon=True
        )
        self._event_thread.start()
    
    def _default_logger(
        self, 
        message: str, 
        level: str = "INFO"
    ) -> None:
        """
        Fallback logging method
        
        Args:
            message: Log message
            level: Logging level
        """
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        
        log_method = {
            "INFO": logging.info,
            "WARNING": logging.warning,
            "ERROR": logging.error
        }.get(level.upper(), logging.info)
        
        log_method(message)
    
    def subscribe(
        self, 
        event_type: Type[T], 
        callback: Callable[[T], None],
        priority: int = 0
    ) -> EventSubscription:
        """
        Subscribe to a specific event type
        
        Args:
            event_type: Event class to subscribe to
            callback: Function to call when event occurs
            priority: Execution priority
        
        Returns:
            EventSubscription instance
        """
        with self._lock:
            subscription = EventSubscription(
                event_type, 
                callback, 
                priority
            )
            
            # Create list for event type if not exists
            if event_type not in self._subscriptions:
                self._subscriptions[event_type] = []
            
            # Add subscription and sort by priority
            self._subscriptions[event_type].append(subscription)
            self._subscriptions[event_type].sort(
                key=lambda sub: sub.priority
            )
            
            self.log(
                f"Subscribed to {event_type.__name__} "
                f"with priority {priority}", 
                "INFO"
            )
            
            return subscription
    
    def unsubscribe(
        self, 
        subscription: EventSubscription
    ) -> bool:
        """
        Remove a specific event subscription
        
        Args:
            subscription: Subscription to remove
        
        Returns:
            Boolean indicating successful removal
        """
        with self._lock:
            event_type = subscription.event_type
            
            if event_type in self._subscriptions:
                try:
                    self._subscriptions[event_type].remove(subscription)
                    self.log(
                        f"Unsubscribed from {event_type.__name__}", 
                        "INFO"
                    )
                    return True
                except ValueError:
                    self.log(
                        "Subscription not found", 
                        "WARNING"
                    )
            
            return False
    
    def publish(
        self, 
        event: Event
    ) -> None:
        """
        Publish an event to the system
        
        Args:
            event: Event instance to publish
        """
        try:
            self._event_queue.put(event)
        except Exception as e:
            self.log(f"Event publishing error: {e}", "ERROR")
    
    def _process_events(self) -> None:
        """
        Background thread for processing events
        """
        while not self._stop_event.is_set():
            try:
                # Block and wait for events with timeout
                event = self._event_queue.get(
                    timeout=1.0
                )
                
                # Process event
                self._dispatch_event(event)
                
                # Mark task as done
                self._event_queue.task_done()
            
            except queue.Empty:
                # No events, continue waiting
                continue
            except Exception as e:
                self.log(f"Event processing error: {e}", "ERROR")
    
    def _dispatch_event(
        self, 
        event: Event
    ) -> None:
        """
        Dispatch event to registered subscribers
        
        Args:
            event: Event to dispatch
        """
        with self._lock:
            # Find matching subscriptions
            matching_subs = self._subscriptions.get(
                type(event), 
                []
            )
            
            # Process subscriptions
            for subscription in matching_subs:
                # Stop propagation if requested
                if event.propagation_stopped:
                    break
                
                # Execute subscription
                if not subscription(event):
                    # Remove invalid subscription
                    self._subscriptions[type(event)].remove(subscription)
    
    def shutdown(self) -> None:
        """
        Gracefully shut down the event system
        """
        self.log("Shutting down event system", "INFO")
        
        # Stop event processing
        self._stop_event.set()
        
        # Wait for event thread to complete
        self._event_thread.join()
        
        # Clear subscriptions
        self._subscriptions.clear()

# Example Custom Event
class ModelLoadedEvent(Event):
    """
    Custom event for model loading
    """
    def __init__(
        self, 
        model_name: str, 
        source: Optional[Any] = None
    ):
        super().__init__(source)
        self.model_name = model_name

# Singleton Event System Instance
event_system = EventSystem()
```

## Development Guidelines

### Event Design Principles
- Create focused, single-purpose events
- Use inheritance for event specialization
- Minimize event payload complexity
- Provide clear event context

### Subscription Best Practices
- Use weak references to prevent memory leaks
- Implement priority-based event handling
- Support dynamic subscription/unsubscription
- Handle callback lifecycle

### Performance Considerations
- Asynchronous event processing
- Minimal blocking operations
- Efficient subscription management
- Thread-safe implementations

## Usage Example

```python
# Example event subscription and publishing
def on_model_loaded(event: ModelLoadedEvent):
    print(f"Model loaded: {event.model_name}")

# Subscribe to event
subscription = event_system.subscribe(
    ModelLoadedEvent, 
    on_model_loaded, 
    priority=0
)

# Publish an event
model_event = ModelLoadedEvent("gpt-3.5-turbo")
event_system.publish(model_event)
```

## Testing Considerations
- [ ] Event dispatching
- [ ] Subscription management
- [ ] Priority handling
- [ ] Thread safety
- [ ] Memory management
- [ ] Error handling

---

**Development Notes:**
- Customize for specific system requirements
- Maintain loose coupling
- Prioritize thread safety
- Implement comprehensive logging
