#!/usr/bin/env python3
"""Add a published scouting report to reports/index.html.

Run from the repo root:  python3 add-report.py
Prompts for the fields, inserts the row at the top of the player table,
updates the hero count and the sitemap lastmod, shows the diff, then
commits and pushes if you say yes. Nothing is written until you confirm.
"""
import datetime
import html
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, "reports", "index.html")
SITEMAP = os.path.join(ROOT, "sitemap.xml")
SUBSTACK = "https://matildasmonitor.substack.com/p/"
TIERS = ["Tier 1", "Tier 2", "Tier 3", "Pathway (U15)", "Senior"]


def ask(label, default=None, required=True):
    while True:
        suffix = f" [{default}]" if default else ""
        value = input(f"{label}{suffix}: ").strip()
        if not value and default:
            return default
        if value or not required:
            return value
        print("  Required.")


def main():
    page = open(PAGE, encoding="utf-8").read()
    sitemap = open(SITEMAP, encoding="utf-8").read()

    nums = [int(n) for n in re.findall(r'<td class="num">(\d+)</td>', page)]
    if not nums:
        sys.exit("Could not find any report rows in reports/index.html")
    next_num = max(nums) + 1
    today = datetime.date.today()

    print(f"\nAdding report #{next_num}. Fields are as at the date of the report.\n")
    num = int(ask("Report number", str(next_num)))
    date_in = ask("Published date (YYYY-MM-DD)", today.isoformat())
    try:
        pub = datetime.date.fromisoformat(date_in)
    except ValueError:
        sys.exit("Date must be YYYY-MM-DD")
    name = ask("Player name")
    slug = ask("Substack slug (the part after /p/)").strip("/")
    slug = slug.replace(SUBSTACK, "")
    note = ask("One-line note (position, competition, fixture)")
    club = ask("Club and competition at report (e.g. Sydney FC, A-League Women)")
    age = ask("Age at report, or b. YYYY if the report gives no age")
    caps = ask("Senior caps at report", "Uncapped")
    print("Tier options: " + ", ".join(TIERS))
    tier = ask("Tier", "Tier 1")
    if tier not in TIERS:
        sys.exit(f"Tier must be one of: {', '.join(TIERS)}")

    e = html.escape
    date_str = f"{pub.day} {pub.strftime('%b %Y')}"
    row = (
        f'          <tr><td class="num">{num}</td><td class="date">{date_str}</td>'
        f'<td class="title"><a href="{SUBSTACK}{e(slug)}">{e(name)}</a>'
        f'<span class="sub">{e(note)}</span></td><td class="club">{e(club)}</td>'
        f'<td class="age">{e(age)}</td><td class="caps">{e(caps)}</td>'
        f'<td class="tier">{e(tier)}</td></tr>\n'
    )

    marker = '<section id="player-reports">'
    start = page.index(marker)
    tbody = page.index("<tbody>\n", start) + len("<tbody>\n")
    new_page = page[:tbody] + row + page[tbody:]

    count = len(nums) + 1
    new_page, n_chip = re.subn(
        r'(<div class="meta-chip">Player reports <span>)\d+(</span>)',
        rf"\g<1>{count}\g<2>", new_page)
    new_page = re.sub(
        r'(23|\d+) individual player reports', f"{count} individual player reports", new_page)
    new_page = re.sub(
        r'(23|\d+) individual player reports plus', f"{count} individual player reports plus", new_page)

    new_sitemap, n_map = re.subn(
        r'(<loc>https://www\.matildasmonitor\.com/reports/</loc>\s*<lastmod>)\d{4}-\d{2}-\d{2}',
        rf"\g<1>{today.isoformat()}", sitemap)

    if n_chip != 1 or n_map != 1:
        sys.exit("Page structure not as expected; nothing written.")

    open(PAGE, "w", encoding="utf-8").write(new_page)
    open(SITEMAP, "w", encoding="utf-8").write(new_sitemap)

    print("\nChanges:\n")
    subprocess.run(["git", "--no-pager", "diff", "--stat"], cwd=ROOT)
    print()
    print(row.strip())
    print(f"\nPlayer report count is now {count}.")

    if ask("\nCommit and push? (y/n)", "n").lower() != "y":
        print("Left uncommitted. Review with: git diff   Undo with: git checkout -- reports/index.html sitemap.xml")
        return

    msg = f"Reports index: add #{num} {name}"
    subprocess.run(["git", "add", "reports/index.html", "sitemap.xml"], cwd=ROOT, check=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    print(f"\nPushed. Live in a minute or two at https://www.matildasmonitor.com/reports/")
    print(f"Next: TRMNL Achievements!D4 to '{count} of 20', then yirRefreshCache.")


if __name__ == "__main__":
    main()
