"""Configuration management for the event flow framework.

This module provides a dynamic settings loader that imports configuration
from a Python module specified by the EF_SETTINGS_MODULE environment variable.
"""

import importlib
import os

from typing import Tuple, Optional

from event_flow.core.exception import SettingNotFound, SettingError


class _Settings:
    """Internal settings manager that loads configuration from a Python module.

    Settings are loaded from a module specified by the EF_SETTINGS_MODULE
    environment variable. All uppercase attributes from that module are
    imported as settings.

    The default module name is 'settings' if no environment variable is set.

    Example:
        # In your settings.py file:
        DATABASE_URL = "postgresql://localhost/mydb"
        API_KEY = "secret123"

        # In your code:
        from event_flow.settings import settings
        print(settings.DATABASE_URL)  # Access loaded settings
    """
    def __init__(self):
        self.reload_settings()

    def check_setting_field(self, namespace: str, fields: Tuple[str]) -> bool:
        """Verify that a setting exists and has required attributes.

        Args:
            namespace: The setting name to check
            fields: Tuple of attribute names that must exist on the setting value

        Returns:
            True if all checks pass

        Raises:
            SettingNotFound: If the setting doesn't exist
            SettingError: If the setting is missing a required attribute
        """
        if not hasattr(self, namespace):
            raise SettingNotFound(f'The configuration item "{namespace}" is not set.')
        value = getattr(self, namespace)
        for field in fields:
            if not hasattr(value, field):
                raise SettingError(
                    f'The value of the configuration item "{namespace}" does not include the "{field}" attribute.')
        return True

    def get_settings(self, namespace: str, check_fields: Optional[Tuple[str]] = None, default=None):
        """Get a setting value with optional field validation.

        Args:
            namespace: The setting name to retrieve
            check_fields: Optional tuple of required attribute names to validate
            default: Default value if setting doesn't exist

        Returns:
            The setting value or default

        Raises:
            SettingNotFound: If check_fields is specified and setting doesn't exist
            SettingError: If check_fields is specified and a required field is missing
        """
        if check_fields and self.check_setting_field(namespace, check_fields):
            return getattr(self, namespace, default)
        else:
            return getattr(self, namespace, default)

    def reload_settings(self):
        """Load or reload settings from the configured module.

        Imports the module specified by EF_SETTINGS_MODULE environment variable
        (defaults to 'settings') and copies all uppercase attributes as settings.

        This allows runtime reloading of configuration values.

        Raises:
            ModuleNotFoundError: If the settings module cannot be imported
        """
        settings_module = os.environ.get('EF_SETTINGS_MODULE')  # noqa
        mod = importlib.import_module(settings_module or 'settings')
        for setting in dir(mod):
            if setting.isupper():
                value = getattr(mod, setting)
                setattr(self, setting, value)


settings = _Settings()
"""Global settings instance.

Import and use this instance to access your application settings:

    from event_flow.settings import settings
    database_url = settings.DATABASE_URL
"""
