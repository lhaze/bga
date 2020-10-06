from logging import Logger
import typing as t

from aiologger.formatters.json import ExtendedJsonFormatter
from aiologger.levels import NAME_TO_LEVEL
from aiologger.loggers.json import JsonLogger
from aiologger.handlers.files import AsyncFileHandler
from asyncblink import NamedAsyncSignal
from rich import print as rprint

from common.files import get_data_filepath

from .config import ProcessState
from .serialization import serialize_kwargs, serialize_value
from .signals import process_signals

SIGNAL_TO_LEVEL: t.Dict[str, str] = {
    "started": "INFO",
    "spider_registered": "DEBUG",
    "spider_started": "INFO",
    "spider_ticked": "DEBUG",
    "url_registered": "DEBUG",
    "url_processed": "DEBUG",
    "url_fetched": "DEBUG",
    "url_failed": "WARNING",
    "url_response_valid": "INFO",
    "url_response_invalid": "WARNING",
    "items_extracted": "INFO",
    "spider_ended": "INFO",
    "error": "ERROR",
    "finished": "INFO",
}
LEVEL_TO_COLOR: t.Dict[str, str] = {
    "DEBUG": "white",
    "INFO": "bright_white",
    "ERROR": "bright_red",
    "WARNING": "bright_yellow",
}


def _rprint_signal_factory(name: str) -> t.Callable[..., None]:
    def rprint_handler(sender, **kwargs):
        sender = serialize_value(sender)
        msg = serialize_kwargs(kwargs)
        level = SIGNAL_TO_LEVEL.get(name, "-")
        level_color = LEVEL_TO_COLOR[level]
        rprint(f"[{level_color}]{level}[/{level_color}] {name} {sender} {msg}")

    return rprint_handler


def setup_print_logging():

    for signal in (
        "spider_started",
        "url_failed",
        "url_response_valid",
        "url_response_invalid",
        "items_extracted",
        "spider_ended",
        "error",
        "finished",
    ):
        process_signals[signal].connect(_rprint_signal_factory(signal), weak=False)


def setup_json_files_logging(process_state: ProcessState):
    logger = JsonLogger("shop_scraping", flatten=True)
    formatter = ExtendedJsonFormatter(exclude_fields=("line_number", "function", "file_path"))
    process_datetime = process_state.start_as_filename
    process_logfile = AsyncFileHandler(filename=get_data_filepath(f"{process_datetime}.process.log"))
    process_logfile.formatter = formatter
    logger.add_handler(process_logfile)
    error_logfile = AsyncFileHandler(filename=get_data_filepath(f"{process_datetime}.error.log"))
    error_logfile.level = "WARNING"
    error_logfile.formatter = formatter
    logger.add_handler(error_logfile)
    signal: NamedAsyncSignal
    for signal in ("error", "url_failed"):
        _aiologging_factory(process_signals[signal], logger, "ERROR")
    for signal in (
        "started",
        "spider_registered",
        "spider_started",
        "spider_ticked",
        "url_registered",
        "url_processed",
        "url_fetched",
        "url_response_valid",
        "url_response_invalid",
        "items_extracted",
        "spider_ended",
        "finished",
    ):
        _aiologging_factory(process_signals[signal], logger, "INFO")


def _aiologging_factory(signal: NamedAsyncSignal, logger: Logger, default_level: str):
    async def logging_function(sender, **kwargs):
        level = SIGNAL_TO_LEVEL.get(f"{signal.name}", default_level)
        assert level in NAME_TO_LEVEL
        method = getattr(logger, level.lower())
        msg = serialize_kwargs(kwargs)
        msg["sender"] = sender.name
        msg["signal"] = signal.name

        await method(msg)

    signal.connect(logging_function, weak=False)
