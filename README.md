# 📧 AI-Powered Email Support Assistant

## 📦 GitHub Repository
Find the source code here: [github.com/PrinceChauhanhub/AI-email-assistant](https://github.com/PrinceChauhanhub/AI-email-assistant)

This project is an **Email Support Assistant** built with **Hugging Face Transformers**, **Sentence Transformers**, and the **Gmail API**.  
It automatically processes customer support emails, analyzes sentiment and priority, and generates intelligent responses using advanced AI technologies.

---

## 🚀 Features
- **Gmail Integration**: OAuth 2.0 authentication with Gmail API
- **AI-Powered Analysis**: Sentiment analysis using Hugging Face Transformers (DistilBERT)
- **Intelligent Priority Scoring**: Automatic classification of urgent vs routine emails
- **RAG System**: Retrieval-Augmented Generation using Sentence Transformers for knowledge-based responses
- **Information Extraction**: Automatic detection of phone numbers, emails, order IDs
- **Frustration Detection**: Identifies upset customers for empathetic handling
- **Interactive Dashboard**: Beautiful Streamlit web interface with real-time analytics
- **Automated Responses**: Template-based response generation with AI context enhancement
- **Database Management**: SQLite storage for conversation tracking and analytics  

---

## 🛠️ Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/email-support-assistant.git
cd email-support-assistant
```

---

### 2. Create Virtual Environment
```bash
conda create -p venv python==3.11 -y
```

Activate the environment:

- **Windows (PowerShell)**
  ```bash
  conda activate venv/
  ```
---

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

### 4. Configure Google Cloud (OAuth Setup)

#### Step 1: Enable Gmail API
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a **new project**
- Enable the **Gmail API**

#### Step 2: Configure OAuth Consent Screen
- Navigate: `APIs & Services → OAuth consent screen`
- Choose **External**
- Fill in **App name, User support email, Developer email**
- Save & Continue  

#### Step 3: Add Scopes
- On the **Scopes** screen → Click **Add or Remove Scopes**  
- Add the following:
  - `https://www.googleapis.com/auth/gmail.readonly`
  - `https://www.googleapis.com/auth/gmail.modify`
  - `https://www.googleapis.com/auth/gmail.send`
- Save → Continue  

#### Step 4: Add Test Users
- Navigate to [Test Users](https://console.cloud.google.com/apis/credentials/consent?project=<YOUR_PROJECT_ID>#testusers)  
- Click **Add Users**  
- Enter your Gmail account (the same one you’ll use for login)  
- Save  

#### Step 5: Create OAuth Credentials
- Go to: `APIs & Services → Credentials → Create Credentials → OAuth Client ID`
- Application type: **Desktop App**
- Download the file → `credentials.json`
- Save it inside:  
  ```
  ./secrets/credentials.json
  ```

---

### 5. First-Time Gmail Authentication
Run:
```bash
python scripts/gmail_auth.py
```

👉 This will open a browser:
- Log in with your **test Gmail account**
- Approve the requested permissions
- A `token.json` will be generated inside `./secrets/`

---

### 6. Run the Application

#### Option 1: Run the Dashboard (Recommended)
```bash
streamlit run src/dashboard.py
```
This opens a web interface at `http://localhost:8501` where you can:
- Process emails with AI analysis
- View analytics and charts
- Send automated responses
- Monitor system performance

#### Option 2: Run Command Line Processing
```bash
python main.py
```
This processes emails in the background and automatically handles urgent requests.

---

## 🖥️ Using the Dashboard

1. **Start the Dashboard**: `streamlit run src/dashboard.py`
2. **Process Emails**: Click "Fetch & Process New Emails" to analyze incoming emails
3. **View Analytics**: See priority distribution, sentiment analysis, and email volume charts
4. **Send Responses**: Click "Send Pending Responses" to deliver AI-generated replies
5. **Individual Management**: Reply to or mark individual emails as resolved

---

## 📂 Project Structure
```
email-support-assistant/
│── main.py                    # Main email processing entry point
│── requirements.txt           # Python dependencies
│── README.md                  # This file
│── .gitignore                # Git ignore rules
│── VIDEO_TRANSCRIPT.md       # Demo video script
│── test_rag.py              # RAG system testing
│
├── data/
│   └── knowledge_base.txt    # Support knowledge base for RAG
│
├── db/
│   └── emails.db            # SQLite database (auto-created)
│
├── secrets/                  # Private files (not in git)
│   ├── credentials.json     # Google OAuth credentials
│   └── token.json          # Authentication tokens (auto-created)
│
├── scripts/
│   ├── init_db.py          # Database initialization
│   ├── gmail_auth.py       # Gmail authentication setup
│   └── clear_database.py   # Database cleanup utility
│
└── src/                     # Core application code
    ├── __init__.py         # Package initializer
    ├── dashboard.py        # Streamlit web interface
    ├── gmails_tools.py     # Gmail API integration
    ├── email_processor.py  # AI email analysis (sentiment, priority)
    ├── response_generator.py # AI response generation
    ├── rag_system.py       # Knowledge retrieval system
    └── database.py         # Data persistence layer
```

---

## 🤖 AI Technologies Used

- **Hugging Face Transformers**: Sentiment analysis using DistilBERT
- **Sentence Transformers**: Knowledge retrieval with 'all-MiniLM-L6-v2' model
- **Scikit-learn**: Cosine similarity for semantic search
- **Custom NLP**: Priority scoring and information extraction algorithms

---

## 📊 Key Features Explained

### **Intelligent Email Processing**
- Automatically filters support-related emails
- Analyzes sentiment (positive, negative, neutral)
- Scores priority (urgent, medium, low) based on keywords and context
- Extracts contact information and requirements

### **RAG System (Retrieval-Augmented Generation)**
- Searches knowledge base for relevant information
- Enhances responses with accurate, up-to-date context
- Uses semantic similarity for intelligent content matching

### **Dashboard Analytics**
- Real-time email volume monitoring
- Priority and sentiment distribution charts
- Individual email management interface
- Performance metrics and insights

---

## ⚙️ Configuration

### Email Filtering
The system processes emails containing these keywords in the subject:
- "support", "query", "request", "help"

### Priority Scoring Algorithm
- **Urgent (4.0+ points)**: Critical keywords (emergency, urgent, critical, cannot access)
- **Medium (2.5-3.9 points)**: Standard support terms with additional factors
- **Low (<2.5 points)**: Simple requests and questions

### Customization
- **Knowledge Base**: Edit `data/knowledge_base.txt` to add your support information
- **Priority Keywords**: Modify `CRITICAL_KEYWORDS` and `MODERATE_KEYWORDS` in `src/email_processor.py`
- **Response Templates**: Customize templates in `src/response_generator.py`

---

## 🔧 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   # Make sure virtual environment is activated
   source venv/bin/activate  # Mac/Linux
   .\venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. **Gmail API 403 errors**
   - Verify your email is added as a Test User in Google Cloud Console
   - Check that all required scopes are enabled
   - Ensure credentials.json is in the secrets/ folder

3. **Dashboard not loading**
   - Check that all dependencies are installed
   - Verify you're running from the correct directory
   - Try: `streamlit run src/dashboard.py --server.port 8502`

4. **No emails being processed**
   - Ensure emails have support keywords in the subject
   - Check Gmail API permissions
   - Verify database is created (should appear in db/emails.db)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## ✅ Notes
- Use the **same Gmail account** that you added as a **Test User**  
- The system works entirely with **open-source AI models** (no OpenAI API key required)
- All email data is stored locally in SQLite database
- Knowledge base can be customized for your specific support needs
- Dashboard provides real-time monitoring and analytics  

## ✅ Notes
🎥 [Watch Video for Explaination](https://drive.google.com/file/d/1SBWvIw5WaENKYBS0yeM23uAGRdbFA9zk/view?usp=sharing)
