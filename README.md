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
