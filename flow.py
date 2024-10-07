from openai import OpenAI
import csv
from langchain.prompts import PromptTemplate
from langchain_community.utilities import SerpAPIWrapper
import os
from dotenv import load_dotenv
load_dotenv()

# Set up OpenAI API credentials
openai_api_key = os.getenv('OPENAI_API_KEY')
serpapi_api_key = os.getenv('SERPAPI_API_KEY')
# Define the prompt template
prompt_template = PromptTemplate(
    input_variables=['prompt'],
    template="{prompt}"
)

# Load the SerpAPI tool to gather information from search results
serpapi_tool = SerpAPIWrapper(serpapi_api_key=serpapi_api_key)

# Define a function to perform the browsing and scanning
def gather_information(prompt):
    # Extract school name and location from the prompt
    school_name, location = extract_school_info(prompt)

    # Perform a search to gather URLs related to the school
    search_query = f"{school_name} {location} staff directory"
    search_results = serpapi_tool.run(search_query)
    
    # Debugging: Print the search results to understand their structure
    # print(f"Search Results: {search_results}")
    
    # Use OpenAI to extract relevant information from search result snippets
    client = OpenAI()
    try:
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": f"Extract the names, job titles, and email addresses from the following search results: {search_results}. Return the data in the format: Name | Job title | Email Address. Each person should be in a separate row. Only return an email address if it contains an '@' symbol, otherwise return 'none found'. No extra text or explanations."}
            ],
            stream=True,
        )
        scanned_information = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                scanned_information += chunk.choices[0].delta.content
    except Exception as e:
        print(f"Error processing content with OpenAI API: {e}")
        scanned_information = "none found"
    
    return scanned_information.strip()

# Helper function to extract school name and location from the prompt
def extract_school_info(prompt):
    parts = prompt.split(' in ')
    if len(parts) >= 2:
        school_name = parts[0].replace('At the school ', '').strip()
        location = parts[1].split(',')[0].strip()
        return school_name, location
    return "", ""

# Function to start searching
def find_staff_info(prompt):
    info = gather_information(prompt)
    return info

# Function to process CSV input and output
def process_csv(input_csv, output_csv):
    with open(input_csv, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    outputs = []

    for index, row in enumerate(rows):
        prompt = row['PROMPT']  # Update to match the exact column name in your CSV file
        response = find_staff_info(prompt)
        print(response)
        outputs.append({"prompt": prompt, "output": response})

    # Write output to a new CSV file
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['prompt', 'output']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(outputs)

# Example usage
input_csv = 'AUTO.csv'
output_csv = 'new_AUTO.csv'

def main():
    process_csv(input_csv, output_csv)
    print(f"Completed processing and saved the results in {output_csv}.")

# Run the example
if __name__ == "__main__":
    main()