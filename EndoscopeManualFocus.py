import subprocess
import octoprint.plugin
from octoprint.events import Events

__plugin_name__ = "EndoscopeManualFocus"
__plugin_version__ = "1.0.0"
__plugin_description__ = "A plugin to adjust focus of endoscope camera upon OctoPrint connection."
__plugin_pythoncompat__ = ">=3.7,<4"

class EndoscopeManualFocus(octoprint.plugin.StartupPlugin, octoprint.plugin.EventHandlerPlugin):

    def on_after_startup(self):
        # This method is called when OctoPrint starts up
        self._logger.info("EndoscopeManualFocus plugin started!")
        self._set_camera_focus()

    def on_event(self, event, payload):
        if event == Events.CONNECTED:
            self._logger.info("Printer connected event detected")
            self._set_camera_focus()

    def _set_camera_focus(self):
        # Disable autofocus
        try:
            subprocess.run(["v4l2-ctl", "-d", "/dev/video0", "-c", "focus_automatic_continuous=0"], check=True)
            self._logger.info("Autofocus disabled successfully.")
        except subprocess.CalledProcessError as e:
            self._logger.error(f"Failed to disable autofocus: {e}")

        # Set manual focus value
        try:
            subprocess.run(["v4l2-ctl", "-d", "/dev/video0", "-c", "focus_absolute=390"], check=True)
            self._logger.info("Manual focus set to 390 successfully.")
        except subprocess.CalledProcessError as e:
            self._logger.error(f"Failed to set manual focus: {e}")

__plugin_implementation__ = EndoscopeManualFocus()