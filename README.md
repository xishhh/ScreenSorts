# ScreenSorts

**AI-Powered Semantic Screenshot Search Engine**

ScreenSorts allows you to search screenshots using natural language instead of filenames. It extracts text via OCR, generates semantic embeddings, and retrieves relevant results through vector similarity search.

## Planned Features

- OCR text extraction from screenshots using PaddleOCR
- Semantic embeddings generation using BGE models
- Vector storage and retrieval with ChromaDB
- Natural language semantic search
- LLM-powered result explanation via Groq API
- Modern Next.js frontend with shadcn/ui
- FastAPI backend with async support
- Docker containerization

## Technology Stack

| Layer | Technology |
| --- | --- |
| Frontend | Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python |
| OCR | PaddleOCR |
| Embeddings | BGE Embeddings |
| Vector DB | ChromaDB |
| LLM | Groq API |
| Containerization | Docker |

## Folder Structure

```
screensorts/
├── frontend/          # Next.js application
│   ├── src/
│   │   ├── app/       # App Router pages
│   │   └── components/# UI components
│   └── ...
├── backend/           # FastAPI application
│   ├── app/           # Application code
│   ├── venv/          # Python virtual environment
│   └── requirements.txt
├── data/              # Screenshot dataset storage
├── vector_store/      # ChromaDB persistence
├── evaluation/        # Evaluation scripts and results
├── docker/            # Docker configuration files
├── docs/              # Documentation
│   └── decisions/     # Architectural decision records
└── ...
```

## Setup Instructions

### Prerequisites

- Node.js 18+
- Python 3.10+
- npm

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend starts at `http://localhost:3000`.

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Linux/Mac
# .\venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The backend starts at `http://localhost:8000`.

### Health Check

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

## Development Roadmap

### Phase 0 — Project Initialization (Current)
- [x] Project structure creation
- [x] Next.js frontend with shadcn/ui
- [x] FastAPI backend with health endpoint
- [x] Environment configuration
- [x] Documentation and git setup

### Phase 1 — OCR Pipeline
- [ ] PaddleOCR integration
- [ ] Screenshot ingestion pipeline
- [ ] Text extraction and storage

### Phase 2 — Search Backend
- [ ] BGE embedding generation
- [ ] ChromaDB vector storage
- [ ] Semantic search endpoint

### Phase 3 — Frontend Integration
- [ ] Search UI with results display
- [ ] Screenshot upload interface
- [ ] Result explanation with Groq

### Phase 4 — Production Readiness
- [ ] Docker setup
- [ ] Testing and evaluation
- [ ] Performance optimization
- [ ] Deployment configuration
