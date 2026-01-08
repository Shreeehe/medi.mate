# 🩺 Medi-Mate

**Intelligent Prescription RAG Assistant with OTC Safety Verification**

Medi-Mate is an AI-powered healthcare assistant that helps users understand their medical prescriptions and verify the safety of over-the-counter (OTC) medicine purchases.

---

## ✨ Features

### 🔍 Prescription Analysis
- **OCR & Extraction:** Upload handwritten or printed prescriptions (PDF/Image) and get structured data extraction using Google Gemini Vision.
- **Interactive Chat:** Ask questions about your prescription like *"When should I take this medicine?"* or *"What are the side effects?"*
- **Context Memory:** The AI remembers your conversation history for natural follow-up questions.

### 💊 OTC Safety Checker
- **Vector-Powered Search:** Uses Pinecone semantic search to find medicine matches efficiently.
- **AI Verification:** LLM-based confirmation ensures accurate categorization.
- **Clear Results:** Medicines are classified as:
  - ✅ **Safe to Buy** - Available OTC
  - ⚠️ **Consult Doctor** - Requires professional advice

### 🔐 User Management
- Secure login/registration with bcrypt password hashing.
- Per-user prescription history and chat sessions.
- Persistent data storage in MongoDB.

### 🎨 Modern UI
- Premium glassmorphism design with animations.
- Responsive Streamlit interface.
- Gradient text, floating icons, and smooth transitions.

---

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│  LangGraph RAG   │────▶│  Google Gemini  │
│   (Frontend)    │     │   (Orchestrate)  │     │     (LLM)       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌──────────────────┐
│    MongoDB      │     │    Pinecone      │
│ (Auth, History) │     │ (Vector Search)  │
└─────────────────┘     └──────────────────┘
```

---

## 📁 Project Structure

```
medi-mate-0.1/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not tracked)
│
├── src/
│   ├── auth.py            # User authentication (MongoDB + bcrypt)
│   ├── config.py          # Configuration & environment loading
│   ├── extractor.py       # Prescription OCR using Gemini Vision
│   ├── graph.py           # LangGraph RAG pipeline
│   ├── ingestion.py       # File processing utilities
│   ├── memory.py          # Chat history & session management
│   ├── otc_data.py        # OTC medicines list (structured data)
│   ├── otc_manager.py     # OTC verification engine
│   ├── utils.py           # Helper functions & logging
│   └── vector_store.py    # Pinecone vector database interface
│
├── data/
│   ├── input/             # Uploaded prescription files
│   └── processed/         # Processed outputs
│
└── tests/
    └── test_otc_check.py  # OTC verification tests
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- MongoDB Atlas account (or local MongoDB)
- Pinecone account
- Google Cloud account (Gemini API)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd medi-mate-0.1
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_google_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   MONGO_URI=mongodb+srv://user:password@cluster.mongodb.net/medi-mate
   ```

5. **Run the application:**
   ```bash
   streamlit run app.py
   ```

---

## 🔧 Configuration

| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Google Gemini API key for LLM and Vision |
| `PINECONE_API_KEY` | Pinecone API key for vector database |
| `MONGO_URI` | MongoDB connection string |

---

## 📖 Usage

### Upload a Prescription
1. Login or create an account.
2. Use the file uploader in the sidebar to upload a prescription (PDF, PNG, JPG).
3. The system will extract medicine details automatically.

### Chat with Your Prescription
- Ask questions like:
  - *"What is the dosage for the first medicine?"*
  - *"Are there any food restrictions?"*
  - *"Explain the timing instructions."*

### Check OTC Safety
1. Click the **"Check for OTC Medicines"** checkbox.
2. View results categorized as Safe or Consult.
3. Navigate to the **OTC List** page to browse all allowed medicines.

---

## 🧪 Testing

Run OTC verification tests:
```bash
python -m pytest tests/test_otc_check.py -v
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Streamlit |
| **LLM / AI** | Google Gemini (Flash Lite) |
| **Vector DB** | Pinecone |
| **Database** | MongoDB |
| **Orchestration** | LangChain, LangGraph |
| **Auth** | bcrypt |

---

## 📄 License

This project is for educational and research purposes.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## ⚠️ Disclaimer

**Medi-Mate is not a substitute for professional medical advice.** Always consult a qualified healthcare provider for medical decisions. The OTC classification is based on general guidelines and may not apply to all regions or individual health conditions.

---

*Built with ❤️ using AI*
