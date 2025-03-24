import pandas as pd

# Load the dataset (modify the file path accordingly)
df = pd.read_csv("Suicide_Detection.csv")  # Use pd.read_excel() for Excel files

# Extract the top 2000 entries
top_2000 = df.head(2000)

# Save to a new file
top_2000.to_csv("top_2000_entries.csv", index=False)

# Display the first few rows
print(top_2000.head())

# Calculate the number of characters in the dataset
num_characters = top_2000.astype(str).applymap(len).sum().sum()

print(f"Total number of characters in 'top_2000_entries.csv': {num_characters}")
