import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

def scrape_warning_lights(url):
    # Add headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Get the webpage content
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize lists to store data
        symbol_names = []
        image_urls = []
        meanings = []
        
        # Find all warning light sections
        warning_sections = soup.find_all(['h2', 'h3', 'h4'], string=re.compile(r'.*Warning Light.*|^\d+\.\s+.*'))
        
        for section in warning_sections:
            # Get the symbol name
            symbol_name = section.get_text().strip()
            # Remove numbering if present
            symbol_name = re.sub(r'^\d+\.\s+', '', symbol_name)
            
            # Find associated image and meaning
            image_url = ""
            meaning = ""
            
            # First try to find images in the content area
            content_div = section.find_parent('div', class_='entry-content')
            if content_div:
                # Look for images that are specifically in wp-content/uploads
                images = content_div.find_all('img', src=re.compile(r'/wp-content/uploads/'))
                for img in images:
                    src = img.get('src', '')
                    if src and '/wp-content/uploads/' in src:
                        image_url = src
                        # Find the meaning in the paragraph that follows the image
                        # Look for the next paragraph that contains the actual meaning
                        next_p = img.find_next('p')
                        while next_p:
                            text = next_p.get_text().strip()
                            # Skip paragraphs that are just the symbol name or empty
                            if text and text != symbol_name and not text.startswith('Click for detailed information'):
                                meaning = text
                                break
                            next_p = next_p.find_next('p')
                        break
            
            # If no image found in content area, try to find any image in wp-content/uploads
            if not image_url:
                img = section.find_next('img', src=re.compile(r'/wp-content/uploads/'))
                if img and 'src' in img.attrs:
                    image_url = img['src']
                    # Find the meaning in the paragraph that follows the image
                    next_p = img.find_next('p')
                    while next_p:
                        text = next_p.get_text().strip()
                        # Skip paragraphs that are just the symbol name or empty
                        if text and text != symbol_name and not text.startswith('Click for detailed information'):
                            meaning = text
                            break
                        next_p = next_p.find_next('p')
            
            # Clean up the image URL
            if image_url:
                # Remove any query parameters
                image_url = image_url.split('?')[0]
                # Ensure it's a complete URL
                if not image_url.startswith('http'):
                    if image_url.startswith('/'):
                        image_url = 'https://carwarninglights.net' + image_url
                    else:
                        image_url = 'https://carwarninglights.net/' + image_url
                # Ensure it ends with .webp
                if not image_url.endswith('.webp'):
                    image_url = image_url + '.webp'
            
            # Clean up the meaning
            if meaning:
                # Remove any "Click for detailed information" text
                meaning = re.sub(r'Click for detailed information.*$', '', meaning, flags=re.MULTILINE)
                # Remove any leading/trailing whitespace
                meaning = meaning.strip()
            
            # Add data to lists
            symbol_names.append(symbol_name)
            meanings.append(meaning)
            image_urls.append(image_url)
            
            # Add a small delay to be respectful to the server
            time.sleep(0.5)
        
        # Create DataFrame
        data = {
            'symbol_name': symbol_names,
            'image_url': image_urls,
            'meaning': meanings
        }
        df = pd.DataFrame(data)
        
        return df
        
    except requests.RequestException as e:
        print(f"Error fetching the webpage {url}: {e}")
        return None
    except Exception as e:
        print(f"Error processing the data from {url}: {e}")
        return None

def main():
    # List of URLs to scrape
    urls = [
        "https://carwarninglights.net/warning-light/50-toyota-camry-dashboard-symbols-and-meanings/",
        "https://carwarninglights.net/warning-light/toyota-venza-dashboard-lights-and-meaning/",
        "https://carwarninglights.net/warning-light/toyota-sequoia-dashboard-symbols-and-meaning/",
        "https://carwarninglights.net/warning-light/toyota-hiace-dashboard-symbols-and-meanings/",
        "https://carwarninglights.net/warning-light/50-toyota-tacoma-dashboard-symbols/",
        "https://carwarninglights.net/warning-light/50-toyota-4runner-dashboard-symbols-and-meanings/",
        "https://carwarninglights.net/warning-light/toyota-corolla-warning-lights/",
        "https://carwarninglights.net/warning-light/toyota-hilux-dashboard-symbols/"
    ]
    
    # Initialize empty DataFrame to store all data
    all_data = pd.DataFrame()
    
    # Process each URL
    for url in urls:
        print(f"\nProcessing {url}...")
        df = scrape_warning_lights(url)
        if df is not None:
            all_data = pd.concat([all_data, df], ignore_index=True)
            print(f"Successfully scraped {len(df)} symbols from {url}")
    
    if not all_data.empty:
        # Save to CSV in current directory
        output_file = 'toyota_dashboard_symbols.csv'
        all_data.to_csv(output_file, index=False)
        print(f"\nTotal symbols scraped: {len(all_data)}")
        print(f"Data successfully saved to {output_file}")
    else:
        print("No data was collected from any of the URLs.")

if __name__ == "__main__":
    main() 