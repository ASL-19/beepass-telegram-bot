import logging


def is_true(s) -> bool:
    """
        Return True if a the variable represents True

        Args,
        s: string or boolean

        Returns:
        Boolean

    """

    if isinstance(s, bool):
        return s
    elif isinstance(s, (str, int)):
        return str(s).lower() in ['true', '1', 't', 'y', 'yes']
    return False


class Empty(object):
    """An empty class used to copy :class:`~logging.LogRecord` objects without reinitializing them."""


class CustomFormatter(logging.Formatter):

    def __init__(self, style='NEUTRAL', *args, **kwargs):
        super(CustomFormatter, self).__init__(*args, **kwargs)

        self.style = style
        self.fmt = "[%(levelname)s] - %(asctime)s - %(name)s - %(message)s - (%(filename)s:%(lineno)d)"

        grey = "\x1b[38;20m"
        yellow = "\x1b[33;20m"
        red = "\x1b[31;20m"
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"

        self.colored_format = {
            logging.DEBUG: f"{grey}{self.fmt}{reset}",
            logging.INFO: f"{grey}{self.fmt}{reset}",
            logging.WARNING: f"{yellow}{self.fmt}{reset}",
            logging.ERROR: f"{red}{self.fmt}{reset}",
            logging.CRITICAL: f"{bold_red}{self.fmt}{reset}"
        }

    def format(self, record):
        # Due to the way that Python's logging module is structured and
        # documented the only (IMHO) clean way to customize its behavior is
        # to change incoming LogRecord objects before they get to the base
        # formatter. However we don't want to break other formatters and
        # handlers, so we copy the log record.
        copy = Empty()
        copy.__class__ = record.__class__
        copy.__dict__.update(record.__dict__)
        if self.style == 'NEUTRAL':
            formatter = logging.Formatter(self.fmt)
        elif self.style == 'COLORED':
            log_fmt = self.colored_format.get(copy.levelno)
            formatter = logging.Formatter(log_fmt)
        record = formatter.format(copy)

        return record


def Log(logger_name,
        style='NEUTRAL',
        is_debug=True,
        fname=None):
    logger = logging.getLogger(logger_name)
    # set the logger's level to the "lowest"
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    formatter = CustomFormatter(style)
    # Clear the custom logger's handlers
    logger.handlers.clear()
    # Clear the custom logger's handlers
    logging.getLogger().handlers.clear()

    if fname is not None:
        # create file handler which logs even debug messages
        fh = logging.FileHandler(fname)
        fh.setLevel(logging.DEBUG)
        # Set formatter
        fh.setFormatter(formatter)
        # add the handlers to logger
        logger.addHandler(fh)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    # Set a different level for the handler
    ch.setLevel(logging.DEBUG if is_true(is_debug) else logging.INFO)
    # Set formatter
    ch.setFormatter(formatter)
    # add the handlers to logger
    logger.addHandler(ch)

    return logger


def get_logger(logger_name, module_name):
    return logging.getLogger(logger_name).getChild(module_name)
