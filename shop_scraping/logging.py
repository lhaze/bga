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
from .signals import SIGNALS


class LogManager:

    CONSOLE_HANDLER = {"spider": {"level": "DEBUG"}, "meta": {"level": "DEBUG"}, "output": {"level": "DEBUG"}}
    FILE_HANLDERS = {
        "error": {"level": "WARNING", "signals": ["meta", "spider"]},
        "meta": {"level": "DEBUG", "signals": ["meta"]},
        "output": {"level": "WARNING", "signals": ["output"]},
        "spider": {"level": "DEBUG", "signals": ["spider"]},
    }
    SIGNAL_TO_LEVEL: t.Dict[str, str] = {
        "meta:spider_registered": "DEBUG",
        "meta:started": "INFO",
        "meta:error": "ERROR",
        "meta:finished": "INFO",
        "output:items_extracted": "INFO",
        "output:url_failed": "WARNING",
        "output:url_response_valid": "INFO",
        "output:url_response_invalid": "WARNING",
        "spider:spider_started": "INFO",
        "spider:spider_ticked": "DEBUG",
        "spider:url_registered": "DEBUG",
        "spider:url_processing_started": "DEBUG",
        "spider:url_fetching_started": "DEBUG",
        "spider:url_fetched": "DEBUG",
        "spider:url_error": "INFO",
        "spider:spider_ended": "INFO",
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
        self._json_loggers: t.Dict[str, JsonLogger] = {}

    async def __aenter__(self):
        self._setup_print_logging()
        self._setup_json_files_logging()

    async def __aexit__(self, *args):
        if self._tasks:
            await asyncio.gather(*self._tasks)
        await asyncio.gather(*(logger.shutdown() for logger in self._json_loggers.values()))

    def _setup_print_logging(self):
        for signal_name, level in self.SIGNAL_TO_LEVEL.items():
            namespace, name = signal_name.split(":")
            if (threshold_level := self.CONSOLE_HANDLER.get(namespace, {}).get("level")) and NAME_TO_LEVEL[
                level
            ] >= NAME_TO_LEVEL[threshold_level]:
                signal = SIGNALS[namespace][name]
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
        formatter = ExtendedJsonFormatter(exclude_fields=("line_number", "function", "file_path"))
        process_datetime = self._process_state.start_as_filename
        for logger_name, config in self.FILE_HANLDERS.items():
            # create logger
            logger = JsonLogger(f"shop_scraping.{logger_name}", flatten=True)
            logfile = AsyncFileHandler(
                filename=get_data_filepath(
                    self.LOG_FILE_PATTERN.format(process_datetime=process_datetime, name=logger_name)
                )
            )
            logfile.formatter = formatter
            logfile.level = config.get("level", "ERROR")
            logger.add_handler(logfile)
            self._json_loggers[logger_name] = logger
            # connect it to signals
            for namespace_name in config["signals"]:
                for signal in SIGNALS[namespace_name].values():
                    self._aiologging_factory(signal, logger)

    def _aiologging_factory(self, signal: NamedAsyncSignal, logger: Logger):
        def logging_function(sender, **kwargs):
            level = self.SIGNAL_TO_LEVEL[signal.name]
            assert level in NAME_TO_LEVEL
            method = getattr(logger, level.lower())
            msg = {"asignal": signal.name, "sender": serialize_value(sender), **serialize_kwargs(kwargs)}
            logging_task = method(msg)
            self._tasks.add(logging_task)
            return logging_task

        signal.connect(logging_function, weak=False)
