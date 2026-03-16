import logging
import sys

def setup_logger(name: str = "safety_evaluator") -> logging.Logger:
    """Configure and return the application logger."""
    logger = logging.getLogger(name)
    
    # Only configure if no handlers are present to avoid duplicate logs
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
    return logger

# Create a default logger instance
logger = setup_logger()
