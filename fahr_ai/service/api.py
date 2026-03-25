from fastapi import FastAPI, Form
from typing import List
from pdf_processor.image_extractor import process_pdf_directory_for_images
from pdf_processor.text_extractor import process_pdf_directory_for_text
from pdf_processor.table_extractor import ExtractTable
from pdf_processor.document_builder import build_processed_data, build_langchain_chunks
import os

app = FastAPI()

@app.post('/process')
def process(
    pdf_dir: str = Form(...),
    doc_type: str = Form(...)
):
    images_map = process_pdf_directory_for_images(pdf_dir, 'working/images')
    text_map = process_pdf_directory_for_text(pdf_dir)
    table_ex = ExtractTable()
    tables_map = {f: table_ex.get_tables(os.path.join(pdf_dir, f)) for f in images_map.keys()}

    processed = build_processed_data(images_map, text_map, tables_map, doc_type)
    chunks = build_langchain_chunks(processed)
    return {
        'processed_data': processed,
        'chunks': chunks
    } 