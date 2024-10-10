import requests
from urllib.parse import urlparse, urlunparse
import re

import warnings
warnings.filterwarnings("ignore")

def check_csv_format(startup_data):
    """
    Validates the format of the CSV file by ensuring required columns are present.
    Prints an error message if invalid, otherwise returns the filtered DataFrame.
    """
    required_columns = ["Name", "Website URL"]

    # Check for missing columns
    missing_columns = [col for col in required_columns if col not in startup_data.columns]
    if missing_columns:
        print(f"CSV not well formatted: Missing column(s): [{', '.join(missing_columns)}]")
        return None  # Return None to indicate failure

    # Return DataFrame with only required columns
    return startup_data[required_columns]

def update_missing_urls(startup_data):
    """
    Checks and updates missing or invalid 'Website URL' entries in a DataFrame,
    and removes language variants from URLs. Prints an error message if there are issues.
    """
    invalid_companies = []
    url_pattern = re.compile(r'^(http|https)://')
    www_pattern = re.compile(r'^www\..+\..+$')  # Matches URLs starting with 'www.' and ending with '.something'
    domain_pattern = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')  # Matches URLs like 'company.com'

    for idx, row in startup_data.iterrows():
        website_url = row["Website URL"]
        company_name = row["Name"]

        # Check if 'Website URL' is a valid string
        if isinstance(website_url, str):
            # If it starts with 'http' or 'https', assume it's valid
            if url_pattern.match(website_url):
                # Clean URL to remove any path (like /en, /nl)
                parsed_url = urlparse(website_url)
                clean_url = urlunparse((parsed_url.scheme, parsed_url.netloc, '', '', '', ''))
                startup_data.at[idx, "Website URL"] = clean_url
                continue

            # If it starts with 'www.' and ends with '.something', prepend 'https://'
            elif www_pattern.match(website_url):
                clean_url = f"https://{website_url.split('/')[0]}"  # Only take the base domain
                startup_data.at[idx, "Website URL"] = clean_url
                continue

            # If it matches a domain like 'company.com', prepend 'https://www.'
            elif domain_pattern.match(website_url):
                startup_data.at[idx, "Website URL"] = f"https://www.{website_url.split('/')[0]}"
                continue

        # Handle missing or invalid URLs
        if not isinstance(website_url, str) or not domain_pattern.match(website_url):
            potential_url = f"http://{company_name.lower().replace(' ', '')}.com" if '.' not in company_name else None

            if potential_url:
                try:
                    response = requests.get(potential_url)
                    if response.status_code == 200:
                        startup_data.at[idx, "Website URL"] = potential_url
                    else:
                        invalid_companies.append(company_name)
                except requests.RequestException:
                    invalid_companies.append(company_name)
            else:
                invalid_companies.append(company_name)

    # Print companies with invalid/missing URLs or return the updated DataFrame
    if invalid_companies:
        print(f"Invalid URLs for the following companies: [{', '.join(invalid_companies)}] please add or delete the row")
        return None  # Return None to indicate failure

    return startup_data

def data_formatting(startup_data):
    """
    Main function to format and validate the startup_data.
    """
    # Step 1: Check CSV format
    formatted_data = check_csv_format(startup_data)
    if formatted_data is None:
        return  # Stop if there's a format error

    # Step 2: Update missing URLs
    formatted_data = update_missing_urls(formatted_data)
    if formatted_data is None:
        return  # Stop if there are invalid URLs

    return formatted_data
