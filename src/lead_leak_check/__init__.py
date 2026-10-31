"""lead-leak-check rule engine (Zapier/Make/n8n lead-pipeline audit rules)."""
from .rules import RULES, analyze_history, check_config, check_description, config_from_text

__all__ = ["RULES", "analyze_history", "check_config", "check_description", "config_from_text"]
