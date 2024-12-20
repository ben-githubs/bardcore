from pathlib import Path
import logging
import sys
import termcolor

from ruamel.yaml import YAML

yaml = YAML(typ="safe")


class MyFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord):
        txt = super().format(record)
        if record.levelno >= logging.ERROR:
            return termcolor.colored(txt, color="red")
        elif record.levelno == logging.WARNING:
            return termcolor.colored(txt, color="yellow")
        else:
            return txt


def configure_logging(config_path: Path) -> None:
    """Configures the logging settings."""
    with config_path.open("r") as f:
        config = yaml.load(f)

    logfile = Path(config.get("logfile", "bardcore.log"))
    if not logfile.is_absolute():
        logfile = config_path.parent / logfile
    logfile.touch()
    file_format = logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(message)s")
    file_handler = logging.FileHandler(logfile)
    file_handler.setFormatter(file_format)
    file_handler.setLevel(logging.DEBUG)

    term_format = MyFormatter(fmt="%(levelname)s: %(message)s")
    term_handler = logging.StreamHandler(sys.stdout)
    term_handler.setFormatter(term_format)
    term_handler.setLevel(logging.WARNING)

    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(term_handler)
    # Default level is Warning, irrespective the handler levels
    root_logger.setLevel(logging.DEBUG)