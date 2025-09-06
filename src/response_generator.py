# src/response_generator.py
import os
from typing import Dict
from rag_system import RAGSystem

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

def _simple_template(email, processed, rag_context=None, contact_info=None):
    """Enhanced template with RAG context and empathetic responses"""
    
    # Priority-based tone selection
    priority = processed.get("priority_label", "Low")
    
    if priority == "Urgent":
        tone = "Thank you for contacting us urgently"
        empathy = "We understand this requires immediate attention and our team is prioritizing your request."
        response_time = "within 1 hour"
    elif priority == "Medium":
        if processed.get("sentiment") == "negative" or processed.get("is_frustrated", False):
            tone = "We apologize for any inconvenience you're experiencing"
            empathy = "We want to resolve this quickly for you."
        else:
            tone = "Thank you for reaching out to us"
            empathy = "We're happy to help with your inquiry."
        response_time = "within 4-6 hours"
    else:  # Low priority
        tone = "Thank you for contacting our support team"
        empathy = "We appreciate your patience as we work to assist you."
        response_time = "within 24 hours"
    
    # Include relevant knowledge base context (with complete text)
    context_section = ""
    if rag_context and len(rag_context) > 0:
        # Find the best relevant context
        relevant_info = ""
        for context in rag_context:
            if context and len(context.strip()) > 10:  # Make sure it's not empty
                relevant_info = context.strip()
                break
        
        if relevant_info:
            # Limit to reasonable length but keep complete sentences
            if len(relevant_info) > 200:
                sentences = relevant_info.split('.')
                relevant_info = '. '.join(sentences[:2]) + '.'
            context_section = f"\nRelevant information:\n{relevant_info}\n"
    
    # Include contact info if found
    contact_section = ""
    if contact_info and (contact_info.get('phones') or contact_info.get('emails')):
        contact_section = "\nWe have your contact information on file for updates.\n"
    
    urgency_response = ""
    if priority == "Urgent":
        urgency_response = "URGENT: We're escalating this to our priority support team immediately. "
    
    body = f"""{tone},

{empathy}

Subject: {email.get('subject')}

{processed.get('summary', 'We have reviewed your inquiry carefully.')}{context_section}
{urgency_response}Next steps:
1) Our technical team will update you {response_time}.
2) {'Priority escalation in progress.' if priority == 'Urgent' else 'If you need immediate assistance, please call our support line.'}
{contact_section}
Best regards,
Customer Support Team
Support Ticket: #{email.get('id', 'TEMP')[:8]}
"""
    return body

try:
    import openai
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

def _build_prompt(email, processed, kb_snippets=None, contact_info=None):
    kb_text = "\n".join(kb_snippets) if kb_snippets else "General support available"
    
    frustration_note = ""
    if processed.get("is_frustrated", False):
        frustration_note = "IMPORTANT: Customer appears frustrated. Acknowledge their frustration empathetically and prioritize resolution."
    
    urgency_note = ""
    if processed.get("priority_label") == "Urgent":
        urgency_note = "URGENT REQUEST: Respond with immediate action steps and escalation if needed."
    
    contact_note = ""
    if contact_info and (contact_info.get('phones') or contact_info.get('emails')):
        contact_note = f"Customer contact info available: {contact_info}"
    
    prompt = f"""
You are a customer support agent. Write a CONCISE, helpful response (MAX 150 words).

CUSTOMER EMAIL:
Subject: {email.get('subject')}
Body: {email.get('body')}

ANALYSIS:
Sentiment: {processed.get('sentiment')}
Priority: {processed.get('priority_label')}
{frustration_note}
{urgency_note}
{contact_note}

KNOWLEDGE BASE CONTEXT:
{kb_text}

REQUIREMENTS:
1. Keep response under 150 words total
2. Address the customer's specific question directly
3. Use knowledge base info if relevant
4. Match tone to priority level
5. Provide 1-2 clear next steps
6. Include ticket reference
7. Be specific, not generic

Write a focused, helpful response: 
6. Include support ticket reference
7. Keep response focused and avoid generic language

Priority-specific guidelines:
- URGENT: Immediate escalation, direct contact promise, quick resolution steps
- MEDIUM: Standard helpful response with clear timeline
- LOW: Patient, thorough response focusing on education

Write a specific response addressing their exact issue:
"""
    return prompt

class ResponseGenerator:
    def __init__(self):
        self.rag_system = RAGSystem()

    def generate_response(self, email: Dict, processed: Dict) -> str:
        # Get RAG context
        query = f"{email.get('subject', '')} {email.get('body', '')}"
        kb_snippets = self.rag_system.retrieve_relevant_context(query, top_k=3)
        
        # Extract contact information and requirements
        contact_info = self.rag_system.extract_contact_info(email.get('body', ''))
        requirements = self.rag_system.extract_requirements(email.get('body', ''))
        
        # Add extracted info to processed data
        processed.update({
            'contact_info': contact_info,
            'requirements': requirements.get('requirements', []),
            'is_frustrated': requirements.get('is_frustrated', False),
            'urgency_score': requirements.get('urgency_score', 0)
        })
        
        # Try OpenAI first, fallback to template
        if OPENAI_KEY and OPENAI_AVAILABLE:
            try:
                openai.api_key = OPENAI_KEY
                prompt = _build_prompt(email, processed, kb_snippets, contact_info)
                resp = openai.ChatCompletion.create(
                    model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[{"role": "system", "content": "You are a helpful support agent. Keep responses concise and under 150 words."},
                              {"role": "user", "content": prompt}],
                    max_tokens=200,  # Reduced to ensure complete responses
                    temperature=0.1  # More focused responses
                )
                return resp["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"OpenAI error: {e}")
        
        # Enhanced fallback template with RAG context
        rag_context = "\n".join(kb_snippets) if kb_snippets else None
        return _simple_template(email, processed, rag_context, contact_info)
