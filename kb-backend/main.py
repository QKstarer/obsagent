import os
import json
import shutil
import tempfile
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from config import VAULT_PATH
from indexer import index_vault
from vectorstore import add_documents, get_stats, clear_all, rebuild_keyword_index
from retriever import retrieve_for_chat, search
from llm import chat, chat_stream
from watcher import start_watcher, stop_watcher, pause_watcher, resume_watcher
from embeddings import embed_progress
from conflict_detector import get_conflict_report, force_scan, detect_conflicts_background
from conversation_saver import save_conversation, get_conversation_stats
from operation_log import log_chat, log_index, log_error, get_recent_logs
from failure_tracker import process_failure_from_chat, get_failure_stats
from progress_tracker import generate_weekly_report, get_progress_stats
from crisproff_kb import save_crisproff_index, get_crisproff_stats
from sgrna_manager import get_sgrna_stats, create_sgrna_record, search_sgrnas
from bsp_analysis import get_analysis_scripts, create_analysis_entry, record_analysis_result, get_bsp_stats, run_methylation_analysis, record_methylation_to_vault
from writing_assistant import generate_methods_section, generate_results_section, generate_discussion_section, save_writing, get_writing_stats
from knowledge_graph import save_knowledge_graph, get_graph_stats
from image_processor import process_image_to_document, process_multiple_images
from entity_recognizer import recognize_entities, find_related_notes, generate_links
from auto_linker import process_file_links, batch_process_links, scan_vault_for_entities
from content_classifier import classify_content, get_suggested_tags, batch_classify
from output_workshop import (
    get_output_templates, create_output_document,
    assess_output_quality, track_output_input, get_output_stats
)

indexing_status = {"running": False, "done": False, "chunks": 0, "error": None}


# ---- Pydantic 请求模型 ----

class ChatRequest(BaseModel):
    query: str

class SgRNARequest(BaseModel):
    gene: str
    sequence: str
    pam: str = "NGG"
    region: str = "TSS 上游 bp"
    cpg_density: str = ""
    gc_content: str = ""
    off_target_score: str = ""
    design_tool: str = "CRISPOR"
    experiment: str = ""
    vector: str = ""
    cell_line: str = ""
    efficiency: str = ""
    system: str = "CRISPRoff"

class BspEntryRequest(BaseModel):
    gene: str
    tool: str = "CRISPResso"
    sample_count: str = "待填写"
    reference: str = "待填写"

class BspResultRequest(BaseModel):
    gene: str
    tool: str
    results: dict

class BspMethylationRequest(BaseModel):
    input_dir: str
    output_dir: str
    gene: str = ""
    sample_range: Optional[str] = None

class WritingRequest(BaseModel):
    gene: str = ""
    experiment: str = ""
    topic: str = ""

class GraphRequest(BaseModel):
    concept: str = "CRISPRoff"

class ImageProcessRequest(BaseModel):
    image_path: str
    title: Optional[str] = None

class ImageUploadRequest(BaseModel):
    filename: str = "image.png"
    data: str

class EntityRequest(BaseModel):
    text: str

class LinkProcessRequest(BaseModel):
    filepath: str

class LinkBatchRequest(BaseModel):
    directory: str

class ClassifyRequest(BaseModel):
    text: str
    filename: str = ""

class ClassifyBatchRequest(BaseModel):
    items: list

class OutputCreateRequest(BaseModel):
    template_type: str
    title: str
    content: str = ""

class OutputAssessRequest(BaseModel):
    content: str
    template_type: str = "paper"


# ---- 后台任务 ----

def _background_index():
    try:
        indexing_status["running"] = True
        pause_watcher()
        print("[INDEX] Starting background indexing...", flush=True)
        documents = index_vault()
        print(f"[INDEX] Chunks found: {len(documents)}, generating embeddings...", flush=True)
        count = add_documents(documents)
        indexing_status["chunks"] = count
        indexing_status["done"] = True
        print(f"[INDEX] Done: {count} chunks indexed", flush=True)
    except Exception as e:
        indexing_status["error"] = str(e)
        print(f"[INDEX] Error: {e}", flush=True)
    finally:
        indexing_status["running"] = False
        resume_watcher()


def _update_crisproff_index():
    """Update CRISPRoff knowledge base index."""
    try:
        save_crisproff_index()
    except Exception as e:
        print(f"[CRISPROFF] Error updating index: {e}", flush=True)


def _schedule_graph_updates():
    """Schedule periodic knowledge graph updates."""
    import schedule
    import time

    def update_graph_job():
        try:
            from knowledge_graph import save_knowledge_graph
            save_knowledge_graph("CRISPRoff")
            print("[GRAPH] Knowledge graph updated", flush=True)
        except Exception as e:
            print(f"[GRAPH] Error updating graph: {e}", flush=True)

    # Run every 6 hours
    schedule.every(6).hours.do(update_graph_job)

    # Run initial update after 5 minutes
    threading.Timer(300, update_graph_job).start()

    # Start scheduler in background
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()


def _update_global_index():
    """Update the global knowledge base index."""
    try:
        from content_processor import update_global_index
        update_global_index()
    except Exception as e:
        print(f"[INDEX] Error updating global index: {e}", flush=True)


def _run_async(coro):
    """Run an async function in a sync context."""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(coro)
    finally:
        loop.close()


# ---- Lifespan ----

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — validate vault path
    if not VAULT_PATH or not os.path.isdir(VAULT_PATH):
        print(f"[STARTUP] WARNING: VAULT_PATH not set or invalid: '{VAULT_PATH}'", flush=True)
        print("[STARTUP] Set OBSIDIAN_VAULT environment variable to your vault path", flush=True)
    # Startup
    try:
        stats = get_stats()
        total = stats.get("total_chunks", 0)
        if total == 0:
            print("[STARTUP] ChromaDB empty, starting background indexing...", flush=True)
            t = threading.Thread(target=_background_index, daemon=True)
            t.start()
        else:
            print(f"[STARTUP] ChromaDB has {total} chunks, rebuilding keyword index...", flush=True)
            threading.Thread(target=rebuild_keyword_index, daemon=True).start()
    except Exception as e:
        print(f"[STARTUP] ChromaDB init error: {e}, will re-index", flush=True)
        t = threading.Thread(target=_background_index, daemon=True)
        t.start()

    try:
        start_watcher()
    except Exception as e:
        print(f"[STARTUP] Watcher error: {e}", flush=True)

    threading.Timer(30, detect_conflicts_background).start()
    threading.Timer(10, _update_global_index).start()
    threading.Timer(15, _update_crisproff_index).start()
    _schedule_graph_updates()

    print("[STARTUP] Server ready", flush=True)
    yield

    # Shutdown
    stop_watcher()


app = FastAPI(title="Obsidian KB Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "app://obsidian.md",
        "http://localhost",
        "http://localhost:*",
        "https://localhost",
    ],
    allow_origin_regex=r"^app://|^http://localhost|^https://localhost",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- 编码处理中间件 ----

@app.middleware("http")
async def decode_body_middleware(request: Request, call_next):
    """统一处理请求体编码，支持 UTF-8 和 GBK。"""
    if request.method in ("POST", "PUT", "PATCH"):
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.body()
            if body:
                for enc in ("utf-8", "gbk"):
                    try:
                        text = body.decode(enc)
                        # Store decoded body for downstream handlers
                        request._decoded_body = json.loads(text)
                        break
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                else:
                    request._decoded_body = None
    response = await call_next(request)
    return response


# ---- API 端点 ----

@app.get("/api/health")
async def health():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "vault_exists": os.path.isdir(VAULT_PATH) if VAULT_PATH else False}


@app.get("/api/status")
async def status():
    stats = get_stats()
    conv_stats = get_conversation_stats()
    return {"status": "ok", "vault": VAULT_PATH, "indexing": indexing_status, "embed_progress": embed_progress, "conversations": conv_stats, **stats}


@app.post("/api/chat")
async def api_chat(request: Request):
    body = await request.body()
    query = _decode_body_query(body)
    result = retrieve_for_chat(query)
    answer = await chat(result["context"], query)
    threading.Thread(
        target=save_conversation,
        args=(query, answer, result["sources"]),
        daemon=True
    ).start()
    log_chat(query, len(result["sources"]))
    threading.Thread(
        target=lambda: _run_async(process_failure_from_chat(query, answer)),
        daemon=True
    ).start()
    return {"answer": answer, "sources": result["sources"]}


@app.post("/api/chat/stream")
async def api_chat_stream(request: Request):
    body = await request.body()
    query = _decode_body_query(body)
    result = retrieve_for_chat(query)

    async def generate():
        async for chunk in chat_stream(result["context"], query):
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'sources': result['sources']}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/search")
async def api_search(q: str = Query(...), top_k: int = Query(5)):
    results = search(q, top_k)
    return {"results": results}


@app.post("/api/index")
async def api_index():
    clear_all()
    documents = index_vault()
    count = add_documents(documents)
    return {"status": "ok", "chunks_indexed": count}


@app.get("/api/files")
async def api_files():
    from indexer import index_vault
    documents = index_vault()
    files = {}
    for d in documents:
        src = d["metadata"]["source"]
        if src not in files:
            files[src] = {"title": d["metadata"]["title"], "tags": d["metadata"]["tags"], "chunks": 0}
        files[src]["chunks"] += 1
    return {"files": files, "total_files": len(files)}


@app.get("/api/conflicts")
async def api_conflicts():
    return get_conflict_report()


@app.post("/api/conflicts/scan")
async def api_conflicts_scan():
    return force_scan()


@app.get("/api/logs")
async def api_logs(count: int = Query(20)):
    return {"logs": get_recent_logs(count)}


@app.get("/api/failures")
async def api_failures():
    return get_failure_stats()


@app.get("/api/progress")
async def api_progress():
    return get_progress_stats()


@app.post("/api/progress/report")
async def api_progress_report():
    threading.Thread(
        target=lambda: _run_async(generate_weekly_report()),
        daemon=True
    ).start()
    return {"status": "started", "message": "周报生成中，请稍后查看 03_输出区/组会汇报/"}


@app.get("/api/crisproff")
async def api_crisproff():
    return get_crisproff_stats()


@app.post("/api/crisproff/index")
async def api_crisproff_index():
    save_crisproff_index()
    return {"status": "ok", "message": "CRISPRoff 知识库索引已更新"}


@app.get("/api/sgrna")
async def api_sgrna(gene: Optional[str] = Query(None)):
    if gene:
        return {"sgrnas": search_sgrnas(gene)}
    return get_sgrna_stats()


@app.post("/api/sgrna/create")
async def api_sgrna_create(req: SgRNARequest):
    filepath = create_sgrna_record(**req.model_dump())
    return {"status": "ok", "filepath": filepath}


@app.get("/api/bsp")
async def api_bsp():
    return get_bsp_stats()


@app.get("/api/bsp/scripts")
async def api_bsp_scripts():
    return get_analysis_scripts()


@app.post("/api/bsp/entry")
async def api_bsp_entry(req: BspEntryRequest):
    filepath = create_analysis_entry(**req.model_dump())
    return {"status": "ok", "filepath": filepath}


@app.post("/api/bsp/result")
async def api_bsp_result(req: BspResultRequest):
    filepath = record_analysis_result(req.gene, req.tool, req.results)
    return {"status": "ok", "filepath": filepath}


@app.post("/api/bsp/methylation")
async def api_bsp_methylation(req: BspMethylationRequest):
    """Run methylation analysis on CRISPResso output."""
    if not req.input_dir or not req.output_dir:
        return {"error": "input_dir and output_dir are required"}

    result = run_methylation_analysis(req.input_dir, req.output_dir, req.sample_range)

    if result.get("success") and req.gene:
        record_methylation_to_vault(req.gene, result)

    return result


@app.get("/api/writing")
async def api_writing():
    return get_writing_stats()


@app.post("/api/writing/methods")
async def api_writing_methods(req: WritingRequest):
    content = await generate_methods_section(req.gene)
    filepath = save_writing(content, "材料与方法", req.gene)
    return {"status": "ok", "content": content, "filepath": filepath}


@app.post("/api/writing/results")
async def api_writing_results(req: WritingRequest):
    content = await generate_results_section(req.experiment)
    filepath = save_writing(content, "结果", req.experiment)
    return {"status": "ok", "content": content, "filepath": filepath}


@app.post("/api/writing/discussion")
async def api_writing_discussion(req: WritingRequest):
    content = await generate_discussion_section(req.topic)
    filepath = save_writing(content, "讨论", req.topic)
    return {"status": "ok", "content": content, "filepath": filepath}


@app.get("/api/graph")
async def api_graph():
    return get_graph_stats()


@app.post("/api/graph/generate")
async def api_graph_generate(req: GraphRequest):
    filepath = save_knowledge_graph(req.concept)
    return {"status": "ok", "filepath": filepath}


@app.post("/api/image/process")
async def api_image_process(req: ImageProcessRequest):
    """Process image and extract text to document."""
    if not req.image_path:
        return {"error": "image_path is required"}
    filepath = await process_image_to_document(req.image_path, req.title)
    return {"status": "ok", "filepath": filepath}


@app.post("/api/image/upload")
async def api_image_upload(req: ImageUploadRequest):
    """Process uploaded image from plugin."""
    if not req.data:
        return {"error": "No image data"}

    import base64 as b64
    # Use NamedTemporaryFile for automatic cleanup
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(b64.b64decode(req.data))
        tmp_path = tmp.name

    try:
        filepath = await process_image_to_document(tmp_path, req.filename)
    finally:
        # Safe cleanup
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    return {"status": "ok", "filepath": filepath}


@app.post("/api/entities/recognize")
async def api_entities_recognize(req: EntityRequest):
    """Recognize entities in text."""
    if not req.text:
        return {"error": "No text provided"}
    entities = recognize_entities(req.text)
    links = generate_links(req.text)
    return {"entities": entities, "links": links}


@app.get("/api/entities/related")
async def api_entities_related(entity: str = Query(...)):
    """Find notes related to an entity."""
    related = find_related_notes(entity)
    return {"related": related}


@app.post("/api/links/process")
async def api_links_process(req: LinkProcessRequest):
    """Process a file and add links to entities."""
    if not req.filepath:
        return {"error": "No filepath provided"}
    abs_path = os.path.join(VAULT_PATH, req.filepath)
    result = process_file_links(abs_path)
    return result


@app.post("/api/links/batch")
async def api_links_batch(req: LinkBatchRequest):
    """Batch process links for all files in a directory."""
    if not req.directory:
        return {"error": "No directory provided"}
    abs_path = os.path.join(VAULT_PATH, req.directory)
    results = batch_process_links(abs_path)
    total_files = len(results)
    files_with_links = sum(1 for r in results if r.get("links_added", 0) > 0)
    total_links_added = sum(r.get("links_added", 0) for r in results)
    return {
        "total_files": total_files,
        "files_with_links": files_with_links,
        "total_links_added": total_links_added,
        "results": results[:20],
    }


@app.get("/api/entities/scan")
async def api_entities_scan():
    """Scan vault and return all entities."""
    entities = scan_vault_for_entities()
    return {"entities": entities, "counts": {k: len(v) for k, v in entities.items()}}


@app.post("/api/classify")
async def api_classify(req: ClassifyRequest):
    """Classify content and suggest folder/tags."""
    if not req.text:
        return {"error": "No text provided"}
    classification = classify_content(req.text, req.filename)
    tags = get_suggested_tags(req.text, classification["category"])
    return {
        "classification": classification,
        "suggested_tags": tags,
    }


@app.post("/api/classify/batch")
async def api_classify_batch(req: ClassifyBatchRequest):
    """Classify a batch of items."""
    if not req.items:
        return {"error": "No items provided"}
    results = batch_classify(req.items)
    return {"results": results}


@app.get("/api/output/templates")
async def api_output_templates():
    """Get all output templates."""
    return get_output_templates()


@app.post("/api/output/create")
async def api_output_create(req: OutputCreateRequest):
    """Create an output document from template."""
    if not req.template_type or not req.title:
        return {"error": "template_type and title are required"}
    filepath = create_output_document(req.template_type, req.title, req.content)
    return {"status": "ok", "filepath": filepath}


@app.post("/api/output/assess")
async def api_output_assess(req: OutputAssessRequest):
    """Assess output quality."""
    if not req.content:
        return {"error": "content is required"}
    result = await assess_output_quality(req.content, req.template_type)
    return result


@app.get("/api/output/stats")
async def api_output_stats():
    """Get output statistics."""
    return get_output_stats()


def _decode_body_query(body: bytes) -> str:
    """Decode JSON body query field, handling both UTF-8 and GBK encoding."""
    for enc in ("utf-8", "gbk"):
        try:
            text = body.decode(enc)
            data = json.loads(text)
            return data["query"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError):
            continue
    # Fallback: force UTF-8
    data = json.loads(body.decode("utf-8", errors="replace"))
    return data["query"]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
