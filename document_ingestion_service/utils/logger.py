import logging
import logging.config
import os
import yaml
from functools import lru_cache

# Path to the main config file, relative to this utils directory
# Assumes utils/ is directly under document_ingestion_service/
# and config/ is also directly under document_ingestion_service/
CONFIG_YAML_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.yaml")
# Project root directory, assuming utils/logger.py is in document_ingestion_service/utils/
PROJECT_ROOT_DIR = os.path.dirname(os.path.dirname(__file__))


# Default logging configuration if config.yaml or its logging section is missing/invalid
DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
}

@lru_cache() # Ensures setup_logging is effectively called only once
def setup_logging():
    """
    Sets up logging configuration for the application.
    Tries to load configuration from config.yaml's 'logging' section.
    Falls back to DEFAULT_LOGGING_CONFIG if issues arise.
    """
    log_config_to_apply = DEFAULT_LOGGING_CONFIG
    config_source_message = "Using default logging configuration."

    try:
        if os.path.exists(CONFIG_YAML_PATH):
            with open(CONFIG_YAML_PATH, 'rt') as f:
                config_data = yaml.safe_load(f)
            
            loaded_log_config = config_data.get('logging')

            if loaded_log_config:
                # Ensure log directory exists if a file handler is configured
                file_handler_config = loaded_log_config.get('handlers', {}).get('file')
                if file_handler_config and 'filename' in file_handler_config:
                    log_file_path_relative = file_handler_config['filename']
                    
                    # Make log_file_path absolute, assuming it's relative to project root
                    log_file_path_absolute = os.path.join(PROJECT_ROOT_DIR, log_file_path_relative)
                    
                    # Update the config with the absolute path for the logger
                    loaded_log_config['handlers']['file']['filename'] = log_file_path_absolute
                    
                    log_dir = os.path.dirname(log_file_path_absolute)
                    if log_dir and not os.path.exists(log_dir):
                        os.makedirs(log_dir, exist_ok=True)
                
                log_config_to_apply = loaded_log_config
                config_source_message = "Logging configured from 'logging' section in config.yaml."
            else:
                config_source_message = "Logging section not found in config.yaml. Using default logging configuration."
        else:
            config_source_message = f"{CONFIG_YAML_PATH} not found. Using default logging configuration."

    except Exception as e:
        # Use basicConfig for immediate logging of this critical error
        logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logging.error(f"Critical error loading logging configuration: {e}. Falling back to default.", exc_info=True)
        log_config_to_apply = DEFAULT_LOGGING_CONFIG 
        config_source_message = f"Error loading logging config: {e}. Using default."

    try:
        logging.config.dictConfig(log_config_to_apply)
    except Exception as e:
        # If dictConfig fails even with defaults, use the most basic setup
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logging.error(f"Failed to apply dictConfig: {e}. Falling back to basicConfig.", exc_info=True)
        config_source_message = f"dictConfig failed: {e}. Using basicConfig."

    # Log how configuration was applied (this will use the newly configured logger)
    init_logger = logging.getLogger("app_setup_logger") 
    init_logger.info(config_source_message)


def get_logger(logger_name: str) -> logging.Logger:
    """
    Returns a configured logger instance.
    Ensures that logging setup has been performed.
    """
    setup_logging() # setup_logging() is idempotent due to @lru_cache
    return logging.getLogger(logger_name)

# Example of how to use it in other modules:
# from document_ingestion_service.utils.logger import get_logger
# logger = get_logger(__name__)
#
# logger.debug("This is a debug message.")
# logger.info("This is an info message.")
# logger.warning("This is a warning message.")
# logger.error("This is an error message.")
# logger.critical("This is a critical message.")
