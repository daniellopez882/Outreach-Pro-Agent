"""
Kimi 2.5 AI Client - Agentic wrapper for intelligent outreach generation
"""
from typing import List, Dict, Any, Optional
from openai import OpenAI
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
import json

from config import settings


class KimiAgent:
    """
    Kimi 2.5 Agent for hyper-personalized outreach
    
    Kimi 2.5 is optimized for:
    - Long context (128k tokens)
    - Deep reasoning
    - Chinese + English bilingual
    - Tool use and function calling
    """
    
    def __init__(self):
        # Prioritize DeepSeek if available, otherwise fallback to Kimi
        if settings.deepseek_api_key:
            logger.info("Initializing Agent with DeepSeek engine")
            self.client = OpenAI(
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url
            )
            self.model = settings.deepseek_model
        else:
            logger.info("Initializing Agent with Kimi engine")
            self.client = OpenAI(
                api_key=settings.kimi_api_key,
                base_url=settings.kimi_base_url
            )
            self.model = settings.kimi_model

    def _call_kimi(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        tools: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Call AI API with retry logic. Mocks responses for demo keys."""
        
        # Check for demo/empty key and return mock response
        # Using a unified check for both keys
        api_key = settings.deepseek_api_key or settings.kimi_api_key
        if not api_key or "test-key" in api_key:
            logger.info("Using MOCK AI response for demo purposes")
            return self._get_mock_response(messages)
            
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            response = self.client.chat.completions.create(**kwargs)
            
            return {
                "content": response.choices[0].message.content,
                "tool_calls": getattr(response.choices[0].message, "tool_calls", None),
                "usage": response.usage.model_dump() if response.usage else None
            }
            
        except Exception as e:
            logger.error(f"Kimi API error: {e}")
            raise

    def _get_mock_response(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Return simulated AI responses based on message content"""
        user_msg = messages[-1]["content"].lower()
        
        # Mock analysis response
        if "analyze this lead" in user_msg or "identify:" in user_msg:
            content = """
            ```json
            {
              "pain_points": [
                "Deployment velocity bottlenecks as the engineering team scales",
                "High infrastructure maintenance overhead",
                "Difficulty in maintaining code quality during hypergrowth"
              ],
              "interests": [
                "DevOps automation",
                "Cloud-native architecture",
                "Engineering productivity metrics"
              ],
              "trigger_events": [
                {
                  "type": "hiring_surge",
                  "description": "15+ engineering openings posted recently",
                  "timestamp": "2024-02-01",
                  "relevance": 0.95
                },
                {
                  "type": "funding",
                  "description": "Company recently raised Series B funding",
                  "timestamp": "2024-01-15",
                  "relevance": 0.90
                }
              ],
              "personalization_hooks": [
                "Recent LinkedIn post about scaling engineering teams",
                "Mention of TechCorp's expansion into new markets",
                "Shared interest in sustainable open-source development"
              ],
              "communication_style": "semi-formal",
              "relevance_score": 0.92,
              "recommended_approach": "problem-solution"
            }
            ```
            """
        
        # Mock email generation response
        elif "write a hyper-personalized cold outreach email" in user_msg:
            content = """
            ```json
            {
              "subject_line": "Your post about deployment bottlenecks",
              "email_body": "Hi Rahul,\\n\\nSaw your LinkedIn post this week about deployment bottlenecks as TechCorp scales. With your Series B and 15+ engineering openings, this timing feels familiar.\\n\\nWe helped Razorpay tackle similar challenges during their hypergrowth phase - they went from 45-minute deploys to 12 minutes, letting their teams ship 3x more features.\\n\\nWorth a 15-minute chat about their approach?\\n\\nBest,\\n[Your Name]",
              "personalization_elements": [
                "References specific LinkedIn post",
                "Mentions Series B funding",
                "Ties to engineering hiring surge",
                "Relevant social proof (Razorpay)"
              ],
              "reasoning": "Lead with a specific trigger event (hiring surge + funding) and provided relevant social proof that directly addresses their scaling bottleneck.",
              "expected_response_rate": 0.18
            }
            ```
            """
            
        else:
            content = "I am the Kimi Agent. In a real scenario, I would process your request and return a thoughtful response. For this demo, I'm providing this generic confirmation."
            
        return {
            "content": content,
            "tool_calls": None,
            "usage": {"prompt_tokens": 100, "completion_tokens": 150, "total_tokens": 250}
        }

    
    async def analyze_lead_profile(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep analysis of lead profile to extract personalization opportunities
        
        Args:
            lead_data: Complete lead information from LinkedIn, company news, etc.
            
        Returns:
            Structured analysis with pain points, interests, trigger events
        """
        
        analysis_prompt = f"""
You are an expert sales intelligence analyst. Analyze this lead's profile and identify:

1. **Pain Points**: What challenges might they be facing based on their role, industry, and recent activity?
2. **Interests**: What topics, technologies, or business areas are they interested in?
3. **Trigger Events**: Recent events that make NOW the perfect time to reach out
4. **Personalization Hooks**: Specific things we can reference to show we did our homework
5. **Communication Style**: How formal/casual should we be based on their online presence?

Lead Data:
```json
{json.dumps(lead_data, indent=2)}
```

Return your analysis as a structured JSON with these exact keys:
- pain_points: [list of identified pain points]
- interests: [list of professional interests]
- trigger_events: [list of recent trigger events with timestamps]
- personalization_hooks: [specific things to mention]
- communication_style: "formal" | "semi-formal" | "casual"
- relevance_score: 0-1 (how relevant our offering is to them)
- recommended_approach: "value-first" | "problem-solution" | "social-proof" | "educational"
"""
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert B2B sales intelligence analyst who identifies personalization opportunities."
            },
            {
                "role": "user",
                "content": analysis_prompt
            }
        ]
        
        response = self._call_kimi(messages, temperature=0.3)
        
        try:
            # Extract JSON from response
            content = response["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(content)
            logger.info(f"Lead analysis complete. Relevance score: {analysis.get('relevance_score', 0)}")
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Kimi response as JSON: {e}")
            # Fallback: return raw response
            return {
                "raw_analysis": response["content"],
                "relevance_score": 0.5
            }
    
    async def generate_personalized_email(
        self,
        lead_data: Dict[str, Any],
        analysis: Dict[str, Any],
        company_context: str,
        value_proposition: str,
        email_goal: str = "schedule_call"
    ) -> Dict[str, Any]:
        """
        Generate hyper-personalized outreach email
        
        Args:
            lead_data: Lead information
            analysis: Output from analyze_lead_profile
            company_context: Your company's value prop
            value_proposition: What you're offering
            email_goal: What action you want them to take
            
        Returns:
            Dict with subject_line, body, personalization_elements
        """
        
        generation_prompt = f"""
You are an expert B2B copywriter specializing in cold outreach that gets 15-20% response rates.

Write a hyper-personalized cold outreach email using this information:

**Lead Info:**
- Name: {lead_data.get('name')}
- Company: {lead_data.get('company')}
- Role: {lead_data.get('job_title')}

**Intelligence:**
{json.dumps(analysis, indent=2)}

**Our Context:**
{company_context}

**Value Proposition:**
{value_proposition}

**Goal:**
{email_goal}

**Critical Rules:**
1. Start with a SPECIFIC observation about their recent activity (post, article, company news)
2. NO generic compliments or fluff
3. Lead with VALUE, not your product
4. Keep it under 150 words
5. One clear call-to-action
6. Use their communication style ({analysis.get('communication_style', 'semi-formal')})
7. Never sound like a template
8. Reference something they posted/wrote in the last 2 weeks if available

Return JSON:
{{
  "subject_line": "...",
  "email_body": "...",
  "personalization_elements": ["element1", "element2", ...],
  "reasoning": "Why this approach will work",
  "expected_response_rate": 0.15-0.20
}}
"""
        
        messages = [
            {
                "role": "system",
                "content": """You are a top 1% B2B copywriter. Your emails:
- Get opened because subjects are curiosity-driven and specific
- Get read because you lead with value
- Get responses because you show you did research
- Never sound like marketing spam"""
            },
            {
                "role": "user",
                "content": generation_prompt
            }
        ]
        
        response = self._call_kimi(messages, temperature=0.8)
        
        try:
            content = response["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            email_data = json.loads(content)
            logger.info(f"Email generated. Expected response rate: {email_data.get('expected_response_rate')}")
            return email_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse email generation response: {e}")
            return {
                "subject_line": "Quick question about your work at " + lead_data.get('company', ''),
                "email_body": response["content"],
                "personalization_elements": [],
                "error": str(e)
            }
    
    async def generate_ab_variants(
        self,
        original_email: Dict[str, Any],
        lead_data: Dict[str, Any],
        num_variants: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Generate A/B test variants with different approaches
        
        Returns list of variant emails with different messaging strategies
        """
        
        variant_prompt = f"""
Generate {num_variants} alternative versions of this email with DIFFERENT strategic approaches:

Original Email:
Subject: {original_email['subject_line']}
Body: {original_email['email_body']}

Lead: {lead_data.get('name')} at {lead_data.get('company')}

Create variants using these different approaches:
1. "Problem-Agitation": Start with their pain point, agitate it, then offer solution
2. "Social Proof": Lead with a similar company/person who got results
3. "Educational": Share a useful insight/framework first, then connect to your offering

Each variant should:
- Have a DIFFERENT subject line strategy
- Take a DIFFERENT opening approach
- Still be hyper-personalized
- Be same length (under 150 words)

Return JSON array:
[
  {{
    "variant_name": "problem-agitation",
    "subject_line": "...",
    "email_body": "...",
    "strategy": "description"
  }},
  ...
]
"""
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert at A/B testing different email approaches."
            },
            {
                "role": "user",
                "content": variant_prompt
            }
        ]
        
        response = self._call_kimi(messages, temperature=0.9)
        
        try:
            content = response["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            variants = json.loads(content)
            return variants if isinstance(variants, list) else [variants]
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse A/B variants: {e}")
            return []
    
    async def generate_follow_up(
        self,
        original_email: Dict[str, Any],
        days_since_sent: int,
        engagement_data: Dict[str, Any],
        sequence_number: int
    ) -> Dict[str, Any]:
        """
        Generate intelligent follow-up based on engagement
        
        Args:
            original_email: The original email sent
            days_since_sent: How many days since original
            engagement_data: Did they open? Click? 
            sequence_number: 1st follow-up, 2nd, etc.
        """
        
        followup_prompt = f"""
Generate follow-up email #{sequence_number} for this cold outreach:

Original Email:
Subject: {original_email['subject_line']}
Body: {original_email['email_body']}

Engagement:
- Days since sent: {days_since_sent}
- Opened: {engagement_data.get('opened', False)}
- Clicked: {engagement_data.get('clicked', False)}

Follow-up Rules:
1. If they opened but didn't reply: Assume they're interested but busy/forgot
2. If they didn't open: Try a completely different angle/subject
3. Keep it SHORT (under 100 words)
4. Add NEW value (new insight, different benefit, timely news)
5. No "just following up" or "bumping this" - that's weak
6. Sequence {sequence_number} should feel natural, not desperate

Return JSON:
{{
  "subject_line": "...",
  "email_body": "...",
  "strategy": "why this follow-up will work"
}}
"""
        
        messages = [
            {
                "role": "system",
                "content": "You create follow-ups that feel helpful, not pushy."
            },
            {
                "role": "user",
                "content": followup_prompt
            }
        ]
        
        response = self._call_kimi(messages, temperature=0.7)
        
        try:
            content = response["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            return json.loads(content)
            
        except json.JSONDecodeError:
            return {
                "subject_line": f"Re: {original_email['subject_line']}",
                "email_body": response["content"]
            }


# Global agent instance
kimi_agent = KimiAgent()
