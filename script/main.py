import pandas as pd
import re
from google_scrape import google_scrape
import asyncio
import warnings
warnings.filterwarnings("ignore")

def linkedin_founder_scrape(founder_name):

    query = f"site: linkedin.com/in/ '{founder_name}'"
    url = f"https://www.google.com/search?q={query}"

    # Appeler la fonction asynchrone google_scrape et attendre le résultat
    soup = asyncio.run(google_scrape(url))

    # Initialize title, description, and LinkedIn URL
    linkedin_title = ""
    linkedin_description = ""
    linkedin_url = ""

    # Extract the headline (title) of the result
    title_div = soup.select('div.BNeawe.vvjwJb.AP7Wnd.UwRFLe')
    if title_div:
        linkedin_title = title_div[0].get_text()

    # Extract the description of the result
    description_div = soup.select('div.BNeawe.s3v9rd.AP7Wnd')
    if description_div:
        linkedin_description = description_div[0].get_text()

    # Extract the first LinkedIn result
    search_results = soup.select('div.BNeawe.UPmit.AP7Wnd.lRVwie')
    for result in search_results:
        text = result.get_text()
        # Check if the text contains a LinkedIn domain and a username
        if 'linkedin.com' in text:
            try:
                # Split the text into domain and username
                domain, username = text.split(' › ')
                domain = domain.strip()  # Clean the domain
                username = username.strip()  # Clean the username

                # Construct the full LinkedIn URL
                linkedin_url = f"https://{domain}/in/{username}/"
                break
            except ValueError:
                # Handle cases where the text does not split as expected
                continue

    # Ajouter les résultats pour chaque fondateur
    linkedin_founder_profile = {
        'Name': founder_name,
        'LinkedIn Title': linkedin_title,
        'LinkedIn Description': linkedin_description,
        'LinkedIn URL': linkedin_url
    }
    return linkedin_founder_profile

def linkedin_company_scrape(key_word):
    linkedin_company_profiles = []  # List to store the results

    # Construct the Google query to search for the LinkedIn company page
    query = f"site:be.linkedin.com/company/ '{key_word}'"
    url = f"https://www.google.com/search?q={query}"

    soup = asyncio.run(google_scrape(url))

    # Initialize title, description, and URL
    linkedin_title = ""
    linkedin_description = ""
    linkedin_url = ""

    # Extract the headline (title) of the result
    title_div = soup.select('div.BNeawe.vvjwJb.AP7Wnd.UwRFLe')
    if title_div:
        linkedin_title = title_div[0].get_text()

    # Extract the description of the result
    description_div = soup.select('div.BNeawe.s3v9rd.AP7Wnd')
    if description_div:
        linkedin_description = description_div[0].get_text()

    # Extract the first LinkedIn company result
    search_results = soup.select('div.BNeawe.UPmit.AP7Wnd.lRVwie')
    for result in search_results:
        text = result.get_text()
        # Check if the text contains a LinkedIn domain for companies
        if 'linkedin.com' in text:
            try:
                # Split the text into domain and company name
                parts = text.split(' › ')
                domain = parts[0].strip()  # Clean the domain
                company_path = parts[2].split(' › ')[0].strip()  # Clean the company name/path

                # Construct the full LinkedIn company URL
                linkedin_url = f"https://{domain}/company/{company_path}/"
                break
            except ValueError:
                    # Handle cases where the text does not split as expected
                    continue

    # Add the results to the list of LinkedIn company profiles
    linkedin_company_profile = {
        'Keyword': key_word,
        'LinkedIn Name': linkedin_title,
        'LinkedIn Description': linkedin_description,
        'LinkedIn URL': linkedin_url
    }

    return linkedin_company_profile

def linkedin_google_scrape(enterprise_name, founder_names):
    """
    Scrapes LinkedIn founder profiles, checks for relevant terms, and matches the enterprise name.
    Based on the results, scrapes LinkedIn for the company or the best matching founder profile.
    Updates and returns the row with new LinkedIn information.
    """

    # Helper function to normalize text: remove spaces, special characters, accents, and convert to lowercase
    def normalize(text):
        return re.sub(r'[\s\-]+', '', text.lower())

    linkedin_founder_profiles = []
    linkedin_company_profile = None

    # List of terms to check for in the profiles
    terms_to_check = ['entrepreneur', 'founder', 'ceo', 'cto', enterprise_name]

    for founder_name in founder_names.split(', '):
        # Scrape LinkedIn profiles for each founder
        linkedin_founder_profile = linkedin_founder_scrape(founder_name)

        # Check if the result from linkedin_founder_scrape is a string (i.e., an error message)
        if isinstance(linkedin_founder_profile, str):
            return None, None

        if isinstance(linkedin_founder_profile, dict):
            profile_text = f"{linkedin_founder_profile['LinkedIn Title']} {linkedin_founder_profile['LinkedIn Description']}"
        else:
            print(f"Error: Expected a dictionary but got {type(linkedin_founder_profile)}: {linkedin_founder_profile}")
            continue

        # Normalize the profile text
        normalized_profile_text = normalize(profile_text)

        # Count the number of matching terms in the profile text
        term_matches = sum(normalize(term) in normalized_profile_text for term in terms_to_check)

        # Only add the profile to linkedin_founder_profiles if there is at least 1 term match
        if term_matches > 0:
            linkedin_founder_profiles.append(linkedin_founder_profile)

    # Track the profile with the most matches and check if the enterprise name is found
    best_profile = None
    max_term_matches = 0
    enterprise_name_found = False

    # Iterate through profiles and find the one with the most matching terms
    for profile in linkedin_founder_profiles:
        profile_text = f"{profile['LinkedIn Title']} {profile['LinkedIn Description']}"
        normalized_profile_text = normalize(profile_text)

        # If enterprise name is found, set the flag
        if normalize(enterprise_name) in normalized_profile_text:
            enterprise_name_found = True

        # Count the number of matching terms in the profile text
        term_matches = sum(normalize(term) in normalized_profile_text for term in terms_to_check)

        # Track the profile with the highest term match count
        if term_matches > max_term_matches:
            best_profile = profile
            max_term_matches = term_matches

    # Scrape LinkedIn based on the conditions
    if enterprise_name_found:
        linkedin_company_profile = linkedin_company_scrape(enterprise_name)
    elif best_profile:
        linkedin_company_profile = linkedin_company_scrape(best_profile['Name'])
    else:
        linkedin_company_profile = linkedin_company_scrape(enterprise_name)

    print(linkedin_founder_profiles, linkedin_company_profile)

    return linkedin_founder_profiles, linkedin_company_profile

linkedin_google_scrape("Entourage", "Stephan King, Alexandre Demain, Alexander Wynaendts")
