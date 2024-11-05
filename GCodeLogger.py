import octoprint.plugin
import os

__plugin_name__ = "GCodeLogger"
__plugin_version__ = "1.0.0"
__plugin_description__ = "Logs G-code commands being sent to the printer"
__plugin_pythoncompat__ = ">=3.7,<4"

class GCodeLoggerPlugin(octoprint.plugin.StartupPlugin,
                         octoprint.plugin.EventHandlerPlugin):
    def __init__(self):
        self._log_file = None  # Initialize log file variable

    def on_after_startup(self):
        self._logger.info("GCodeLoggerPlugin started")
        save_dir = "/media/sdcard/snapshots"  # Save location directory on SD card
        log_file_name = "gcode_log.txt"  # Log file name
        save_path = os.path.join(save_dir, log_file_name)  # Full path to save the log file

        # Ensure the directory exists
        if not os.path.exists(save_dir):
            self._logger.info(f"Directory {save_dir} does not exist. Creating it.")
            try:
                os.makedirs(save_dir)
                self._logger.info(f"Directory {save_dir} created successfully.")
            except Exception as e:
                self._logger.error(f"Failed to create directory {save_dir}: {e}")
                return

        # Open the log file
        try:
            self._log_file = open(save_path, "a")
            self._logger.info(f"Log file opened at {save_path}.")
        except Exception as e:
            self._logger.error(f"Failed to open log file {save_path}: {e}")

    def on_event(self, event, payload):
        if event == octoprint.events.Events.PRINT_STARTED:
            self._logger.info("Print started, logging G-code commands.")

    def log_gcode_command(self, phase, cmd, cmd_type, gcode, subcode=None, tags=None):
        """Log G-code commands during their processing phases."""
        log_entry = f"Phase: {phase}, G-code Command: {cmd.strip()}\n"
        try:
            self._logger.info(log_entry.strip())
            if self._log_file:
                self._log_file.write(log_entry)
        except Exception as e:
            self._logger.error(f"Failed to log G-code command: {e}")

    def on_shutdown(self):
        if self._log_file:
            self._log_file.close()
            self._logger.info("Log file closed.")

    # Define the hooks
    __plugin_hooks__ = {
        "octoprint.comm.protocol.gcode.queuing": log_gcode_command,
        "octoprint.comm.protocol.gcode.queued": log_gcode_command,
        "octoprint.comm.protocol.gcode.sending": log_gcode_command,
        "octoprint.comm.protocol.gcode.sent": log_gcode_command,
    }

__plugin_implementation__ = GCodeLoggerPlugin()
