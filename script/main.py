from .lemlist_formatting import lemlist_formatting
import time

def main(startup_data):

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
