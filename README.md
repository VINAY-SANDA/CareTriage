# AI Clinical Pipeline MVP

A comprehensive medical AI system for symptom analysis, clinical reasoning, and report generation following ICMR Standard Treatment Workflows.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Gemini API Key (free from Google AI Studio)

### Installation

1. **Install Backend Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Install Frontend Dependencies**
```bash
cd frontend
npm install
```

3. **Upload ICMR Documents**
Place your ICMR STW PDF files in:
```
backend/data/icmr_documents/
```

4. **Train ML Model (first time only)**
```bash
cd backend
python train_model.py
```

### Running the Application

**Option 1: Use the startup script**
```bash
run.bat
```

**Option 2: Manual start**
```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Then open: http://localhost:3000

## 📁 Project Structure

```
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── agents/    # AI agents (6 components)
│   │   ├── models/    # Pydantic schemas
│   │   ├── knowledge_base/  # Medical ontology
│   │   └── utils/     # Helpers
│   └── data/          # ICMR documents & training data
├── frontend/          # React + Vite UI
└── .env              # API keys (create this)
```

## 🏥 System Components

1. **Symptom Disambiguation Agent** - Converts symptoms to clinical terms
2. **ICMR STW Retrieval Agent** - RAG with FAISS vector DB
3. **Clinical Triage Agent** - Structured clinical interviews
4. **Personalization Agent** - Cultural adaptation
5. **Red-Flag ML Engine** - XGBoost risk assessment
6. **Report Generator** - Clinician & patient reports

## ⚠️ Disclaimer

This is a prototype for educational purposes. NOT for actual medical diagnosis.
