# api.py
from fastapi import FastAPI
from pydantic import BaseModel
from rag_pipeline import PropertyRAG
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(title="HomeHive API", version="1.0")

# Allow frontend or local tools to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG pipeline
rag = PropertyRAG()

# Request model
class QueryRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"message": "HomeHive API is up and running!"}

@app.post("/query")
def query_rag(request: QueryRequest):
    q = request.query.strip()
    if not q:
        return {"error": "Empty query"}
    narrative, preview_df, full_df = rag.process_query(q)

    preview = preview_df.to_dict(orient="records") if not preview_df.empty else []
    full = full_df.to_dict(orient="records") if not full_df.empty else preview

    return {
        "response": narrative,
        "preview": preview,
        "results": full
    }
