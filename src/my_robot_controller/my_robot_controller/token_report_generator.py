"""
Token Cost Report Generator

Generates comprehensive reports of token usage and costs
in various formats (text, HTML, JSON).
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os


class ReportGenerator:
    """Generate token usage reports"""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load data from log file"""
        if not self.log_file.exists():
            return {}
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _calculate_stats(self) -> Dict:
        """Calculate comprehensive statistics"""
        logs = self.data.get('usage_logs', [])
        
        stats = {
            "report_date": datetime.now().isoformat(),
            "total_logs": len(logs),
            "total_tokens": 0,
            "total_cost": 0.0,
            "date_range": {
                "start": logs[0].get('timestamp', '')[:10] if logs else '',
                "end": logs[-1].get('timestamp', '')[:10] if logs else ''
            },
            "by_model": {},
            "by_source": {},
            "by_date": {},
            "hourly_stats": {},
            "cost_breakdown": {}
        }
        
        for log in logs:
            model = log.get('model', 'unknown')
            source = log.get('source', 'unknown')
            tokens = log.get('total_tokens', 0)
            cost = log.get('total_cost', 0)
            timestamp = log.get('timestamp', '')
            
            # Totals
            stats['total_tokens'] += tokens
            stats['total_cost'] += cost
            
            # By model
            if model not in stats['by_model']:
                stats['by_model'][model] = {
                    'count': 0, 'input': 0, 'output': 0, 'tokens': 0, 'cost': 0.0
                }
            stats['by_model'][model]['count'] += 1
            stats['by_model'][model]['input'] += log.get('input_tokens', 0)
            stats['by_model'][model]['output'] += log.get('output_tokens', 0)
            stats['by_model'][model]['tokens'] += tokens
            stats['by_model'][model]['cost'] += cost
            
            # By source
            if source not in stats['by_source']:
                stats['by_source'][source] = {'count': 0, 'tokens': 0, 'cost': 0.0}
            stats['by_source'][source]['count'] += 1
            stats['by_source'][source]['tokens'] += tokens
            stats['by_source'][source]['cost'] += cost
            
            # By date
            date_key = timestamp[:10] if timestamp else ''
            if date_key:
                if date_key not in stats['by_date']:
                    stats['by_date'][date_key] = {'count': 0, 'tokens': 0, 'cost': 0.0}
                stats['by_date'][date_key]['count'] += 1
                stats['by_date'][date_key]['tokens'] += tokens
                stats['by_date'][date_key]['cost'] += cost
            
            # Hourly stats
            hour_key = timestamp[:13] if timestamp else ''
            if hour_key:
                if hour_key not in stats['hourly_stats']:
                    stats['hourly_stats'][hour_key] = {'count': 0, 'cost': 0.0}
                stats['hourly_stats'][hour_key]['count'] += 1
                stats['hourly_stats'][hour_key]['cost'] += cost
        
        # Round costs
        stats['total_cost'] = round(stats['total_cost'], 8)
        for model_stats in stats['by_model'].values():
            model_stats['cost'] = round(model_stats['cost'], 8)
        for source_stats in stats['by_source'].values():
            source_stats['cost'] = round(source_stats['cost'], 8)
        for date_stats in stats['by_date'].values():
            date_stats['cost'] = round(date_stats['cost'], 8)
        for hour_stats in stats['hourly_stats'].values():
            hour_stats['cost'] = round(hour_stats['cost'], 8)
        
        return stats
    
    def generate_text_report(self) -> str:
        """Generate a text format report"""
        stats = self._calculate_stats()
        
        report = []
        report.append("=" * 100)
        report.append("TOKEN USAGE AND COST REPORT".center(100))
        report.append("=" * 100)
        report.append(f"\nReport Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Period: {stats['date_range']['start']} to {stats['date_range']['end']}")
        report.append(f"Total Entries: {stats['total_logs']:,}\n")
        
        # Summary
        report.append("-" * 100)
        report.append("SUMMARY".center(100))
        report.append("-" * 100)
        report.append(f"Total Tokens Used: {stats['total_tokens']:,}")
        report.append(f"Total Cost: ${stats['total_cost']:.8f}\n")
        
        # By Model
        report.append("-" * 100)
        report.append("BY MODEL".center(100))
        report.append("-" * 100)
        report.append(f"{'Model':<30} {'Requests':<12} {'Input':<12} {'Output':<12} {'Total':<12} {'Cost':<15}")
        report.append("-" * 100)
        
        for model, data in sorted(stats['by_model'].items()):
            report.append(
                f"{model:<30} {data['count']:<12} {data['input']:<12,} "
                f"{data['output']:<12,} {data['tokens']:<12,} ${data['cost']:<14.8f}"
            )
        
        # By Source
        report.append("\n" + "-" * 100)
        report.append("BY SOURCE".center(100))
        report.append("-" * 100)
        report.append(f"{'Source':<20} {'Requests':<12} {'Tokens':<15} {'Cost':<15} {'Avg Cost/Req':<15}")
        report.append("-" * 100)
        
        for source, data in sorted(stats['by_source'].items()):
            avg_cost = data['cost'] / data['count'] if data['count'] > 0 else 0
            report.append(
                f"{source:<20} {data['count']:<12} {data['tokens']:<15,} "
                f"${data['cost']:<14.8f} ${avg_cost:<14.8f}"
            )
        
        # By Date
        if stats['by_date']:
            report.append("\n" + "-" * 100)
            report.append("BY DATE".center(100))
            report.append("-" * 100)
            report.append(f"{'Date':<15} {'Requests':<12} {'Tokens':<15} {'Cost':<15}")
            report.append("-" * 100)
            
            for date, data in sorted(stats['by_date'].items()):
                report.append(
                    f"{date:<15} {data['count']:<12} {data['tokens']:<15,} ${data['cost']:<14.8f}"
                )
        
        # Top models by cost
        report.append("\n" + "-" * 100)
        report.append("TOP MODELS BY COST".center(100))
        report.append("-" * 100)
        
        sorted_models = sorted(stats['by_model'].items(), key=lambda x: x[1]['cost'], reverse=True)
        for i, (model, data) in enumerate(sorted_models[:5], 1):
            percentage = (data['cost'] / stats['total_cost'] * 100) if stats['total_cost'] > 0 else 0
            report.append(f"{i}. {model}: ${data['cost']:.8f} ({percentage:.1f}%)")
        
        report.append("\n" + "=" * 100)
        
        return "\n".join(report)
    
    def generate_html_report(self, output_file: Path) -> None:
        """Generate an HTML format report"""
        stats = self._calculate_stats()
        
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>Token Usage Report - {datetime.now().strftime('%Y-%m-%d')}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }",
            ".container { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
            "h1 { text-align: center; color: #333; }",
            "h2 { color: #0066cc; border-bottom: 2px solid #0066cc; padding-bottom: 10px; }",
            ".summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }",
            ".summary-card { background-color: #f9f9f9; padding: 15px; border-left: 4px solid #0066cc; }",
            ".summary-card .value { font-size: 24px; font-weight: bold; color: #0066cc; }",
            ".summary-card .label { color: #666; font-size: 14px; }",
            "table { width: 100%; border-collapse: collapse; margin: 20px 0; }",
            "th { background-color: #0066cc; color: white; padding: 12px; text-align: left; }",
            "td { padding: 10px; border-bottom: 1px solid #ddd; }",
            "tr:hover { background-color: #f5f5f5; }",
            ".footer { text-align: center; color: #999; font-size: 12px; margin-top: 20px; }",
            "</style>",
            "</head>",
            "<body>",
            "<div class='container'>",
            f"<h1>Token Usage and Cost Report</h1>",
            f"<p style='text-align: center; color: #666;'>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
            "",
            "<div class='summary'>",
            f"<div class='summary-card'><div class='label'>Total Entries</div><div class='value'>{stats['total_logs']:,}</div></div>",
            f"<div class='summary-card'><div class='label'>Total Tokens</div><div class='value'>{stats['total_tokens']:,}</div></div>",
            f"<div class='summary-card'><div class='label'>Total Cost</div><div class='value'>${stats['total_cost']:.8f}</div></div>",
            "</div>",
            "",
            "<h2>By Model</h2>",
            "<table>",
            "<tr><th>Model</th><th>Requests</th><th>Input Tokens</th><th>Output Tokens</th><th>Total Tokens</th><th>Cost</th></tr>",
        ]
        
        for model, data in sorted(stats['by_model'].items()):
            html.append(
                f"<tr>"
                f"<td>{model}</td>"
                f"<td>{data['count']}</td>"
                f"<td>{data['input']:,}</td>"
                f"<td>{data['output']:,}</td>"
                f"<td>{data['tokens']:,}</td>"
                f"<td>${data['cost']:.8f}</td>"
                f"</tr>"
            )
        
        html.extend([
            "</table>",
            "",
            "<h2>By Source</h2>",
            "<table>",
            "<tr><th>Source</th><th>Requests</th><th>Tokens</th><th>Cost</th><th>Avg Cost/Request</th></tr>",
        ])
        
        for source, data in sorted(stats['by_source'].items()):
            avg_cost = data['cost'] / data['count'] if data['count'] > 0 else 0
            html.append(
                f"<tr>"
                f"<td>{source}</td>"
                f"<td>{data['count']}</td>"
                f"<td>{data['tokens']:,}</td>"
                f"<td>${data['cost']:.8f}</td>"
                f"<td>${avg_cost:.8f}</td>"
                f"</tr>"
            )
        
        html.extend([
            "</table>",
            "<div class='footer'>",
            f"<p>Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
            "</div>",
            "</div>",
            "</body>",
            "</html>"
        ])
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(html))
    
    def generate_json_report(self) -> Dict:
        """Generate a JSON format report"""
        return self._calculate_stats()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Token Cost Report Generator')
    parser.add_argument(
        '--log-file',
        type=Path,
        default=Path(__file__).parent.parent / 'data' / 'token_logs' / 'token_usage.json',
        help='Path to token usage log file'
    )
    parser.add_argument(
        '--text',
        action='store_true',
        help='Generate text report (print to stdout)'
    )
    parser.add_argument(
        '--html',
        type=Path,
        help='Generate HTML report and save to file'
    )
    parser.add_argument(
        '--json',
        type=Path,
        help='Generate JSON report and save to file'
    )
    
    args = parser.parse_args()
    
    generator = ReportGenerator(args.log_file)
    
    if args.text:
        print(generator.generate_text_report())
    
    if args.html:
        generator.generate_html_report(args.html)
        print(f"HTML report saved to: {args.html}")
    
    if args.json:
        report = generator.generate_json_report()
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"JSON report saved to: {args.json}")
    
    if not any([args.text, args.html, args.json]):
        # Default to text
        print(generator.generate_text_report())


if __name__ == '__main__':
    main()
