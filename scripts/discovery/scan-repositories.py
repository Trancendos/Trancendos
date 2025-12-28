#!/usr/bin/env python3
"""
Activity 1: Repository Discovery & Inventory Scanner

Scans all GitHub repositories under Trancendos organization and generates
comprehensive inventory with metadata, workflows, and classification.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List

try:
    from github import Github
    from github.GithubException import GithubException
except ImportError:
    print("Error: PyGithub not installed. Run: pip install PyGithub")
    sys.exit(1)


class RepositoryScanner:
    """Scans and catalogs all GitHub repositories."""

    def __init__(self, github_token: str):
        self.github = Github(github_token)
        self.user = self.github.get_user()
        self.scan_results = {
            "scan_timestamp": datetime.utcnow().isoformat(),
            "scanner_version": "1.0.0",
            "total_repos": 0,
            "repositories": [],
            "classifications": {
                "CORE": [],
                "ACTIVE": [],
                "CONSOLIDATE": [],
                "ARCHIVE": [],
                "DEPRECATE": []
            }
        }

    def classify_repository(self, repo) -> str:
        """
        Intelligently classify repository based on activity and importance.
        
        Classification rules:
        - CORE: Active, many issues/PRs, recent commits, high importance
        - ACTIVE: Regular commits, moderate activity
        - CONSOLIDATE: Related repos that should be merged
        - ARCHIVE: No recent activity, but preserve
        - DEPRECATE: Obsolete, mark for eventual removal
        """
        # Get repository metrics
        try:
            commits = repo.get_commits()
            latest_commit = commits[0] if commits.totalCount > 0 else None
            days_since_commit = (datetime.now() - latest_commit.commit.author.date).days if latest_commit else 999
        except:
            days_since_commit = 999

        open_issues = repo.open_issues_count
        stars = repo.stargazers_count
        forks = repo.forks_count

        # Core repositories (ecosystem critical)
        core_repos = [
            'trancendos-ecosystem',
            'Luminous-MastermindAI',
            'Trancendos-Core',
            'compliance-framework',
            'platform-sync-buffer',
            'Trancendos'  # This repo itself
        ]

        if repo.name in core_repos:
            return "CORE"
        
        # Active: Recent commits (< 30 days) or active issues
        if days_since_commit < 30 or open_issues > 5:
            return "ACTIVE"
        
        # Archive: No recent activity (> 180 days) but not empty
        if days_since_commit > 180 and repo.size > 0:
            return "ARCHIVE"
        
        # Deprecate: Fork or empty repo
        if repo.fork or repo.size == 0:
            return "DEPRECATE"
        
        # Default: needs consolidation
        return "CONSOLIDATE"

    def scan_repository(self, repo) -> Dict:
        """Extract comprehensive metadata from a repository."""
        try:
            # Get workflows
            workflows = []
            try:
                for workflow in repo.get_workflows():
                    workflows.append({
                        "name": workflow.name,
                        "path": workflow.path,
                        "state": workflow.state
                    })
            except:
                pass

            # Get languages
            languages = repo.get_languages()

            # Get branches
            branches = [branch.name for branch in repo.get_branches()]

            # Get tags
            tags = [tag.name for tag in repo.get_tags()[:10]]  # Limit to recent 10

            classification = self.classify_repository(repo)

            repo_data = {
                "id": repo.id,
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "html_url": repo.html_url,
                "classification": classification,
                "visibility": "private" if repo.private else "public",
                "fork": repo.fork,
                "archived": repo.archived,
                "disabled": repo.disabled,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat(),
                "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                "size_kb": repo.size,
                "default_branch": repo.default_branch,
                "languages": languages,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "watchers": repo.watchers_count,
                "open_issues": repo.open_issues_count,
                "has_issues": repo.has_issues,
                "has_projects": repo.has_projects,
                "has_wiki": repo.has_wiki,
                "has_pages": repo.has_pages,
                "has_downloads": repo.has_downloads,
                "topics": repo.get_topics(),
                "branches": branches,
                "tags": tags,
                "workflows": workflows,
                "license": repo.license.name if repo.license else None,
            }

            self.scan_results["repositories"].append(repo_data)
            self.scan_results["classifications"][classification].append(repo.name)

            return repo_data

        except GithubException as e:
            print(f"Error scanning {repo.name}: {e}")
            return None

    def scan_all_repositories(self, max_repos: int = None) -> Dict:
        """Scan all repositories accessible to the user."""
        print(f"🔍 Scanning repositories for {self.user.login}...")
        print(f"📊 Total repositories: {self.user.public_repos}")

        repos = self.user.get_repos()
        count = 0

        for repo in repos:
            if max_repos and count >= max_repos:
                break
            
            print(f"  [{count + 1}] {repo.full_name} ...", end="")
            result = self.scan_repository(repo)
            if result:
                print(f" ✅ {result['classification']}")
            else:
                print(" ❌ ERROR")
            count += 1

        self.scan_results["total_repos"] = count

        # Print summary
        print("\n📈 Classification Summary:")
        for classification, repos in self.scan_results["classifications"].items():
            print(f"  {classification}: {len(repos)} repositories")

        return self.scan_results

    def save_results(self, output_path: str):
        """Save scan results to JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(self.scan_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Scan GitHub repositories and generate inventory"
    )
    parser.add_argument(
        '--output',
        default='inventory/repositories.json',
        help='Output JSON file path'
    )
    parser.add_argument(
        '--max-repos',
        type=int,
        help='Maximum number of repositories to scan (for testing)'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'yaml'],
        default='json',
        help='Output format'
    )
    
    args = parser.parse_args()

    # Get GitHub token from environment
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("\nSet it with: export GITHUB_TOKEN='your_token_here'")
        sys.exit(1)

    # Run scan
    scanner = RepositoryScanner(github_token)
    results = scanner.scan_all_repositories(max_repos=args.max_repos)
    scanner.save_results(args.output)

    print("\n✅ Discovery scan complete!")


if __name__ == "__main__":
    main()
