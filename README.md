# 🚀 RAG Chatbot API (FastAPI + LangChain + PostgreSQL)

A production-grade **Retrieval-Augmented Generation (RAG)** backend built with **FastAPI**, **LangChain**, and **PostgreSQL (pgvector)**.
This project enables users to upload documents, process them into embeddings, and perform intelligent conversational Q&A using LLMs.

---

## 📌 Features

* 📄 **Multi-file Upload Support** (PDF, DOCX, TXT)
* 🧠 **Semantic Search with pgvector**
* 💬 **Chat-based Q&A over Documents**
* ⚡ **Async FastAPI Architecture**
* 🧵 **Session-based Context Handling**
* 📊 **Chunking + Embedding Pipeline**
* 🧾 **Automatic Document Summarization**
* ☁️ **AWS S3 Integration (optional)**
* 🔄 **Background Processing (FastAPI Tasks / Queue-ready)**
* 🧩 **Scalable & Microservices-ready Design**

---

## 🏗️ Architecture Overview

```
User Query
   │
   ▼
FastAPI API Layer
   │
   ├── File Upload Service
   │       └── Chunking + Embedding (LangChain)
   │
   ├── Chat Service
   │       ├── Query Classification (Doc vs General)
   │       ├── Semantic Search (pgvector)
   │       └── LLM Response Generation
   │
   └── Storage Layer
           ├── PostgreSQL (Metadata + Embeddings)
           └── S3 (Files)
```

---

## 🧰 Tech Stack

| Layer            | Technology            |
| ---------------- | --------------------- |
| Backend          | FastAPI (Python)      |
| AI/LLM           | LangChain + OpenAI    |
| Database         | PostgreSQL + pgvector |
| Storage          | AWS S3                |
| Async ORM        | SQLAlchemy (Async)    |
| Queue (Optional) | Celery / SQS          |
| Embeddings       | OpenAI / HuggingFace  |

---

## 📂 Project Structure

```
app/
├── controllers/                 # Handles incoming requests (business logic entry)
│   ├── chatController.py
│   ├── fileUploaderController.py
│   └── semanticSearchController.py
│
├── helpers/                     # Utility & shared helper functions
│   ├── config.py
│   ├── databaseConnection.py
│   ├── exception.py
│   └── helper.py
│
├── models/                      # Database models (ORM)
│   ├── chatModel.py
│   └── documentModel.py
│
├── routers/                     # API route definitions
│   └── chatRouter.py
│
├── schemas/                     # Pydantic schemas (request/response validation)
│   └── chatSchema.py
│
├── worker/                      # Background processing (RAG pipeline & async jobs)
│   ├── config.py
│   ├── db.py
│   ├── doc_parser.py
│   ├── embedding.py
│   ├── listener.py
│   ├── rag_worker.py
│   └── temp/                    # Temporary files / intermediate processing
│
├── main.py                      # FastAPI application entry point
│
.env                             # Environment variables
.gitignore
README.md
myenv/                           # Virtual environment (should be gitignored)
```

---

## ⚙️ Setup & Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-username/rag-chatbot-api.git
cd rag-chatbot-api
```

### 2. Create Virtual Environment

```bash
python -m venv myenv
source myenv/bin/activate  # Mac/Linux
myenv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

Create `.env` file:

```env
OPENAI_API_KEY=your_key
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
AWS_ACCESS_KEY=your_key
AWS_SECRET_KEY=your_secret
S3_BUCKET=your_bucket
```

---

## 🗄️ Database Setup

Enable pgvector:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Run migrations (if using Alembic):

```bash
alembic upgrade head
```

---

## ▶️ Run the Application

```bash
uvicorn app.main:app --reload
```

API Docs:

```
http://localhost:8000/docs
```

---

## 🔍 Core Workflow

### 📤 Document Upload Flow

1. Upload file
2. Extract text
3. Split into chunks
4. Generate embeddings
5. Store in PostgreSQL (pgvector)
6. Save file in S3 (optional)

---

### 💬 Chat Flow

1. User sends query
2. System decides:

   * General query → Direct LLM
   * Document query → Semantic search
3. Retrieve top-k relevant chunks
4. Send context + query to LLM
5. Return response

---

## 🧠 Smart Optimization (Important)

To reduce cost & latency:

* ✅ Query classification before semantic search
* ✅ Limit search to **recent/session documents**
* ✅ Cache embeddings/results
* ✅ Use top-k retrieval instead of full scan

---

## 📡 API Endpoints

### Upload File

```http
POST /upload
```

### Ask Question

```http
POST /chat
```

### Get Documents

```http
GET /documents
```

---

## 🧪 Example Request

```json
POST /chat

{
  "session_id": "abc123",
  "query": "Summarize my uploaded documents"
}
```

---

## 🔐 Security & Best Practices

* Use **JWT Authentication**
* Validate file types & size
* Secure S3 bucket (no public ACL)
* Use async DB operations
* Add rate limiting

---

## 🚀 Future Improvements

* 🔄 Streaming responses
* 🧠 Hybrid search (keyword + vector)
* 🗃️ Multi-tenant support
* 📊 Analytics dashboard
* 🤖 Agent-based workflows
* 🧾 Document versioning

---

## 🤝 Contributing

Contributions are welcome!
Please fork the repo and submit a pull request.

---

# 👨‍💻 Author

**Rupesh Rajhans**
rupesh.rajhans92@gmail.com
(Software Engineer | GenAI Developer | AI SaaS Builder)

---

## ⭐ Support

If you like this project, give it a ⭐ on GitHub!

---
