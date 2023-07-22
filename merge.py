import glob
import json
import os

# Get a list of all JSON files starting with "webshare"
file_list = glob.glob("webshare-*.txt")

# Define an empty list to store all the data
merged_list = []

# Iterate over each JSON file
for file_name in file_list:
    with open(file_name) as file:
        # Load the JSON data from the file
        data = json.load(file)
        # Append the list from the current file to the merged list
        merged_list.extend(data)

# Read merge file
with open("merged-webshare.txt") as file:
    data = json.load(file)
    merged_list.extend(data)

# Write the merged list to a new JSON file
with open("merged-webshare.txt", "w") as output_file:
    json.dump(merged_list, output_file)

# Delete trash files
for file_name in file_list:
    os.remove(file_name)
