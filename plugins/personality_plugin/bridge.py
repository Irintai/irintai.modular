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

    def get_system_prompt_hook(self):
        """
        Returns a function that can modify the system prompt
        
        Returns:
            Function to modify system prompts
        """
        def modify_system_prompt(original_prompt, personality_plugin):
            """
            Modify the system prompt based on active personality profile
            
            Args:
                original_prompt: The original system prompt
                personality_plugin: Reference to the personality plugin instance
                
            Returns:
                Modified system prompt
            """
            try:
                active_profile = personality_plugin.get_active_profile()
                
                if not active_profile:
                    return original_prompt
                    
                # Apply style modifiers to the prompt
                modified_prompt = original_prompt
                
                # Add style instructions based on profile
                style_modifiers = active_profile.get("style_modifiers", {})
                if style_modifiers:
                    # Convert modifiers to natural language descriptions
                    style_descriptions = []
                    
                    if style_modifiers.get("formality", 0.5) > 0.7:
                        style_descriptions.append("formal and professional")
                    elif style_modifiers.get("formality", 0.5) < 0.3:
                        style_descriptions.append("casual and conversational")
                        
                    if style_modifiers.get("complexity", 0.5) > 0.7:
                        style_descriptions.append("using sophisticated language")
                    elif style_modifiers.get("complexity", 0.5) < 0.3:
                        style_descriptions.append("using simple, clear language")
                        
                    if style_modifiers.get("empathy", 0.5) > 0.7:
                        style_descriptions.append("empathetic and understanding")
                    
                    if style_modifiers.get("directness", 0.5) > 0.7:
                        style_descriptions.append("direct and straightforward")
                    elif style_modifiers.get("directness", 0.5) < 0.3:
                        style_descriptions.append("tactful and diplomatic")
                        
                    if style_modifiers.get("humor", 0.5) > 0.7:
                        style_descriptions.append("with occasional humor")
                        
                    if style_modifiers.get("creativity", 0.5) > 0.7:
                        style_descriptions.append("creative and imaginative")
                    elif style_modifiers.get("creativity", 0.5) < 0.3:
                        style_descriptions.append("factual and precise")
                        
                    if style_modifiers.get("conciseness", 0.5) > 0.7:
                        style_descriptions.append("concise and to the point")
                    elif style_modifiers.get("conciseness", 0.5) < 0.3:
                        style_descriptions.append("with detailed explanations")
                    
                    # Add style instructions to prompt
                    if style_descriptions:
                        style_text = ", ".join(style_descriptions)
                        if not modified_prompt.endswith('.'):
                            modified_prompt += '.'
                        modified_prompt += f" Communicate in a style that is {style_text}."
                
                # Add prefix if available
                prefix = active_profile.get("prefix", "")
                if prefix and not modified_prompt.startswith(prefix):
                    modified_prompt = prefix + modified_prompt
                
                # Add suffix if available
                suffix = active_profile.get("suffix", "")
                if suffix and not modified_prompt.endswith(suffix):
                    modified_prompt = modified_prompt + suffix
                
                return modified_prompt
                
            except Exception as e:
                # Log error but return original prompt
                if hasattr(self.core_system, "log"):
                    self.core_system.log(f"Error modifying system prompt: {e}", "ERROR")
                return original_prompt
                
        return modify_system_prompt

    def register_with_memory(self, personality_plugin):
        """
        Register personality data with the memory system
        
        Args:
            personality_plugin: Reference to personality plugin instance
            
        Returns:
            True if registered successfully, False otherwise
        """
        try:
            if not hasattr(self.core_system, "memory_system"):
                return False
                
            memory_system = self.core_system.memory_system
            
            # Get the active profile
            active_profile = personality_plugin.get_active_profile()
            if not active_profile:
                return False
            
            # Format profile data as text
            profile_text = f"ACTIVE PERSONALITY PROFILE: {active_profile.get('name', 'Unknown')}\n\n"
            profile_text += f"Description: {active_profile.get('description', '')}\n"
            
            # Add style information
            profile_text += "\nStyle characteristics:\n"
            style_modifiers = active_profile.get("style_modifiers", {})
            for name, value in style_modifiers.items():
                profile_text += f"- {name}: {value:.1f}\n"
            
            # Create metadata
            metadata = {
                "source": "personality_plugin",
                "category": "assistant_configuration",
                "subject": "personality_profile",
                "profile_name": active_profile.get("name", "Unknown"),
                "text": profile_text,
                "timestamp": self._get_timestamp(),
                "importance": 0.8  # High importance to ensure it's retrieved
            }
            
            # Add to memory system
            return memory_system.add_to_index([profile_text], [metadata])
            
        except Exception as e:
            if hasattr(self.core_system, "log"):
                self.core_system.log(f"Error registering with memory: {e}", "ERROR")
            return False

    def _get_timestamp(self):
        """
        Get the current timestamp in the format used by the system
        
        Returns:
            Timestamp string
        """
        import time
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def apply_personality_to_config(self, personality_plugin):
        """
        Apply personality settings to the core configuration
        
        Args:
            personality_plugin: Reference to personality plugin instance
            
        Returns:
            True if applied successfully, False otherwise
        """
        try:
            if not hasattr(self.core_system, "config_manager"):
                return False
                
            config_manager = self.core_system.config_manager
            
            # Get active profile
            active_profile = personality_plugin.get_active_profile()
            if not active_profile:
                return False
            
            # Get formatting preferences
            formatting = active_profile.get("formatting", {})
            
            # Apply configuration changes
            config_updates = {
                "personality": {
                    "active_profile": active_profile.get("name", ""),
                    "use_markdown": formatting.get("use_markdown", True),
                    "emphasize_key_points": formatting.get("emphasize_key_points", False),
                    "paragraph_structure": formatting.get("paragraph_structure", "standard")
                }
            }
            
            # Update configuration using category setter if available
            if hasattr(config_manager, "set_category"):
                config_manager.set_category("personality", config_updates["personality"])
            else:
                # Fall back to individual settings
                for key, value in config_updates["personality"].items():
                    full_key = f"personality.{key}"
                    config_manager.set(full_key, value)
            
            return True
            
        except Exception as e:
            if hasattr(self.core_system, "log"):
                self.core_system.log(f"Error applying personality to config: {e}", "ERROR")
            return False

    def register_ui_hooks(self, personality_plugin):
        """
        Register hooks for UI integration
        
        Args:
            personality_plugin: Reference to personality plugin instance
            
        Returns:
            True if hooks registered successfully, False otherwise
        """
        try:
            # Check if event system exists
            if not hasattr(self.core_system, "event_system"):
                if hasattr(self.core_system, "plugin_manager"):
                    # Use plugin manager's event system if available
                    plugin_manager = self.core_system.plugin_manager
                    if hasattr(plugin_manager, "trigger_event"):
                        # Register to necessary events
                        plugin_manager.register_event_handler(
                            "personality_plugin", 
                            "chat_message_sent", 
                            lambda **kwargs: self._on_message_sent(kwargs.get("message", ""), personality_plugin)
                        )
                        
                        plugin_manager.register_event_handler(
                            "personality_plugin", 
                            "ui_refresh", 
                            lambda **kwargs: self._on_ui_refresh(personality_plugin)
                        )
                        
                        return True
                
                # No event system available
                return False
                        
            # Use core event system directly if available
            event_system = self.core_system.event_system
            
            # Register handlers
            event_system.register_handler(
                "chat_message_sent", 
                lambda message: self._on_message_sent(message, personality_plugin)
            )
            
            event_system.register_handler(
                "ui_refresh",
                lambda: self._on_ui_refresh(personality_plugin)
            )
            
            return True
            
        except Exception as e:
            if hasattr(self.core_system, "log"):
                self.core_system.log(f"Error registering UI hooks: {e}", "ERROR")
            return False

    def _on_message_sent(self, message, personality_plugin):
        """
        Handle chat message sent event
        
        Args:
            message: Message text
            personality_plugin: Reference to personality plugin instance
        """
        try:
            # Skip if auto-remember is disabled
            if not personality_plugin.get_config().get("auto_remember", True):
                return
                
            # Register the current personality with memory
            self.register_with_memory(personality_plugin)
        except Exception as e:
            if hasattr(self.core_system, "log"):
                self.core_system.log(f"Error in message handler: {e}", "ERROR")

    def _on_ui_refresh(self, personality_plugin):
        """
        Handle UI refresh event
        
        Args:
            personality_plugin: Reference to personality plugin instance
        """
        try:
            # Update any UI-related state
            if hasattr(personality_plugin, "refresh_ui") and callable(personality_plugin.refresh_ui):
                personality_plugin.refresh_ui()
        except Exception as e:
            if hasattr(self.core_system, "log"):
                self.core_system.log(f"Error in UI refresh handler: {e}", "ERROR")

    def create_message_modifier(self, personality_plugin):
        """
        Create a message modifier function for the chat engine
        
        Args:
            personality_plugin: Reference to personality plugin instance
            
        Returns:
            Message modifier function
        """
        def message_modifier(content, role):
            """
            Modify messages based on active personality profile
            
            Args:
                content: Message content
                role: Message role (user/assistant)
                
            Returns:
                Modified message content
            """
            try:
                # Only modify assistant messages
                if role != "assistant":
                    return content
                    
                # Get active profile
                active_profile = personality_plugin.get_active_profile()
                if not active_profile:
                    return content
                    
                # Apply style transformations from helpers
                from plugins.personality_plugin.core.helpers import apply_style_transforms
                return apply_style_transforms(content, active_profile)
                
            except Exception as e:
                # Log error but return original content
                if hasattr(self.core_system, "log"):
                    self.core_system.log(f"Error in message modifier: {e}", "ERROR")
                return content
                    
        return message_modifier