#!/usr/bin/env python3
"""
Real-time Token Usage Monitor

This script provides a simple command-line interface to monitor
token usage and costs in real-time.
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import os


class TokenMonitor:
    """Monitor token usage and costs"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.last_check_count = 0
    
    def load_logs(self) -> Dict:
        """Load logs from JSON file"""
        if not self.log_file.exists():
            return {}
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def get_recent_logs(self, minutes: int = 60) -> List[Dict]:
        """Get logs from the last N minutes"""
        data = self.load_logs()
        logs = data.get('usage_logs', [])
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent = []
        
        for log in logs:
            try:
                log_time = datetime.fromisoformat(log.get('timestamp', ''))
                if log_time >= cutoff_time:
                    recent.append(log)
            except:
                pass
        
        return recent
    
    def get_stats(self, logs: List[Dict]) -> Dict:
        """Calculate statistics from logs"""
        if not logs:
            return {
                "count": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "by_model": {},
                "by_source": {}
            }
        
        stats = {
            "count": len(logs),
            "total_tokens": 0,
            "total_cost": 0.0,
            "by_model": {},
            "by_source": {}
        }
        
        for log in logs:
            model = log.get('model', 'unknown')
            source = log.get('source', 'unknown')
            tokens = log.get('total_tokens', 0)
            cost = log.get('total_cost', 0)
            
            stats["total_tokens"] += tokens
            stats["total_cost"] += cost
            
            if model not in stats["by_model"]:
                stats["by_model"][model] = {"count": 0, "tokens": 0, "cost": 0.0}
            stats["by_model"][model]["count"] += 1
            stats["by_model"][model]["tokens"] += tokens
            stats["by_model"][model]["cost"] += cost
            
            if source not in stats["by_source"]:
                stats["by_source"][source] = {"count": 0, "tokens": 0, "cost": 0.0}
            stats["by_source"][source]["count"] += 1
            stats["by_source"][source]["tokens"] += tokens
            stats["by_source"][source]["cost"] += cost
        
        return stats
    
    def print_dashboard(self, stats: Dict):
        """Print a dashboard-style display"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print(f"\n{'='*80}")
        print(f"{'TOKEN USAGE MONITOR - ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^80}")
        print(f"{'='*80}\n")
        
        print(f"Total Requests: {stats['count']:<20} Total Tokens: {stats['total_tokens']:,}")
        print(f"Total Cost:     ${stats['total_cost']:.8f}")
        print()
        
        if stats['by_model']:
            print(f"{'MODEL':<30} {'REQ':<8} {'TOKENS':<15} {'COST':<15}")
            print("-" * 70)
            for model, data in sorted(stats['by_model'].items()):
                print(f"{model:<30} {data['count']:<8} {data['tokens']:<15,} ${data['cost']:<14.8f}")
            print()
        
        if stats['by_source']:
            print(f"{'SOURCE':<20} {'REQ':<8} {'TOKENS':<15} {'COST':<15}")
            print("-" * 60)
            for source, data in sorted(stats['by_source'].items()):
                print(f"{source:<20} {data['count']:<8} {data['tokens']:<15,} ${data['cost']:<14.8f}")
        
        print(f"\n{'='*80}")
        print("Press Ctrl+C to exit | Auto-refreshing every 10 seconds")
        print(f"{'='*80}\n")
    
    def watch(self, minutes: int = 60, interval: int = 10):
        """Watch token usage with auto-refresh"""
        print(f"Monitoring token usage from the last {minutes} minutes")
        print(f"Auto-refreshing every {interval} seconds...")
        
        try:
            while True:
                logs = self.get_recent_logs(minutes)
                stats = self.get_stats(logs)
                self.print_dashboard(stats)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Real-time Token Usage Monitor'
    )
    parser.add_argument(
        '--log-file',
        type=Path,
        default=Path(__file__).parent.parent / 'data' / 'token_logs' / 'token_usage.json',
        help='Path to token usage log file'
    )
    parser.add_argument(
        '--minutes',
        type=int,
        default=60,
        help='Show logs from last N minutes (default: 60)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='Auto-refresh interval in seconds (default: 10)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Show once and exit (no auto-refresh)'
    )
    
    args = parser.parse_args()
    
    monitor = TokenMonitor(args.log_file)
    
    if args.once:
        logs = monitor.get_recent_logs(args.minutes)
        stats = monitor.get_stats(logs)
        monitor.print_dashboard(stats)
    else:
        monitor.watch(args.minutes, args.interval)


if __name__ == '__main__':
    main()
