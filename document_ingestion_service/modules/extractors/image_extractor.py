import os
import fitz  # PyMuPDF
import docx
from typing import List, Dict, Union, Optional


class ImageExtractor:
    def __init__(self, dpi: int = 300):
        """
        Initialize the DocumentImageExtractor.

        Args:
            dpi (int): DPI resolution for page screenshots (default: 300)
        """
        self.dpi = dpi

    def process_file(self, file_path: str, output_dir: str) -> Dict:
        """
        Process a PDF or DOCX file to extract screenshots and images.

        Args:
            file_path (str): Path to the PDF or DOCX file
            output_dir (str): Directory to save extracted images and screenshots

        Returns:
            Dict: Dictionary containing results of extraction
        """
        # Create result structure
        result = {
            "page_screenshots": [],
            "embedded_images": []
        }

        result["page_screenshots"] = self.extract_screenshots_from_pdf(file_path, output_dir)
        result["embedded_images"] = self.extract_images_from_pdf(file_path, output_dir)

        return result

    def extract_screenshots_from_pdf(self, pdf_path: str, output_folder: str) -> List[Dict]:
        """
        Extract screenshots of all pages from a PDF file.

        Args:
            pdf_path (str): Path to the PDF file
            output_folder (str): Directory to save screenshots

        Returns:
            List[Dict]: List of dictionaries containing screenshot metadata
        """
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Create subfolder for page screenshots
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        screenshots_folder = os.path.join(output_folder, "pages")
        os.makedirs(screenshots_folder, exist_ok=True)

        # Open PDF document
        doc = fitz.open(pdf_path)
        results = []

        # Extract screenshots for each page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # Create pixmap with specified DPI
            pix = page.get_pixmap(dpi=self.dpi)
            # Define output path
            output_name = f"{base_name}_page-{page_num + 1}.png"
            output_path = os.path.join(screenshots_folder, output_name)
            # Save pixmap as PNG
            pix.save(output_path)
            # Add to results
            results.append({
                'page_number': page_num + 1,
                'image_path': output_path,
                'width': pix.width,
                'height': pix.height
            })

        doc.close()
        return results

    def extract_images_from_pdf(self, pdf_path: str, output_folder: str) -> List[Dict]:
        """
        Extract embedded images from a PDF file.

        Args:
            pdf_path (str): Path to the PDF file
            output_folder (str): Directory to save images

        Returns:
            List[Dict]: List of dictionaries containing image metadata
        """
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)

        # Create subfolder for embedded images
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        images_folder = os.path.join(output_folder, "images")
        os.makedirs(images_folder, exist_ok=True)

        # Open PDF document
        doc = fitz.open(pdf_path)
        images = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Create output filename
                output_name = f"{base_name}_page{page_num + 1}_img{img_index + 1}.{image_ext}"
                output_path = os.path.join(images_folder, output_name)

                with open(output_path, "wb") as img_file:
                    img_file.write(image_bytes)

                # Add metadata to results
                images.append({
                    'page_number': page_num + 1,
                    'index': img_index + 1,
                    'image_path': output_path,
                    'format': image_ext,
                    'width': base_image.get("width", 0),
                    'height': base_image.get("height", 0)
                })

        doc.close()
        return images
