import logging
import sys

def setup_logger(name: str, level: str = "INFO", device_id: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(numeric_level)
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        
        # Format: LEVEL  [component] Message
        # The user requested deviceId or cameraId where applicable, but we'll include it in the message or via LoggerAdapter
        formatter = logging.Formatter(
            '%(levelname)s\t[%(name)s] %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

class EdgeLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        device_id = self.extra.get('device_id', 'unknown')
        return f"{msg} [device={device_id}]", kwargs
