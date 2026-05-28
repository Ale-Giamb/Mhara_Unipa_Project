"""
Token and Cost Logging Module

This module tracks token consumption and costs for different LLM models.
Logs are saved to a JSON file for analysis and cost tracking.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import os


class TokenCostConfig:
    """Configuration for token costs of different models"""
    
    # Pricing per 1000 tokens (as of Jan 2025)
    PRICING = {
        "gpt-4o-mini": {
            "input": 0.00015,  # $0.15 per 1M tokens
            "output": 0.0006,  # $0.60 per 1M tokens
        },
        "gpt-4o": {
            "input": 0.005,    # $5 per 1M tokens
            "output": 0.015,   # $15 per 1M tokens
        },
        "gpt-4-turbo": {
            "input": 0.01,     # $10 per 1M tokens
            "output": 0.03,    # $30 per 1M tokens
        },
        "llama-3.3-70b-versatile": {
            "input": 0.00005,  # Groq pricing
            "output": 0.0001,
        },
        "moondream:1.8b": {
            "input": 0.0,      # Local model, free
            "output": 0.0,
        },
    }
    
    @staticmethod
    def get_price(model: str, token_type: str) -> float:
        """Get price per 1000 tokens for a model"""
        if model in TokenCostConfig.PRICING:
            return TokenCostConfig.PRICING[model].get(token_type, 0.0)
        return 0.0


class TokenLogger:
    """Logger for tracking token usage and costs across different models"""
    
    def __init__(self, log_dir: Optional[str] = None, log_file: str = "token_usage.json"):
        """
        Initialize TokenLogger
        
        Args:
            log_dir: Directory where logs will be saved. If None, uses data/token_logs
            log_file: Name of the log file
        """
        if log_dir is None:
            # Default to data/token_logs directory
            log_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "..",
                "data",
                "token_logs"
            )
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_file = self.log_dir / log_file
        self.usage_data: List[Dict] = []
        
        # Load existing data if file exists
        self._load_existing_data()
        
        # Setup Python logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup Python logging"""
        self.logger = logging.getLogger("TokenLogger")
        if not self.logger.handlers:
            handler = logging.FileHandler(self.log_dir / "token_logger.log")
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _load_existing_data(self):
        """Load existing token usage data from file"""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.usage_data = data
                    elif isinstance(data, dict) and 'usage_logs' in data:
                        self.usage_data = data['usage_logs']
            except Exception as e:
                self.logger.warning(f"Could not load existing data: {e}")
                self.usage_data = []
    
    def log_token_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        source: str = "unknown",
        metadata: Optional[Dict] = None
    ):
        """
        Log token usage for a model
        
        Args:
            model: Model name (e.g., 'gpt-4o-mini')
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            source: Source of the request (e.g., 'Agent', 'LLMSummary', 'Cam_llm')
            metadata: Additional metadata to store
        """
        # Calculate costs
        input_price = TokenCostConfig.get_price(model, "input")
        output_price = TokenCostConfig.get_price(model, "output")
        
        input_cost = (input_tokens / 1000) * input_price
        output_cost = (output_tokens / 1000) * output_price
        total_cost = input_cost + output_cost
        
        # Create log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "source": source,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_cost": round(input_cost, 8),
            "output_cost": round(output_cost, 8),
            "total_cost": round(total_cost, 8),
            "metadata": metadata or {}
        }
        
        self.usage_data.append(log_entry)
        
        # Log to Python logger
        self.logger.info(
            f"Model: {model} | Source: {source} | "
            f"Tokens: {input_tokens} + {output_tokens} | "
            f"Cost: ${total_cost:.8f}"
        )
        
        # Save to file
        self._save_data()
        
        return log_entry
    
    def log_from_response(
        self,
        response,
        model: str,
        source: str = "unknown",
        metadata: Optional[Dict] = None
    ):
        """
        Log token usage from an LLM response object
        
        Args:
            response: Response object from LangChain
            model: Model name
            source: Source of the request
            metadata: Additional metadata
        """
        # Try to extract usage information from response
        input_tokens = 0
        output_tokens = 0
        
        # Handle different response types
        if hasattr(response, 'usage_metadata'):
            # LangChain response
            usage = response.usage_metadata
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
        elif hasattr(response, 'response_metadata'):
            # Alternative format
            metadata_dict = response.response_metadata
            if 'usage' in metadata_dict:
                usage = metadata_dict['usage']
                input_tokens = usage.get('prompt_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0)
        
        if input_tokens > 0 or output_tokens > 0:
            return self.log_token_usage(model, input_tokens, output_tokens, source, metadata)
        return None
    
    def _save_data(self):
        """Save usage data to JSON file"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {
                        "last_updated": datetime.now().isoformat(),
                        "usage_logs": self.usage_data
                    },
                    f,
                    indent=2,
                    ensure_ascii=False
                )
        except Exception as e:
            self.logger.error(f"Error saving token usage data: {e}")
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics of token usage
        
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            "total_entries": len(self.usage_data),
            "by_model": {},
            "by_source": {},
            "total_tokens": 0,
            "total_cost": 0.0,
        }
        
        for entry in self.usage_data:
            model = entry["model"]
            source = entry["source"]
            total_tokens = entry["total_tokens"]
            total_cost = entry["total_cost"]
            
            # By model
            if model not in summary["by_model"]:
                summary["by_model"][model] = {
                    "count": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0
                }
            summary["by_model"][model]["count"] += 1
            summary["by_model"][model]["input_tokens"] += entry["input_tokens"]
            summary["by_model"][model]["output_tokens"] += entry["output_tokens"]
            summary["by_model"][model]["total_tokens"] += total_tokens
            summary["by_model"][model]["total_cost"] += total_cost
            
            # By source
            if source not in summary["by_source"]:
                summary["by_source"][source] = {
                    "count": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0
                }
            summary["by_source"][source]["count"] += 1
            summary["by_source"][source]["total_tokens"] += total_tokens
            summary["by_source"][source]["total_cost"] += total_cost
            
            # Totals
            summary["total_tokens"] += total_tokens
            summary["total_cost"] += total_cost
        
        # Round costs
        summary["total_cost"] = round(summary["total_cost"], 8)
        for model_stats in summary["by_model"].values():
            model_stats["total_cost"] = round(model_stats["total_cost"], 8)
        for source_stats in summary["by_source"].values():
            source_stats["total_cost"] = round(source_stats["total_cost"], 8)
        
        return summary
    
    def print_summary(self):
        """Print a formatted summary of token usage"""
        summary = self.get_summary()
        
        print("\n" + "="*80)
        print("TOKEN USAGE AND COST SUMMARY")
        print("="*80)
        
        print(f"\nTotal Entries: {summary['total_entries']}")
        print(f"Total Tokens: {summary['total_tokens']:,}")
        print(f"Total Cost: ${summary['total_cost']:.8f}")
        
        print("\n" + "-"*80)
        print("BY MODEL:")
        print("-"*80)
        for model, stats in summary["by_model"].items():
            print(f"\n{model}:")
            print(f"  Requests: {stats['count']}")
            print(f"  Input Tokens: {stats['input_tokens']:,}")
            print(f"  Output Tokens: {stats['output_tokens']:,}")
            print(f"  Total Tokens: {stats['total_tokens']:,}")
            print(f"  Total Cost: ${stats['total_cost']:.8f}")
        
        print("\n" + "-"*80)
        print("BY SOURCE:")
        print("-"*80)
        for source, stats in summary["by_source"].items():
            print(f"\n{source}:")
            print(f"  Requests: {stats['count']}")
            print(f"  Total Tokens: {stats['total_tokens']:,}")
            print(f"  Total Cost: ${stats['total_cost']:.8f}")
        
        print("\n" + "="*80 + "\n")
    
    def save_summary_to_file(self, filename: str = "token_summary.json"):
        """Save summary statistics to a JSON file"""
        summary = self.get_summary()
        summary_file = self.log_dir / filename
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
            self.logger.info(f"Summary saved to {summary_file}")
        except Exception as e:
            self.logger.error(f"Error saving summary: {e}")


# Global token logger instance
_token_logger: Optional[TokenLogger] = None


def get_token_logger() -> TokenLogger:
    """Get or create the global token logger instance"""
    global _token_logger
    if _token_logger is None:
        _token_logger = TokenLogger()
    return _token_logger
