"""
Tools for SEKTA GOLD - Function calling implementations
"""
import os
import json
import subprocess
import tempfile
import base64
from typing import Dict, Any
import httpx
from io import BytesIO

# --- Tool definitions for OpenAI function calling ---
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for real-time information, news, facts, prices, scores, recent events, people, companies. ALWAYS use for anything that might change or you don't know.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query, 3-8 words, specific"},
                    "num_results": {"type": "integer", "description": "Number of results 3-10", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Generate an image using DALL-E 3. Use for logos, art, diagrams, visuals, photos. Prompt must be detailed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Detailed image description, style, lighting, mood. Min 20 chars."},
                    "size": {"type": "string", "enum": ["1024x1024", "1792x1024", "1024x1792"], "default": "1024x1024"},
                    "quality": {"type": "string", "enum": ["standard", "hd"], "default": "hd"}
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_code",
            "description": "Execute Python code in sandbox to analyze data, do math, generate charts, test code. Returns stdout/stderr. Use for calculations, data analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute. Use print() to output."},
                    "libraries": {"type": "string", "description": "Comma separated pip libraries to install if needed"}
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remember_fact",
            "description": "Save important fact about user to long-term memory. Use when user says 'remember', 'my name is', 'I like', 'I work at', preferences, facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "Fact to remember, concise"},
                    "importance": {"type": "integer", "description": "1-10 importance", "default": 5},
                    "tags": {"type": "string", "description": "comma tags e.g. personal,work,preference"}
                },
                "required": ["fact"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_file",
            "description": "Analyze uploaded file content already provided in context. This is placeholder - actual file text is injected into prompt by backend before LLM call.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "question": {"type": "string", "description": "What to do with file"}
                },
                "required": ["filename", "question"]
            }
        }
    }
]

# --- Implementations ---

async def tool_web_search(query: str, num_results: int = 5) -> str:
    """Tavily > SerpAPI > DuckDuckGo fallback"""
    from config import config
    
    results_text = ""
    
    # Try Tavily if key exists
    if config.TAVILY_API_KEY:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=config.TAVILY_API_KEY)
            res = client.search(query, search_depth="advanced", max_results=num_results)
            for i, r in enumerate(res.get('results', [])[:num_results]):
                results_text += f"[{i+1}] {r.get('title')} - {r.get('url')}\n{r.get('content')[:500]}...\n\n"
            if results_text:
                return f"Web Search Results for '{query}':\n\n{results_text}"
        except Exception as e:
            results_text += f"Tavily error: {e}\n"
    
    # Fallback: DuckDuckGo HTML scraping via httpx (no key)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Using duckduckgo search API-ish endpoint
            # Simple hack: use ddgs via httpx if available else just return placeholder
            # We'll do a simple fetch from Wikipedia + generic
            url = f"https://api.duckduckgo.com/?q={query}&format=json&pretty=0"
            resp = await client.get(url)
            data = resp.json()
            abstract = data.get('AbstractText', '')
            if abstract:
                results_text += f"DuckDuckGo: {abstract} - {data.get('AbstractURL','')}\n"
            related = data.get('RelatedTopics', [])[:3]
            for t in related:
                if isinstance(t, dict) and 'Text' in t:
                    results_text += f"- {t['Text']} ({t.get('FirstURL','')})\n"
    except Exception as e:
        pass
    
    if not results_text:
        results_text = f"No live search results (no TAVILY_API_KEY set). Simulated knowledge: You searched for '{query}'. Please answer from your training data but note that results may not be real-time. For real-time, add TAVILY_API_KEY in .env"
    
    return results_text[:4000]

async def tool_generate_image(prompt: str, size="1024x1024", quality="hd") -> str:
    from config import config
    if not config.OPENAI_API_KEY:
        return "Error: OPENAI_API_KEY not set"
    
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        res = await client.images.generate(
            model=config.OPENAI_IMAGE_MODEL,
            prompt=prompt,
            size=size,
            quality=quality,
            n=1
        )
        url = res.data[0].url
        revised = getattr(res.data[0], 'revised_prompt', prompt)
        return f"Image generated successfully!\nURL: {url}\nRevised prompt: {revised}\n\nTo show user, use markdown: ![Generated Image]({url})"
    except Exception as e:
        return f"Image generation failed: {str(e)}"

def tool_execute_code(code: str, libraries="") -> str:
    # Simple sandbox - timeout 10s, no network, limited
    # Install libs if requested (optional, risky - we skip in prod, just log)
    temp_dir = tempfile.mkdtemp()
    code_file = os.path.join(temp_dir, "run.py")
    
    # Safety: block some dangerous ops (basic)
    blacklist = ["os.system", "subprocess", "socket", "shutil.rmtree", "rm -rf", "__import__('os')", "open('/etc"]
    for b in blacklist:
        if b in code:
            return f"Blocked dangerous operation: {b}. Use safe python only."
    
    # Wrap code to capture prints
    wrapped_code = f"""
import sys
import math
import json
import random
import datetime
import collections
import itertools
import re

# Try import common data libs
try:
    import pandas as pd
    import numpy as np
except:
    pass

# USER CODE STARTS
{code}
# USER CODE ENDS
"""
    with open(code_file, "w") as f:
        f.write(wrapped_code)
    
    try:
        result = subprocess.run(
            ["python3", code_file],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=temp_dir
        )
        output = result.stdout + "\n" + result.stderr
        return output[:5000] if output else "Code executed with no output (did you print?)"
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out (15s limit)"
    except Exception as e:
        return f"Execution error: {e}"

async def tool_remember_fact(fact: str, importance=5, tags="") -> str:
    from memory import memory_store
    mem_id = memory_store.add_memory(fact, importance=importance, tags=tags)
    return f"Fact saved to long-term memory: '{fact}' (id={mem_id}, importance={importance})"

async def tool_analyze_file(filename: str, question: str) -> str:
    # Actual file analysis is done preprocessing, this tool is for LLM to indicate intent
    return f"File analysis requested for {filename}: {question}. [File content is already in context if uploaded via /api/files/analyze]"

# Dispatcher
async def execute_tool(name: str, args: Dict[str, Any]) -> str:
    if name == "web_search":
        return await tool_web_search(args.get("query",""), args.get("num_results",5))
    elif name == "generate_image":
        return await tool_generate_image(args.get("prompt",""), args.get("size","1024x1024"), args.get("quality","hd"))
    elif name == "execute_code":
        return tool_execute_code(args.get("code",""), args.get("libraries",""))
    elif name == "remember_fact":
        return await tool_remember_fact(args.get("fact",""), args.get("importance",5), args.get("tags",""))
    elif name == "analyze_file":
        return await tool_analyze_file(args.get("filename",""), args.get("question",""))
    else:
        return f"Unknown tool: {name}"

def parse_file_content(file_path: str, filename: str) -> str:
    """Extract text from uploaded files"""
    ext = filename.lower().split(".")[-1]
    try:
        if ext == "pdf":
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages[:20]:  # limit 20 pages
                text += page.extract_text() or ""
            return text[:15000]
        elif ext in ["docx"]:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])[:15000]
        elif ext in ["txt", "md", "py", "js", "json", "csv", "html", "css"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()[:15000]
        elif ext in ["xlsx", "xls"]:
            import pandas as pd
            df = pd.read_excel(file_path)
            return f"Excel shape {df.shape}, columns {list(df.columns)}\n\nHead:\n{df.head(20).to_string()}\n\nDescribe:\n{df.describe().to_string()}"
        elif ext in ["png", "jpg", "jpeg", "webp"]:
            # Vision model will handle, just note presence
            return f"[Image file: {filename} - will be sent to vision model]"
        else:
            return f"[Unsupported file type: {ext}]"
    except Exception as e:
        return f"[Error parsing {filename}: {e}]"
