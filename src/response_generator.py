# src/response_generator.py
import os
from typing import Dict
from rag_system import RAGSystem

OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

def _simple_template(email, processed, rag_context=None, contact_info=None):
    """Enhanced template with RAG context and empathetic responses"""
    
    # Determine tone based on sentiment and frustration
    if processed.get("sentiment") == "negative" or processed.get("is_frustrated", False):
        tone = "We sincerely apologize for the inconvenience and understand your frustration"
        empathy = "Your experience is not meeting our standards, and we want to make this right immediately."
    else:
        tone = "Thank you for reaching out to us"
        empathy = "We're here to help and ensure you have the best experience possible."
    
    # Include relevant knowledge base context
    context_section = ""
    if rag_context:
        context_section = f"\nBased on your inquiry, here's what we can help with:\n{rag_context[:200]}...\n"
    
    # Include contact info if found
    contact_section = ""
    if contact_info and (contact_info.get('phones') or contact_info.get('emails')):
        contact_section = "\nWe have your contact information on file for updates.\n"
    
    urgency_response = ""
    if processed.get("priority_label") == "Urgent":
        urgency_response = "Given the urgent nature of your request, we're prioritizing this for immediate attention. "
    
    body = f"""{tone},

{empathy}

Subject: {email.get('subject')}

Summary of your issue:
{processed.get('summary', 'We have reviewed your inquiry carefully.')}
{context_section}
{urgency_response}Next steps:
1) Our technical team is investigating this issue and will update you within 2-4 hours.
2) If you need immediate assistance, please call our priority support line.
3) Any additional details (screenshots, error messages, order ID) will help us resolve this faster.
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
You are an expert customer support agent. Write a professional, empathetic, and solution-focused response (max 200 words).

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
1. Address the customer's specific concerns
2. Use relevant knowledge base information
3. Maintain professional yet warm tone
4. Provide clear next steps
5. If customer is frustrated, acknowledge and apologize
6. Include support ticket reference
7. Offer additional assistance channels if urgent

Write the response now:
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
                    messages=[{"role": "system", "content": "You are a helpful support agent."},
                              {"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.2
                )
                return resp["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"OpenAI error: {e}")
        
        # Enhanced fallback template with RAG context
        rag_context = "\n".join(kb_snippets) if kb_snippets else None
        return _simple_template(email, processed, rag_context, contact_info)
