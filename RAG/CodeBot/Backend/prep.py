from dotenv import load_dotenv
import os
import json
from tqdm import tqdm
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv(dotenv_path="../.env")

# Local project directories
LOCAL_REPOS = [
    "/home/zen-zap/Code/rune",
    "/home/zen-zap/Code/julis",
    "/home/zen-zap/Code/mini_tcp",
    "/home/zen-zap/Code/blog_os",
    "/home/zen-zap/Code/lox",
]

ALLOWED_EXTENSIONS = [".rs", ".toml"]
CHUNK_SIZE = 20
OVERLAP = 5
EMBED_MODEL = "text-embedding-ada-002"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VSTORE_PATH = "chroma_code_db"
MANIFEST_PATH = "code_manifest.json"

def gather_code_files_from_dirs(dirs, extensions):
    code_files = []
    for directory in dirs:
        for root, _, files in os.walk(directory):
            for f in files:
                if any(f.endswith(ext) for ext in extensions):
                    code_files.append(os.path.join(root, f))
    return code_files

def load_manifest(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_manifest(path, manifest):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def build_current_manifest(code_files):
    return {f: os.path.getmtime(f) for f in code_files}

def needs_reembedding(vstore_path, code_files, manifest_path):
    # If vectorstore or manifest is missing, re-embed
    if not os.path.exists(vstore_path) or not os.path.exists(manifest_path):
        return True
    prev_manifest = load_manifest(manifest_path)
    curr_manifest = build_current_manifest(code_files)
    # Re-embed if any file is new, missing, or has changed mtime
    return prev_manifest != curr_manifest

def chunk_file(filepath, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Could not read {filepath}: {e}")
        return []
    chunks = []
    for i in range(0, len(lines), chunk_size - overlap):
        chunk = lines[i:i+chunk_size]
        if chunk:
            chunk_text = "".join(chunk)
            chunks.append({
                "text": chunk_text,
                "file": filepath,
                "start_line": i+1
            })
    return chunks

# ---- MAIN LOGIC ----

print("Gathering local code files...")
code_files = gather_code_files_from_dirs(LOCAL_REPOS, ALLOWED_EXTENSIONS)
print(f"Found {len(code_files)} local code files.")

if needs_reembedding(VSTORE_PATH, code_files, MANIFEST_PATH):
    print("Vectorstore missing or outdated OR code files changed, chunking and embedding...")
    all_chunks = []
    for file in tqdm(code_files, desc="Chunking files"):
        all_chunks.extend(chunk_file(file))
    print(f"Total chunks: {len(all_chunks)}")
    texts = [c["text"] for c in all_chunks]
    metadatas = [{"file": c["file"], "start_line": c["start_line"]} for c in all_chunks]

    print("Embedding and saving vectorstore...")
    embeddings = OpenAIEmbeddings(
        model=EMBED_MODEL,
    )
    vectorstore = Chroma.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=VSTORE_PATH
    )
    print("Vectorstore ready!")
    # Save new manifest
    save_manifest(MANIFEST_PATH, build_current_manifest(code_files))
else:
    print(f"Vectorstore already exists at {VSTORE_PATH} and code files unchanged, skipping re-embedding.")
