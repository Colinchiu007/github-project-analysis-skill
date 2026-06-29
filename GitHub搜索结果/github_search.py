import requests
import time
import json
import sys
from datetime import datetime

keywords = [
    'multi-platform publish',
    'social media publisher',
    'content distribution',
    'cross-posting',
    'auto publish',
    'xiaohongshu api',
    'douyin api',
    'tiktok api',
    'rpa automation',
    'browser automation',
    'playwright',
    'electron desktop app',
    'social media scheduler',
    'batch posting',
    'social media analytics'
]

results = {}
headers = {"Accept": "application/vnd.github.v3+json"}

print(f"Starting search at: {datetime.utcnow().isoformat()}Z")
print(f"Total keywords: {len(keywords)}")

for i, kw in enumerate(keywords, 1):
    print(f"\nProcessing {i}/{len(keywords)}: {kw}")
    query = f"{kw} stars:>10000"
    print(f"Query: {query}")

    url = "https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 10
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            total = data.get("total_count", 0)
            items = data.get("items", [])
            print(f"Found {total} total repositories, showing top {len(items)}")

            for repo in items:
                repo_id = repo["id"]
                if repo_id not in results:
                    results[repo_id] = {
                        "name": repo["full_name"],
                        "url": repo["html_url"],
                        "stars": repo["stargazers_count"],
                        "language": repo.get("language") or "N/A",
                        "description": (repo.get("description") or "N/A")[:200],
                        "keywords": [kw]
                    }
                else:
                    if kw not in results[repo_id]["keywords"]:
                        results[repo_id]["keywords"].append(kw)
                print(f"  Added: {repo['full_name']} (stars: {repo['stargazers_count']})")
        elif response.status_code == 403:
            print(f"Rate limited! Waiting 60s...")
            time.sleep(60)
        else:
            print(f"Error: {response.status_code} - {response.text[:200]}")
            time.sleep(10)

        time.sleep(6)

    except Exception as e:
        print(f"Exception: {e}")
        time.sleep(10)

print(f"\nSearch completed. Total unique projects found: {len(results)}")

sorted_results = sorted(results.values(), key=lambda x: x["stars"], reverse=True)

with open("github_search_data.json", "w", encoding="utf-8") as f:
    json.dump(sorted_results, f, ensure_ascii=False, indent=2)

print("Raw data saved to github_search_data.json")

# Build markdown report
keyword_results = {}
for kw in keywords:
    keyword_results[kw] = []
    for repo in sorted_results:
        if kw in repo["keywords"]:
            keyword_results[kw].append(repo)

report = "# GitHub API Search Report\n\n"
report += "## Search Details\n\n"
report += f"- **Search Time**: {datetime.utcnow().isoformat()}Z\n"
report += f"- **Keywords**: {len(keywords)} keywords\n"
report += f"- **Filter**: Stars > 10,000\n"
report += f"- **Unique Projects Found**: {len(sorted_results)}\n\n"

report += "---\n\n"
report += "## Results by Keyword\n\n"

for kw in keywords:
    repos = keyword_results[kw]
    report += f"### {kw}\n\n"
    if not repos:
        report += "No projects with >10K stars found.\n\n"
        continue
    report += "| Rank | Repository | Stars | Language | Description |\n"
    report += "|------|-----------|-------|----------|-------------|\n"
    for idx, repo in enumerate(repos, 1):
        desc = repo["description"].replace("|", "\\|")[:80]
        report += f"| {idx} | [{repo['name']}]({repo['url']}) | {repo['stars']:,} | {repo['language']} | {desc} |\n"
    report += "\n"

report += "---\n\n"
report += "## Statistics\n\n"

# Top 10 projects
report += "### Top 10 Projects by Stars\n\n"
report += "| Rank | Repository | Stars | Language | Matched Keywords |\n"
report += "|------|-----------|-------|----------|------------------|\n"
for idx, repo in enumerate(sorted_results[:10], 1):
    kw_list = ", ".join(repo["keywords"][:3])
    if len(repo["keywords"]) > 3:
        kw_list += f" (+{len(repo['keywords']) - 3} more)"
    report += f"| {idx} | [{repo['name']}]({repo['url']}) | {repo['stars']:,} | {repo['language']} | {kw_list} |\n"
report += "\n"

# Language distribution
languages = {}
for repo in sorted_results:
    lang = repo["language"]
    if lang and lang != "N/A":
        languages[lang] = languages.get(lang, 0) + 1
top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:10]

report += "### Language Distribution (Top 10)\n\n"
report += "| Language | Count |\n"
report += "|----------|-------|\n"
for lang, count in top_languages:
    report += f"| {lang} | {count} |\n"
report += "\n"

# Keyword coverage
report += "### Keyword Coverage\n\n"
report += "| Keyword | Projects Found |\n"
report += "|---------|----------------|\n"
for kw in keywords:
    count = len(keyword_results[kw])
    report += f"| {kw} | {count} |\n"
report += "\n"

# Summary
report += "### Summary\n\n"
if sorted_results:
    avg_stars = sum(r["stars"] for r in sorted_results) / len(sorted_results)
    report += f"- **Total unique projects**: {len(sorted_results)}\n"
    report += f"- **Average stars per project**: {avg_stars:,.0f}\n"
    report += f"- **Highest star count**: {sorted_results[0]['stars']:,} ({sorted_results[0]['name']})\n"
    if top_languages:
        report += f"- **Most common language**: {top_languages[0][0]} ({top_languages[0][1]} projects)\n"
else:
    report += "- No projects found matching criteria.\n"

report += "\n---\n*Report generated from GitHub API search results*\n"

with open("github_search_report.md", "w", encoding="utf-8") as f:
    f.write(report)

print(f"Report saved to github_search_report.md")
print(f"Report length: {len(report)} characters")
