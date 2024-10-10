import openai
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import requests
import re
import os
from dotenv import load_dotenv
import time
from concurrent.futures import ThreadPoolExecutor

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
username = os.getenv("PROXY_USERNAME")
password = os.getenv("PROXY_PASSWORD")
proxy = os.getenv("PROXY_URL")
proxy_auth = "{}:{}@{}".format(username, password, proxy)
proxies = {
    'http': f'http://{proxy_auth}',
    'https': f'http://{proxy_auth}'
}

import warnings
warnings.filterwarnings("ignore")

def website_scraping(website_url, use_external_proxy=False):
    """
    Scrapes the content of the given website URL and extracts structured information.
    """
    important_tags = ['h1', 'h2', 'h3', 'p', 'ul', 'li', 'strong', 'em']  # Tags we want to extract
    structured_text = []

    try:
        # Make the HTML request with proxies
        response = requests.get(website_url, proxies=proxies, verify=False, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes
    except requests.exceptions.RequestException as e:
        return f"Failed to scrape the website. Error: {str(e)}"

    # Parse the page content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the page title
    page_title = soup.title.get_text(strip=True) if soup.title else "No Title"
    structured_text.append(f"H1: {page_title}")

    # Extract the meta description
    meta_description = soup.find('meta', attrs={'name': 'description'})
    if meta_description:
        structured_text.append(f"DESCRIPTION: {meta_description['content']}")

    # Extract important tags from the page
    for tag in soup.find_all(important_tags):
        if tag.name in ['h1', 'h2', 'h3']:
            structured_text.append(f"{tag.name.upper()}: {tag.get_text(strip=True)}")
        elif tag.name == 'p':
            text = tag.get_text(strip=True)
            if len(text) > 10:  # Only add meaningful paragraphs
                structured_text.append(f"PARAGRAPH: {text}")
        elif tag.name == 'ul':
            structured_text.append("LIST:")
        elif tag.name == 'li':
            structured_text.append(f"- {tag.get_text(strip=True)}")
        elif tag.name == 'strong':
            structured_text.append(f"**{tag.get_text(strip=True)}**")
        elif tag.name == 'em':
            structured_text.append(f"*{tag.get_text(strip=True)}*")

    return "\n".join(structured_text)

def website_links(website_url, use_external_proxy=False):
    """
    Scrapes the content of the given website URL and extracts structured information.
    """
    important_tags = ['h1', 'h2', 'h3', 'p', 'ul', 'li', 'strong', 'em']  # Tags to extract
    structured_text = []

    try:
        # Make the HTML request with proxies
        response = requests.get(website_url, proxies=proxies, verify=False, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes
    except requests.exceptions.RequestException as e:
        return f"Failed to scrape the website. Error: {str(e)}"

    # Parse the page content
    soup = BeautifulSoup(response.content, 'html.parser')
    
    links = set()

    # Extract the page title
    page_title = soup.title.get_text(strip=True) if soup.title else "No Title"
    structured_text.append(f"H1: {page_title}")

    # Extract the meta description
    meta_description = soup.find('meta', attrs={'name': 'description'})
    if meta_description:
        structured_text.append(f"DESCRIPTION: {meta_description['content']}")

    # Extract important tags from the page
    for tag_name in important_tags:
        for tag in soup.find_all(tag_name):
            if tag_name in ['h1', 'h2', 'h3']:
                structured_text.append(f"{tag_name.upper()}: {tag.get_text(strip=True)}")
            elif tag_name == 'p':
                text = tag.get_text(strip=True)
                if len(text) > 10:  # Only add meaningful paragraphs
                    structured_text.append(f"PARAGRAPH: {text}")
            elif tag_name == 'ul':
                structured_text.append("LIST:")
            elif tag_name == 'li':
                structured_text.append(f"- {tag.get_text(strip=True)}")
            elif tag_name == 'strong':
                structured_text.append(f"**{tag.get_text(strip=True)}**")
            elif tag_name == 'em':
                structured_text.append(f"*{tag.get_text(strip=True)}*")

    # Find all links on the page
    for link in soup.find_all('a', href=True):
        full_link = urljoin(website_url, link['href'])

        # Check if the link starts with the same website_url
        if full_link.startswith(website_url) and full_link != website_url and urlparse(full_link).path != '/':
            links.add(full_link)

    return "\n".join(structured_text), links

def gpt_link_selection(website_links):
    prompt = f"""
    From the following list of URLs on a company website, choose the 2 most relevant pages to determine if the company is a SaaS startup. Prioritize URLs that:

    - Clearly describe the company's product or services.
    - Provide information on pricing, subscription plans, or service delivery methods.
    - Include details about the types of clients the company serves.

    Ignore URLs related to blogs, careers, or unrelated marketing content.

    Return the top 2 URLs, each on a new line, with no additional text or formatting.

    **Link list**
    {website_links}
    """

    # Send the prompt to GPT-4o-mini
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract the full GPT response
    gpt_response = response['choices'][0]['message']['content'].strip()

    # Use regex to extract URLs (plain text only, no markdown)
    links = re.findall(r'(https?://[^\s]+)', gpt_response)

    # Return the top 2 links
    return links[:2]

def gpt_website_screen(website_data):
    prompt = f"""
    You are an expert in classifying companies product/service as "Software" or "Hardware" based on the following dictionary of website links and their corresponding content.
    The dictionary following dictionnary is structured as link1: content1, link2: content2, etc. Based on this data, determine if the company is primarily a Software or Hardware company.

    {website_data}

    Give a binary output:
    - "1" for a Software company
    - "0" for a Hardware company
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    gpt_analysis = response['choices'][0]['message']['content'].strip()
    gpt_answer = [char for char in gpt_analysis if char.isdigit()][-1]

    return gpt_answer, gpt_analysis

def website_screening(website_url):
    try:
        # Step 1: Scrape the landing page content and links
        website_page, link_list = website_links(website_url)

        # Step 2: Select the most relevant links using GPT
        selected_links = gpt_link_selection(link_list)

        # Step 3: Scrape all relevant website links and store in a dictionary
        website_data = {website_url: website_page}
        for selected_link in selected_links:
            link_content = website_scraping(selected_link)
            website_data[selected_link] = link_content

        if sum(len(value) for value in website_data.values()) < 1000:
            return "1", website_data

        # Step 4: Perform final GPT screening (or processing)
        website_screen, gpt_analysis = gpt_website_screen(website_data)
        return website_screen, website_data

    except Exception as e:
        return None, str(e)

def website_process_chunk(chunk, startup_data):
    """
    Process a chunk of 30 website URLs in parallel
    """
    def track_progress(website_url, idx):
        result = website_screening(website_url)
        return result

    # Create a ThreadPoolExecutor to parallelize the scraping and screening
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda url, idx: track_progress(url, idx), chunk['Website URL'], range(len(chunk))))
    return results

def parallel_website_screening(startup_data):
    """
    Running the scraping and GPT screening in parallel in chunks of 25
    """

    # Split the data into chunks of 25
    chunks = [startup_data.iloc[i:i + 25] for i in range(0, len(startup_data), 25)]
    all_results = []

    # Process each chunk, sleep between chunks
    for idx, chunk in enumerate(chunks):
        chunk_results = website_process_chunk(chunk, startup_data)
        all_results.extend(chunk_results)

        # Optional: sleep for a bit between chunks to avoid overloading resources
        if idx < len(chunks) - 1:
            time.sleep(60)

    # Convert results into two separate columns
    startup_data['GPT Website Screen'], startup_data['Website Data'] = zip(*all_results)

    return startup_data
