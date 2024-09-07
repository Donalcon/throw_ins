

def log_missing_data(df):
    # Identify columns that contain 'wide' in their name
    wide_columns = [col for col in df.columns if 'wide' in col]

    # Open a text file to write the missing data information
    with open("./prem/data/who_scored_urls/missing_data.txt", "w") as file:
        # Loop through each row and check if any 'wide' columns have missing values
        for index, row in df.iterrows():
            if row[wide_columns].isnull().any():
                # If a missing value is found in any 'wide' column, save the unique identifier
                team = row['team']
                opp = row['opp']
                date = row['date']
                unique_id = f"{team}_{opp}_{date}"
                # Write the unique identifier to the file
                file.write(f"{unique_id}\n")