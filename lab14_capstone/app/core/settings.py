import json
import os

class SettingsHandler:
    SETTINGS_FILE = "settings.json"

    @staticmethod
    def load():
        if os.path.exists(SettingsHandler.SETTINGS_FILE):
            try:
                with open(SettingsHandler.SETTINGS_FILE, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    @staticmethod
    def save(settings):
        with open(SettingsHandler.SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)

    @staticmethod
    def get(key, default=None):
        return SettingsHandler.load().get(key, default)

    @staticmethod
    def set(key, value):
        settings = SettingsHandler.load()
        settings[key] = value
        SettingsHandler.save(settings)
