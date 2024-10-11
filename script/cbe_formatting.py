import pandas as pd
import io

def cbe_formatting(files):
    """
    Load and process monthly activity and enterprise data, then return a list of unique relevant entity numbers
    with at least one NaceCode starting with '62' or '63' and none starting with excluded codes, only for NaceVersion 2008.
    """

    # Construct the file paths for the activity and enterprise data
    activity_file = io.BytesIO(files['activity_insert.csv'])
    enterprise_file = io.BytesIO(files['enterprise_insert.csv'])

    # Load the CSV files into DataFrames
    main_df = pd.read_csv(activity_file)
    enterprise_df = pd.read_csv(enterprise_file)

    # Merge activity and enterprise data on EntityNumber and EnterpriseNumber
    main_df = pd.merge(main_df, enterprise_df, left_on="EntityNumber", right_on="EnterpriseNumber", how="left")

    total_enterprise = pd.DataFrame(main_df["EntityNumber"].drop_duplicates(), columns=["EntityNumber"])
    print("Length of total enterprises:", len(total_enterprise))

    # Define the is_relevant function here
    def is_relevant(group):
        # Filter NaceCodes only for rows where NaceVersion is 2008
        nace_codes_2008 = [str(nace_code) for nace_code, nace_version in zip(group["NaceCode"], group["NaceVersion"]) if nace_version == 2008]

        # Check if there is any NaceCode starting with '62' or '63' in NaceVersion 2008
        has_tech_code = any(code.startswith(('582', '62', '63')) for code in nace_codes_2008)

        # Check if there is any NaceCode starting with excluded codes in NaceVersion 2008
        has_excluded_code = any(
            code.startswith(excluded) for code in nace_codes_2008
            for excluded in ['0',
                             '1',
                             '2',
                             '681', '682']
        )

        # Return True only if it has a '62' or '63' NaceCode and no excluded code in NaceVersion 2008
        return has_tech_code and not has_excluded_code

    # Group by EntityNumber and filter based on the new logic
    filtered_df = main_df.groupby("EntityNumber").filter(is_relevant)

    # Get unique EntityNumbers
    startup_data = pd.DataFrame(filtered_df["EntityNumber"].drop_duplicates(), columns=["EntityNumber"])

    return startup_data
