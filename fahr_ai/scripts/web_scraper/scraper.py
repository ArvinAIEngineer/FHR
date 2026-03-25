import os
import re
import asyncio
import json
import base64
import requests
import pandas as pd
from joblib import Parallel, delayed
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin
from weasyprint import HTML
from io import BytesIO
from langchain_community.document_loaders import RecursiveUrlLoader


CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(CURRENT_DIRECTORY, "assets"), exist_ok=True)
SAVE_DIR = os.path.join(CURRENT_DIRECTORY, "assets")


class HtmlExtractor:
    def __init__(self):
        """Initialize the HtmlExtractor instance."""
        pass

    def extract_table(self, table) -> str:
        """
        Extracts tabular data from an HTML table element and converts it to CSV format.

        Args:
            table: BeautifulSoup table element to extract data from

        Returns:
            str: CSV formatted string containing the table data
        """
        df = pd.read_html(str(table), flavor="bs4")[0]
        return df.to_csv(index=False)

    def extract_image(self, image, base_url: str) -> str:
        """
        Downloads an image from a URL and converts it to base64 encoded string.

        Args:
            image: BeautifulSoup image element containing the image source
            base_url (str): Base URL to resolve relative image URLs

        Returns:
            str: Base64 encoded string of the image data, or None if download fails
        """
        img_url = urljoin(base_url, image["src"])
        try:
            img_data = requests.get(img_url).content
            b64_data = base64.b64encode(img_data).decode("utf-8")
            return b64_data
        except:
            return None

    def extract(self, html_content: str, base_url: str) -> dict[str, str]:
        """
        Extracts text, tables, images and URLs from HTML content.

        Args:
            html_content (str): Raw HTML content to parse
            base_url (str): Base URL to resolve relative URLs

        Returns:
            dict: Dictionary containing extracted content with keys:
                - extracted_text: Plain text content
                - extracted_tables: List of CSV formatted tables
                - extracted_images: List of base64 encoded images
                - extracted_urls: List of absolute URLs
        """
        soup = BeautifulSoup(html_content, "lxml")
        # Extract and process all content types in parallel
        tables = [self.extract_table(table) for table in soup.find_all("table")]
        images = [self.extract_image(image, base_url) for image in soup.find_all("img", src=True)]
        images = [img for img in images if img is not None]
        urls = [urljoin(base_url, a["href"]) for a in soup.find_all("a", href=True)]
        text = soup.get_text(separator="\n", strip=True)
        return {
            "extracted_text": text,
            "extracted_tables": tables,
            "extracted_images": images,
            "extracted_urls": urls,
        }


class WebScraper:
    def __init__(self):
        """Initialize the WebScraper instance."""
        pass

    async def get_links_with_content(self, url: str, max_depth: int) -> dict[str, str]:
        """
        Asynchronously retrieves content from a URL and its linked pages up to max_depth.

        Args:
            url (str): Starting URL to scrape
            max_depth (int): Maximum depth of links to follow

        Returns:
            dict: Dictionary containing document content and metadata
        """
        loader = RecursiveUrlLoader(
            url=url,
            max_depth=max_depth,
            timeout=60,
            use_async=True,
        )
        docs = await loader.aload()
        return docs

    def get_organized_content(self, doc) -> dict:
        """
        Processes and organizes content extracted from a document.

        Args:
            doc: Document object containing page content and metadata

        Returns:
            dict: Organized content including metadata, extracted content and statistics
        """
        meta_data = doc.metadata
        content = doc.page_content
        base_url = meta_data.get("source", "")
        organized_content = HtmlExtractor().extract(content, base_url)

        text_length = len(organized_content["extracted_text"])
        num_tables = len(organized_content["extracted_tables"])
        num_images = len(organized_content["extracted_images"])

        return {
            **organized_content,
            **meta_data,
            "base_url": base_url,
            "html": content,
            "text_length": text_length,
            "num_tables": num_tables,
            "num_images": num_images,
        }

    def create_and_save_pdf(self, link: dict, save_dir: str) -> None:
        """
        Creates and saves a PDF file from HTML content.

        Args:
            link (dict): Dictionary containing HTML content and metadata
            save_dir (str): Directory to save the PDF file
        """
        try:
            # Create sanitized filename from URL
            base_url = re.sub(r"[^a-zA-Z0-9]", "_", link.get("base_url"))
            pdf_path = f"{save_dir}/scraped_pdfs/{base_url}.pdf"
            html = link.get("html")
            # Add custom page orientation
            orient = """@page {size: 1920px 1080px; margin: 10px; }"""
            placeholder = "<head><style>{}</style>".format(orient)
            html = html.replace("<head>", placeholder)
            HTML(string=html).write_pdf(pdf_path)
        except Exception as e:
            print(f"Error creating PDF for {link.get('base_url')}: {e}")

    def scrape(
        self,
        url: str,
        max_depth: int,
        return_results: bool = False,
        save_results: bool = False,
        save_pdf: bool = False,
        save_dir: str = SAVE_DIR,
        min_content_length: int = 300,
    ) -> list[dict] | None:
        """
        Main scraping function that coordinates the entire scraping process.

        Args:
            url (str): Starting URL to scrape
            max_depth (int): Maximum depth of links to follow
            return_results (bool): Whether to return the scraped results
            save_results (bool): Whether to save results to JSON file
            save_pdf (bool): Whether to save content as PDFs
            save_dir (str): Directory to save output files
            min_content_length (int): Minimum text length to keep a page

        Returns:
            list[dict] | None: List of dictionaries containing scraped content if return_results is True
        """
        # Asynchronously get all links and their content
        link_docs = asyncio.run(self.get_links_with_content(url, max_depth))

        # Process content extraction in parallel using joblib
        taskq = tqdm([delayed(self.get_organized_content)(doc) for doc in link_docs], desc="extracting data")
        with Parallel(n_jobs=min(len(link_docs), os.cpu_count()), verbose=0, prefer="threads") as parallel:
            organized_links = parallel(taskq)

        # Filter out links with little or no content
        filtered_links = [link for link in tqdm(organized_links, desc="filtering empty links") if link["text_length"] > min_content_length]

        if save_pdf:
            # Save the extracted data to a JSON file
            os.makedirs(f"{save_dir}/scraped_pdfs", exist_ok=True)

            taskq = tqdm([delayed(self.create_and_save_pdf)(link, save_dir) for link in filtered_links], desc="Saving PDFs")
            with Parallel(n_jobs=min(len(filtered_links), os.cpu_count()), verbose=0, prefer="processes") as parallel:
                parallel(taskq)

        if save_results:
            # Save the extracted data to a JSON file
            with open(os.path.join(save_dir, "scraped_data.json"), "w") as f:
                json.dump(filtered_links, f, indent=4)

        if return_results:
            return filtered_links


if __name__ == "__main__":
    url = "https://www.fahr.gov.ae"  # Replace with the URL you want to scrape
    scraper = WebScraper()
    results = scraper.scrape(url=url, max_depth=10, return_results=False, save_results=True, save_pdf=True, save_dir=SAVE_DIR, min_content_length=300)
