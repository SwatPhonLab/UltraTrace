import logging
import os
import platform

from typing import Optional

logger = logging.getLogger(__name__)

try:
    from ttkthemes import ThemedTk  # type: ignore
except ImportError:
    logger.warning("Unable to load themes")
    from tkinter import Tk as ThemedTk  # noqa: F401


def get_theme(name: Optional[str]) -> Optional[str]:
    if name is not None:
        return name

    if platform.system() == "Linux":
        try:

            import xrp  # type: ignore

            Xresources_path = os.path.join(os.environ["HOME"], ".Xresources")
            if os.path.exists(Xresources_path):
                Xresources = xrp.parse_file(Xresources_path)
                if "*TtkTheme" in Xresources.resources:
                    return Xresources.resources["*TtkTheme"]
                if "*TkTheme" in Xresources.resources:
                    return Xresources.resources["*TkTheme"]
                return "clam"

        except Exception as e:
            logger.warning("Error loading themes: " + str(e))

    return None
