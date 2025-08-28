"""
Web Scraping Module - INGESTION UTILITY
This is a standalone utility for data collection, NOT loaded during FastAPI runtime.
Based on no1_scraping_engine.ipynb implementation.
"""

import time
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class ScrapedDocument:
    """Represents a scraped research document."""
    title: str
    content: str
    url: str
    metadata: Dict[str, Any]
    abstract: Optional[str] = None
    authors: List[str] = None
    publication_date: Optional[str] = None
    doi: Optional[str] = None


class ResearchScraper:
    """
    Web scraper for research papers and academic content.
    Based on no1_scraping_engine.ipynb - STANDALONE INGESTION TOOL.
    """
    
    def __init__(
        self,
        delay_between_requests: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize research scraper.
        
        Args:
            delay_between_requests: Respectful delay between requests
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.delay = delay_between_requests
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        
        # Set respectful headers
        self.session.headers.update({
            'User-Agent': 'PsyWiz Research Bot 1.0 (Educational Purpose)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Track visited URLs to avoid duplicates
        self.visited_urls: Set[str] = set()
        
        logger.info("ResearchScraper initialized for data collection")
    
    def scrape_url(self, url: str) -> Optional[ScrapedDocument]:
        """
        Scrape a single research paper URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            ScrapedDocument or None if scraping failed
        """
        if url in self.visited_urls:
            logger.info(f"URL already visited: {url}")
            return None
        
        try:
            logger.info(f"Scraping: {url}")
            
            # Respectful delay
            time.sleep(self.delay)
            
            # Make request with retries
            response = self._make_request(url)
            if not response:
                return None
            
            # Parse content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract document information
            doc = self._extract_document_info(url, soup)
            
            if doc:
                self.visited_urls.add(url)
                logger.info(f"Successfully scraped: {doc.title[:50]}...")
                return doc
            else:
                logger.warning(f"No content extracted from {url}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {str(e)}")
            return None
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Make HTTP request with retries."""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        logger.error(f"All request attempts failed for {url}")
        return None
    
    def _extract_document_info(self, url: str, soup: BeautifulSoup) -> Optional[ScrapedDocument]:
        """Extract document information from parsed HTML."""
        try:
            # Extract title
            title = self._extract_title(soup)
            if not title:
                return None
            
            # Extract main content
            content = self._extract_content(soup)
            if not content or len(content) < 100:
                return None
            
            # Extract metadata
            metadata = self._extract_metadata(url, soup)
            
            # Extract specific academic fields
            abstract = self._extract_abstract(soup)
            authors = self._extract_authors(soup)
            pub_date = self._extract_publication_date(soup)
            doi = self._extract_doi(soup)
            
            return ScrapedDocument(
                title=title,
                content=content,
                url=url,
                metadata=metadata,
                abstract=abstract,
                authors=authors or [],
                publication_date=pub_date,
                doi=doi
            )
            
        except Exception as e:
            logger.error(f"Error extracting document info: {str(e)}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract document title."""
        # Try multiple title selectors
        title_selectors = [
            'h1.article-title',
            'h1.entry-title',
            'h1.post-title',
            'h1[class*="title"]',
            'title',
            'h1',
            '.title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                if len(title) > 5:  # Reasonable title length
                    return title
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main content from the page."""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Try content selectors in order of preference
        content_selectors = [
            'article',
            '.article-content',
            '.content',
            '.post-content',
            '.entry-content',
            'main',
            '#content',
            '.main-content'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator='\n', strip=True)
                if len(text) > 200:  # Reasonable content length
                    return self._clean_content(text)
        
        # Fallback: extract all paragraph text
        paragraphs = soup.find_all('p')
        if paragraphs:
            text = '\n'.join([p.get_text(strip=True) for p in paragraphs])
            return self._clean_content(text)
        
        return None
    
    def _clean_content(self, text: str) -> str:
        """Clean extracted content."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove common noise patterns
        text = re.sub(r'cookie.*?policy|privacy.*?policy', '', text, flags=re.IGNORECASE)
        text = re.sub(r'subscribe.*?newsletter', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def _extract_abstract(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract abstract if available."""
        abstract_selectors = [
            '.abstract',
            '#abstract',
            '[class*="abstract"]',
            '.summary'
        ]
        
        for selector in abstract_selectors:
            element = soup.select_one(selector)
            if element:
                abstract = element.get_text(strip=True)
                if 50 < len(abstract) < 2000:  # Reasonable abstract length
                    return abstract
        
        return None
    
    def _extract_authors(self, soup: BeautifulSoup) -> List[str]:
        """Extract author names."""
        authors = []
        
        author_selectors = [
            '.author',
            '.authors',
            '[class*="author"]',
            '.byline'
        ]
        
        for selector in author_selectors:
            elements = soup.select(selector)
            for element in elements:
                author_text = element.get_text(strip=True)
                # Simple author extraction (can be improved)
                if author_text and len(author_text) < 100:
                    authors.append(author_text)
        
        return authors[:10]  # Limit to reasonable number
    
    def _extract_publication_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date."""
        date_selectors = [
            'time[datetime]',
            '.publication-date',
            '.date',
            '[class*="date"]'
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                # Try datetime attribute first
                date = element.get('datetime')
                if not date:
                    date = element.get_text(strip=True)
                
                if date and len(date) > 4:  # Basic date validation
                    return date
        
        return None
    
    def _extract_doi(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract DOI if available."""
        # Look for DOI patterns
        doi_pattern = re.compile(r'10\.\d{4,}/[^\s]+')
        
        # Check text content for DOI
        text = soup.get_text()
        doi_match = doi_pattern.search(text)
        if doi_match:
            return doi_match.group()
        
        # Check meta tags
        doi_meta = soup.find('meta', {'name': 'citation_doi'})
        if doi_meta:
            return doi_meta.get('content')
        
        return None
    
    def _extract_metadata(self, url: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract general metadata."""
        metadata = {
            "source_url": url,
            "domain": urlparse(url).netloc,
            "scraping_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "document_type": "scraped_content"
        }
        
        # Extract meta description
        description = soup.find('meta', {'name': 'description'})
        if description:
            metadata["description"] = description.get('content', '')
        
        # Extract keywords
        keywords = soup.find('meta', {'name': 'keywords'})
        if keywords:
            metadata["keywords"] = keywords.get('content', '')
        
        return metadata
    
    def scrape_urls(self, urls: List[str]) -> List[ScrapedDocument]:
        """
        Scrape multiple URLs.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of successfully scraped documents
        """
        scraped_docs = []
        
        logger.info(f"Starting to scrape {len(urls)} URLs")
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing URL {i}/{len(urls)}")
            
            doc = self.scrape_url(url)
            if doc:
                scraped_docs.append(doc)
            
            # Progress logging
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(urls)} URLs processed, {len(scraped_docs)} successful")
        
        logger.info(f"Scraping complete: {len(scraped_docs)}/{len(urls)} URLs successfully scraped")
        return scraped_docs


# CLI utility function for standalone usage
def main():
    """CLI entry point for web scraping."""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Scrape research papers for PsyWiz ingestion")
    parser.add_argument("urls", nargs="+", help="URLs to scrape")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--delay", "-d", type=float, default=1.0, help="Delay between requests")
    
    args = parser.parse_args()
    
    scraper = ResearchScraper(delay_between_requests=args.delay)
    scraped_docs = scraper.scrape_urls(args.urls)
    
    if args.output:
        # Save results to JSON
        output_data = [
            {
                "title": doc.title,
                "content": doc.content,
                "url": doc.url,
                "metadata": doc.metadata,
                "abstract": doc.abstract,
                "authors": doc.authors,
                "publication_date": doc.publication_date,
                "doi": doc.doi
            }
            for doc in scraped_docs
        ]
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {args.output}")
    
    logger.info(f"Scraping complete: {len(scraped_docs)} documents scraped")


if __name__ == "__main__":
    main()