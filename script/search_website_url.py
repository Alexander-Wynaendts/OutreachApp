import pandas as pd
import requests
import os
from dotenv import load_dotenv
import re
import warnings
from concurrent.futures import ThreadPoolExecutor
warnings.filterwarnings("ignore")

load_dotenv()
dataforseo_auth = os.getenv("DATAFORSEO_AUTH")
scrapin_api = os.getenv("SCRAPIN_API")

def linkedin_founder_scrape(founder_name):
    # Prepare a list to store the formatted data
    linkedin_founder_profile = []

    query = f"site: be.linkedin.com/in/ '{founder_name}'"

    url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"

    # Correct the payload format
    payload = f"[{{\"keyword\":\"{query}\", \"location_code\":2826, \"language_code\":\"en\", \"device\":\"desktop\", \"depth\":5}}]".encode('utf-8')

    headers = {
        'Authorization': f'Basic {dataforseo_auth}',  # Using the API key from .env
        'Content-Type': 'application/json'
    }
    # Send the POST request to the API
    response = requests.request("POST", url, headers=headers, data=payload)
    # Check if the response is successful
    if response.json()["status_code"] == 20000:
        json_data = response.json()
        items = json_data['tasks'][0]['result'][0]['items']

    else:
        # Return default values on failure
        linkedin_founder_profile.append({
            'LinkedIn Title': "-",
            'LinkedIn Description': "-",
            'LinkedIn URL': "-"
        })
        return linkedin_founder_profile


    for item in items:
        if item:  # Ensure the item is not None
            linkedin_title = item.get('title', '-')
            linkedin_description = item.get('description', '-')
            linkedin_url = item.get('url', '-')
        else:
            linkedin_title = linkedin_description = linkedin_url = "-"

        # Append the extracted data to the linkedin_founder_profile list
        linkedin_founder_profile.append({
            'LinkedIn Title': linkedin_title,
            'LinkedIn Description': linkedin_description,
            'LinkedIn URL': linkedin_url
        })

    return linkedin_founder_profile

def founder_website_retrieval(linkedin_url):
    # Define the Scrapin API URL
    url = "https://api.scrapin.io/enrichment/profile"
    querystring = {
        "apikey": scrapin_api,
        "linkedInUrl": linkedin_url
    }
    response = requests.get(url, params=querystring)

    # Check if the response is valid
    if response.status_code == 200:
        json_data = response.json()
        # Safeguard against missing 'company' key in the JSON response
        if json_data and json_data["company"]:
            linkedin_company_url = json_data["company"].get("linkedInUrl", "")
            website_url = json_data["company"].get("websiteUrl", "")
            return linkedin_company_url, website_url
        else:
            # Return empty values if no company data found
            return "-", "-"
    else:
        # Handle the case where the API request fails or the response is invalid
        return "-", "-"

def linkedin_google_scrape(enterprise_name, founder_names):
    def normalize(text):
        return re.sub(r'[\s\-]+', '', text.lower())

    terms_to_check = [
    # English
    'entrepreneur', 'founder',
    # French
    'entrepreneur', 'fondateur',
    # Dutch
    'ondernemer', 'oprichter',
    # German
    'unternehmer', 'gründer',
]

    linkedin_founder_profiles = []
    linkedin_company_url = None
    website_url = None
    term_matched_profile = None

    # Process each founder's name
    for founder_name in founder_names.split(', '):
        founder_profiles = linkedin_founder_scrape(founder_name)

        # Skip if no profiles found or empty response
        if not founder_profiles or founder_profiles == "-":
            continue

        for profile in founder_profiles:
            if profile:
                linkedin_title = profile.get('LinkedIn Title', '-')
                linkedin_description = profile.get('LinkedIn Description', '-')
                linkedin_url = profile.get('LinkedIn URL', '-')

                profile_text = f"{linkedin_title} {linkedin_description}"
                normalized_profile_text = normalize(profile_text)

                # First check: if enterprise_name is in the title or description
                if normalize(enterprise_name) in normalized_profile_text:
                    linkedin_founder_profiles.append({
                        'LinkedIn Title': linkedin_title,
                        'LinkedIn Description': linkedin_description,
                        'LinkedIn URL': linkedin_url
                    })
                    linkedin_company_url, website_url = founder_website_retrieval(linkedin_url)
                    break

                # Second check: if any term from terms_to_check is in the title or description
                elif any(normalize(term) in normalized_profile_text for term in terms_to_check):
                    linkedin_founder_profiles.append({
                        'LinkedIn Title': linkedin_title,
                        'LinkedIn Description': linkedin_description,
                        'LinkedIn URL': linkedin_url
                    })
                    # Store the first profile that matches
                    if term_matched_profile is None:
                        term_matched_profile = profile

    # If no match found, use the first matched profile based on terms
    if not linkedin_company_url:
        if term_matched_profile:
            linkedin_company_url, website_url = founder_website_retrieval(term_matched_profile['LinkedIn URL'])
        else:
            linkedin_founder_profiles = "-"
            linkedin_company_url = "-"
            website_url = "-"

    return linkedin_founder_profiles, linkedin_company_url, website_url

def search_website_url(startup_data):
    # Split the data into rows with and without website URLs
    data_with_no_website = startup_data[startup_data['Website URL'].isna()]
    data_with_website = startup_data[startup_data['Website URL'].notna()]

    def process_row(row_tuple):
        index, row = row_tuple
        name = row['Name']
        founders_name = row['Founders Name']
        linkedin_data = linkedin_google_scrape(name, founders_name)
        return linkedin_data

    # Process each row without a website URL
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(process_row, data_with_no_website.iterrows()))

    # Convert the results into a DataFrame
    results_df = pd.DataFrame(results, columns=["LinkedIn Founder", "LinkedIn URL", "Website URL"])

    # Assign the new values (LinkedIn Founder, LinkedIn URL, and Website URL) to the corresponding rows
    data_with_no_website.reset_index(drop=True, inplace=True)
    data_with_no_website['LinkedIn Founder'] = results_df['LinkedIn Founder']
    data_with_no_website['LinkedIn URL'] = results_df['LinkedIn URL']
    data_with_no_website['Website URL'] = results_df['Website URL']

    # Combine the rows with existing Website URLs and newly updated rows
    startup_data = pd.concat([data_with_website, data_with_no_website], ignore_index=True)

    return startup_data
