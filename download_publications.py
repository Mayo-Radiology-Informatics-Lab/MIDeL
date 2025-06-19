#!/usr/bin/env python3
"""
Publication PDF Downloader

This script reads a CSV file with publication information and downloads PDFs
from DOI links, saving them with structured filenames.

Required CSV columns: Title, First Author, Publication Year, DOI

Usage:
    python download_publications.py

Requirements:
    pip install requests pandas beautifulsoup4 lxml
"""

import pandas as pd
import requests
import os
import re
import time
import ssl
import urllib3
import getpass
import json
from urllib.parse import urljoin, urlparse
from pathlib import Path
from datetime import datetime
import logging

# Disable SSL warnings for requests with verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_ssl_setup():
    """
    Check SSL setup and provide guidance for macOS users.
    """
    try:
        # Test basic SSL connection
        response = requests.get('https://httpbin.org/get', timeout=10, verify=True)
        logger.info("SSL verification working correctly")
        return True
    except requests.exceptions.SSLError as e:
        logger.warning("SSL verification issues detected")
        logger.warning("This is common on macOS. The script will continue with SSL verification disabled.")
        logger.warning("For better security, consider running: /Applications/Python\\ 3.x/Install\\ Certificates.command")
        return False
    except Exception as e:
        logger.warning(f"SSL check failed: {str(e)}")
        return False

def clean_filename(text):
    """Clean text to be safe for filename use."""
    # Remove or replace problematic characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Replace multiple spaces with single space
    cleaned = cleaned.strip()
    # Limit length to avoid filesystem issues
    if len(cleaned) > 200:
        cleaned = cleaned[:200] + "..."
    return cleaned

def clean_doi(doi):
    """
    Clean and standardize DOI format.
    
    Args:
        doi (str): Raw DOI string
        
    Returns:
        str: Cleaned DOI identifier (without URL prefix)
    """
    doi = doi.strip()
    
    # Remove common URL prefixes if present
    if doi.startswith('https://doi.org/'):
        doi = doi.replace('https://doi.org/', '')
    elif doi.startswith('http://doi.org/'):
        doi = doi.replace('http://doi.org/', '')
    elif doi.startswith('doi:'):
        doi = doi.replace('doi:', '')
    elif doi.startswith('DOI:'):
        doi = doi.replace('DOI:', '')
    
    # Ensure DOI starts with 10.
    if not doi.startswith('10.'):
        logger.warning(f"DOI doesn't start with '10.': {doi}")
    
    return doi

def resolve_doi_to_pdf_url(doi):
    """
    Resolve a DOI identifier to a PDF URL by:
    1. Using the standard DOI resolver (https://doi.org/)
    2. Following redirects to publisher page
    3. Parsing the page for PDF download links
    
    Args:
        doi (str): DOI identifier (e.g., "10.1038/nature12373")
        
    Returns:
        str or None: PDF URL if found, None otherwise
    """
    # Clean DOI identifier
    clean_doi_id = clean_doi(doi)
    doi_url = f"https://doi.org/{clean_doi_id}"
    
    logger.info(f"Resolving DOI identifier: {clean_doi_id}")
    logger.info(f"DOI resolver URL: {doi_url}")
    
    try:
        # Set headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Resolve DOI through official resolver
        # Try with SSL verification first, then without if it fails
        try:
            response = requests.get(doi_url, headers=headers, allow_redirects=True, timeout=30, verify=True)
            response.raise_for_status()
        except requests.exceptions.SSLError:
            logger.warning(f"SSL verification failed for {doi_url}, trying without verification")
            response = requests.get(doi_url, headers=headers, allow_redirects=True, timeout=30, verify=False)
            response.raise_for_status()
        
        publisher_url = response.url
        logger.info(f"DOI resolved to publisher page: {publisher_url}")
        
        # Check if we were redirected directly to a PDF
        if publisher_url.lower().endswith('.pdf'):
            logger.info(f"DOI resolved directly to PDF: {publisher_url}")
            return publisher_url
        
        # Parse the publisher page to find PDF links
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Strategy 1: Look for links with PDF-related text or attributes
        pdf_candidates = []
        
        # Find links with PDF-related text
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True).lower()
            
            # Check for PDF indicators in text
            if any(indicator in text for indicator in ['pdf', 'download', 'full text']):
                pdf_candidates.append((href, f"text: {text}"))
            
            # Check for PDF indicators in href
            if any(indicator in href.lower() for indicator in ['.pdf', 'pdf', 'download']):
                pdf_candidates.append((href, f"href: {href}"))
        
        # Strategy 2: Publisher-specific PDF URL patterns
        publisher_patterns = get_publisher_pdf_patterns(publisher_url, soup)
        pdf_candidates.extend(publisher_patterns)
        
        # Strategy 3: Look for meta tags with PDF info
        meta_pdf_url = find_pdf_in_meta_tags(soup, publisher_url)
        if meta_pdf_url:
            pdf_candidates.append((meta_pdf_url, "meta tag"))
        
        # Process candidates and return the best match
        for candidate_url, source in pdf_candidates:
            # Convert relative URLs to absolute
            if candidate_url.startswith('/'):
                base_url = f"{urlparse(publisher_url).scheme}://{urlparse(publisher_url).netloc}"
                candidate_url = base_url + candidate_url
            elif not candidate_url.startswith('http'):
                candidate_url = urljoin(publisher_url, candidate_url)
            
            # Validate URL looks like a PDF
            if is_likely_pdf_url(candidate_url):
                logger.info(f"Found PDF candidate from {source}: {candidate_url}")
                return candidate_url
        
        # If no specific PDF found, try the publisher URL itself (might be a PDF)
        logger.warning(f"No specific PDF link found, trying publisher URL: {publisher_url}")
        return publisher_url
        
    except Exception as e:
        logger.error(f"Error resolving DOI {clean_doi_id}: {str(e)}")
        return None

def get_publisher_pdf_patterns(url, soup):
    """
    Get publisher-specific PDF URL patterns.
    
    Args:
        url (str): Publisher page URL
        soup: BeautifulSoup object of the page
        
    Returns:
        list: List of (url, source) tuples for potential PDF links
    """
    candidates = []
    
    try:
        if 'ncbi.nlm.nih.gov' in url:
            # PubMed Central
            if '/pmc/articles/' in url:
                pmc_match = re.search(r'/pmc/articles/([^/]+)', url)
                if pmc_match:
                    pmc_id = pmc_match.group(1)
                    pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"
                    candidates.append((pdf_url, "PMC pattern"))
            
            # Look for PDF links in PMC pages
            for link in soup.find_all('a', href=True):
                if 'pdf' in link['href'] and '/pmc/' in link['href']:
                    candidates.append((link['href'], "PMC PDF link"))
        
        elif 'nature.com' in url:
            # Nature publications
            for link in soup.find_all('a', href=True):
                if '.pdf' in link['href'] or 'download' in link['href']:
                    candidates.append((link['href'], "Nature pattern"))
        
        elif 'sciencedirect.com' in url or 'elsevier.com' in url:
            # Elsevier/ScienceDirect
            for link in soup.find_all('a', href=True):
                if 'pdfdownload' in link['href'] or 'pdf' in link['href']:
                    candidates.append((link['href'], "Elsevier pattern"))
        
        elif 'springer.com' in url or 'link.springer.com' in url:
            # Springer
            for link in soup.find_all('a', href=True):
                if 'content/pdf' in link['href'] or 'download' in link['href']:
                    candidates.append((link['href'], "Springer pattern"))
        
        elif 'wiley.com' in url:
            # Wiley
            for link in soup.find_all('a', href=True):
                if 'pdfdirect' in link['href'] or 'pdf' in link['href']:
                    candidates.append((link['href'], "Wiley pattern"))
        
        elif 'ieee.org' in url:
            # IEEE
            for link in soup.find_all('a', href=True):
                if 'pdf' in link['href'] and 'download' in link.get_text(strip=True).lower():
                    candidates.append((link['href'], "IEEE pattern"))
    
    except Exception as e:
        logger.warning(f"Error in publisher pattern matching: {str(e)}")
    
    return candidates

def find_pdf_in_meta_tags(soup, base_url):
    """
    Look for PDF URLs in meta tags.
    
    Args:
        soup: BeautifulSoup object
        base_url (str): Base URL for relative links
        
    Returns:
        str or None: PDF URL if found
    """
    try:
        # Look for citation_pdf_url meta tag (common in academic papers)
        pdf_meta = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        if pdf_meta and pdf_meta.get('content'):
            return pdf_meta['content']
        
        # Look for other PDF-related meta tags
        for meta in soup.find_all('meta'):
            content = meta.get('content', '')
            if content and '.pdf' in content.lower():
                return content
    
    except Exception as e:
        logger.warning(f"Error searching meta tags: {str(e)}")
    
    return None

def is_likely_pdf_url(url):
    """
    Check if URL is likely to point to a PDF.
    
    Args:
        url (str): URL to check
        
    Returns:
        bool: True if likely a PDF URL
    """
    url_lower = url.lower()
    
    # Direct PDF file
    if url_lower.endswith('.pdf'):
        return True
    
    # Common PDF URL patterns
    pdf_indicators = [
        'pdf',
        'download',
        'filetype=pdf',
        'content-type=application/pdf'
    ]
    
    return any(indicator in url_lower for indicator in pdf_indicators)

def try_alternative_doi_resolver(doi_url):
    """
    Try alternative DOI resolvers as fallback.
    
    Args:
        doi_url (str): Alternative DOI resolver URL
        
    Returns:
        str or None: PDF URL if found, None otherwise
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        # Try with and without SSL verification
        try:
            response = requests.get(doi_url, headers=headers, allow_redirects=True, timeout=30, verify=True)
        except requests.exceptions.SSLError:
            response = requests.get(doi_url, headers=headers, allow_redirects=True, timeout=30, verify=False)
        
        response.raise_for_status()
        
        # Simple check - if we get redirected to a PDF or a page with PDF links
        if response.url.lower().endswith('.pdf'):
            return response.url
            
        # Try to find PDF links in the response
        if 'pdf' in response.text.lower():
            # Basic regex to find PDF links
            pdf_matches = re.findall(r'href=["\']([^"\']*\.pdf[^"\']*)["\']', response.text, re.IGNORECASE)
            if pdf_matches:
                return urljoin(response.url, pdf_matches[0])
        
        return response.url  # Return the page URL as last resort
        
    except Exception as e:
        logger.warning(f"Alternative resolver failed: {str(e)}")
        return None

def load_publications_json(filepath):
    """
    Load existing publications.json file.
    
    Args:
        filepath (str): Path to publications.json file
        
    Returns:
        list: List of year groups, or empty list if file doesn't exist
    """
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.info(f"Publications file {filepath} not found, will create new one")
            return []
    except Exception as e:
        logger.error(f"Error loading publications.json: {str(e)}")
        return []

def save_publications_json(data, filepath):
    """
    Save publications data to JSON file.
    
    Args:
        data (list): Publications data
        filepath (str): Path to save file
        
    Returns:
        bool: True if successful
    """
    try:
        # Create backup of existing file
        if os.path.exists(filepath):
            backup_path = filepath + f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(filepath, backup_path)
            logger.info(f"Created backup: {backup_path}")
        
        # Sort years in descending order
        data.sort(key=lambda x: float('inf') if x['year'] == 'older' else x['year'], reverse=True)
        
        # Save new file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Updated publications.json: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving publications.json: {str(e)}")
        return False

def generate_publication_id(year, first_author, title):
    """
    Generate a unique publication ID.
    
    Args:
        year (str): Publication year
        first_author (str): First author last name
        title (str): Publication title
        
    Returns:
        str: Unique publication ID
    """
    # Clean and truncate components
    year_clean = str(year)
    author_clean = re.sub(r'[^a-zA-Z]', '', first_author)[:15]
    title_clean = re.sub(r'[^a-zA-Z0-9\s]', '', title)
    title_words = title_clean.split()[:5]  # First 5 words
    title_short = '_'.join(title_words)
    
    # Create ID
    pub_id = f"{year_clean}_{author_clean}_{title_short}".lower()
    
    # Remove any double underscores
    pub_id = re.sub(r'_+', '_', pub_id)
    
    return pub_id

def add_publication_to_json(publications_data, year, first_author, title, doi, pdf_url=None):
    """
    Add a new publication to the publications data structure.
    
    Args:
        publications_data (list): Existing publications data
        year (str): Publication year
        first_author (str): First author last name
        title (str): Publication title
        doi (str): DOI
        pdf_url (str): PDF URL if available
        
    Returns:
        bool: True if added, False if duplicate found
    """
    try:
        # Generate publication ID
        pub_id = generate_publication_id(year, first_author, title)
        
        # Check for duplicates by title (case-insensitive)
        title_lower = title.lower()
        for year_group in publications_data:
            for pub in year_group.get('publications', []):
                if pub.get('title', '').lower() == title_lower:
                    logger.warning(f"Duplicate publication found: {title}")
                    return False
        
        # Determine year category
        try:
            year_int = int(year)
            if year_int < 2022:
                year_category = "older"
            else:
                year_category = year_int
        except ValueError:
            year_category = "older"
        
        # Find or create year group
        year_group = None
        for group in publications_data:
            if group['year'] == year_category:
                year_group = group
                break
        
        if year_group is None:
            year_group = {
                'year': year_category,
                'publications': []
            }
            publications_data.append(year_group)
        
        # Create publication entry
        publication = {
            'id': pub_id,
            'title': title,
            'url': pdf_url if pdf_url else '',  # Leave empty if no URL resolved
            'type': 'journal',
            'status': 'published'
        }
        
        # Add to publications
        year_group['publications'].append(publication)
        
        logger.info(f"Added publication: {title} ({year})")
        return True
        
    except Exception as e:
        logger.error(f"Error adding publication {title}: {str(e)}")
        return False

def update_publications_json_file(csv_data, publications_json_path):
    """
    Update the publications.json file with data from CSV.
    
    Args:
        csv_data (DataFrame): CSV data with publications
        publications_json_path (str): Path to publications.json file
        
    Returns:
        tuple: (added_count, skipped_count)
    """
    logger.info("Updating publications.json file...")
    
    # Load existing publications
    publications_data = load_publications_json(publications_json_path)
    
    added_count = 0
    skipped_count = 0
    
    for index, row in csv_data.iterrows():
        try:
            title = str(row['Title']).strip()
            first_author = str(row['First Author']).strip()
            year = str(row['Publication Year']).strip()
            doi = str(row['DOI']).strip()
            
            # Skip rows with missing data
            if pd.isna(row['Title']) or pd.isna(row['DOI']) or not title or not doi:
                logger.warning(f"Skipping row {index + 1}: missing title or DOI")
                skipped_count += 1
                continue
            
            # Try to resolve DOI to get URL (but don't fail if it doesn't work)
            pdf_url = None
            try:
                pdf_url = resolve_doi_to_pdf_url(doi)
                if pdf_url and not is_likely_pdf_url(pdf_url):
                    pdf_url = None  # Don't use if it doesn't look like a PDF
            except Exception as e:
                logger.warning(f"Could not resolve DOI for {title}: {str(e)}")
            
            # Add to publications data
            if add_publication_to_json(publications_data, year, first_author, title, doi, pdf_url):
                added_count += 1
            else:
                skipped_count += 1
                
        except Exception as e:
            logger.error(f"Error processing row {index + 1}: {str(e)}")
            skipped_count += 1
    
    # Save updated publications.json
    if added_count > 0:
        if save_publications_json(publications_data, publications_json_path):
            logger.info(f"Successfully updated publications.json: {added_count} added, {skipped_count} skipped")
        else:
            logger.error("Failed to save publications.json")
    else:
        logger.info("No new publications to add to publications.json")
    
    return added_count, skipped_count

def download_pdf(url, filepath, max_retries=3, session=None):
    """
    Download a PDF from URL to filepath.
    
    Args:
        url (str): URL to download from
        filepath (str): Local filepath to save to
        max_retries (int): Maximum number of retry attempts
        session: Authenticated requests session (optional)
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Use provided session or create a new one
    if session is None:
        session = requests.Session()
    # Try different user agents to avoid blocking
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]
    
    for attempt in range(max_retries):
        # Try different user agents on retries
        headers = {
            'User-Agent': user_agents[attempt % len(user_agents)],
            'Accept': 'application/pdf,application/octet-stream,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': url,  # Some sites require a referer
        }
        
        try:
            logger.info(f"Downloading (attempt {attempt + 1}): {url}")
            # Try with SSL verification first, then without if it fails
            try:
                response = session.get(url, headers=headers, stream=True, timeout=60, verify=True)
                response.raise_for_status()
            except requests.exceptions.SSLError:
                logger.warning(f"SSL verification failed for {url}, trying without verification")
                response = session.get(url, headers=headers, stream=True, timeout=60, verify=False)
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if response.status_code == 403:
                    logger.warning(f"Access forbidden (403) for {url} - may require subscription or institutional access")
                    # Try a different approach for 403 errors
                    if attempt < max_retries - 1:
                        logger.info("Trying with different headers and delay...")
                        time.sleep(5)  # Wait longer between attempts
                        continue
                raise
            
            # Check if response is actually a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
                # Check first few bytes for PDF signature
                first_chunk = next(response.iter_content(1024), b'')
                if not first_chunk.startswith(b'%PDF'):
                    logger.warning(f"URL may not be a PDF: {url}")
                    # Continue anyway - might still be a PDF
            
            # Download the file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify file was downloaded and has content
            if os.path.getsize(filepath) > 1000:  # At least 1KB
                logger.info(f"Successfully downloaded: {filepath}")
                return True
            else:
                logger.warning(f"Downloaded file seems too small: {filepath}")
                os.remove(filepath)
                
        except Exception as e:
            logger.error(f"Download attempt {attempt + 1} failed: {str(e)}")
            if os.path.exists(filepath):
                os.remove(filepath)
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    
    return False

def create_download_report(publications_dir, successful, failed, failed_papers=None):
    """
    Create a summary report of the download process.
    
    Args:
        publications_dir (Path): Directory containing downloaded PDFs
        successful (int): Number of successful downloads
        failed (int): Number of failed downloads
        failed_papers (list): List of dictionaries with failed paper details
    """
    try:
        # List downloaded files
        pdf_files = list(publications_dir.glob("*.pdf"))
        
        report_path = publications_dir / "download_report.txt"
        with open(report_path, 'w') as f:
            f.write("Publication Download Report\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Total processed: {successful + failed}\n")
            f.write(f"Successful downloads: {successful}\n")
            f.write(f"Failed downloads: {failed}\n")
            if successful + failed > 0:
                f.write(f"Success rate: {(successful/(successful + failed)*100):.1f}%\n\n")
            
            f.write("Downloaded Files:\n")
            f.write("-" * 20 + "\n")
            for pdf_file in sorted(pdf_files):
                size_mb = pdf_file.stat().st_size / (1024 * 1024)
                f.write(f"{pdf_file.name} ({size_mb:.1f} MB)\n")
            
            # Add failed downloads section
            if failed_papers and len(failed_papers) > 0:
                f.write(f"\nFailed Downloads ({len(failed_papers)}):\n")
                f.write("-" * 30 + "\n")
                for paper in failed_papers:
                    f.write(f"{paper['title']} | {paper['authors']} | {paper['doi']}\n")
            
            f.write(f"\nReport generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print(f"Download report saved to: {report_path}")
        
    except Exception as e:
        logger.warning(f"Could not create download report: {str(e)}")

def authenticate_rsna(session, username, password):
    """
    Authenticate with RSNA website.
    
    Args:
        session: requests.Session object
        username (str): RSNA username
        password (str): RSNA password
        
    Returns:
        bool: True if authentication successful
    """
    try:
        logger.info("Attempting to authenticate with RSNA...")
        
        # Get the login page first
        login_url = "https://pubs.rsna.org/action/showLogin"
        
        try:
            response = session.get(login_url, timeout=30, verify=True)
        except requests.exceptions.SSLError:
            response = session.get(login_url, timeout=30, verify=False)
        
        if response.status_code != 200:
            logger.error(f"Could not access RSNA login page: {response.status_code}")
            return False
        
        # Extract any necessary form data (CSRF tokens, etc.)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the login form
        login_form = soup.find('form', {'id': 'loginForm'}) or soup.find('form', action=lambda x: x and 'login' in x.lower())
        
        if not login_form:
            logger.error("Could not find login form on RSNA page")
            return False
        
        # Prepare login data
        login_data = {
            'username': username,
            'password': password,
        }
        
        # Add any hidden form fields
        for input_field in login_form.find_all('input', type='hidden'):
            name = input_field.get('name')
            value = input_field.get('value', '')
            if name:
                login_data[name] = value
        
        # Submit login
        login_action = login_form.get('action', '/action/doLogin')
        if not login_action.startswith('http'):
            login_action = 'https://pubs.rsna.org' + login_action
        
        try:
            login_response = session.post(login_action, data=login_data, timeout=30, verify=True)
        except requests.exceptions.SSLError:
            login_response = session.post(login_action, data=login_data, timeout=30, verify=False)
        
        # Check if login was successful
        if login_response.status_code == 200:
            # Look for indicators of successful login
            if 'logout' in login_response.text.lower() or 'sign out' in login_response.text.lower():
                logger.info("RSNA authentication successful!")
                return True
            elif 'invalid' in login_response.text.lower() or 'error' in login_response.text.lower():
                logger.error("RSNA authentication failed - invalid credentials")
                return False
        
        logger.warning("RSNA authentication status unclear - continuing anyway")
        return True  # Assume success if we can't determine otherwise
        
    except Exception as e:
        logger.error(f"RSNA authentication error: {str(e)}")
        return False

def main():
    """Main function to process the CSV and download PDFs."""
    
    # Check SSL setup
    ssl_working = check_ssl_setup()
    if not ssl_working:
        print("Note: SSL verification issues detected. Downloads will continue with reduced security.")
        print("This is common on macOS and the script should still work.\n")
    
    # Ask for credentials if needed
    rsna_username = None
    rsna_password = None
    
    use_rsna_auth = input("Do you have RSNA credentials? (y/n): ").lower().strip()
    if use_rsna_auth in ['y', 'yes']:
        rsna_username = input("RSNA Username: ").strip()
        rsna_password = getpass.getpass("RSNA Password (hidden): ")
        if not rsna_username or not rsna_password:
            print("Username or password is empty. Continuing without RSNA authentication.")
            rsna_username = rsna_password = None
    
    # Ask about updating publications.json
    update_json = input("Do you want to update publications.json file? (y/n): ").lower().strip()
    update_json = update_json in ['y', 'yes']
    
    publications_json_path = './assets/html/publications.json'
    if update_json and not os.path.exists('./assets'):
        print("Warning: ./assets/html/ directory not found. publications.json will be created in current directory.")
        publications_json_path = './publications.json'
    
    # Create session for authentication
    auth_session = requests.Session()
    rsna_authenticated = False
    
    if rsna_username and rsna_password:
        rsna_authenticated = authenticate_rsna(auth_session, rsna_username, rsna_password)
    
    # Keep track of publishers that consistently return 403
    blocked_publishers = set()
    subscription_domains = {
        'pubs.rsna.org': 'RSNA (Radiological Society of North America)',
        'www.sciencedirect.com': 'ScienceDirect/Elsevier',
        'link.springer.com': 'Springer',
        'onlinelibrary.wiley.com': 'Wiley Online Library',
        'journals.lww.com': 'Lippincott Williams & Wilkins',
        'academic.oup.com': 'Oxford Academic'
    }
    
    # Check if CSV file exists
    csv_file = 'pubs.csv'
    if not os.path.exists(csv_file):
        logger.error(f"CSV file '{csv_file}' not found in current directory")
        print(f"Please ensure '{csv_file}' exists in the current directory")
        return
    
    # Create publications directory
    publications_dir = Path('publications')
    publications_dir.mkdir(exist_ok=True)
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_file)
        logger.info(f"Read {len(df)} rows from {csv_file}")
        
        # Verify required columns exist
        required_columns = ['Title', 'First Author', 'Publication Year', 'DOI']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            print(f"CSV must contain columns: {required_columns}")
            print(f"Found columns: {list(df.columns)}")
            return
        
        # Update publications.json if requested
        json_added = 0
        json_skipped = 0
        if update_json:
            try:
                json_added, json_skipped = update_publications_json_file(df, publications_json_path)
                print(f"\nPublications.json update: {json_added} added, {json_skipped} skipped")
            except Exception as e:
                logger.error(f"Failed to update publications.json: {str(e)}")
                print("Failed to update publications.json. Continuing with PDF downloads...")
        
        # Process each row
        successful_downloads = 0
        failed_downloads = 0
        failed_papers = []  # Track details of failed downloads
        
        for index, row in df.iterrows():
            try:
                title = str(row['Title']).strip()
                first_author = str(row['First Author']).strip()
                year = str(row['Publication Year']).strip()
                doi = str(row['DOI']).strip()
                
                # Skip rows with missing data
                if pd.isna(row['Title']) or pd.isna(row['DOI']) or not doi:
                    logger.warning(f"Skipping row {index + 1}: missing title or DOI")
                    failed_downloads += 1
                    failed_papers.append({
                        'title': title if title else 'Missing Title',
                        'authors': first_author if first_author else 'Missing Author',
                        'doi': doi if doi else 'Missing DOI'
                    })
                    continue
                
                # Create filename
                filename_parts = [year, first_author, title]
                filename_clean = '-'.join([clean_filename(part) for part in filename_parts if part])
                filename = f"{filename_clean}.pdf"
                filepath = publications_dir / filename
                
                # Skip if file already exists
                if filepath.exists():
                    logger.info(f"File already exists, skipping: {filename}")
                    successful_downloads += 1
                    continue
                
                logger.info(f"Processing row {index + 1}: {title[:50]}...")
                
                # Resolve DOI to PDF URL
                pdf_url = resolve_doi_to_pdf_url(doi)
                if not pdf_url:
                    logger.error(f"Could not resolve DOI to URL: {doi}")
                    # Try alternative DOI resolvers as fallback
                    alternative_resolvers = [
                        f"https://dx.doi.org/{clean_doi(doi)}",
                        f"http://doi.org/{clean_doi(doi)}"
                    ]
                    
                    for alt_url in alternative_resolvers:
                        logger.info(f"Trying alternative resolver: {alt_url}")
                        pdf_url = try_alternative_doi_resolver(alt_url)
                        if pdf_url:
                            break
                    
                    if not pdf_url:
                        failed_downloads += 1
                        failed_papers.append({
                            'title': title,
                            'authors': first_author,
                            'doi': doi
                        })
                        continue
                
                # Download PDF - use authenticated session for RSNA
                download_session = auth_session if rsna_authenticated and 'rsna.org' in pdf_url else None
                if download_pdf(pdf_url, filepath, session=download_session):
                    successful_downloads += 1
                else:
                    logger.error(f"Failed to download PDF for: {title[:50]}...")
                    failed_downloads += 1
                    failed_papers.append({
                        'title': title,
                        'authors': first_author,
                        'doi': doi
                    })
                
                # Be respectful to servers
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing row {index + 1}: {str(e)}")
                failed_downloads += 1
                failed_papers.append({
                    'title': title if 'title' in locals() else 'Unknown Title',
                    'authors': first_author if 'first_author' in locals() else 'Unknown Author',
                    'doi': doi if 'doi' in locals() else 'Unknown DOI'
                })
                continue
        
        # Summary
        total_processed = successful_downloads + failed_downloads
        logger.info(f"Processing complete!")
        logger.info(f"Total papers processed: {total_processed}")
        logger.info(f"Successful downloads: {successful_downloads}")
        logger.info(f"Failed downloads: {failed_downloads}")
        
        print(f"\nSummary:")
        print(f"Total papers processed: {total_processed}")
        print(f"Successful downloads: {successful_downloads}")
        print(f"Failed downloads: {failed_downloads}")
        print(f"PDFs saved in: {publications_dir.absolute()}")
        
        if update_json:
            print(f"\nPublications.json Summary:")
            print(f"Publications added to JSON: {json_added}")
            print(f"Publications skipped (duplicates): {json_skipped}")
            if json_added > 0:
                print(f"Publications.json updated: {publications_json_path}")
        
        # Create a summary report
        create_download_report(publications_dir, successful_downloads, failed_downloads, failed_papers)
        
        if failed_downloads > 0:
            print(f"\nNote: {failed_downloads} downloads failed.")
            print("Common reasons for failures:")
            print("- Publisher requires subscription/institutional access")
            print("- Anti-bot protection blocking automated downloads")
            print("- DOI points to abstract page without public PDF")
            print("- Temporary server issues")
            print("\nCheck the log messages above for specific error details.")
            print("You may need to manually download some papers from publisher websites.")
        
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}")
        print(f"Error: Could not read CSV file. Please check the file format.")

if __name__ == "__main__":
    print("Publication PDF Downloader & JSON Updater")
    print("=" * 50)
    print("This script will:")
    print("1. Download PDFs from DOI links in pubs.csv")
    print("2. Optionally update publications.json for the MIDeL website")
    print("")
    print("Required CSV columns: Title, First Author, Publication Year, DOI")
    print("PDFs will be saved to ./publications/ directory")
    print("publications.json will be updated with new entries (URLs may be empty)")
    print("")
    print("Note for macOS users:")
    print("If you encounter SSL certificate errors, you can fix them by running:")
    print("  /Applications/Python\\ 3.*/Install\\ Certificates.command")
    print("Or the script will continue with SSL verification disabled.")
    print("=" * 50)
    
    main()