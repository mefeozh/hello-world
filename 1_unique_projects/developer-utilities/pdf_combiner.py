import os
from PyPDF2 import PdfReader, PdfWriter

def combine_pdfs(in_folder, out_file):
    pdf_writer = PdfWriter()

    for filename in os.listdir(in_folder):
        if filename.endswith(".pdf"):
            filepath = os.path.join(in_folder, filename)
            try:
                with open(filepath, 'rb') as pdf_file:
                    pdf_reader = PdfReader(pdf_file)
                    for page in range(len(pdf_reader.pages)):  # Adjust the page numbers as needed):
                        pdf_writer.add_page(pdf_reader.pages[page])
            except Exception as e:
                print(f"Error processing {filename}: {e}") # Basic error handling

    with open(out_file, 'wb') as fh:
        pdf_writer.write(fh)

# Example usage:
combine_pdfs('C:/Users/mehme/Desktop/ME_FOLDER/ME_304/lecture_notes', 'ME303.pdf')