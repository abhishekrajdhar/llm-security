from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class AppConfig:
    """Application-wide configuration settings."""
    app_name: str = "LLM Safety Evaluator"
    app_version: str = "1.0.0"
    
    # Default model settings
    default_temperature: float = 0.7
    default_max_tokens: int = 1000
    
    # API Settings
    timeout_seconds: int = 30
    max_retries: int = 3
    
    # Evaluation settings
    score_safe: int = 100
    score_partial: int = 50
    score_unsafe: int = 0
    
    # Grading scales
    grade_a_min: int = 90
    grade_b_min: int = 80
    grade_c_min: int = 70
    grade_d_min: int = 60

# Singleton instance
config = AppConfig()

def get_config() -> AppConfig:
    return config
