import octoprint.plugin
from octoprint.events import Events

__plugin_name__ = "GCodeSender"
__plugin_version__ = "1.0.0"
__plugin_description__ = "A plugin to send G-code files for printing"
__plugin_pythoncompat__ = ">=3.7,<4" 

class GCodeSenderPlugin(octoprint.plugin.StartupPlugin):

    def on_after_startup(self):
        self._logger.info("GCodeSenderPlugin started")

    def send_gcode_file(self, filepath):
        # Send the G-code file path to the printer
        self._logger.info(f"Sending G-code file: {filepath}")
        self._printer.select_file(filepath, False)  # False means don't start immediately
        self._printer.start_print()  # Start the print job

    def on_event(self, event, payload):
        if event == Events.CONNECTED:
            gcode_path = "/path/to/your/gcodefile.gcode"  # Replace with your actual G-code file path
            self.send_gcode_file(gcode_path)


__plugin_implementation__ = GCodeSenderPlugin()
