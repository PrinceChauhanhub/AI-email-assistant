# test_rag.py - Test script for RAG functionality
from src.rag_system import RAGSystem
from src.email_processor import EmailProcessor
from src.response_generator import ResponseGenerator

def test_rag_system():
    print("Testing RAG System...")
    
    # Test email samples
    test_emails = [
        {
            "id": "test1",
            "sender": "customer@example.com", 
            "subject": "Urgent: Cannot access my account",
            "body": "I'm extremely frustrated! I cannot login to my account and I need access immediately. My phone number is 555-123-4567. This is critical for my business.",
            "date": "2025-01-06"
        },
        {
            "id": "test2",
            "sender": "user@company.com",
            "subject": "Help with billing inquiry", 
            "body": "Hi, I have a question about my recent invoice. Order ID is ABC-123-XYZ. Can you help me understand the charges? My email is backup@company.com",
            "date": "2025-01-06"
        }
    ]
    
    # Initialize components
    rag_system = RAGSystem()
    processor = EmailProcessor()
    responder = ResponseGenerator()
    
    for email in test_emails:
        print(f"\n{'='*50}")
        print(f"Processing: {email['subject']}")
        print(f"{'='*50}")
        
        # Process email
        processed = processor.process_email(email)
        
        # Generate response
        response = responder.generate_response(email, processed)
        
        print(f"\n📧 Original Email:")
        print(f"Subject: {email['subject']}")
        print(f"Body: {email['body']}")
        
        print(f"\n🔍 Analysis:")
        print(f"Sentiment: {processed['sentiment']}")
        print(f"Priority: {processed['priority_label']} (Score: {processed['priority_score']})")
        print(f"Frustrated: {processed['is_frustrated']}")
        print(f"Contact Info: {processed['contact_info']}")
        print(f"Requirements: {processed['requirements']}")
        
        print(f"\n🤖 AI Response:")
        print(response)
        
        # Test RAG retrieval
        query = f"{email['subject']} {email['body']}"
        relevant_context = rag_system.retrieve_relevant_context(query, top_k=2)
        print(f"\n📚 Retrieved Knowledge:")
        for i, context in enumerate(relevant_context, 1):
            print(f"{i}. {context[:100]}...")

if __name__ == "__main__":
    test_rag_system()
