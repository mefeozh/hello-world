import os
import sys
import argparse
from markitdown import MarkItDown

def copy_to_clipboard(text):
    """
    Copies the given text to the Windows Clipboard using native ctypes.
    Falls back to subprocess call to clip.exe if ctypes fails.
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Try ctypes first for native, robust UTF-16 copy (handles all unicode chars)
    try:
        import ctypes
        OpenClipboard = ctypes.windll.user32.OpenClipboard
        EmptyClipboard = ctypes.windll.user32.EmptyClipboard
        SetClipboardData = ctypes.windll.user32.SetClipboardData
        CloseClipboard = ctypes.windll.user32.CloseClipboard
        GlobalAlloc = ctypes.windll.kernel32.GlobalAlloc
        GlobalLock = ctypes.windll.kernel32.GlobalLock
        GlobalUnlock = ctypes.windll.kernel32.GlobalUnlock

        GMEM_MOVEABLE = 0x0002
        CF_UNICODETEXT = 13

        if OpenClipboard(None):
            try:
                EmptyClipboard()
                # Windows Unicode clipboard expects UTF-16 Little Endian
                encoded = text.encode('utf-16le') + b'\x00\x00'
                h_mem = GlobalAlloc(GMEM_MOVEABLE, len(encoded))
                if h_mem:
                    ptr = GlobalLock(h_mem)
                    if ptr:
                        ctypes.memmove(ptr, encoded, len(encoded))
                        GlobalUnlock(h_mem)
                        if SetClipboardData(CF_UNICODETEXT, h_mem):
                            CloseClipboard()
                            return True
            finally:
                try:
                    CloseClipboard()
                except Exception:
                    pass
    except Exception:
        pass

    # Fallback to command line 'clip' utility
    try:
        import subprocess
        # Pipe string to clip.exe
        process = subprocess.Popen(['clip'], stdin=subprocess.PIPE, text=True, encoding='utf-8')
        process.communicate(input=text)
        if process.returncode == 0:
            return True
    except Exception:
        pass

    return False

def select_file_gui():
    """
    Opens a standard Windows file picker dialog to let user select a file.
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # Initialize and hide the main tkinter window
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)  # Bring the dialog to the front
        
        file_path = filedialog.askopenfilename(
            title="Select Document to Parse to Markdown",
            filetypes=[
                ("Supported Files (*.pdf, *.docx, *.xlsx, *.pptx, etc.)", "*.pdf;*.docx;*.xlsx;*.pptx;*.html;*.csv;*.json;*.xml;*.txt;*.zip"),
                ("PDF Files (*.pdf)", "*.pdf"),
                ("All Files (*.*)", "*.*")
            ]
        )
        return file_path
    except Exception:
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Convert documents (especially PDFs) to Markdown using Microsoft's MarkItDown and copy to clipboard."
    )
    parser.add_argument("file_path", nargs="?", help="Path to the file to convert. If omitted, a file picker will open.")
    parser.add_argument("-o", "--output", help="Custom output path for the Markdown file. Defaults to <input_file_basename>.md")
    parser.add_argument("--no-clipboard", action="store_true", help="Do not copy the output to the clipboard.")
    
    args = parser.parse_args()
    
    file_path = args.file_path
    
    # If no file path is provided via CLI argument, open file picker GUI
    if not file_path:
        print("No file path provided. Launching file picker dialog...")
        file_path = select_file_gui()
        
        # If GUI was cancelled or failed, fall back to console text prompt
        if not file_path:
            file_path = input("Enter the path to the document file (or drag & drop here): ").strip()
            # Strip enclosing quotes if user dragged and dropped file into terminal
            if file_path.startswith(('"', "'")) and file_path.endswith(('"', "'")):
                file_path = file_path[1:-1]
                
    if not file_path:
        print("Operation cancelled. No file path specified.")
        sys.exit(0)
        
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        sys.exit(1)
        
    # Get absolute path for clarity
    file_path = os.path.abspath(file_path)
    print(f"\n[+] Processing: {file_path}")
    
    try:
        # Initialize MarkItDown
        markitdown = MarkItDown()
        
        # Convert file
        result = markitdown.convert(file_path)
        markdown_text = result.text_content
        
        if not markdown_text:
            print("Warning: Conversion returned empty content.")
            markdown_text = ""
            
        # Determine output file path
        if args.output:
            output_path = os.path.abspath(args.output)
        else:
            base, _ = os.path.splitext(file_path)
            output_path = f"{base}.md"
            
        # Save output file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
            
        print(f"[+] Successfully converted and saved to: {output_path}")
        
        # Copy to clipboard
        if not args.no_clipboard and markdown_text:
            print("[-] Copying Markdown text to clipboard...")
            success = copy_to_clipboard(markdown_text)
            if success:
                print("[+] Clipboard updated successfully! Ready to paste into your AI.")
            else:
                print("[!] Warning: Copying to clipboard failed.")
                
        # Print summary
        words = len(markdown_text.split())
        chars = len(markdown_text)
        print(f"\nStats:")
        print(f"  - File Name:  {os.path.basename(file_path)}")
        print(f"  - Characters: {chars:,}")
        print(f"  - Words:      {words:,}")
        print(f"  - Save Path:  {output_path}")
        
    except Exception as e:
        print(f"[!] An error occurred during conversion: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
