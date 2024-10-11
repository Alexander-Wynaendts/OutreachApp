import requests
from bs4 import BeautifulSoup

import os
from dotenv import load_dotenv

import time
import random
import re
from concurrent.futures import ThreadPoolExecutor

load_dotenv()
username = os.getenv("PROXY_USERNAME")
password = os.getenv("PROXY_PASSWORD")
proxy = os.getenv("PROXY_URL")
proxy_auth = "{}:{}@{}".format(username, password, proxy)
proxies = {
    "http": "http://{}".format(proxy_auth),
    "https": "http://{}".format(proxy_auth)
}
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

def cbe_page_scraping(enterprise_number):
    """
    Scrape the CBE website for a given enterprise_number using requests and a proxy.
    """

    website_url = f"https://kbopub.economie.fgov.be/kbopub/zoeknummerform.html?nummer={enterprise_number}"

    try:
        # Make a request to the website using the proxy
        response = requests.get(website_url, headers=headers, timeout=10)

        # Parse the page content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Check for CAPTCHA
        captcha_header = soup.find('h3')
        if captcha_header and "CAPTCHA Test" in captcha_header.get_text():
            print(f"Captcha detected, retrying in 60 seconds...")
            time.sleep(60)
            return "-"

        # Check if the table with id 'table' is present
        table = soup.find('div', {'id': 'table'})
        if not table:
            return "-"

        # Extract data from the table
        enterprise_data = []
        current_section = None

        rows = table.find_all('tr')
        for row in rows:
            section_header = row.find('h2')
            if section_header:
                current_section = section_header.get_text(strip=True)
                enterprise_data.append(f"\n=== {current_section} ===\n")
                continue

            cols = row.find_all('td')
            if len(cols) == 1 and current_section:
                value = cols[0].get_text(separator=' ').strip()
                if value:
                    enterprise_data.append(f"{value}")
            elif len(cols) >= 2:
                key = cols[0].get_text(separator=' ').strip()
                value = cols[1].get_text(separator=' ').strip()
                if key and value:
                    enterprise_data.append(f"{key}: {value}")

        # Return the structured data
        cbe_info = "\n".join(enterprise_data)
        return cbe_info

    except requests.exceptions.RequestException as e:
        print(f"Error occurred while scraping: {e}")
        return "-"

def cbe_data_extraction(cbe_info):
    """
    Extracts the enterprise's trade name or legal name, founder names, email, website info, and founding year from the CBE information.
    If the website is not available but the email is, it extracts the domain from the email to use as the website.
    """
    enterprise_name = None
    email = None
    website = None
    founding_year = None

    # Extract the trade name (Commerciële Naam) if available
    name_match = re.search(r'Naam.*::\s*(.*)', cbe_info)
    if name_match:
        # Extract the name and stop at the first occurrence of 'Sinds', 'Naam', or 'Taal'
        enterprise_name = re.split(r'\s*(Sinds|Naam|Taal)\s*', name_match.group(1).strip())[0].strip()

    # Extract founder names from "Functies" section
    founder_names = []
    functies_section_match = re.search(r'=== Functies ===(.*?)===', cbe_info, re.DOTALL)
    if functies_section_match:
        for line in functies_section_match.group(1).splitlines():
            if ':' in line:
                name_part = line.split(':', 1)[1].strip()
                if ',' in name_part:
                    last_name, first_name = map(str.strip, name_part.split(',', 1))
                    founder_names.append(f"{first_name} {last_name}")

    # Extract email if available
    email_match = re.search(r'E-mail::\s*([^\s]+)', cbe_info)
    if email_match and '@' in email_match.group(1):
        email = email_match.group(1).strip()

    # Extract website if available
    website_match = re.search(r'Webadres::\s*([^\s]+)', cbe_info)
    if website_match and re.search(r'\.\w{2,}', website_match.group(1)):
        website = website_match.group(1).strip()

    # If no website is found, use the domain part of the email
    if not website and email and '@' in email:
        domain = email.split('@')[1]
        if domain not in ["gmail.com", "hotmail.com", "yahoo.com"]:
            website = f"http://www.{domain}"

    # Extract the founding year from "Begindatum::"
    begindatum_match = re.search(r'Begindatum::\s*(\d{1,2}\s*[a-zA-Z]+\s*\d{4})', cbe_info)
    if begindatum_match:
        # Extract the year from the date
        founding_year = re.search(r'\d{4}', begindatum_match.group(1)).group()

    return enterprise_name, founder_names, email, website, founding_year

def cbe_analysis(enterprise_number):
    """
    Analyze a given enterprise number. If scraping fails on the first attempt,
    retry once after sleeping for 5 seconds. Print a message if the second attempt is successful.
    """

    # First attempt to scrape
    cbe_info = cbe_page_scraping(enterprise_number)

    # Check if the first attempt was successful
    if not cbe_info or cbe_info == "-":
        # If it fails, wait for 5 seconds and retry
        print(f"First attempt failed, retrying in 5 seconds...")
        time.sleep(5)

        # Second attempt to scrape
        cbe_info = cbe_page_scraping(enterprise_number)

        # If the second attempt succeeds, print a reassuring message
        if cbe_info and cbe_info != "-":
            print("Success on the second attempt. Moving forward.")
        else:
            return (enterprise_number, "-", None, None, None, None, None)

    # Extract enterprise name, founder names, email, website, and founding year
    enterprise_name, founder_names, email, website, founding_year = cbe_data_extraction(cbe_info)

    if not founder_names:  # Check if the list is empty or None
        return (enterprise_number, None, None, None, None, None, None)

    # Check if any founder's last name is in the company name
    enterprise_name_lower = enterprise_name.lower()
    for full_name in founder_names:
        last_name = full_name.split()[-1].lower()  # Extract the last name of the founder
        if last_name in enterprise_name_lower:
            return (enterprise_number, None, None, None, None, None, None)

    # Check if the founding year is older than 2019
    if founding_year and int(founding_year) < 2019:
        return (enterprise_number, None, None, None, None, None, None)

    return (enterprise_number, enterprise_name, cbe_info, email, website, founder_names, founding_year)

import time
import random
from concurrent.futures import ThreadPoolExecutor

def cbe_screening(startup_data):
    """
    Process each startup based on the given enterprise number in parallel using ThreadPoolExecutor.
    It returns the CBE info, website, email, and founding year if it's a valid startup.
    The startup_data is assumed to be a DataFrame or dictionary-like object containing the 'EntityNumber' of the startups.
    """

    all_results = []

    # Define a helper function for processing each row
    def process_enterprise(enterprise_number):
        # Simulating a delay for each request
        time.sleep(random.uniform(10, 30))  # Random sleep between 1 and 3 seconds
        return cbe_analysis(enterprise_number)

    # Use ThreadPoolExecutor to process each enterprise in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Display progress while processing each startup
        all_results = []
        for idx, result in enumerate(executor.map(process_enterprise, startup_data['EntityNumber'])):
            all_results.append(result)
            print(f"Progress: {idx + 1}/{len(startup_data)}")  # Display progress

    # Prepare to update the DataFrame with the results
    rows_to_drop = []
    for result in all_results:
        enterprise_number, enterprise_name, cbe_info, email, website_url, founder_names, founding_year = result
        if cbe_info is None:
            rows_to_drop.append(enterprise_number)
        else:
            # Update the DataFrame with the valid results
            startup_data.loc[startup_data["EntityNumber"] == enterprise_number, "CBE Info"] = cbe_info
            startup_data.loc[startup_data["EntityNumber"] == enterprise_number, "Name"] = enterprise_name
            startup_data.loc[startup_data["EntityNumber"] == enterprise_number, "Email"] = email
            startup_data.loc[startup_data["EntityNumber"] == enterprise_number, "Website URL"] = website_url
            startup_data.loc[startup_data["EntityNumber"] == enterprise_number, "Founders Name"] = ', '.join(founder_names)
            startup_data.loc[startup_data["EntityNumber"] == enterprise_number, "Founding Year"] = founding_year

    # Drop the rows where (enterprise_number, None, None, None, None) was returned
    startup_data = startup_data[~startup_data['EntityNumber'].isin(rows_to_drop)]

    return startup_data
