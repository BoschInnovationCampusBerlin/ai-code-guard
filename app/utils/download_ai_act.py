"""Script to download and process the EU AI Act."""

import os
import requests
import tempfile
from pypdf import PdfReader
import argparse
from app.utils.config import get_data_dir

def download_eu_ai_act(output_file=None):
    """Download the EU AI Act and convert it to text.
    
    Args:
        output_file: Path to save the text file. If None, a default path is used.
        
    Returns:
        Path to the saved text file.
    """
    if output_file is None:
        data_dir = get_data_dir()
        output_file = os.path.join(data_dir, "eu_ai_act.txt")
    
    # URL to the EU AI Act PDF
    url = "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32024R1689"
    
    print(f"Downloading EU AI Act from {url}...")
    
    # Create a temporary file for the PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_path = tmp_file.name
    
    try:
        # Download the PDF
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(tmp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded PDF to {tmp_path}")
        
        # Extract text from PDF
        text = ""
        with open(tmp_path, 'rb') as f:
            pdf = PdfReader(f)
            for page in pdf.pages:
                text += page.extract_text() + "\n\n"
        
        # Save text to file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
            
        print(f"Saved EU AI Act text to {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Error downloading or processing the EU AI Act: {e}")
        raise
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and process the EU AI Act")
    parser.add_argument(
        "--output", "-o",
        help="Path to save the output text file",
        default=None
    )
    args = parser.parse_args()
    
    download_eu_ai_act(args.output)
