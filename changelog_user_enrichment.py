import requests
from bs4 import BeautifulSoup
import re
import time

# Function to extract patterns from the page and update Airtable
def extract_links(url, record_id, api_key, base_id, table_name):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    page_text = soup.get_text()

    # Regular expressions for LinkedIn and X patterns
    linkedin_pattern = re.compile(r'in/([\w-]+)')  # Updated to capture hyphens
    x_pattern = re.compile(r'@([\w-]+)')  # Updated to capture hyphens

    # Finding all matches
    linkedin_matches = linkedin_pattern.findall(page_text)
    x_matches = x_pattern.findall(page_text)

    # Preparing URLs
    linkedin_urls = [f"https://www.linkedin.com/in/{match}/" for match in linkedin_matches]
    x_urls = [f"https://x.com/{match}" for match in x_matches]

    # Printing the full URLs
    for url in linkedin_urls:
        print(f"linkedin = {url}")
    for url in x_urls:
        print(f"x = {url}")

    # Check existing LinkedIn and X fields before updating
    airtable_url = f"https://api.airtable.com/v0/{base_id}/{table_name}/{record_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(airtable_url, headers=headers)
        response.raise_for_status()
        record_data = response.json()

        existing_linkedin = record_data['fields'].get('LinkedIn', '')
        existing_x = record_data['fields'].get('X', '')

        if not existing_linkedin and not existing_x:
            update_data = {
                "fields": {
                    "LinkedIn": ", ".join(linkedin_urls),
                    "X": ", ".join(x_urls)
                }
            }
            requests.patch(airtable_url, json=update_data, headers=headers)
        else:
            print(f"Skipping record {record_id} as LinkedIn or X already exists.")

    except requests.RequestException as e:
        print(f"Error updating Airtable record {record_id}: {e}")

# Function to fetch URLs from Airtable
def get_airtable_urls(api_key, base_id, table_name):
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching Airtable data: {e}")
        return []

    records = response.json().get('records', [])
    print(records)

    # Filter records where Status is exactly 'New' and Type is exactly ['User']
    records_to_process = [
        (record['id'], record['fields'].get('Author'))
        for record in records
        if record['fields'].get('Status') == 'New' and record['fields'].get('Type') == ['User']
    ]
    return records_to_process

# Main function to process URLs from Airtable
if __name__ == "__main__":
    API_KEY = os.getenv("TOKEN_AIRTABLE")
    BASE_ID = 'appKhM4requBnJGOc'
    TABLE_NAME = 'tbliWzB2T9dTEJJRD'

    records = get_airtable_urls(API_KEY, BASE_ID, TABLE_NAME)
    print(records)
    for record_id, url in records:
        if url:
            print(url)
            extract_links(url, record_id, API_KEY, BASE_ID, TABLE_NAME)
            time.sleep(2)