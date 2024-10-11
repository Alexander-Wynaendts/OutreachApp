from .search_website_url import search_website_url
from .cbe_formatting import cbe_formatting
from .cbe_screening import cbe_screening

def main(files):

    print("="*60)
    print("⚠️ WARNING: Process will shut down after 4 hours!")
    print("If you see more than **5000** 'Nace Code Filter: ...' messages,")
    print("please contact the developer immediately to resolve the issue.")
    print("="*60)

    # Format the input files
    startup_data = cbe_formatting(files)

    # Print the number of filtered rows based on NACE code
    print(f"Nace Code Filter: {len(startup_data)}")

    # Limit the data to the first 100 rows for processing
    startup_data = startup_data[:50]

    # Check if startup_data is empty, return it if true
    if startup_data.empty:
        return startup_data

    # Apply CBE screening to the data
    startup_data = cbe_screening(startup_data)

    # Print the number of filtered rows after CBE screening
    print(f"CBE Screen Filter: {len(startup_data)}")

    # Check again if startup_data is empty, return it if true
    if startup_data.empty:
        return startup_data

    # Search for website URLs in the data
    startup_data = search_website_url(startup_data)

    return startup_data
