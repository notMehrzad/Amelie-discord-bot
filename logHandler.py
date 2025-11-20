import logging
from colorama import Fore, Style, init
init(autoreset=True)  # ensures colors reset automatically

class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.INFO: Fore.BLUE,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT
    }

    def format(self, record: logging.LogRecord):
        color = self.COLORS.get(record.levelno, "")
        message = super().format(record)
        return color + message + Style.RESET_ALL


def loggerSetup(loggerName: str):
    """
    Creates and configures a logger with separate file and console handlers.

    Parameters
    ----------
    loggerName : str
        The name of the logger, typically __name__ from the caller.

    Returns
    -------
    logging.Logger
        A configured logger instance ready for use.
    """

    logger = logging.getLogger(loggerName)
    logger.setLevel(logging.INFO)

    #prevents duplicate handlers
    if logger.handlers:
        return logger
    
    #file handler
    fileHandler = logging.FileHandler(filename = "log.log", mode = "w", encoding = "utf-8")
    fileHandler.setLevel(logging.WARNING) #only warning, error and critical loggings are stored in file
    fileHandlerFormat = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt = "%I:%M:%S %p")
    fileHandler.setFormatter(fileHandlerFormat)

    #console handler
    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.INFO) #everything will be logged on the console
    consoleHandlerFormat = ColorFormatter("%(name)s - %(levelname)s - %(message)s")
    consoleHandler.setFormatter(consoleHandlerFormat)

    logger.addHandler(fileHandler) #adds file handler
    logger.addHandler(consoleHandler) #adds console handler

    return logger