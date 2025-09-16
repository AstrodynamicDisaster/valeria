import requests
import ollama
import sys, pymupdf, pathlib

def load_image(image_path_or_url):
    """Load image bytes from a local path or URL."""
    if image_path_or_url.startswith('http://') or image_path_or_url.startswith('https://'):
        print(f"Downloading image from: {image_path_or_url}")
        response = requests.get(image_path_or_url)
        response.raise_for_status() # Ensure download was successful
        return response.content
    elif '.pdf' in image_path_or_url:
        print(f"Loading PDF from local path: {image_path_or_url}")
        return get_pdf_pages(image_path_or_url)
    else :
        print(f"Loading image from local path: {image_path_or_url}")
        with open(image_path_or_url, 'rb') as f:
            return f.read()
        
def vision_inference(prompt, image_path_or_url, model='hf.co/unsloth/gemma-3-4b-it-GGUF:Q4_K_M'):
    try:
        image_bytes = load_image(image_path_or_url)
        
        print(f"\nSending prompt to qwen2.5vl-3b ({model}): '{prompt}'")
        response = ollama.chat(
            model=model,
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                    'images': image_bytes, # Image bytes are passed here
                }
            ]
        )
        
        if 'message' in response and 'content' in response['message']:
            print(f"\n Qwen Says:\n{response['message']['content']}")
        else:
            print(f"Unexpected response format from Ollama: {response}")
            
    except Exception as e:
        print(f"An error occurred: {e}")

def text_inference(prompt, image_path_or_url, model='hf.co/unsloth/gemma-3-4b-it-GGUF:Q4_K_M'):
    try:
        pdf_extract_text(image_path_or_url)
        with open(image_path_or_url + ".txt", 'rb') as f:
            image_bytes = f.read()
        
        print(f"\nSending prompt to qwen2.5vl-3b ({model}): '{prompt}'")
        response = ollama.chat(
            model=model,
            messages=[
                {
                    'role': 'user',
                    'content': prompt+ "\n" + image_bytes.decode('utf-8')
                }
            ]
        )
        
        if 'message' in response and 'content' in response['message']:
            print(f"\n Qwen Says:\n{response['message']['content']}")
        else:
            print(f"Unexpected response format from Ollama: {response}")
            
    except Exception as e:
        print(f"An error occurred: {e}")

# Write a function that calls openAI vision model to extract the text from a file


def pdf_extract_text(pdf_path):
    with pymupdf.open(pdf_path) as doc:  # open document
        text = chr(12).join([page.get_text() for page in doc])
    # write as a binary file to support non-ASCII characters
    pathlib.Path(pdf_path + ".txt").write_bytes(text.encode())
    return None

def get_pdf_pages(pdf_path):
    """Extract pages from a PDF and return as a list of images."""
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    images = []
    for page in doc:
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        images.append(img_data)
    return images

if __name__ == "__main__":
    print("--- Example: Analyzing a URL Image with Qwen2.5-VL ---")
    # Example image of a car license plate
    local_image_path = "T_Dec.pdf"
    pdf_extract_text(local_image_path)


    print("\n--- Example: Describing a Local Image with Qwen2.5-VL ---")
    try: 
        text_inference(
            prompt="Extract all the names of the employees from the extracted data from a pdf document",
            image_path_or_url=local_image_path
        )
        # vision_inference(
        #      prompt="Extract all the names of the employees from the extracted data from a pdf document",
        #      image_path_or_url=local_image_path
        #  )
    except ImportError:
        print("PIL not installed, cannot create dummy image. Please install it with 'pip install pillow'.")
    except Exception as e:
        print(f"Error with local image example: {e}")
    finally:
        print("\n--- End of Examples ---")