#!/usr/bin/env python3
"""
Activity 1: Platform Data Discovery Scanner

Scans data across integrated platforms (Notion, Linear, Jira, etc.)
and generates unified inventory.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List


class PlatformScanner:
    """Scans integrated platforms for data inventory."""

    def __init__(self):
        self.scan_results = {
            "scan_timestamp": datetime.utcnow().isoformat(),
            "scanner_version": "1.0.0",
            "platforms": {}
        }

    def scan_notion(self, api_key: str) -> Dict:
        """Scan Notion workspace."""
        print("🔍 Scanning Notion workspace...")
        
        try:
            # Import Notion client (if available)
            from notion_client import Client
            
            notion = Client(auth=api_key)
            
            # Get all pages
            results = notion.search(filter={"property": "object", "value": "page"})
            
            pages = []
            for page in results.get("results", []):
                pages.append({
                    "id": page["id"],
                    "title": page.get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled"),
                    "url": page.get("url"),
                    "created_time": page.get("created_time"),
                    "last_edited_time": page.get("last_edited_time"),
                })
            
            # Get databases
            db_results = notion.search(filter={"property": "object", "value": "database"})
            
            databases = []
            for db in db_results.get("results", []):
                databases.append({
                    "id": db["id"],
                    "title": db.get("title", [{}])[0].get("plain_text", "Untitled"),
                    "url": db.get("url"),
                })
            
            return {
                "status": "success",
                "total_pages": len(pages),
                "total_databases": len(databases),
                "pages": pages[:50],  # Limit to 50 for summary
                "databases": databases
            }
        
        except ImportError:
            print("  ⚠️  Notion client not installed (pip install notion-client)")
            return {"status": "skipped", "reason": "notion-client not installed"}
        except Exception as e:
            print(f"  ❌ Error scanning Notion: {e}")
            return {"status": "error", "error": str(e)}

    def scan_linear(self, api_key: str) -> Dict:
        """Scan Linear workspace."""
        print("🔍 Scanning Linear workspace...")
        
        # TODO: Implement Linear API scanning
        return {"status": "not_implemented"}

    def scan_jira(self, api_token: str) -> Dict:
        """Scan Jira workspace."""
        print("🔍 Scanning Jira workspace...")
        
        # TODO: Implement Jira API scanning
        return {"status": "not_implemented"}

    def scan_all_platforms(self) -> Dict:
        """Scan all configured platforms."""
        print("🌐 Scanning integrated platforms...\n")

        # Notion
        notion_key = os.environ.get('NOTION_API_KEY')
        if notion_key:
            self.scan_results["platforms"]["notion"] = self.scan_notion(notion_key)
        else:
            print("  ⚠️  NOTION_API_KEY not set, skipping Notion scan")

        # Linear
        linear_key = os.environ.get('LINEAR_API_KEY')
        if linear_key:
            self.scan_results["platforms"]["linear"] = self.scan_linear(linear_key)
        else:
            print("  ⚠️  LINEAR_API_KEY not set, skipping Linear scan")

        # Jira
        jira_token = os.environ.get('JIRA_API_TOKEN')
        if jira_token:
            self.scan_results["platforms"]["jira"] = self.scan_jira(jira_token)
        else:
            print("  ⚠️  JIRA_API_TOKEN not set, skipping Jira scan")

        return self.scan_results

    def save_results(self, output_path: str):
        """Save scan results to JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.scan_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Scan integrated platforms and generate inventory"
    )
    parser.add_argument(
        '--output',
        default='inventory/platforms.json',
        help='Output JSON file path'
    )
    
    args = parser.parse_args()

    # Run scan
    scanner = PlatformScanner()
    results = scanner.scan_all_platforms()
    scanner.save_results(args.output)

    print("\n✅ Platform scan complete!")


if __name__ == "__main__":
    main()
