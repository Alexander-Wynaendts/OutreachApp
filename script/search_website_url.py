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
    query = f"site:linkedin.com/in/ '{founder_name}'"

    url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"

    # Correct the payload format
    payload = f"[{{\"keyword\":\"{query}\", \"location_code\":2826, \"language_code\":\"en\", \"device\":\"desktop\", \"depth\":10}}]"

    headers = {
        'Authorization': f'Basic {dataforseo_auth}',  # Using the API key from .env
        'Content-Type': 'application/json'
    }
    # Send the POST request to the API
    response = requests.request("POST", url, headers=headers, data=payload)

    # Extract items from the API response
    items = response.json()['tasks'][0]['result'][0]['items']

    # Prepare a list to store the formatted data
    linkedin_founder_profile = []

    # Loop through each item in the 'items' list
    for item in items:
        # Extract the LinkedIn title, description, and URL
        linkedin_title = item.get('title')
        linkedin_description = item.get('description')
        linkedin_url = item.get('url')

        # Append the extracted data to the linkedin_founder_profile list as a dictionary
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

    linkedin_company_url = response.json()["company"]["linkedInUrl"]
    website_url = response.json()["company"]["websiteUrl"]

    return linkedin_company_url, website_url

def linkedin_google_scrape(enterprise_name, founder_names):
    # Helper function to normalize text: remove spaces, special characters, accents, and convert to lowercase
    def normalize(text):
        return re.sub(r'[\s\-]+', '', text.lower())

    # Initialize terms to check in profiles
    terms_to_check = ['entrepreneur', 'founder']

    linkedin_founder_profiles = []
    linkedin_company_url = None
    website_url = None
    term_matched_profile = None  # Store the first profile that matches terms_to_check

    # Step 2: Run every founder_name through linkedin_founder_scrape
    for founder_name in founder_names.split(', '):
        print(f"Processing: {founder_name}")
        # Scrape LinkedIn profiles for each founder
        founder_profiles = linkedin_founder_scrape(founder_name)

        # Check if the result is valid
        if isinstance(founder_profiles, str):
            continue  # Skip this founder if the scrape returned an error message or string

        # Add valid profiles to the list in the desired format
        for profile in founder_profiles:
            linkedin_title = profile.get('LinkedIn Title', '')
            linkedin_description = profile.get('LinkedIn Description', '')
            linkedin_url = profile.get('LinkedIn URL', '')

            profile_text = f"{linkedin_title} {linkedin_description}"
            normalized_profile_text = normalize(profile_text)

            # First check: if enterprise_name is in the title or description
            if normalize(enterprise_name) in normalized_profile_text:
                print(f"NAME MATCH {linkedin_url}")
                linkedin_founder_profiles.append({
                    'LinkedIn Title': linkedin_title,
                    'LinkedIn Description': linkedin_description,
                    'LinkedIn URL': linkedin_url
                })
                # Run website retrieval for the first profile that matches the enterprise_name
                linkedin_company_url= "yes.om"
                #linkedin_company_url, website_url = founder_website_retrieval(linkedin_url)
                break  # Stop once we find a match with the enterprise_name

            # Second check: if any term from terms_to_check is in the title or description
            elif any(normalize(term) in normalized_profile_text for term in terms_to_check):
                print(f"TERM MATCH {linkedin_url}")
                linkedin_founder_profiles.append({
                    'LinkedIn Title': linkedin_title,
                    'LinkedIn Description': linkedin_description,
                    'LinkedIn URL': linkedin_url
                })
                # Store the first profile that matches a term from terms_to_check
                if term_matched_profile is None:
                    term_matched_profile = profile

    # After adding all linkedin_founder_profiles, check if no enterprise_name was found and use term match
    if linkedin_company_url is None and term_matched_profile:
        print(f"Using TERM MATCH {term_matched_profile['LinkedIn URL']} for website retrieval")
        #linkedin_company_url, website_url = founder_website_retrieval(term_matched_profile['LinkedIn URL'])

    # Step 3: If no profiles contained the enterprise name or any terms from terms_to_check, set a fallback
    if not linkedin_founder_profiles:
        linkedin_company_url = f"site:linkedin.com/in/ '{enterprise_name}'"

    # Step 4: Return only the profiles where the title or description contain terms_to_check or enterprise_name
    return linkedin_founder_profiles, linkedin_company_url, website_url

def search_website_url(startup_data):
    # Split the data into rows with and without website URLs
    data_with_no_website = startup_data[startup_data['Website'].isna()]
    data_with_website = startup_data[startup_data['Website'].notna()]

    # Define a helper function to process each row
    def process_row(row):
        name = row['Name']
        founders_name = row['Founders Name']
        # Call your linkedin_google_scrape function with the appropriate parameters
        linkedin_data = linkedin_google_scrape(name, founders_name)
        return linkedin_data

    # Use ThreadPoolExecutor to parallelize scraping
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(process_row, data_with_no_website.iterrows()))

    # Convert the results back into DataFrame format and assign back to data_with_no_website
    results_df = pd.DataFrame(results, columns=["LinkedIn Founder", "LinkedIn URL", "Website URL"])
    data_with_no_website = pd.concat([data_with_no_website.reset_index(drop=True), results_df], axis=1)

    # Combine the original data with website URLs and the new scraped data
    startup_data = pd.concat([data_with_website, data_with_no_website], ignore_index=True)

    return startup_data
