class PersonalityPlugin:
    name = "personality_plugin"
    friendly_name = "Personality Plugin"
    version = "1.0"
    description = "Provides personality switching and emotional context tuning."
    tags = ["core", "personality", "extension"]

    def __init__(self):
        self.log = print
        self.profiles = {}
        self.active_profile = None

    def activate(self):
        self._load_profiles()
        self.set_active("Default")
        self.log("Personality Plugin Activated")

    def deactivate(self):
        self.log("Personality Plugin Deactivated")

    def get_interface(self):
        return {
            "get_active_personality": self.get_active,
            "set_personality": self.set_active,
            "list_personalities": self.list_profiles
        }

    def _load_profiles(self):
        self.profiles = {
            "Default": {
                "tone": "neutral",
                "prefix": "",
                "description": "Balanced and calm"
            },
            "Empath": {
                "tone": "compassionate",
                "prefix": "Please speak freely. I'm here to understand.",
                "description": "Warm and supportive"
            },
            "Sage": {
                "tone": "reflective",
                "prefix": "Let us explore this together, thoughtfully.",
                "description": "Philosophical and deep"
            },
            "Rebel": {
                "tone": "fiery",
                "prefix": "No bullshit. Let's get real.",
                "description": "Unfiltered and bold"
            }
        }

    def set_active(self, name):
        if name in self.profiles:
            self.active_profile = self.profiles[name]
            self.log(f"Switched to personality: {name}")
            return True
        return False

    def get_active(self):
        return self.active_profile

    def list_profiles(self):
        return list(self.profiles.keys())