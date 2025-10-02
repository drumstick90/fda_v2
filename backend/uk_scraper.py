"""
UK Drug Information Scraper for eMC (Electronic Medicines Compendium)
Adds British drug indications to your FDA Search webapp
"""

import httpx
import asyncio
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional

class UKDrugScraper:
    """Scraper for UK drug information from eMC"""
    
    BASE_URL = "https://www.medicines.org.uk"
    SEARCH_URL = f"{BASE_URL}/emc/search"
    
    @staticmethod
    async def search_uk_drug(drug_name: str) -> Dict[str, str]:
        """
        Search for UK drug information from eMC
        Returns British indications and licensing info
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Search for the drug
                search_params = {"q": drug_name}
                response = await client.get(UKDrugScraper.SEARCH_URL, params=search_params)
                
                if response.status_code != 200:
                    return {
                        "drug": drug_name,
                        "uk_indications": f"Search failed: HTTP {response.status_code}",
                        "source": "eMC",
                        "url": ""
                    }
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find first product link
                product_links = soup.find_all('a', href=re.compile(r'/emc/product/'))
                
                if not product_links:
                    return {
                        "drug": drug_name,
                        "uk_indications": "No UK product found",
                        "source": "eMC",
                        "url": ""
                    }
                
                # Get the first product page
                product_url = UKDrugScraper.BASE_URL + product_links[0]['href']
                product_response = await client.get(product_url)
                
                if product_response.status_code != 200:
                    return {
                        "drug": drug_name,
                        "uk_indications": "Failed to load product page",
                        "source": "eMC",
                        "url": product_url
                    }
                
                product_soup = BeautifulSoup(product_response.text, 'html.parser')
                
                # Extract indications (Section 4.1)
                indications = UKDrugScraper._extract_indications(product_soup)
                
                return {
                    "drug": drug_name,
                    "uk_indications": indications,
                    "source": "eMC (UK)",
                    "url": product_url
                }
                
            except Exception as e:
                return {
                    "drug": drug_name,
                    "uk_indications": f"Error: {str(e)}",
                    "source": "eMC",
                    "url": ""
                }
    
    @staticmethod
    def _extract_indications(soup: BeautifulSoup) -> str:
        """Extract indications from eMC product page"""
        
        # Look for section 4.1 (Therapeutic indications)
        section_headers = soup.find_all(['h2', 'h3', 'h4'], string=re.compile(r'4\.1|Therapeutic indications|Indications', re.IGNORECASE))
        
        for header in section_headers:
            # Find the content after this header
            content_elem = header.find_next_sibling(['p', 'div'])
            if content_elem:
                # Clean up the text
                text = content_elem.get_text(strip=True)
                if len(text) > 50:  # Ensure it's substantial content
                    return text
        
        # Fallback: look for any text containing "indicated for"
        indicated_elements = soup.find_all(string=re.compile(r'indicated for', re.IGNORECASE))
        if indicated_elements:
            for elem in indicated_elements:
                parent = elem.parent
                if parent:
                    text = parent.get_text(strip=True)
                    if len(text) > 50:
                        return text
        
        return "UK indications not found in standard format"

# Example usage
async def test_uk_scraper():
    """Test the UK scraper"""
    drugs = ["risperidone", "haloperidol", "fluoxetine"]
    
    for drug in drugs:
        print(f"\\nSearching UK data for: {drug}")
        result = await UKDrugScraper.search_uk_drug(drug)
        print(f"UK Indications: {result['uk_indications'][:200]}...")
        print(f"Source: {result['source']}")

if __name__ == "__main__":
    asyncio.run(test_uk_scraper())