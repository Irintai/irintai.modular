class PersonalityBridge:
    """
    Bridge between the Personality Plugin and Irintai core system
    
    Provides fallback implementations and adaptation layer to ensure
    the plugin works across different versions of the core system.
    """
    
    def __init__(self, core_system):
        """
        Initialize the bridge
        
        Args:
            core_system: Reference to Irintai core system
        """
        self.core_system = core_system
        self._patched = False
        
    def ensure_compatibility(self):
        """
        Ensure the core system is compatible with the plugin
        
        Adds any missing hooks or functionality required by the plugin.
        """
        if self._patched:
            return
            
        # Patch chat engine if needed
        if hasattr(self.core_system, "chat_engine"):
            self._patch_chat_engine()
            
        # Patch memory system if needed
        if hasattr(self.core_system, "memory_system"):
            self._patch_memory_system()
            
        self._patched = True
        
    def _patch_chat_engine(self):
        """
        Patch the chat engine to ensure it supports message modification
        """
        chat_engine = self.core_system.chat_engine
        
        # Add message modifiers list if not present
        if not hasattr(chat_engine, "_message_modifiers"):
            chat_engine._message_modifiers = []
            
        # Add register_message_modifier method if not present
        if not hasattr(chat_engine, "register_message_modifier"):
            def register_message_modifier(modifier_function):
                if not hasattr(chat_engine, "_message_modifiers"):
                    chat_engine._message_modifiers = []
                chat_engine._message_modifiers.append(modifier_function)
                
            chat_engine.register_message_modifier = register_message_modifier
            
        # Add unregister_message_modifier method if not present
        if not hasattr(chat_engine, "unregister_message_modifier"):
            def unregister_message_modifier(modifier_function):
                if hasattr(chat_engine, "_message_modifiers"):
                    if modifier_function in chat_engine._message_modifiers:
                        chat_engine._message_modifiers.remove(modifier_function)
                        
            chat_engine.unregister_message_modifier = unregister_message_modifier
            
        # Patch send_message method to apply modifiers if not already patched
        if not hasattr(chat_engine, "_original_send_message"):
            # Save original method
            chat_engine._original_send_message = chat_engine.send_message
            
            # Create patched method
            def send_message_patched(content, on_response=None):
                # Process the message through modifiers
                if hasattr(chat_engine, "_message_modifiers"):
                    for modifier in chat_engine._message_modifiers:
                        try:
                            content = modifier(content, "user")
                        except Exception as e:
                            # Log error but continue
                            if hasattr(chat_engine, "log"):
                                chat_engine.log(f"Error in message modifier: {e}", "ERROR")
                
                # Call original method
                result = chat_engine._original_send_message(content, on_response)
                
                # Process response if it's a string
                if isinstance(result, str) and hasattr(chat_engine, "_message_modifiers"):
                    modified_result = result
                    for modifier in chat_engine._message_modifiers:
                        try:
                            modified_result = modifier(modified_result, "assistant")
                        except Exception as e:
                            # Log error but continue
                            if hasattr(chat_engine, "log"):
                                chat_engine.log(f"Error in message modifier: {e}", "ERROR")
                    return modified_result
                
                return result
                
            # Replace method
            chat_engine.send_message = send_message_patched
    
    def _patch_memory_system(self):
        """
        Patch the memory system to ensure it supports adding personality data
        """
        memory_system = self.core_system.memory_system
        
        # Add add_to_index method if not present
        if not hasattr(memory_system, "add_to_index"):
            def add_to_index(docs, metadata):
                if hasattr(memory_system, "log"):
                    memory_system.log("Memory system does not support adding to index", "WARNING")
                return False
                
            memory_system.add_to_index = add_to_index