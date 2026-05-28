#!/usr/bin/env python3
"""
Token and Cost Analysis Tool

This script provides utilities to view and analyze token usage logs.
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os


def load_token_logs(log_file: Path) -> Dict:
    """Load token usage logs from JSON file"""
    if not log_file.exists():
        print(f"Log file not found: {log_file}")
        return {}
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading log file: {e}")
        return {}


def print_detailed_logs(data: Dict, limit: Optional[int] = None):
    """Print detailed logs with pagination"""
    logs = data.get('usage_logs', [])
    
    if not logs:
        print("No usage logs found.")
        return
    
    # Apply limit if specified
    if limit:
        logs = logs[-limit:]  # Get last N logs
    
    print(f"\n{'='*120}")
    print("DETAILED TOKEN USAGE LOGS")
    print(f"{'='*120}\n")
    
    print(f"{'Timestamp':<25} {'Model':<25} {'Source':<15} {'Input':<10} {'Output':<10} {'Total':<10} {'Cost':<12}")
    print("-" * 120)
    
    for log in logs:
        timestamp = log.get('timestamp', '')[:19]
        model = log.get('model', '')[:24]
        source = log.get('source', '')[:14]
        input_tokens = log.get('input_tokens', 0)
        output_tokens = log.get('output_tokens', 0)
        total_tokens = log.get('total_tokens', 0)
        cost = log.get('total_cost', 0)
        
        print(f"{timestamp:<25} {model:<25} {source:<15} {input_tokens:<10} {output_tokens:<10} {total_tokens:<10} ${cost:<11.8f}")
    
    print(f"\n{'='*120}\n")


def print_summary(data: Dict):
    """Print summary statistics"""
    logs = data.get('usage_logs', [])
    
    if not logs:
        print("No usage logs found.")
        return
    
    # Calculate totals
    summary = {
        "total_entries": len(logs),
        "by_model": {},
        "by_source": {},
        "total_tokens": 0,
        "total_cost": 0.0,
        "date_range": {
            "first": logs[0].get('timestamp', '')[:10] if logs else '',
            "last": logs[-1].get('timestamp', '')[:10] if logs else ''
        }
    }
    
    for log in logs:
        model = log.get('model', 'unknown')
        source = log.get('source', 'unknown')
        
        if model not in summary["by_model"]:
            summary["by_model"][model] = {
                "count": 0, "input": 0, "output": 0, "total": 0, "cost": 0.0
            }
        if source not in summary["by_source"]:
            summary["by_source"][source] = {
                "count": 0, "total": 0, "cost": 0.0
            }
        
        summary["by_model"][model]["count"] += 1
        summary["by_model"][model]["input"] += log.get('input_tokens', 0)
        summary["by_model"][model]["output"] += log.get('output_tokens', 0)
        summary["by_model"][model]["total"] += log.get('total_tokens', 0)
        summary["by_model"][model]["cost"] += log.get('total_cost', 0)
        
        summary["by_source"][source]["count"] += 1
        summary["by_source"][source]["total"] += log.get('total_tokens', 0)
        summary["by_source"][source]["cost"] += log.get('total_cost', 0)
        
        summary["total_tokens"] += log.get('total_tokens', 0)
        summary["total_cost"] += log.get('total_cost', 0)
    
    # Print summary
    print(f"\n{'='*80}")
    print("TOKEN USAGE AND COST SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"Report Period: {summary['date_range']['first']} to {summary['date_range']['last']}")
    print(f"Total Entries: {summary['total_entries']:,}")
    print(f"Total Tokens: {summary['total_tokens']:,}")
    print(f"Total Cost: ${summary['total_cost']:.8f}\n")
    
    print("-" * 80)
    print("BY MODEL:")
    print("-" * 80)
    for model, stats in sorted(summary["by_model"].items()):
        print(f"\n{model}:")
        print(f"  Requests: {stats['count']}")
        print(f"  Input Tokens: {stats['input']:,}")
        print(f"  Output Tokens: {stats['output']:,}")
        print(f"  Total Tokens: {stats['total']:,}")
        print(f"  Total Cost: ${stats['cost']:.8f}")
        if stats['count'] > 0:
            print(f"  Avg Cost/Request: ${stats['cost']/stats['count']:.8f}")
    
    print("\n" + "-" * 80)
    print("BY SOURCE:")
    print("-" * 80)
    for source, stats in sorted(summary["by_source"].items()):
        print(f"\n{source}:")
        print(f"  Requests: {stats['count']}")
        print(f"  Total Tokens: {stats['total']:,}")
        print(f"  Total Cost: ${stats['cost']:.8f}")
        if stats['count'] > 0:
            print(f"  Avg Tokens/Request: {stats['total']/stats['count']:.0f}")
            print(f"  Avg Cost/Request: ${stats['cost']/stats['count']:.8f}")
    
    print(f"\n{'='*80}\n")


def export_csv(data: Dict, output_file: Path):
    """Export logs to CSV format"""
    import csv
    
    logs = data.get('usage_logs', [])
    
    if not logs:
        print("No logs to export.")
        return
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'model', 'source', 'input_tokens', 'output_tokens',
                'total_tokens', 'input_cost', 'output_cost', 'total_cost'
            ])
            writer.writeheader()
            
            for log in logs:
                writer.writerow({
                    'timestamp': log.get('timestamp', ''),
                    'model': log.get('model', ''),
                    'source': log.get('source', ''),
                    'input_tokens': log.get('input_tokens', 0),
                    'output_tokens': log.get('output_tokens', 0),
                    'total_tokens': log.get('total_tokens', 0),
                    'input_cost': log.get('input_cost', 0),
                    'output_cost': log.get('output_cost', 0),
                    'total_cost': log.get('total_cost', 0),
                })
        
        print(f"Exported {len(logs)} logs to {output_file}")
    except Exception as e:
        print(f"Error exporting to CSV: {e}")


def filter_by_date(logs: List[Dict], days: int) -> List[Dict]:
    """Filter logs from last N days"""
    if not logs:
        return []
    
    cutoff_date = datetime.now() - timedelta(days=days)
    filtered = []
    
    for log in logs:
        log_date = datetime.fromisoformat(log.get('timestamp', ''))
        if log_date >= cutoff_date:
            filtered.append(log)
    
    return filtered


def main():
    parser = argparse.ArgumentParser(
        description='Token and Cost Usage Analysis Tool'
    )
    parser.add_argument(
        '--log-file',
        type=Path,
        default=Path(__file__).parent.parent / 'data' / 'token_logs' / 'token_usage.json',
        help='Path to token usage log file'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary statistics'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed logs'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of detailed logs to show (last N)'
    )
    parser.add_argument(
        '--export-csv',
        type=Path,
        help='Export logs to CSV file'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=None,
        help='Filter logs from last N days'
    )
    
    args = parser.parse_args()
    
    # Load data
    data = load_token_logs(args.log_file)
    
    if not data:
        print("No data available.")
        return
    
    # Filter by date if specified
    if args.days:
        logs = filter_by_date(data.get('usage_logs', []), args.days)
        data['usage_logs'] = logs
    
    # Show output
    if args.export_csv:
        export_csv(data, args.export_csv)
    elif args.detailed:
        print_detailed_logs(data, args.limit)
    else:
        # Default: show summary
        print_summary(data)


if __name__ == '__main__':
    main()
