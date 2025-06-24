from dotenv import load_dotenv
import os
import glob
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langsmith import utils, traceable
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

load_dotenv(dotenv_path="../.env")

EMBED_MODEL = "text-embedding-ada-002"
MODEL_NAME = "gpt-4o"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SAVE_ROOT = "github_code"
CHUNK_SIZE = 20
OVERLAP = 5
REPOS = [
    "zen-zap/ROC",   
    "zen-zap/rune",
    "zen-zap/julis",
]

embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
vectorstore = Chroma(
    persist_directory="chroma_code_db",
    embedding_function=embeddings
)

code_files = []
for root, dirs, files in os.walk(SAVE_ROOT):
    for f in files:
        if f.endswith((".rs")):
            code_files.append(os.path.join(root, f))

@traceable
def retrieve_code(query, vectorstore, k=4):
    results = vectorstore.similarity_search(query, k=k)
    return results

@traceable
def rag_answer(query, vectorstore, model_name=MODEL_NAME, k=4):
    results = retrieve_code(query, vectorstore, k)
    context = "\n\n".join([f"File: {r.metadata['file']} (Line {r.metadata['start_line']})\n{r.page_content}" for r in results])

    prompt = ChatPromptTemplate.from_template("""
You are an expert Rust code assistant.

Given these code snippets from the project, and a user query, suggest the best code or improvement. 
Do NOT mention file names, line numbers, or file locations in your response. 
Just provide the code and a short, clear explanation of your choices.

---CODE SNIPPETS---
{context}
---END SNIPPETS---

User query: {query}

Respond with an improved code suggestion and a concise explanation.
    """)

    llm = ChatOpenAI(model=model_name)
    chain = prompt | llm
    response = chain.invoke({"context": context, "query": query})

    return response.content

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class CompleteRequest(BaseModel):
    code: str

@app.post("/complete")
async def complete_code(request: CompleteRequest):
    code = request.code
    lines = code.rstrip().splitlines()
    if not lines:
        query = ""
    else:
        query = f"Continue this code:\n{code}\n"
    suggestion = rag_answer(query, vectorstore)
    return {"suggestion": suggestion}

@app.get("/details")
async def get_details():
    return {
        "embedding_model": EMBED_MODEL,
        "llm_model": MODEL_NAME,
        "repos": REPOS,
        "chunk_size": CHUNK_SIZE,
        "overlap": OVERLAP,
        "vectorstore_path": "chroma_code_db",
        "total_files": len(code_files),
        # "total_chunks": Optional, you can save this info in a meta.json during data prep
        "openai_key_loaded": bool(OPENAI_API_KEY),
        "tracing_enabled": utils.tracing_is_enabled()
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/files")
async def get_sample_files(n: int = 10):
    all_fetched = glob.glob(f"{SAVE_ROOT}/**/*", recursive=True)
    sample = [f for f in all_fetched[:n]]
    return {"sample_files": sample}
