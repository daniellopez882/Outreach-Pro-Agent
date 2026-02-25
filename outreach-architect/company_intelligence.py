"""
Company Intelligence Gatherer - News, funding, hiring signals
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx
from loguru import logger
from bs4 import BeautifulSoup

from config import settings


class CompanyIntelligence:
    """
    Gather company intelligence from multiple sources:
    - Recent news articles
    - Press releases
    - Funding announcements
    - Job postings (growth signal)
    - Social media activity
    """
    
    def __init__(self):
        self.newsapi_key = settings.newsapi_key
        self.serpapi_key = settings.serpapi_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_company_news(
        self,
        company_name: str,
        days_back: int = 30,
        max_articles: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get recent news about a company
        
        Uses NewsAPI for reliable news aggregation
        """
        
        if not self.newsapi_key:
            logger.warning("NewsAPI key not configured, using web scraping")
            return await self._scrape_google_news(company_name, days_back, max_articles)
        
        try:
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': f'"{company_name}"',
                'from': from_date,
                'sortBy': 'publishedAt',
                'language': 'en',
                'pageSize': max_articles,
                'apiKey': self.newsapi_key
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            articles = []
            for article in data.get('articles', []):
                articles.append({
                    'title': article['title'],
                    'description': article.get('description'),
                    'url': article['url'],
                    'source': article['source']['name'],
                    'published_at': article['publishedAt'],
                    'content_snippet': article.get('content', '')[:500]
                })
            
            logger.info(f"Found {len(articles)} news articles for {company_name}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching company news: {e}")
            return []
    
    async def _scrape_google_news(
        self,
        company_name: str,
        days_back: int,
        max_articles: int
    ) -> List[Dict[str, Any]]:
        """Fallback: Scrape Google News if NewsAPI not available"""
        
        try:
            # Google News search URL
            query = f"{company_name} news"
            url = f"https://news.google.com/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            
            response = await self.client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            
            # Find article elements (structure may change)
            article_elements = soup.find_all('article')[:max_articles]
            
            for article in article_elements:
                title_elem = article.find('h3')
                link_elem = article.find('a')
                time_elem = article.find('time')
                
                if title_elem and link_elem:
                    articles.append({
                        'title': title_elem.text.strip(),
                        'url': 'https://news.google.com' + link_elem.get('href', ''),
                        'published_at': time_elem.get('datetime') if time_elem else None,
                        'source': 'Google News'
                    })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping Google News: {e}")
            return []
    
    async def check_hiring_signals(self, company_name: str) -> Dict[str, Any]:
        """
        Check if company is hiring (growth signal)
        
        Checks:
        - Number of open positions
        - Recent job postings
        - Departments hiring
        """
        
        try:
            # LinkedIn Jobs search
            url = f"https://www.linkedin.com/jobs/search/?keywords={company_name}"
            
            response = await self.client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Count job postings
            job_cards = soup.find_all('div', class_=re.compile('job-search-card'))
            
            hiring_data = {
                'is_hiring': len(job_cards) > 0,
                'open_positions': len(job_cards),
                'recent_postings': []
            }
            
            for job in job_cards[:5]:
                title_elem = job.find('h3', class_=re.compile('job-search-card__title'))
                location_elem = job.find('span', class_=re.compile('job-search-card__location'))
                
                if title_elem:
                    hiring_data['recent_postings'].append({
                        'title': title_elem.text.strip(),
                        'location': location_elem.text.strip() if location_elem else None
                    })
            
            logger.info(f"{company_name} hiring status: {hiring_data['open_positions']} positions")
            return hiring_data
            
        except Exception as e:
            logger.error(f"Error checking hiring signals: {e}")
            return {'is_hiring': False, 'open_positions': 0, 'recent_postings': []}
    
    async def get_funding_info(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Get recent funding announcements (major trigger event)
        
        Uses Crunchbase-style search or news aggregation
        """
        
        try:
            # Search for funding news
            query = f"{company_name} funding Series raise investment"
            news = await self.get_company_news(query, days_back=90, max_articles=5)
            
            funding_keywords = ['funding', 'raise', 'series', 'investment', 'million', 'venture']
            
            funding_news = [
                article for article in news
                if any(keyword in article['title'].lower() for keyword in funding_keywords)
            ]
            
            if funding_news:
                return {
                    'recent_funding': True,
                    'funding_articles': funding_news,
                    'signal_strength': 'high'  # Strong trigger event
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting funding info: {e}")
            return None
    
    async def get_company_website_content(self, website_url: str) -> Dict[str, Any]:
        """
        Scrape company website for:
        - Mission/vision
        - Recent blog posts
        - Product launches
        """
        
        try:
            response = await self.client.get(website_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content') if meta_desc else None
            
            # Extract page title
            title = soup.find('title')
            page_title = title.text.strip() if title else None
            
            # Look for blog section
            blog_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'blog' in href or 'news' in href or 'press' in href:
                    blog_links.append({
                        'text': link.text.strip(),
                        'url': href if href.startswith('http') else website_url + href
                    })
            
            return {
                'website_url': website_url,
                'title': page_title,
                'description': description,
                'blog_section': blog_links[:5],
                'scraped_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scraping company website: {e}")
            return {'website_url': website_url, 'error': str(e)}
    
    async def enrich_company_data(self, company_name: str, website: str = None) -> Dict[str, Any]:
        """
        Complete company intelligence gathering
        
        Combines all sources into a comprehensive profile
        """
        
        logger.info(f"Enriching company data for: {company_name}")
        
        # Gather data from multiple sources concurrently
        import asyncio
        
        tasks = [
            self.get_company_news(company_name, days_back=30, max_articles=10),
            self.check_hiring_signals(company_name),
            self.get_funding_info(company_name)
        ]
        
        if website:
            tasks.append(self.get_company_website_content(website))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        company_data = {
            'company_name': company_name,
            'website': website,
            'recent_news': results[0] if not isinstance(results[0], Exception) else [],
            'hiring_signals': results[1] if not isinstance(results[1], Exception) else {},
            'funding_info': results[2] if not isinstance(results[2], Exception) else None,
            'enriched_at': datetime.utcnow().isoformat()
        }
        
        if website and len(results) > 3:
            company_data['website_data'] = results[3] if not isinstance(results[3], Exception) else {}
        
        # Calculate trigger event score
        trigger_score = 0
        if company_data['funding_info']:
            trigger_score += 0.4
        if company_data['hiring_signals'].get('open_positions', 0) > 5:
            trigger_score += 0.3
        if len(company_data['recent_news']) > 5:
            trigger_score += 0.2
        
        company_data['trigger_score'] = trigger_score
        
        logger.info(f"Company enrichment complete. Trigger score: {trigger_score}")
        return company_data


# Global instance
company_intel = CompanyIntelligence()
