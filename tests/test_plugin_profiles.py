from src.core.plugin_installer import PLUGIN_PROFILES, PluginInstaller

def test_all_known_plugins_have_profiles():
    for name in PluginInstaller.__dict__.get("KNOWN_PLUGINS", {}):
        assert name in PLUGIN_PROFILES

def test_shared_ai_plugins_are_manual():
    assert PLUGIN_PROFILES["fal-texture-pbr-generator"]["entry_mode"] == "manual"
    assert PLUGIN_PROFILES["Procedural-PBR"]["entry_mode"] == "manual"
    assert PLUGIN_PROFILES["SubstanceDesignerTools"]["entry_mode"] == "manual"
