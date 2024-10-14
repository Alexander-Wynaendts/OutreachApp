import pandas as pd

def extract_first_last_names(people_column):
    if pd.isna(people_column):
        return []
    names = people_column.split(", ")
    name_pairs = []
    for name in names:
        split_name = name.split(" ")
        if len(split_name) > 1:
            first_name = split_name[0]
            last_name = " ".join(split_name[1:])
        else:
            first_name = split_name[0]
            last_name = ""
        name_pairs.append((first_name, last_name))
    return name_pairs

def lemlist_foramtting(startup_data):

    # Create a new DataFrame with expanded rows for multiple people
    rows = []
    for index, row in startup_data.iterrows():
        name_pairs = extract_first_last_names(row['People'])
        for first_name, last_name in name_pairs:
            rows.append({
                'companyName': row['Name'],
                'firstName': first_name,
                'lastName': last_name,
                'email': row['Email'],
                'linkedinURL': row['LinkedIn URL'],
                'companyDomain': row['Website']
            })

    # Convert the list of rows into a DataFrame
    startup_data = pd.DataFrame(rows)

    return startup_data
