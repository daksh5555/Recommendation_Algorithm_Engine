import pandas as pd

# Load the original CSV file
input_file = 'xyz.csv'  # Replace with the path to your input CSV file
data = pd.read_csv(input_file)

# Extract the relevant columns
extracted_data = data[['id', 'view_count', 'rating_count', 'upvote_count', 'share_count', 'comment_count']]

# Save the extracted data to a new CSV file
output_file = 'extracted_popularity_data.csv'  # Replace with the desired output file name
extracted_data.to_csv(output_file, index=False)

print(f"Data successfully extracted and saved to {output_file}")
