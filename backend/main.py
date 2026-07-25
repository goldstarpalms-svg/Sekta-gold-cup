"""
SEKTA GOLD CUP - Ultimate Chatbot Backend
FastAPI + OpenAI + Streaming + Tools + Memory + Vision + Files
Better than all chatbots in history.
"""
import os
import json
import uuid
import asyncio
import base64
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx

from config import config
from memory import memory_store
from prompts import AGENTS, get_agent, list_agents
from tools import TOOL_DEFINITIONS, execute_tool, parse_file_content

# Check config
config.check()

app = FastAPI(title="SEKTA GOLD API", version="2.0.0 - Ultimate")

# CORS - allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In prod, lock to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure dirs
os.makedirs("data", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("generated_images", exist_ok=True)

# --- Models ---
class ChatMessage(BaseModel):
    role: str  # user, assistant, system, tool
    content: str
    images: Optional[List[str]] = None  # base64 or URLs
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    chat_id: Optional[str] = None
    agent_id: str = "sekta-omni"
    model: Optional[str] = None
    stream: bool = True
    temperature: float = 0.7
    use_web_search: bool = True
    use_memory: bool = True
    files_context: Optional[str] = None  # pre-parsed file content

class ImageGenRequest(BaseModel):
    prompt: str
    size: str = "1024x1024"
    quality: str = "hd"

class TTSRequest(BaseModel):
    text: str
    voice: str = "alloy"
    model: Optional[str] = None

# --- OpenAI Client Helper ---
def get_openai_client():
    if not config.OPENAI_API_KEY or "YOUR_NEW_KEY" in config.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set. Create .env from .env.example")
    from openai import AsyncOpenAI
    return AsyncOpenAI(api_key=config.OPENAI_API_KEY)

# --- Routes ---

@app.get("/")
async def root():
    return {
        "name": "SEKTA GOLD CUP API",
        "version": "2.0-ULTIMATE",
        "status": "🏆 Gold Standard Online",
        "agents": len(AGENTS),
        "features": ["streaming", "vision", "image-gen", "web-search", "memory", "code-exec", "files", "voice"],
        "docs": "/docs"
    }

@app.get("/api/agents")
async def get_agents():
    return list_agents()

@app.get("/api/models")
async def list_models():
    try:
        client = get_openai_client()
        models = await client.models.list()
        # filter chat models
        chat_models = [m.id for m in models.data if "gpt" in m.id or "o1" in m.id][:20]
        return {"models": chat_models, "default": config.OPENAI_MODEL}
    except Exception as e:
        return {"models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1-preview"], "default": config.OPENAI_MODEL, "error": str(e)}

@app.get("/api/chats")
async def list_chats():
    return memory_store.list_chats()

@app.get("/api/chats/{chat_id}")
async def get_chat(chat_id: str):
    chat = memory_store.get_chat(chat_id)
    if not chat:
        raise HTTPException(404, "Chat not found")
    return chat

@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str):
    memory_store.delete_chat(chat_id)
    return {"deleted": chat_id}

@app.post("/api/chats")
async def create_chat(title: str = "New Chat", agent_id: str = "sekta-omni"):
    chat_id = memory_store.create_chat(title=title, agent_id=agent_id)
    return {"chat_id": chat_id, "title": title, "agent_id": agent_id}

@app.get("/api/memory")
async def get_memories():
    return memory_store.list_memories()

@app.get("/api/memory/search")
async def search_memory(q: str):
    results = memory_store.search_memories(q)
    return {"query": q, "results": results}

@app.post("/api/files/analyze")
async def analyze_files(files: List[UploadFile] = File(...)):
    """Upload and parse files, return context string"""
    contexts = []
    for file in files:
        file_id = str(uuid.uuid4())[:8]
        ext = file.filename.split(".")[-1] if "." in file.filename else "txt"
        save_path = os.path.join("uploads", f"{file_id}_{file.filename}")
        
        content = await file.read()
        if len(content) > config.MAX_FILE_SIZE_MB * 1024 * 1024:
            contexts.append(f"File {file.filename} too large (> {config.MAX_FILE_SIZE_MB}MB)")
            continue
        
        with open(save_path, "wb") as f:
            f.write(content)
        
        # For images, we'll return base64 for vision
        if ext.lower() in ["png","jpg","jpeg","webp"]:
            b64 = base64.b64encode(content).decode()
            contexts.append(f"IMAGE:{file.filename}:data:image/{ext};base64,{b64[:100]}... [full image will be sent to vision]")
            # Also keep path
            contexts.append(f"File {file.filename} uploaded as image, available for vision model.")
        else:
            text = parse_file_content(save_path, file.filename)
            contexts.append(f"--- FILE: {file.filename} ---\n{text}\n--- END FILE ---")
    
    combined = "\n\n".join(contexts)
    return {"files_context": combined, "num_files": len(files)}

@app.post("/api/image/generate")
async def generate_image(req: ImageGenRequest):
    client = get_openai_client()
    try:
        res = await client.images.generate(
            model=config.OPENAI_IMAGE_MODEL,
            prompt=req.prompt,
            size=req.size,
            quality=req.quality,
            n=1
        )
        return {"url": res.data[0].url, "revised_prompt": getattr(res.data[0], 'revised_prompt', req.prompt)}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/audio/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    client = get_openai_client()
    try:
        temp_path = f"uploads/{uuid.uuid4()}_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        with open(temp_path, "rb") as audio_file:
            transcript = await client.audio.transcriptions.create(
                model=config.OPENAI_STT_MODEL,
                file=audio_file
            )
        os.remove(temp_path)
        return {"text": transcript.text}
    except Exception as e:
        raise HTTPException(500, f"Transcription failed: {e}")

@app.post("/api/audio/speak")
async def text_to_speech(req: TTSRequest):
    client = get_openai_client()
    try:
        response = await client.audio.speech.create(
            model=req.model or config.OPENAI_TTS_MODEL,
            voice=req.voice,
            input=req.text[:4000]
        )
        audio_path = f"generated_images/{uuid.uuid4()}.mp3"
        response.stream_to_file(audio_path)
        # Return as base64 or file path - for simplicity, return path and serve static?
        # We'll return audio as base64 for frontend quick play
        with open(audio_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return {"audio_base64": b64, "format": "mp3"}
    except Exception as e:
        raise HTTPException(500, f"TTS failed: {e}")

# --- CORE CHAT LOGIC WITH STREAMING + TOOLS ---

@app.post("/api/chat")
async def chat_stream(request: ChatRequest):
    """
    Ultimate chat endpoint - streams with tool calling loop, memory, vision.
    """
    client = get_openai_client()
    agent = get_agent(request.agent_id)
    model = request.model or config.OPENAI_MODEL
    
    # Build system prompt with memory & files
    system_content = agent["system_prompt"]
    
    if request.use_memory and config.ENABLE_MEMORY:
        # Search relevant memories based on last user message
        last_user_msg = next((m.content for m in reversed(request.messages) if m.role == "user"), "")
        if last_user_msg:
            relevant = memory_store.search_memories(last_user_msg, limit=5)
            if relevant:
                mem_str = "\n".join([f"- {m['content']} (importance {m['importance']})" for m in relevant])
                system_content += f"\n\n[RELEVANT LONG-TERM MEMORIES ABOUT USER]:\n{mem_str}"
        
        facts = memory_store.get_facts_str()
        if facts and facts != "No facts yet.":
            system_content += f"\n\n[USER FACTS]:\n{facts}"
    
    if request.files_context:
        system_content += f"\n\n[UPLOADED FILES CONTEXT]:\n{request.files_context[:12000]}"  # truncate
    
    # Prepare OpenAI messages
    openai_messages: List[Dict] = [{"role": "system", "content": system_content}]
    
    # Convert chat messages to OpenAI format, handling vision
    for msg in request.messages:
        if msg.images:
            # Vision message
            content_parts = [{"type": "text", "text": msg.content}]
            for img_b64 in msg.images:
                # If it's already data URL, use it, else assume url
                if img_b64.startswith("data:image"):
                    content_parts.append({"type": "image_url", "image_url": {"url": img_b64}})
                elif img_b64.startswith("http"):
                    content_parts.append({"type": "image_url", "image_url": {"url": img_b64}})
                else:
                    # assume base64
                    content_parts.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})
            openai_messages.append({"role": msg.role, "content": content_parts})
        else:
            openai_messages.append({"role": msg.role, "content": msg.content})
    
    # Tool calling loop (max 5 iterations)
    async def event_generator():
        nonlocal openai_messages
        tool_calls_executed = 0
        max_tool_loops = 5
        
        for _ in range(max_tool_loops):
            try:
                # Stream the completion
                stream = await client.chat.completions.create(
                    model=model,
                    messages=openai_messages,
                    tools=TOOL_DEFINITIONS if config.ENABLE_WEB_SEARCH or config.ENABLE_IMAGE_GEN else None,
                    tool_choice="auto" if tool_calls_executed < 3 else "none",
                    temperature=request.temperature,
                    stream=True,
                    max_tokens=4000
                )
                
                full_content = ""
                tool_calls_buffer: Dict[int, Dict] = {}
                
                async for chunk in stream:
                    delta = chunk.choices[0].delta
                    
                    # Handle tool calls streaming
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_buffer:
                                tool_calls_buffer[idx] = {"id": "", "name": "", "arguments": ""}
                            if tc.id:
                                tool_calls_buffer[idx]["id"] += tc.id
                            if tc.function:
                                if tc.function.name:
                                    tool_calls_buffer[idx]["name"] += tc.function.name
                                if tc.function.arguments:
                                    tool_calls_buffer[idx]["arguments"] += tc.function.arguments
                    
                    # Handle content
                    if delta.content:
                        full_content += delta.content
                        # stream to client as SSE
                        yield f"data: {json.dumps({'type': 'content', 'content': delta.content})}\n\n"
                
                # If we have tool calls, execute them
                if tool_calls_buffer:
                    tool_calls_executed += len(tool_calls_buffer)
                    
                    # Add assistant message with tool calls to history
                    openai_messages.append({
                        "role": "assistant",
                        "content": full_content or None,
                        "tool_calls": [
                            {
                                "id": v["id"],
                                "type": "function",
                                "function": {"name": v["name"], "arguments": v["arguments"]}
                            } for v in tool_calls_buffer.values()
                        ]
                    })
                    
                    # Execute each tool
                    for tc_idx, tc_data in tool_calls_buffer.items():
                        tool_name = tc_data["name"]
                        try:
                            args = json.loads(tc_data["arguments"] or "{}")
                        except:
                            args = {}
                        
                        yield f"data: {json.dumps({'type': 'tool_start', 'tool': tool_name, 'args': args})}\n\n"
                        
                        try:
                            result = await execute_tool(tool_name, args)
                        except Exception as e:
                            result = f"Tool {tool_name} failed: {e}"
                        
                        # Send tool result to client
                        yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'result': result[:2000]})}\n\n"
                        
                        # Add tool result to messages for next loop
                        openai_messages.append({
                            "role": "tool",
                            "tool_call_id": tc_data["id"],
                            "name": tool_name,
                            "content": result
                        })
                    
                    # Continue loop to get final answer after tools
                    continue
                else:
                    # No tool calls, we are done - save chat if needed
                    final_assistant_msg = full_content
                    if request.chat_id:
                        chat = memory_store.get_chat(request.chat_id)
                        if chat:
                            msgs = chat["messages"]
                            # Append latest user + assistant
                            # Reconstruct from request.messages (last) + assistant
                            last_user = request.messages[-1].dict() if request.messages else {}
                            msgs.append(last_user)
                            msgs.append({"role": "assistant", "content": final_assistant_msg})
                            # Title generation if first chat
                            title = chat["title"]
                            if title == "New Chat" and len(msgs) >= 2:
                                title = (request.messages[-1].content[:40] + "...") if request.messages else "Chat"
                            memory_store.save_messages(request.chat_id, msgs, title=title)
                    
                    yield f"data: {json.dumps({'type': 'done', 'full_content': final_assistant_msg})}\n\n"
                    break
                    
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
                break
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no"
    })

@app.post("/api/chat/completion")
async def chat_completion(request: ChatRequest):
    """Non-streaming version for simpler clients"""
    client = get_openai_client()
    agent = get_agent(request.agent_id)
    model = request.model or config.OPENAI_MODEL
    
    system_content = agent["system_prompt"]
    if request.files_context:
        system_content += f"\n\nFILES:\n{request.files_context[:12000]}"
    
    messages = [{"role": "system", "content": system_content}]
    for m in request.messages:
        messages.append({"role": m.role, "content": m.content})
    
    try:
        resp = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=request.temperature,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto"
        )
        msg = resp.choices[0].message
        content = msg.content
        
        # Handle tool calls one-shot
        if msg.tool_calls:
            messages.append(msg.model_dump())
            for tc in msg.tool_calls:
                result = await execute_tool(tc.function.name, json.loads(tc.function.arguments))
                messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.function.name, "content": result})
            # second call
            resp2 = await client.chat.completions.create(model=model, messages=messages, temperature=request.temperature)
            content = resp2.choices[0].message.content
        
        return {"content": content, "model": model, "agent": agent["name"]}
    except Exception as e:
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    import uvicorn
    print(f"""
🏆 SEKTA GOLD CUP — Ultimate Chatbot Backend Starting...
   Agent Count: {len(AGENTS)}
   Model: {config.OPENAI_MODEL}
   Port: {config.BACKEND_PORT}
   Features: WebSearch={config.ENABLE_WEB_SEARCH} Memory={config.ENABLE_MEMORY} ImageGen={config.ENABLE_IMAGE_GEN}
   
   👉 Open http://localhost:{config.BACKEND_PORT}/docs for API docs
   👉 Frontend should run on http://localhost:5173
   
   ⚠️  If you leaked your key, revoke it at https://platform.openai.com/api-keys
    """)
    uvicorn.run("main:app", host="0.0.0.0", port=config.BACKEND_PORT, reload=True)
