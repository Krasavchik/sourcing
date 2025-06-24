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


Roadmap:
- run.py (changelog nightly is ignoring duplicates, not inserting them in the database, hence missing signal on returning repo. For later: maybe refreshing existing entities based on that information would be useful)