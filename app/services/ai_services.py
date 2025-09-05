import asyncio
from groq import Groq
import time
from typing import List, Tuple
import logging
import os
from app.databases.models import NewsArticle

from dotenv import load_dotenv
load_dotenv()

class AIService:
    
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.rate_limit_delay = 1.2  # Seconds between API calls
        self.last_call_time = 0
        
    async def _rate_limit(self):
        """Handle rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        self.last_call_time = time.time()
    
    async def classify_and_summarize(self, body: str) -> Tuple[str, str]:
        
        await self._rate_limit()
        
        prompt = f"""
        Analyze this news article and provide:
        1. Topic classification (choose ONE from: Technology, Business, Health, Environment, Politics, Sports, Entertainment, Science, General)
        2. A concise 5-10 sentence summary
        
        Article Body: {body[:2000]}...  # Limit body length
        
        Response format:
        TOPIC: [topic]
        SUMMARY: [summary]
        """
        ai_model = "llama-3.1-8b-instant"
        print("Doing summarization/classification with model..." + ai_model)
        try:
            response = self.client.chat.completions.create(
                #model="llama-3.3-70b-versatile",  # Good balance of speed and quality
                model=ai_model,  # Faster, cheaper but less accurate
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1  # Low temperature for consistent classification
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse response
            lines = content.split('\n')
            topic = "General"
            summary = ""
            
            for line in lines:
                if line.startswith("TOPIC:"):
                    topic = line.replace("TOPIC:", "").strip()
                elif line.startswith("SUMMARY:"):
                    summary = line.replace("SUMMARY:", "").strip()
            
            return topic, summary
            
        except Exception as e:
            logging.error(f"AI processing error: {e}")
            return "General", f"Summary unavailable due to error: {str(e)}"
    
    async def batch_process_articles(self, articles: List[NewsArticle]) -> List[Tuple[int, str, str]]:
        """Process multiple articles with rate limiting"""
        results = []
        
        for article in articles:
            try:
                topic, summary = await self.classify_and_summarize(
                    article.body
                )
                results.append((article.id, topic, summary))
                logging.info(f"Processed article {article.id}: {topic}")
                
            except Exception as e:
                logging.error(f"Failed to process article {article.id}: {e}")
                results.append((article.id, "General", "Summary unavailable"))
        
        return results