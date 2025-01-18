import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime, timedelta

# Fetch secrets from environment variables
github_api_token = os.getenv("TOKEN_GITHUB_API")
airtable_token = os.getenv("TOKEN_AIRTABLE")

if not github_api_token or not airtable_token:
    raise ValueError("Missing required tokens. Ensure environment variables are set.")

# Use the tokens as needed
print("Successfully retrieved tokens!")

AIRTABLE_BASE_ID = "appKhM4requBnJGOc"
AIRTABLE_TABLE_ID = "tblgUEvOxS3HIcX5F"

# Input: URL of the website
# Get the current date
current_date = datetime.now()

# Subtract one day to get yesterday's date
yesterday_date = current_date - timedelta(days=1)

# Format the date as YYYY/MM/DD
formatted_date = yesterday_date.strftime("%Y/%m/%d")

# Build the URL
base_url = "https://nightly.changelog.com"
input_url = f"{base_url}/{formatted_date}"
filename = f"exports/export_changelog_{yesterday_date.year}_{yesterday_date.month:02d}_{yesterday_date.day:02d}.csv"

# Overwritting the URL if need be
#input_url = "https://nightly.changelog.com/2025/01/04"

# Build the exclusion list
exclusion_list = ["https://github.com/thechangelog", "https://github.com/trending", "https://github.com/NVIDIA", "https://github.com/NJU-PCALab", "https://github.com/bytedance"]

# Function to scrape all URLs from the given website
def scrape_urls(website_url):
    try:
        response = requests.get(website_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all anchor tags
        links = [a.get('href') for a in soup.find_all('a', href=True)]
        return links
    except requests.RequestException as e:
        print(f"Error accessing {website_url}: {e}")
        return []

# Function to check if a URL redirects to github.com
def check_redirect_to_github(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        if 'github.com' in response.url:
            return True, response.url
    except requests.RequestException:
        pass
    return False, None

# Function to check if a URL is a GitHub repository
def is_github_repo(url):
    pattern = r"^https://github\.com/([^/]+)/([^/]+)$"
    match = re.match(pattern, url)
    if match:
        author = f"https://github.com/{match.group(1)}"
        repo = url
        return True, author, repo
    return False, None, None


def query_github_repo(repo_url):
    if not repo_url.startswith("https://github.com/"):
        raise ValueError("Invalid GitHub repository URL")

    # Extract the owner and repo name from the URL
    parts = repo_url.split("https://github.com/")[-1].split("/")
    if len(parts) < 2:
        raise ValueError("Incomplete GitHub repository URL")

    owner, repo = parts[:2]

    # Construct the API call
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    headers={
        "Accept": "application/vnd.github.v3+json",
        "Authorization": "Bearer {github_api_token}"
    }
    try:
        response = requests.get(api_url, headers=headers)  # Pass headers as a keyword argument
        response.raise_for_status()
        repo_data = response.json()

        # Extract required information
        repo_name = repo_data.get("name", "Unknown Repo")
        repo_description = repo_data.get("description", "No description available")
        star_count = repo_data.get("stargazers_count", 0)

        return repo_name, repo_description, star_count
    except requests.RequestException as e:
        print(f"Error querying GitHub API: {e}")
        return None, None, None

def get_github_author_info(author_url):
    username = author_url.split("https://github.com/")[-1]
    api_url = f"https://api.github.com/users/{username}"
    headers={
        "Accept": "application/vnd.github.v3+json",
        "Authorization": "Bearer {github_api_token}"
    }
    try:
        response = requests.get(api_url, headers=headers)  # Pass headers as a keyword argument
        response.raise_for_status()
        user_data = response.json()
        user_name = user_data.get("name")
        user_type = user_data.get("type")
        blog = user_data.get("blog") or "No website"
        bio = user_data.get("bio") or "No bio"
        location = user_data.get("location") or "No location"
        return user_name, user_type, blog, bio, location
    except requests.RequestException as e:
        print(f"Error fetching data for {username}: {e}")
        return None, None, "No website", "No bio", "No location"

# Function to push a row to Airtable
def push_to_airtable(row):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_ID}"
    headers = {
        "Authorization": f"Bearer {airtable_token}",
        "Content-Type": "application/json"
    }

     # Ensure Type and Status are lists for Airtable's multiple-choice fields
    type_value = row.get("Type", [])
    if not isinstance(type_value, list):
        type_value = [type_value] if type_value else []

    # Prepare the data payload
    data = {
        "fields": {
            "Repo": row.get("Repo"),
            "Repo_name": row.get("Repo_name"),
            "Repo_desc": row.get("Repo_desc"),
            "Star_count": row.get("Star_count"),
            "Author": row.get("Author"),
            "Name": row.get("Name"),
            "Type": type_value,
            "Website": row.get("Website"),
            "Bio": row.get("Bio"),
            "Location": row.get("Location"),
        }
    }

    # Send POST request to Airtable
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print(f"Successfully pushed row: {row['Repo']}")
    else:
        print(f"Failed to push row: {row['Repo']}, Error: {response.text}")


urls = scrape_urls(input_url)

# Step 2: Check for redirection to github.com
github_redirects = pd.DataFrame(columns=["Created_date", "Status" , "Repo", "Repo_name", "Repo_desc" , "Star_count" , "Author", "Name", "Type", "Website", "Bio", "Location"])
for url in urls:
    if not url.startswith("http"):
        url = requests.compat.urljoin(input_url, url)  # Handle relative URLs
    is_redirect, redirected_url = check_redirect_to_github(url)
    if is_redirect:
        is_repo, author, repo = is_github_repo(redirected_url)
        if is_repo:
            github_redirects = pd.concat([
                github_redirects, 
                pd.DataFrame([{"Created_date" : current_date , "Status" : "New" , "Repo": repo, "Author": author}])
            ], ignore_index=True)

for index, row in github_redirects.iterrows():
    if row['Author'] in exclusion_list:
        github_redirects.drop(index, inplace=True)


for index, row in github_redirects.iterrows():
    user_name, user_type, blog, bio, location = get_github_author_info(row['Author'])
    repo_name, repo_desc, star_count = query_github_repo(row['Repo'])
    github_redirects.at[index, 'Repo_name'] = repo_name
    github_redirects.at[index, 'Repo_desc'] = repo_desc
    github_redirects.at[index, 'Star_count'] = star_count  # Fixed the column name
    github_redirects.at[index, 'Name'] = user_name
    github_redirects.at[index, 'Type'] = user_type
    github_redirects.at[index, 'Website'] = blog
    github_redirects.at[index, 'Bio'] = bio
    github_redirects.at[index, 'Location'] = location

github_redirects['Star_count'] = pd.to_numeric(github_redirects['Star_count'], errors='coerce')

# Push each row in the DataFrame to Airtable
for _, row in github_redirects.iterrows():
    push_to_airtable(row)