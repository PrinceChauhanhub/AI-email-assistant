# src/rag_system.py
import os
import re
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle

class RAGSystem:
    def __init__(self, knowledge_base_path="data/knowledge_base.txt"):
        self.knowledge_base_path = knowledge_base_path
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.knowledge_chunks = []
        self.chunk_embeddings = None
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """Load and chunk the knowledge base"""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split into sections based on headers
            sections = re.split(r'\n([A-Z &]+:)\n', content)
            
            for i in range(1, len(sections), 2):
                if i+1 < len(sections):
                    header = sections[i].strip()
                    content_text = sections[i+1].strip()
                    
                    # Further split content into individual points
                    points = re.split(r'\n- ', content_text)
                    for point in points:
                        if point.strip():
                            chunk = f"{header} {point.strip()}"
                            self.knowledge_chunks.append(chunk)
            
            # Generate embeddings for chunks
            if self.knowledge_chunks:
                self.chunk_embeddings = self.model.encode(self.knowledge_chunks)
                
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
            self.knowledge_chunks = ["General support information available."]
            self.chunk_embeddings = self.model.encode(self.knowledge_chunks)
    
    def retrieve_relevant_context(self, query, top_k=3):
        """Retrieve most relevant knowledge base chunks for a query"""
        if not self.knowledge_chunks:
            return []
        
        query_embedding = self.model.encode([query])
        similarities = cosine_similarity(query_embedding, self.chunk_embeddings)[0]
        
        # Get top-k most similar chunks
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        relevant_chunks = [self.knowledge_chunks[i] for i in top_indices if similarities[i] > 0.1]
        
        return relevant_chunks
    
    def extract_contact_info(self, email_body):
        """Extract phone numbers and email addresses from email body"""
        phone_pattern = r'(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        phones = re.findall(phone_pattern, email_body)
        emails = re.findall(email_pattern, email_body)
        
        return {
            'phones': ['-'.join(phone) for phone in phones],
            'emails': emails
        }
    
    def extract_requirements(self, email_body):
        """Extract customer requirements and urgency indicators"""
        urgency_keywords = ['urgent', 'immediately', 'asap', 'critical', 'emergency', 'cannot access', 'locked out', 'broken', 'not working']
        frustration_keywords = ['frustrated', 'angry', 'upset', 'disappointed', 'terrible', 'awful', 'worst', 'hate', 'ridiculous']
        
        urgency_score = sum(1 for keyword in urgency_keywords if keyword.lower() in email_body.lower())
        frustration_score = sum(1 for keyword in frustration_keywords if keyword.lower() in email_body.lower())
        
        # Extract sentences containing question words or request indicators
        sentences = re.split(r'[.!?]+', email_body)
        requirements = []
        
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['how', 'what', 'when', 'where', 'why', 'can you', 'please', 'need', 'want', 'help']):
                requirements.append(sentence.strip())
        
        return {
            'requirements': requirements[:3],  # Top 3 requirements
            'urgency_score': urgency_score,
            'frustration_score': frustration_score,
            'is_frustrated': frustration_score > 0
        }
