# Web Scraper Module

This web scraper module is a powerful tool for extracting and organizing content from web pages. It provides functionality for recursive crawling, parallel processing, and saving results in a structured format. The module is designed to handle various types of content, including text, tables, images, and URLs, making it a versatile solution for web scraping tasks.

## Features

- **Table Extraction**: Converts HTML tables into CSV format.
- **Image Extraction**: Downloads images and encodes them in Base64 format.
- **URL Extraction**: Extracts all hyperlinks from a webpage.
- **Text Content Extraction**: Extracts plain text content from HTML.
- **Recursive URL Crawling**: Crawls websites up to a specified depth.
- **Parallel Processing**: Speeds up content extraction using parallel processing.
- **Save Results**: Saves extracted data in JSONL format for easy reuse.

## Dependencies

The module requires the following Python libraries:
- `beautifulsoup4`
- `pandas`
- `requests`
- `joblib`
- `langchain_community`
- `tqdm`

Install these dependencies using pip:
```bash
pip install beautifulsoup4 pandas requests joblib langchain_community tqdm
```

Other Dependencies:
```bash
sudo apt install libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libcairo2
```

Usage

Example 1: Recursive Search with Max Depth
This example demonstrates how to scrape a website recursively up to a specified depth.

```Python
from scraper import WebScraper

# Initialize the WebScraper
scraper = WebScraper()

# Define the starting URL and maximum depth
url = "https://example.com"
max_depth = 2

# Scrape the website
results = scraper.scrape(
    url=url,
    max_depth=max_depth,
    return_results=True,  # Return the results as a list of dictionaries
    save_results=True,    # Save the results to a JSONL file
    save_dir="./scraped_data"  # Directory to save the results
)

# Print the results
for result in results:
    print(result)
```



Example 2: Single Link with Max Depth = 0
This example demonstrates how to scrape a single webpage without recursive crawling.

```Python
from scraper import WebScraper

# Initialize the WebScraper
scraper = WebScraper()

# Define the starting URL and maximum depth
url = "https://example.com"
max_depth = 0

# Scrape the webpage
results = scraper.scrape(
    url=url,
    max_depth=max_depth,
    return_results=True,  # Return the results as a list of dictionaries
    save_results=False    # Do not save the results to a file
)

# Print the results
for result in results:
    print(result)
```

OUTPUTS:

The module organizes the extracted content into a dictionary with the following keys:
* extracted_text: Plain text content from the webpage.
* extracted_tables: A list of tables in CSV format.
* extracted_images: A list of Base64-encoded image data.
* extracted_urls: A list of URLs found on the webpage.
* Additional metadata such as the source URL and base URL.

Example Output

Here is an example of the output for a single webpage:

```json
{
    "extracted_text": "Welcome to Example.com\nThis is a sample webpage.",
    "extracted_tables": [
        "Column1,Column2\nValue1,Value2\nValue3,Value4"
    ],
    "extracted_images": [
        "iVBORw0KGgoAAAANSUhEUgAAAAUA..."
    ],
    "extracted_urls": [
        "https://example.com/page1",
        "https://example.com/page2"
    ],
    "source": "https://example.com",
    "base_url": "https://example.com"
}
```

Notes

* The module saves results in JSONL format when save_results=True. Each line in the file represents a JSON object for a single webpage.
* The max_depth parameter controls the depth of recursive crawling. Set it to 0 for single-page scraping.
* Use the return_results parameter to retrieve the results directly in your Python code.

This module is ideal for tasks such as data collection, content analysis, and web research. Customize it to suit your specific scraping needs! ```