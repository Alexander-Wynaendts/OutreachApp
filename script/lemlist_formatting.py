import pandas as pd
import re

def extract_first_last_names(people_column):
    if pd.isna(people_column):
        return []

    # Split by "; " to handle multiple people in the same cell
    people_entries = people_column.split("; ")
    name_email_pairs = []

    for person in people_entries:
        # Use regex to extract name and email
        match = re.match(r"(.*?)(?:<(.+?)>)?$", person.strip())
        if match:
            full_name = match.group(1).strip()
            email = match.group(2) if match.group(2) else ''

            # Split the full name into first and last names
            split_name = full_name.split(" ", 1)
            first_name = split_name[0]
            last_name = split_name[1] if len(split_name) > 1 else ''

            name_email_pairs.append((first_name, last_name, email))

    return name_email_pairs

def lemlist_formatting(startup_data):
    # Create a new DataFrame with expanded rows for multiple people
    rows = []
    for index, row in startup_data.iterrows():
        name_email_pairs = extract_first_last_names(row['People'])
        for first_name, last_name, email in name_email_pairs:
            rows.append({
                'companyName': row['Name'],
                'firstName': first_name,
                'lastName': last_name,
                'email': email if email else row['Email'],  # Use the extracted email, or fall back to existing column
                'linkedinUrl': row['LinkedIn URL'],
                'companyDomain': row['Website']
            })

    # Convert the list of rows into a DataFrame
    startup_data = pd.DataFrame(rows)

    return startup_data
