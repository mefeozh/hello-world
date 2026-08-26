#!/usr/bin/env python3
"""
PDF Splitter - A versatile command-line and interactive utility to extract page ranges from PDF files.
Supports both:
  - Start and End page numbers (1-based, inclusive)
  - Start page and Count of pages to extract

Requirements:
  - pypdf (recommended) or PyPDF2
"""

import sys
import os
import argparse

# Try importing modern pypdf first, then fall back to PyPDF2
try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    try:
        from PyPDF2 import PdfReader, PdfWriter
    except ImportError:
        print("Error: The 'pypdf' or 'PyPDF2' package is not installed.")
        print("Please install pypdf by running: pip install pypdf")
        sys.exit(1)

def print_banner():
    banner = """
==================================================
              📄 PDF SPLITTER UTILITY ✂️
==================================================
    """
    print(banner)

def clean_path(path):
    """Clean quote characters and surrounding whitespace from user-inputted paths."""
    if not path:
        return ""
    path = path.strip()
    if (path.startswith('"') and path.endswith('"')) or (path.startswith("'") and path.endswith("'")):
        path = path[1:-1]
    return os.path.abspath(path.strip())

def extract_pages(input_path, output_path, start_page, end_page=None, count=None):
    """
    Extracts pages from a PDF and saves them to a new PDF.
    
    start_page: 1-based index (e.g. 1 is the first page)
    end_page: 1-based index (inclusive)
    count: number of pages to extract from start_page
    """
    input_path = clean_path(input_path)
    output_path = clean_path(output_path)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input PDF file not found: {input_path}")

    # Read the PDF
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)
    
    if total_pages == 0:
        raise ValueError("The input PDF file contains no pages.")

    # Determine internal 0-based start and end indices
    start_idx = start_page - 1
    
    if start_idx < 0 or start_idx >= total_pages:
        raise ValueError(f"Start page {start_page} is out of bounds. The PDF has {total_pages} pages.")

    if count is not None:
        if count <= 0:
            raise ValueError("Page count must be greater than 0.")
        end_idx = start_idx + count - 1
    elif end_page is not None:
        end_idx = end_page - 1
        if end_idx < start_idx:
            raise ValueError(f"End page {end_page} cannot be earlier than start page {start_page}.")
    else:
        raise ValueError("Either end page or count must be specified.")

    # Bound check the end page index
    if end_idx >= total_pages:
        print(f"\n⚠️ Warning: Requested page range goes up to page {end_idx + 1}, but PDF only has {total_pages} pages.")
        print(f"   Adjusting extraction range to end at the last page (page {total_pages}).")
        end_idx = total_pages - 1

    # Extract pages and write
    writer = PdfWriter()
    
    pages_to_extract = list(range(start_idx, end_idx + 1))
    print(f"\n📂 Extracting pages {start_page} to {end_idx + 1} (Total: {len(pages_to_extract)} pages)...")
    
    for idx in pages_to_extract:
        writer.add_page(reader.pages[idx])

    # Save to output file
    with open(output_path, 'wb') as out_file:
        writer.write(out_file)

    print(f"✅ Success! Extracted PDF saved successfully to:\n   {output_path}\n")

def interactive_mode():
    print_banner()
    
    # 1. Get input file
    while True:
        raw_input = input("📥 Drag & drop or enter the path to the input PDF file:\n> ")
        input_path = clean_path(raw_input)
        if not input_path:
            print("❌ Input path cannot be empty. Please try again.\n")
            continue
        if not os.path.exists(input_path):
            print(f"❌ File not found at: {input_path}\nPlease enter a valid path.\n")
            continue
        if not input_path.lower().endswith(".pdf"):
            print("⚠️ Warning: The file doesn't seem to have a .pdf extension. Continuing anyway...\n")
        break

    # Read file properties
    try:
        reader = PdfReader(input_path)
        total_pages = len(reader.pages)
        print(f"ℹ️ Loaded successfully! The PDF has {total_pages} page(s).")
    except Exception as e:
        print(f"❌ Failed to read the PDF file: {e}")
        return

    # 2. Get selection method
    print("\nHow would you like to specify the pages to extract?")
    print("  [1] Start page and End page (e.g. from page 2 to page 5)")
    print("  [2] Start page and Count of pages (e.g. from page 2, extract 4 pages)")
    
    choice = ""
    while choice not in ["1", "2"]:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice not in ["1", "2"]:
            print("❌ Invalid choice. Please enter 1 or 2.")

    # 3. Get page numbers
    start_page = None
    end_page = None
    count = None

    while True:
        try:
            start_val = input(f"\nEnter start page (1 to {total_pages}): ").strip()
            start_page = int(start_val)
            if start_page < 1 or start_page > total_pages:
                print(f"❌ Start page must be between 1 and {total_pages}.")
                continue
            break
        except ValueError:
            print("❌ Please enter a valid integer.")

    if choice == "1":
        while True:
            try:
                end_val = input(f"Enter end page (inclusive, {start_page} to {total_pages}): ").strip()
                end_page = int(end_val)
                if end_page < start_page:
                    print(f"❌ End page cannot be less than start page ({start_page}).")
                    continue
                if end_page > total_pages:
                    print(f"⚠️ End page {end_page} exceeds total pages ({total_pages}). It will be capped at {total_pages}.")
                break
            except ValueError:
                print("❌ Please enter a valid integer.")
    else:
        max_possible_count = total_pages - start_page + 1
        while True:
            try:
                count_val = input(f"Enter number of pages to extract (1 to {max_possible_count}): ").strip()
                count = int(count_val)
                if count < 1:
                    print("❌ Count must be at least 1.")
                    continue
                if count > max_possible_count:
                    print(f"⚠️ Count {count} exceeds remaining pages. It will be capped at {max_possible_count}.")
                break
            except ValueError:
                print("❌ Please enter a valid integer.")

    # 4. Determine default output name
    dir_name, file_name = os.path.split(input_path)
    base_name, ext = os.path.splitext(file_name)
    
    if choice == "1":
        default_out_name = f"{base_name}_pages_{start_page}_to_{min(end_page, total_pages)}{ext}"
    else:
        actual_end = min(start_page + count - 1, total_pages)
        default_out_name = f"{base_name}_pages_{start_page}_to_{actual_end}{ext}"
        
    default_out_path = os.path.join(dir_name, default_out_name)

    print(f"\n✏️ Enter the path/name for the output PDF.")
    print(f"   [Press Enter to use default: {default_out_name}]")
    raw_output = input("> ").strip()
    
    if raw_output:
        output_path = clean_path(raw_output)
        # If user entered just a filename, place it in the same directory as the input file
        if not os.path.isabs(output_path) and not os.path.dirname(output_path):
            output_path = os.path.join(dir_name, output_path)
    else:
        output_path = default_out_path

    # Ensure output has .pdf extension
    if not output_path.lower().endswith(".pdf"):
        output_path += ".pdf"

    # 5. Execute extraction
    try:
        extract_pages(
            input_path=input_path,
            output_path=output_path,
            start_page=start_page,
            end_page=end_page,
            count=count
        )
    except Exception as e:
        print(f"\n❌ Error during page extraction: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="PDF Splitter - Extract page ranges from PDF files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract pages 1 to 5 (inclusive)
  python PDF_splitter.py -i document.pdf -o output.pdf --start 1 --end 5
  
  # Extract 3 pages starting from page 10 (i.e. pages 10, 11, 12)
  python PDF_splitter.py -i document.pdf -o output.pdf --start 10 --count 3
  
  # Run in interactive wizard mode
  python PDF_splitter.py
"""
    )
    parser.add_argument("-i", "--input", help="Path to the input PDF file")
    parser.add_argument("-o", "--output", help="Path to the output PDF file")
    parser.add_argument("-s", "--start", type=int, help="Start page number (1-based index)")
    parser.add_argument("-e", "--end", type=int, help="End page number (1-based index, inclusive)")
    parser.add_argument("-c", "--count", type=int, help="Number of pages to extract")

    # If no arguments are passed, run interactive mode
    if len(sys.argv) == 1:
        interactive_mode()
        return

    args = parser.parse_args()

    # If any arg is passed, enforce required inputs for command-line mode
    if not args.input:
        parser.error("the following arguments are required: -i/--input (or run with no arguments for interactive mode)")
    if not args.start:
        parser.error("the following arguments are required when using command-line: -s/--start")
    if not args.end and not args.count:
        parser.error("either -e/--end or -c/--count must be specified when using command-line")
    if args.end and args.count:
        parser.error("cannot specify both -e/--end and -c/--count")

    # Construct default output file if not provided
    input_path = clean_path(args.input)
    if args.output:
        output_path = clean_path(args.output)
    else:
        dir_name, file_name = os.path.split(input_path)
        base_name, ext = os.path.splitext(file_name)
        if args.end:
            output_path = os.path.join(dir_name, f"{base_name}_split_{args.start}_{args.end}{ext}")
        else:
            output_path = os.path.join(dir_name, f"{base_name}_split_{args.start}_c{args.count}{ext}")

    try:
        extract_pages(
            input_path=input_path,
            output_path=output_path,
            start_page=args.start,
            end_page=args.end,
            count=args.count
        )
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
