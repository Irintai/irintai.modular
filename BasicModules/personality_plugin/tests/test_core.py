def test_profiles():
    from plugins.personality_plugin import PersonalityPlugin
    plugin = PersonalityPlugin()
    plugin.activate()
    assert 'Default' in plugin.list_profiles()
