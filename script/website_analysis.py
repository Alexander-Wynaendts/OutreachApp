import openai
from concurrent.futures import ThreadPoolExecutor
import time
import ast
import re
import os
from dotenv import load_dotenv
import warnings

warnings.filterwarnings("ignore")

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def gpt_enterprise_analysis(website_data):
    prompt = f"""
    You are an expert in analyzing companies based on the following dictionary of website links and their corresponding content. You are provided with a company's website scraped content stored in the following dictionary format (link1:content1, link2:content2, ...):

    {website_data}

    Analyze the content and return the following details in the exact format specified:

    Product/Service: <One-sentence description of the company’s main product or service>
    Industry: <Industry>
    Client Type: <B2B or B2C>
    Revenue Model: <Revenue model>
    Market Region: <Market region>
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    gpt_analysis = response['choices'][0]['message']['content'].strip()

    description_match = re.search(r"Product/Service: (.+?)\n", gpt_analysis)
    industry_match = re.search(r"Industry: (.+?)\n", gpt_analysis)
    client_match = re.search(r"Client Type: (.+?)\n", gpt_analysis)
    revenue_match = re.search(r"Revenue Model: (.+?)\n", gpt_analysis)
    region_match = re.search(r"Market Region: (.+?)(?:\n|$)", gpt_analysis)

    formated_analysis = {
        "GPT Description": description_match.group(1) if description_match else "N.A.",
        "GPT Industry": industry_match.group(1) if industry_match else "N.A.",
        "GPT Client Type": client_match.group(1) if client_match else "N.A.",
        "GPT Revenue Model": revenue_match.group(1) if revenue_match else "N.A.",
        "GPT Region": region_match.group(1) if region_match else "N.A.",
    }

    return gpt_analysis, formated_analysis

def website_analysis_process(startup_data):
    """
    Running the GPT analysis in parallel for filtered SaaS data.
    """

    def track_progress(website_data, idx):
        """
        Perform GPT analysis with rate limiting and retry mechanism.
        """
        try:
            gpt_analysis, formated_analysis = gpt_enterprise_analysis(website_data)
            return gpt_analysis, formated_analysis
        except openai.error.RateLimitError:
            print(f"Rate limit reached, retrying after 5 seconds...")
            time.sleep(5)
            return track_progress(website_data, idx)
        except Exception as e:
            print(f"Error on index {idx}: {e}")
            return None, None

    # Apply the transformation to the 'Website Data' column
    startup_data['Website Data'] = startup_data['Website Data'].apply(str)

    # Iterate over all companies in `startup_data`
    for index, row in startup_data.iterrows():
        # Case 1: If 'GPT Website Screen' is 0, mark fields as "Not SaaS"
        if row['GPT Website Screen'] == "0":
            startup_data.at[index, 'GPT Raw Analysis'] = "Not SaaS"
            startup_data.at[index, 'GPT Description'] = "Not SaaS"
            startup_data.at[index, 'GPT Industry'] = "Not SaaS"
            startup_data.at[index, 'GPT Client Type'] = "Not SaaS"
            startup_data.at[index, 'GPT Revenue Model'] = "Not SaaS"
            startup_data.at[index, 'GPT Region'] = "Not SaaS"

        # Case 2: If Website Data length is <= 1000, mark fields as "No Data"
        elif len(row['Website Data']) <= 1000:
            startup_data.at[index, 'GPT Raw Analysis'] = "No Data"
            startup_data.at[index, 'GPT Description'] = "No Data"
            startup_data.at[index, 'GPT Industry'] = "No Data"
            startup_data.at[index, 'GPT Client Type'] = "No Data"
            startup_data.at[index, 'GPT Revenue Model'] = "No Data"
            startup_data.at[index, 'GPT Region'] = "No Data"

    # Filter only SaaS companies with sufficient data (Website Data length > 1000)
    saas_data = startup_data[(startup_data['GPT Website Screen'] == "1") &
                             (startup_data['Website Data'].apply(lambda x: len(x) > 1000))]

    # Create a ThreadPoolExecutor to parallelize the GPT analysis
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(track_progress, saas_data['Website Data'], range(len(saas_data))))

    # Add GPT analysis to `startup_data` for SaaS companies
    for i, (gpt_analysis, formated_analysis) in enumerate(results):
        if gpt_analysis and formated_analysis:
            index = saas_data.index[i]
            startup_data.at[index, 'GPT Raw Analysis'] = gpt_analysis
            startup_data.at[index, 'GPT Description'] = formated_analysis['GPT Description']
            startup_data.at[index, 'GPT Industry'] = formated_analysis['GPT Industry']
            startup_data.at[index, 'GPT Client Type'] = formated_analysis['GPT Client Type']
            startup_data.at[index, 'GPT Revenue Model'] = formated_analysis['GPT Revenue Model']
            startup_data.at[index, 'GPT Region'] = formated_analysis['GPT Region']

    # Drop unnecessary columns and save final version
    startup_data = startup_data.drop(columns=['GPT Website Screen', 'GPT Raw Analysis'])

    return startup_data
