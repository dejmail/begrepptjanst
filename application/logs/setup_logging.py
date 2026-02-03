import logging
import logging.config
import os
import socket

if (socket.gethostname() == 'suijin.oderland.com') and ('eav' in os.getcwd()):
        FILENAME = '/home/vgrinfor/begreppstjanst-eav/logs.log'
elif socket.gethostname() == 'W450772':
    if os.path.isdir('/mnt/c'):
        FILENAME = '/mnt/c/Users/liath1/coding/begrepptjanst/logs.log'
    else:
        FILENAME = '/home/liath1/coding/begrepptjanst/logs.log'

# Allow runtime configuration of logging level via environment or Django settings
LOG_LEVEL = os.getenv("LOG_LEVEL", None)
try:
    # Prefer Django setting when available (useful in production)
    from django.conf import settings as django_settings
    if LOG_LEVEL is None:
        LOG_LEVEL = getattr(django_settings, "LOG_LEVEL", None)
except Exception:
    # Not running under Django setup yet; ignore
    pass
if LOG_LEVEL is None:
    LOG_LEVEL = "DEBUG"
LOG_LEVEL = str(LOG_LEVEL).upper()
# Validate level name
if not hasattr(logging, LOG_LEVEL):
    LOG_LEVEL = "DEBUG"

# Ensure log directory exists for the file handler (create if missing)
if "FILENAME" in locals():
    log_dir = os.path.dirname(FILENAME) or ""
    if log_dir:
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            # If directory cannot be created, fallback to current working dir
            FILENAME = os.path.join(os.getcwd(), os.path.basename(FILENAME))

logging_schema = {
    # Always 1. Schema versioning may be added in a future release of logging
    "version": 1,
    # "Name of formatter" : {Formatter Config Dict}
    "formatters": {
        # Formatter Name
        "standard": {
            # class is always "logging.Formatter"
            "class": "logging.Formatter",
            # Optional: logging output format
            "format": "%(asctime)s\t%(levelname)s\t%(filename)s:%(lineno)d\t%(message)s",
            # Optional: asctime format
            "datefmt": "%d %b %y %H:%M:%S"
        }
    },
    'filters': {
        'ignore_http_logs': {
            '()': 'django.utils.log.CallbackFilter',
            'callback': lambda record: record.name not in ('django.server', 'django.request'),
        },
    },
    # Handlers use the formatter names declared above
    "handlers": {
        # Name of handler
        "console": {
            # The class of logger. A mixture of logging.config.dictConfig() and
            # logger class-specific keyword arguments (kwargs) are passed in here.
            "class": "logging.StreamHandler",
            # This is the formatter name declared above
            "formatter": "standard",
            "level": LOG_LEVEL,
            "filters": ["ignore_http_logs"],  # ✅ Ignore HTTP logs
            # The default is stderr
            "stream": "ext://sys.stdout"
        },
        # Same as the StreamHandler example above, but with different
        # handler-specific kwargs.
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "level": LOG_LEVEL,
            "filename": FILENAME,
            "mode": "a",
            "encoding": "utf-8",
            "maxBytes": 500000,
            "backupCount": 4
        }
    },
    # Loggers use the handler names declared above
    "loggers" : {
        "__main__": {  # if __name__ == "__main__"
            # Use a list even if one handler is used
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False
        },
        'django.server': {  # ✅ Disable Django's default HTTP logging
            'handlers': ['console'],
            'level': 'CRITICAL',  # Logs only critical errors
            'propagate': False,
        },
        'django.request': {  # ✅ Disable detailed HTTP request logs
            'handlers': ['console'],
            'level': 'CRITICAL',
            'propagate': False,
        },
    },
    # Just a standalone kwarg for the root logger
    "root" : {
        "level": LOG_LEVEL,
        "handlers": ["console","file"]
    }
}

logging.config.dictConfig(logging_schema)
logging.debug('logging has been set up')
