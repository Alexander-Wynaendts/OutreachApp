import pandas as pd
import re
import random

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

            # If the email contains "info", set it to None
            if "info" in email.lower():
                email = None

            name_email_pairs.append((first_name, last_name, email))

    return name_email_pairs

def lemlist_formatting(startup_data):

    first_email_objects = [
        "Investing in {companyName}: A Quick Chat?",
        "Supporting {companyName} with Early-Stage Funding",
        "{companyName} & Entourage Capital: Let’s Talk",
        "Intro Entourage <> {companyName}"
    ]

    first_email_content_intro = [
        "I'm Tibe from Entourage, a new VC fund led by Pieterjan Bouten, co-founder of Showpad. We specialize in early-stage B2B SaaS and think {companyName} has incredible potential. I'd love to chat about how we can support {companyName} growth.",
        "I'm reaching out from Entourage Capital, a new fund led by Pieterjan Bouten. We focus on early-stage B2B SaaS investments, and I see a lot of potential in {companyName}. I'd love to discuss how we can support your growth plans."
    ]

    first_email_content_meeting = [
        "Let me know if you'd like to schedule 30 minutes for a quick intro.",
        "Feel free to book some time with me at your convenience.",
        "If you're open to it, let's schedule some time for a quick call."
    ]

    first_email_content_goodbye = [
        "Best regards,",
        "Hopefully talk soon,"
    ]

    followup_email_content_intro = [
        "I wanted to follow up on my last email to see if you had a chance to review it. I’d love to discuss how Entourage Capital could help {companyName}.",
        "Just following up to check if you’ve had a chance to look at my previous email. I'd love to connect and explore potential synergies between Entourage and {companyName}.",
        "I’m reaching out again to follow up on my previous email about potential collaboration between Entourage Capital and {companyName}."
    ]

    followup_email_content_meeting = [
        "Feel free to reach out whenever it works for you.",
        "Let me know when could be the best time for you!",
        "Let me know if you’d like to connect."
    ]

    followup_email_content_goodbye = [
        "Best,",
        "Best regards,"
    ]

    rows = []

    # Loop through each row in the startup_data DataFrame
    for index, row in startup_data.iterrows():
        name_email_pairs = extract_first_last_names(row['People'])

        for first_name, last_name, email in name_email_pairs:
            # Make a random selection for each email component
            first_email_object = random.choice(first_email_objects).format(companyName=row['Name'])
            first_email_intro = random.choice(first_email_content_intro).format(companyName=row['Name'])
            first_email_meeting = random.choice(first_email_content_meeting)
            first_email_goodbye = random.choice(first_email_content_goodbye)

            followup_email_intro = random.choice(followup_email_content_intro).format(companyName=row['Name'])
            followup_email_meeting = random.choice(followup_email_content_meeting)
            followup_email_goodbye = random.choice(followup_email_content_goodbye)

            # Append the formatted row data with random elements
            rows.append({
                'companyName': row['Name'],
                'firstName': first_name,
                'lastName': last_name,
                'email': email if email else row['Email'],
                'FirstEmailObject': first_email_object,
                'FirstEmailContentIntro': first_email_intro,  # Directly add random intro
                'FirstEmailContentMeeting': first_email_meeting,  # Directly add random meeting part
                'FirstEmailContentGoodbye': first_email_goodbye,  # Directly add random goodbye
                'FollowupEmailContentIntro': followup_email_intro,  # Directly add random follow-up intro
                'FollowupEmailContentMeeting': followup_email_meeting,  # Directly add random follow-up meeting part
                'FollowupEmailContentGoodbye': followup_email_goodbye,  # Directly add random follow-up goodbye
            })

    # Convert the list of rows into a DataFrame
    formatted_data = pd.DataFrame(rows)
    return formatted_data
