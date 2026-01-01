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
        summary = "Meeting Summary:\n\n"
        summary += "Key Discussion Points:\n"
        
        keywords = ['roadmap', 'sprint', 'review', 'demo', 'sync', 'architecture', 'support']
        found_keywords = [kw for kw in keywords if kw.lower() in transcript.lower()]
        
        if found_keywords:
            summary += f"- The meeting covered topics including: {', '.join(found_keywords)}\n"
        
        summary += f"- Total speakers/participants: {len([line for line in lines if 'Speaker' in line or '[' in line])}\n"
        summary += f"- Meeting duration: Approximately {len(lines) * 10} seconds\n\n"
        
        summary += "Action Items:\n"
        summary += "- Follow up on discussed topics\n"
        summary += "- Schedule next meeting if needed\n"
        summary += "- Share meeting notes with team\n"
        
        return summary
