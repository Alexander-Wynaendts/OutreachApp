from .lemlist_formatting import lemlist_formatting
import time

def main(startup_data):

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    website_url = 'http://httpbin.org/ip'

    # Record the start time
    start_time = time.time()

    # Format the input files
    startup_data = lemlist_formatting(startup_data)

    # Record the end time and calculate the elapsed time
    end_time = time.time()
    elapsed_time = end_time - start_time

    # Print the total time taken by the process
    print(f"Total process time: {elapsed_time:.2f} seconds")

    return startup_data
