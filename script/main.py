from .search_website_url import search_website_url
from .cbe_formatting import cbe_formatting
from .cbe_screening import cbe_screening

def main(files):

    startup_data = cbe_formatting(files)

    startup_data = startup_data[:20]

    startup_data = cbe_screening(startup_data)

    #startup_data = search_website_url(startup_data)

    return startup_data
