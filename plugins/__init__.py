# プラグインシステム

from .base import DownloadPlugin, PluginManager
from .http_plugin import HTTPDownloadPlugin

try:
    from .youtube_plugin import YouTubeDLPlugin

    YOUTUBE_PLUGIN_AVAILABLE = True
except ImportError:
    YOUTUBE_PLUGIN_AVAILABLE = False

__all__ = ["DownloadPlugin", "PluginManager", "HTTPDownloadPlugin"]

if YOUTUBE_PLUGIN_AVAILABLE:
    __all__.append("YouTubeDLPlugin")
