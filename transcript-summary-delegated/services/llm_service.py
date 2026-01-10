"""
LLM Service
Handles transcript summarization using LLM
"""

import os


class LLMService:
    """Facade for LLM operations"""
    
    def __init__(self, use_mock=True):
        self.use_mock = use_mock
        self.api_key = os.getenv('LLM_API_KEY', '')
    
    def generate_summary(self, transcript):
        """Generate a summary from a transcript"""
        if self.use_mock:
            return self._generate_mock_summary(transcript)
        
        raise NotImplementedError("Real LLM integration not yet implemented")
    
    def _generate_mock_summary(self, transcript):
        """Generate a mock summary using simple logic (simulating LLM)"""
        lines = transcript.split('\n')
        
        # Generate HTML-formatted summary
        summary = "<h3>Meeting Summary</h3>\n\n"
        summary += "<h4>Key Discussion Points:</h4>\n<ul>\n"
        
        keywords = ['roadmap', 'sprint', 'review', 'demo', 'sync', 'architecture', 'support']
        found_keywords = [kw for kw in keywords if kw.lower() in transcript.lower()]
        
        if found_keywords:
            summary += f"<li>The meeting covered topics including: <strong>{', '.join(found_keywords)}</strong></li>\n"
        
        summary += f"<li>Total speakers/participants: <strong>{len([line for line in lines if 'Speaker' in line or '[' in line])}</strong></li>\n"
        summary += f"<li>Meeting duration: Approximately <strong>{len(lines) * 10} seconds</strong></li>\n"
        summary += "</ul>\n\n"
        
        summary += "<h4>Action Items:</h4>\n<ol>\n"
        summary += "<li>Follow up on discussed topics</li>\n"
        summary += "<li>Schedule next meeting if needed</li>\n"
        summary += "<li>Share meeting notes with team</li>\n"
        summary += "</ol>\n"
        
        return summary
