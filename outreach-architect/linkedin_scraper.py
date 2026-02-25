"""
LinkedIn Profile Scraper and Analyzer
"""
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re
import httpx
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings


class LinkedInScraper:
    """
    LinkedIn profile scraper with multiple methods:
    1. Public profile scraping (no login required)
    2. Session-based scraping (with login)
    3. API-based (if using official LinkedIn API)
    """
    
    def __init__(self):
        self.session = httpx.Client(timeout=30.0)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.is_logged_in = False
    
    def login(self, email: str = None, password: str = None) -> bool:
        """
        Login to LinkedIn (for enhanced scraping)
        Note: Use at your own risk - LinkedIn may ban accounts for scraping
        """
        email = email or settings.linkedin_email
        password = password or settings.linkedin_password
        
        if not email or not password:
            logger.warning("No LinkedIn credentials provided. Using public scraping only.")
            return False
        
        try:
            # LinkedIn login flow
            # WARNING: This is a simplified version. Production should handle:
            # - CSRF tokens
            # - Captcha detection
            # - Rate limiting
            # - Session persistence
            
            login_url = "https://www.linkedin.com/uas/login-submit"
            
            response = self.session.post(
                login_url,
                data={
                    'session_key': email,
                    'session_password': password,
                },
                headers=self.headers
            )
            
            if response.status_code == 200 and 'feed' in response.url:
                self.is_logged_in = True
                logger.info("Successfully logged into LinkedIn")
                return True
            
            logger.error("Failed to login to LinkedIn")
            return False
            
        except Exception as e:
            logger.error(f"LinkedIn login error: {e}")
            return False
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=4, max=30))
    async def scrape_profile(self, linkedin_url: str) -> Dict[str, Any]:
        """
        Scrape LinkedIn profile data
        
        Returns:
            Dict with profile information including:
            - name, headline, location
            - current_company, job_title
            - about_section
            - experience, education
            - skills, certifications
        """
        
        try:
            # Clean URL
            if not linkedin_url.startswith('http'):
                linkedin_url = f"https://www.linkedin.com/in/{linkedin_url}"
            
            # Fetch profile page
            response = self.session.get(linkedin_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract profile data
            profile_data = self._parse_profile_html(soup, linkedin_url)
            
            logger.info(f"Successfully scraped profile: {profile_data.get('name')}")
            return profile_data
            
        except Exception as e:
            logger.error(f"Error scraping LinkedIn profile {linkedin_url}: {e}")
            return {
                'linkedin_url': linkedin_url,
                'error': str(e),
                'scraped_at': datetime.utcnow().isoformat()
            }
    
    def _parse_profile_html(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Parse LinkedIn profile HTML and extract structured data"""
        
        profile = {
            'linkedin_url': url,
            'scraped_at': datetime.utcnow().isoformat()
        }
        
        # Name
        name_elem = soup.find('h1', class_=re.compile('text-heading-xlarge|top-card-layout__title'))
        profile['name'] = name_elem.text.strip() if name_elem else None
        
        # Headline
        headline_elem = soup.find('div', class_=re.compile('text-body-medium|top-card-layout__headline'))
        profile['headline'] = headline_elem.text.strip() if headline_elem else None
        
        # Location
        location_elem = soup.find('span', class_=re.compile('top-card__subline-item|text-body-small'))
        profile['location'] = location_elem.text.strip() if location_elem else None
        
        # About section
        about_elem = soup.find('div', class_=re.compile('core-section-container__content|about-section'))
        profile['about'] = about_elem.text.strip() if about_elem else None
        
        # Current company and role
        experience_section = soup.find('section', id=re.compile('experience'))
        if experience_section:
            first_job = experience_section.find('li')
            if first_job:
                title_elem = first_job.find('div', class_=re.compile('t-bold'))
                company_elem = first_job.find('span', class_=re.compile('t-normal'))
                
                profile['current_job_title'] = title_elem.text.strip() if title_elem else None
                profile['current_company'] = company_elem.text.strip() if company_elem else None
        
        # Skills
        skills_section = soup.find('section', id=re.compile('skills'))
        if skills_section:
            skills = [s.text.strip() for s in skills_section.find_all('span', class_=re.compile('skill-name'))]
            profile['skills'] = skills[:10]  # Top 10 skills
        
        return profile
    
    async def get_recent_activity(self, linkedin_url: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent posts and activity from a LinkedIn profile
        
        Note: This requires being logged in for full access
        """
        
        if not self.is_logged_in:
            logger.warning("Not logged in - recent activity may be limited")
        
        try:
            # Construct activity feed URL
            username = linkedin_url.split('/in/')[-1].rstrip('/')
            activity_url = f"https://www.linkedin.com/in/{username}/recent-activity/all/"
            
            response = self.session.get(activity_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            activities = []
            
            # Find post elements
            posts = soup.find_all('div', class_=re.compile('feed-shared-update-v2'))[:limit]
            
            for post in posts:
                activity = {}
                
                # Post text
                text_elem = post.find('div', class_=re.compile('feed-shared-text'))
                activity['content'] = text_elem.text.strip() if text_elem else None
                
                # Post timestamp
                time_elem = post.find('time')
                activity['posted_at'] = time_elem.get('datetime') if time_elem else None
                
                # Post type (article, image, video, etc.)
                activity['type'] = 'post'  # Simplified
                
                # Engagement metrics
                likes_elem = post.find('span', class_=re.compile('social-details-social-counts__reactions-count'))
                comments_elem = post.find('button', class_=re.compile('social-details-social-counts__comments'))
                
                activity['likes'] = likes_elem.text.strip() if likes_elem else '0'
                activity['comments'] = comments_elem.text.strip() if comments_elem else '0'
                
                activities.append(activity)
            
            logger.info(f"Retrieved {len(activities)} recent activities")
            return activities
            
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []
    
    async def search_people(
        self,
        keywords: str = None,
        company: str = None,
        title: str = None,
        location: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for LinkedIn profiles matching criteria
        
        This is a simplified version. Production should use:
        - LinkedIn Sales Navigator API
        - Or a dedicated scraping service like PhantomBuster
        """
        
        # Construct search URL
        search_params = []
        if keywords:
            search_params.append(f"keywords={keywords}")
        if company:
            search_params.append(f"company={company}")
        if title:
            search_params.append(f"title={title}")
        if location:
            search_params.append(f"location={location}")
        
        search_url = f"https://www.linkedin.com/search/results/people/?{'&'.join(search_params)}"
        
        try:
            response = self.session.get(search_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            
            # Find search result elements
            search_results = soup.find_all('li', class_=re.compile('reusable-search__result-container'))[:limit]
            
            for result in search_results:
                profile = {}
                
                # Name and profile URL
                name_elem = result.find('span', attrs={'aria-hidden': 'true'})
                profile_link = result.find('a', class_=re.compile('app-aware-link'))
                
                profile['name'] = name_elem.text.strip() if name_elem else None
                profile['linkedin_url'] = profile_link.get('href') if profile_link else None
                
                # Headline
                headline_elem = result.find('div', class_=re.compile('entity-result__primary-subtitle'))
                profile['headline'] = headline_elem.text.strip() if headline_elem else None
                
                # Location
                location_elem = result.find('div', class_=re.compile('entity-result__secondary-subtitle'))
                profile['location'] = location_elem.text.strip() if location_elem else None
                
                results.append(profile)
            
            logger.info(f"Found {len(results)} profiles matching search criteria")
            return results
            
        except Exception as e:
            logger.error(f"Error searching LinkedIn: {e}")
            return []


# Global scraper instance
linkedin_scraper = LinkedInScraper()
