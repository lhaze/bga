import asyncio
import typing as t

from aiologger import Logger
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


class LogManager:

    CONSOLE_HANDLER = {"level": "INFO"}
    FILE_HANLDERS = {
        "process": {"level": "INFO", "signals": "process"},
        "error": {"level": "WARNING", "signals": "process"},
        "meta": {"level": "INFO", "signals": "meta"},
    }
    SIGNAL_TO_LEVEL: t.Dict[str, str] = {
        "process:started": "INFO",
        "process:spider_registered": "DEBUG",
        "process:spider_started": "WARNING",
        "process:spider_ticked": "DEBUG",
        "process:url_registered": "DEBUG",
        "process:url_processed": "DEBUG",
        "process:url_fetched": "DEBUG",
        "process:url_failed": "WARNING",
        "process:url_response_valid": "INFO",
        "process:url_response_invalid": "WARNING",
        "process:items_extracted": "INFO",
        "process:spider_ended": "INFO",
        "process:error": "ERROR",
        "process:finished": "ERROR",
    }
    LEVEL_TO_COLOR: t.Dict[str, str] = {
        "DEBUG": "white",
        "INFO": "bright_white",
        "ERROR": "bright_red",
        "WARNING": "bright_yellow",
    }
    LOG_FILE_PATTERN = "shop_scraping/{process_datetime}.{name}.log"

    def __init__(self, process_state: ProcessState) -> None:
        self._process_state = process_state
        self._tasks: t.Set[asyncio.Task] = set()

    async def __aenter__(self):
        self._setup_print_logging()
        self._setup_json_files_logging()

    async def __aexit__(self, *args):
        await self._json_logger.shutdown()
        if self._tasks:
            await asyncio.gather(*self._tasks)

    def _setup_print_logging(self):

        for signal_name, level in self.SIGNAL_TO_LEVEL.items():
            if NAME_TO_LEVEL[level] >= NAME_TO_LEVEL[self.CONSOLE_HANDLER["level"]]:
                signal = process_signals[signal_name.split(":")[1]]
                signal.connect(self._rprint_signal_factory(signal_name), weak=False)

    def _rprint_signal_factory(self, name: str) -> t.Callable[..., None]:
        def rprint_handler(sender, **kwargs):
            sender = serialize_value(sender)
            msg = serialize_kwargs(kwargs)
            level = self.SIGNAL_TO_LEVEL.get(name, "-")
            level_color = self.LEVEL_TO_COLOR[level]
            rprint(f"[{level_color}]{level}[/{level_color}] {name} {sender} {msg}")

        return rprint_handler

    def _setup_json_files_logging(self):
        logger = JsonLogger("shop_scraping", flatten=True)
        formatter = ExtendedJsonFormatter(exclude_fields=("line_number", "function", "file_path"))
        process_datetime = self._process_state.start_as_filename
        process_logfile = AsyncFileHandler(
            filename=get_data_filepath(self.LOG_FILE_PATTERN.format(process_datetime=process_datetime, name="process"))
        )
        process_logfile.formatter = formatter
        logger.add_handler(process_logfile)
        error_logfile = AsyncFileHandler(
            filename=get_data_filepath(self.LOG_FILE_PATTERN.format(process_datetime=process_datetime, name="error"))
        )
        error_logfile.level = "WARNING"
        error_logfile.formatter = formatter
        logger.add_handler(error_logfile)
        signal: NamedAsyncSignal
        for signal in process_signals.values():
            self._aiologging_factory(signal, logger)
        self._json_logger = logger

    def _aiologging_factory(self, signal: NamedAsyncSignal, logger: Logger):
        def logging_function(sender, **kwargs):
            level = self.SIGNAL_TO_LEVEL[signal.name]
            assert level in NAME_TO_LEVEL
            method = getattr(logger, level.lower())
            msg = serialize_kwargs(kwargs)
            msg["sender"] = sender
            msg["signal"] = signal.name
            logging_task = method(msg)
            self._tasks.add(logging_task)
            return logging_task

        signal.connect(logging_function, weak=False)
