"""EKIP Root Configuration Bridge.

Changes made:
- Re-exported Config from config/settings.py to preserve backward compatibility across all modules.
"""

from config.settings import Config

__all__ = ["Config"]
