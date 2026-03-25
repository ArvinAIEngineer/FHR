import sys
import io
import time
import logging
import os
from datetime import datetime, timezone, timedelta
from functools import wraps
import inspect

# UAE Timezone (Gulf Standard Time - GST is UTC+4)
UAE_TZ = timezone(timedelta(hours=4))

# Check if running in Docker
RUNNING_IN_DOCKER = os.environ.get("IN_DOCKER", "false").lower() == "true"
LOG_DIR = "logs" if not RUNNING_IN_DOCKER else "/var/log/app"
os.makedirs(LOG_DIR, exist_ok=True)

uae_now = datetime.now(UAE_TZ)
log_filename = os.path.join(LOG_DIR, f"app_log_{uae_now.strftime('%Y-%m-%d')}.log")

# Custom UAE formatter
class UAETimestampedFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super().__init__(datefmt="%Y-%m-%d %H:%M:%S", *args, **kwargs)

    def formatTime(self, record, datefmt=None):
        ct = datetime.fromtimestamp(record.created, tz=UAE_TZ)
        return ct.strftime(datefmt or self.default_time_format)

    def format(self, record):
        if not hasattr(record, 'asctime'):
            record.asctime = self.formatTime(record, self.datefmt)

        class_name = getattr(record, 'class_name', 'N/A')
        func_name = getattr(record, 'func_name', 'N/A')
        conversation_id = getattr(record, 'conversation_id', 'N/A')

        return (f"{record.asctime} | {record.levelname} | {class_name} | "
                f"{func_name} | ConversationID={conversation_id} | {record.getMessage()}")

# Configure handlers
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(UAETimestampedFormatter())
handlers = [stdout_handler]

if not RUNNING_IN_DOCKER or os.environ.get("LOG_TO_FILE", "true").lower() == "true":
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(UAETimestampedFormatter())
    handlers.append(file_handler)

logging.basicConfig(level=logging.INFO, handlers=handlers)

# Context adapter
class ContextLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        kwargs.setdefault('extra', {})
        kwargs['extra']['class_name'] = self.extra.get('class_name', 'N/A')
        kwargs['extra']['func_name'] = self.extra.get('func_name', 'N/A')
        kwargs['extra']['conversation_id'] = self.extra.get('conversation_id', 'N/A')
        return msg, kwargs
    
    def set_context(self, class_name=None, func_name=None):
        if class_name:
            self.extra['class_name'] = class_name
        if func_name:
            self.extra['func_name'] = func_name

# Factory for logger
# Cache handlers to avoid adding duplicates
conversation_handlers = {}

def get_logger(conversation_id=None):
    frame = inspect.currentframe().f_back
    class_name = frame.f_locals.get('self', None).__class__.__name__ if 'self' in frame.f_locals else 'Global'
    func_name = frame.f_code.co_name
    conv_id = conversation_id or 'N/A'
    
    context = {
        'class_name': class_name,
        'func_name': func_name,
        'conversation_id': conv_id
    }

    logger_name = f"{class_name}.{func_name}.{conv_id}"
    base_logger = logging.getLogger(logger_name)
    base_logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if not base_logger.handlers:
        # Stream handler (stdout)
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(UAETimestampedFormatter())
        base_logger.addHandler(stdout_handler)

        # Optional: create per-conversation log file
        if not RUNNING_IN_DOCKER or os.environ.get("LOG_TO_FILE", "true").lower() == "true":
            if conv_id != 'N/A':
                log_path = os.path.join(LOG_DIR, f"conv_{conv_id}.log")
            else:
                # fallback
                log_path = os.path.join(LOG_DIR, f"app_log_{uae_now.strftime('%Y-%m-%d')}.log")

            file_handler = logging.FileHandler(log_path, encoding='utf-8')
            file_handler.setFormatter(UAETimestampedFormatter())
            base_logger.addHandler(file_handler)

    return ContextLoggerAdapter(base_logger, context)


# Decorator
def log_execution(func):
    is_coroutine = inspect.iscoroutinefunction(func)

    def _update_logger_context(logger, self_instance, func):
        class_name = self_instance.__class__.__name__ if self_instance else "Global"
        func_name = func.__name__
        if isinstance(logger, ContextLoggerAdapter):
            logger.set_context(class_name=class_name, func_name=func_name)
            
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        self_instance = args[0] if args and hasattr(args[0], 'logger') else None
        logger = getattr(self_instance, 'logger', get_logger())
        _update_logger_context(logger, self_instance, func)
        logger.info("Entering function")
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Function executed successfully in {duration:.2f} seconds")
            return result
        except Exception as e:
            logger.error(f"Exception: {str(e)}")
            raise
        finally:
            logger.info("Exiting function")

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        self_instance = args[0] if args and hasattr(args[0], 'logger') else None
        logger = getattr(self_instance, 'logger', get_logger())
        _update_logger_context(logger, self_instance, func)
        logger.info("Entering function")
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Function executed successfully in {duration:.2f} seconds")
            return result
        except Exception as e:
            logger.error(f"Exception: {str(e)}")
            raise
        finally:
            logger.info("Exiting function")

    return async_wrapper if is_coroutine else sync_wrapper

# Test function
def test_uae_logging():
    logger = get_logger(conversation_id="test-456")
    logger.info("Testing UAE timezone logging")
    logger.info(f"Current UAE time: {datetime.now(UAE_TZ).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    return "UAE logging test completed"

if __name__ == "__main__":
    test_result = test_uae_logging()
    print(f"Test result: {test_result}")
