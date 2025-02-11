import octoprint.plugin
from octoprint.events import Events
from octoprint.filemanager import FileDestinations

__plugin_name__ = "GCodeSender"
__plugin_version__ = "1.0.0"
__plugin_description__ = "A plugin to send G-code files for printing"
__plugin_pythoncompat__ = ">=3.7,<4"

class GCodeSenderPlugin(octoprint.plugin.EventHandlerPlugin):

    def on_after_startup(self):
        self._logger.info("GCodeSenderPlugin started, HELLO!")

    def send_gcode_file(self, filename):
        # Ensure the file is in OctoPrint's local storage
        file_path = self._file_manager.path_on_disk(FileDestinations.LOCAL, filename)
        self._logger.info(f"Sending G-code file: {file_path}")

        # Select and start the print job
        self._printer.select_file(file_path, False)  # False means don't start immediately
        self._printer.start_print()  # Start the print job

    def on_event(self, event, payload):
        if event == Events.CONNECTED:
            self._logger.info("Printer connected event detected")
            filename = "Cute_Mini_Octopus.gcode"  # File name in OctoPrint's local storage
            self.send_gcode_file(filename)

__plugin_implementation__ = GCodeSenderPlugin()