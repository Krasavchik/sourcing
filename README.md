# README

# Changelog Scraper

A Python application that scrapes and analyzes GitHub repositories featured on [changelog.com](https://nightly.changelog.com).

## Features

- Automatically scrapes the previous day's changelog entries
- Extracts GitHub repository URLs and metadata
- Queries the GitHub API to get repository details like:
  - Star count
  - Description
  - Author information
- Enriches data with author social media profiles (LinkedIn, X/Twitter)
- Exports data to CSV and Airtable


# Command lines:
python3 -m sources.changelog_nightly.run
python -m qualifiers.run_all
python -m opportunity_builder.run


Roadmap:
- [ ] Aggregate entities into opportunities
- [ ] Design scoring algorithm by hand
-- [ ]First investment criterion
-- [ ] then qualitative thesis
- [ ] Garbage collector: how do we delete some rows in the system after a certain period of time to avoid maintaining a super large dataset
- [ ] run.py (changelog nightly is ignoring duplicates, not inserting them in the database, hence missing signal on returning repo. For later: maybe refreshing existing entities based on that information would be useful)
- [ ] do a page or chrome extension that will add a webpage (repo, website,...) to the raw item database
- [ ] new source module: custom search github every monday eg. https://github.com/search?q=created%3A%3E2025-06-18+stars%3A%3E10&type=Repositories&ref=advsearch&l=&l=
- [ ] new source: every new companies listed on crunchbase / dealroom / affinity