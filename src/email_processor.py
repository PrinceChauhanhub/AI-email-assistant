# src/email_processor.py
import re
from typing import Dict, Any
from rag_system import RAGSystem

try:
    from transformers import pipeline
    _sent_pipeline = pipeline("sentiment-analysis")
except Exception:
    _sent_pipeline = None

PHONE_RE = re.compile(r"(\+?\d[\d\-\s]{7,}\d)")
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
ORDER_RE = re.compile(r"(?:order|ord|#)\s*([A-Z0-9\-]{3,20})", re.I)

CRITICAL_KEYWORDS = {
    "urgent", "immediately", "asap", "critical", "emergency",
    "cannot access", "can't access", "unable to access",
    "down", "outage", "payment failed", 
    "locked", "blocked", "broken", "not working"
}

MODERATE_KEYWORDS = {
    "help", "support", "issue", "problem", "error", "refund"
}

FRUSTRATION_KEYWORDS = {
    "frustrated", "angry", "upset", "disappointed", "terrible", 
    "awful", "worst", "hate", "ridiculous", "unacceptable"
}

class EmailProcessor:
    def __init__(self):
        self.rag_system = RAGSystem()

    def sentiment(self, text: str) -> str:
        if not text:
            return "neutral"
        if _sent_pipeline:
            try:
                r = _sent_pipeline(text[:512])[0]
                label = r.get("label", "").lower()
                if label.startswith("neg"):
                    return "negative"
                if label.startswith("pos"):
                    return "positive"
            except Exception:
                pass

        neg_words = ["not", "can't", "cannot", "frustrat", "angry",
                     "disappoint", "error", "issue", "problem", "fail"]
        pos_words = ["thanks", "thank you", "great", "happy",
                     "good", "fixed", "resolved"]

        t = text.lower()
        neg = sum(t.count(w) for w in neg_words)
        pos = sum(t.count(w) for w in pos_words)

        if neg > pos and neg > 0:
            return "negative"
        if pos > neg and pos > 0:
            return "positive"
        return "neutral"

    def extract(self, text: str) -> Dict[str, Any]:
        phones = [re.sub(r"[^\d+]", "", p) for p in PHONE_RE.findall(text)]
        emails = EMAIL_RE.findall(text)
        orders = ORDER_RE.findall(text)
        
        # Enhanced extraction using RAG system
        contact_info = self.rag_system.extract_contact_info(text)
        requirements = self.rag_system.extract_requirements(text)
        
        return {
            "phones": phones + contact_info.get('phones', []), 
            "emails": emails + contact_info.get('emails', []), 
            "order_ids": orders,
            "requirements": requirements.get('requirements', []),
            "urgency_indicators": requirements.get('urgency_score', 0),
            "frustration_level": requirements.get('frustration_score', 0)
        }

    def priority(self, text: str, sentiment: str, extracted: Dict = None, is_paid=False) -> Dict[str, Any]:
        score = 0.0
        t = text.lower()
        
        # True critical keywords (high urgency)
        if any(k in t for k in CRITICAL_KEYWORDS):
            score += 3.0
            
        # Moderate keywords (normal support requests)
        elif any(k in t for k in MODERATE_KEYWORDS):
            score += 1.0
            
        # Frustration indicators
        if any(k in t for k in FRUSTRATION_KEYWORDS):
            score += 1.5
            
        # Topic-based scoring
        if "login" in t or "password" in t:
            score += 1.0
        if "payment" in t or "billing" in t or "refund" in t:
            score += 1.5
        if "account" in t and ("locked" in t or "blocked" in t):
            score += 2.0
            
        # Sentiment-based scoring
        if sentiment == "negative":
            score += 1.0
            
        # Enhanced scoring from extracted data
        if extracted:
            score += extracted.get('urgency_indicators', 0) * 0.5
            score += extracted.get('frustration_level', 0) * 0.3
            
        if is_paid:
            score += 1.0

        # More realistic thresholds
        if score >= 4.0:
            label = "Urgent"
        elif score >= 2.5:
            label = "Medium"
        else:
            label = "Low"
            
        return {"score": round(score, 2), "label": label}

    def summarize(self, text: str, max_len: int = 200) -> str:
        import re
        s = re.split(r'(?<=[.!?])\s+', text.strip())
        summary = (" ".join(s[:3]))[:max_len] if s else text[:max_len]
        
        # Add urgency indicator to summary if present
        if any(k in text.lower() for k in CRITICAL_KEYWORDS):
            summary = f"[URGENT] {summary}"
        
        return summary

    def process_email(self, email: Dict[str, Any], is_paid: bool = False) -> Dict[str, Any]:
        text = (email.get("subject", "") or "") + "\n" + (email.get("body", "") or "")
        sent = self.sentiment(text)
        extracted = self.extract(text)
        priority = self.priority(text, sent, extracted, is_paid=is_paid)
        summary = self.summarize(text)
        
        # Check for frustration indicators
        is_frustrated = any(k in text.lower() for k in FRUSTRATION_KEYWORDS)
        
        return {
            "sentiment": sent,
            "extracted": extracted,
            "priority_score": priority["score"],
            "priority_label": priority["label"],
            "summary": summary,
            "is_frustrated": is_frustrated,
            "contact_info": {
                "phones": extracted.get("phones", []),
                "emails": extracted.get("emails", [])
            },
            "requirements": extracted.get("requirements", [])
        }
