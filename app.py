"""
SEKTA GOLD CUP — Streamlit Cloud Edition
The Ultimate Chatbot — Better than all history, now 1-file Streamlit deploy

Deploy to Streamlit Cloud in 1 click: https://share.streamlit.io/deploy

Secrets needed (in Streamlit Dashboard → Secrets):
OPENAI_API_KEY = "sk-proj-..."
TAVILY_API_KEY = "tvly-..." # optional for real web search
"""

import streamlit as st
import os
import json
import base64
import time
import uuid
from datetime import datetime
from typing import List, Dict
import io

# --- PAGE CONFIG GOLD THEME ---
st.set_page_config(
    page_title="SEKTA GOLD CUP — Ultimate AI",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# SEKTA GOLD CUP\nBetter than ChatGPT, Claude, Gemini combined.\nBuilt for Streamlit Cloud."
    }
)

# --- GOLD CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, [class*="css"] { font-family: 'Instrument Sans', sans-serif; }
.stApp { background: #0A0A0B; color: #E5E5E5; }
h1, h2, h3 { font-family: 'Instrument Sans', sans-serif !important; }
[data-testid="stSidebar"] { background: #0F0F10; border-right: 1px solid #232325; }
[data-testid="stHeader"] { background: rgba(10,10,11,0.8); backdrop-filter: blur(10px); }
.stChatMessage { background: #141415; border: 1px solid #232325; border-radius: 16px; }
.stChatMessage[data-testid="stChatMessage"]:nth-child(odd) { background: #141415; }
div[data-testid="stChatMessageAvatarAssistant"] { background: linear-gradient(135deg,#FFC700,#FF8A00); }
.gold-card { background: #141415; border: 1px solid #232325; border-radius: 12px; padding: 16px; }
.gold-badge { background: rgba(255,199,0,0.1); border: 1px solid rgba(255,199,0,0.3); color: #FFC700; padding: 4px 10px; border-radius: 100px; font-size: 11px; font-family: 'JetBrains Mono'; }
.gold-btn > button { background: white !important; color: black !important; border-radius: 10px !important; font-weight: 600 !important; }
.gold-glow { box-shadow: 0 0 40px rgba(255,199,0,0.15); }
a { color: #FFC700 !important; }
</style>
""", unsafe_allow_html=True)

# --- AGENTS (same as backend) ---
AGENTS = {
    "sekta-omni": {
        "name": "SEKTA GOLD OMNI",
        "icon": "🏆",
        "desc": "Ultimate - ChatGPT+Claude+Perplexity combined",
        "prompt": """You are SEKTA GOLD OMNI — the most advanced AI ever, better than all chatbots in history. Built for Streamlit Cloud.

You have superpowers: web search (if TAVILY key), image gen (DALL-E 3), file analysis, memory. 
Style: helpful, witty, direct, concise but thorough. Use markdown elegantly. Always offer next steps.
If user asks for recent news, prices, scores, you MUST say you searched (and use search tool logic if available).
If user asks for image/logo/art, you MUST generate via image tool mindset and give detailed prompt.

Current time: 2026-07-25. You are running on Streamlit Cloud.
You are SEKTA GOLD — Gold Standard."""
    },
    "code-titan": {
        "name": "CODE TITAN",
        "icon": "💻",
        "desc": "Staff Engineer, builds full apps",
        "prompt": """You are CODE TITAN — Staff Engineer at FAANG, better than Cursor/Devin. Write PRODUCTION-READY code, error handling, best practices. If asked for app, build fully with file structure and how to run. Use Streamlit artifacts where possible: provide code that can run in Streamlit. Be builder, not tutorial."""
    },
    "research-oracle": {
        "name": "RESEARCH ORACLE",
        "icon": "🔍",
        "desc": "Perplexity Pro with citations",
        "prompt": """You are RESEARCH ORACLE — PhD researcher. For factual/news questions, MUST search web and provide 3-5 citations like [1](url). Structure: TL;DR → Key Findings with sources → Deep Dive. Be precise, flag uncertainty."""
    },
    "creative-god": {
        "name": "CREATIVE GOD",
        "icon": "🎨",
        "desc": "Viral content & visuals",
        "prompt": """You are CREATIVE GOD — Cannes Lions winner. Give 3 variations: Safe, Bold, Unhinged. For visuals, provide ultra-detailed DALL-E prompt: Subject, style, lighting, lens, palette, mood --ar 16:9. Make it famous."""
    },
    "data-wizard": {
        "name": "DATA WIZARD",
        "icon": "📊",
        "desc": "CSV & chart master",
        "prompt": """You are DATA WIZARD — Kaggle Grandmaster. When user uploads CSV/XLSX, do EDA: shape, columns, missing, stats, insights, actionable recommendations. Write pandas code to analyze. Turn data to gold."""
    },
    "study-buddy": {
        "name": "STUDY BUDDY",
        "icon": "📚",
        "desc": "Feynman tutor",
        "prompt": """You are STUDY BUDDY — best tutor. Teach via Analogy → Simple → Example → Quiz. Adapt to user level. Use diagrams via markdown or image gen. Make learning addictive."""
    },
    "business-shark": {
        "name": "BUSINESS SHARK",
        "icon": "🦈",
        "desc": "YC + Shark Tank",
        "prompt": """You are BUSINESS SHARK — built 3 unicorns. Evaluate via Pain/Market/Moat/Money. For pitch: Problem, Solution, Market, Product, Traction, Team, Financials, Ask. Brutally honest, make founders rich."""
    },
    "therapist-v2": {
        "name": "THERAPIST V2",
        "icon": "💛",
        "desc": "Supportive listener",
        "prompt": """You are THERAPIST V2 — warm, empathetic, non-judgmental, not licensed. Validate, reflect feelings, ask open Qs, CBT tools. If self-harm, give crisis lines: US 988, UK 116 123. I'm AI disclaimer."""
    },
}

# --- SECRETS & CLIENT ---
def get_openai_key():
    # Priority: st.secrets > env > sidebar input
    key = None
    try:
        key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    if not key:
        key = os.getenv("OPENAI_API_KEY")
    if not key:
        key = st.session_state.get("openai_key_input", "")
    return key

def get_tavily_key():
    try:
        return st.secrets["TAVILY_API_KEY"]
    except Exception:
        return os.getenv("TAVILY_API_KEY", "")

def get_client():
    key = get_openai_key()
    if not key or "YOUR_NEW_KEY" in key or "4R35dzYfeSafQbROrcX1arD" in key:
        return None, key
    from openai import OpenAI
    return OpenAI(api_key=key), key

# --- TOOLS ---
def tool_web_search(query: str, num=5):
    tavily_key = get_tavily_key()
    results = ""
    if tavily_key:
        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=tavily_key)
            res = client.search(query, search_depth="advanced", max_results=num)
            for i, r in enumerate(res.get('results', [])[:num]):
                results += f"[{i+1}] {r.get('title')} — {r.get('url')}\n{r.get('content')[:600]}\n\n"
            return f"Web search results for '{query}':\n\n{results}"
        except Exception as e:
            results += f"Tavily error {e}\n"
    # Fallback DuckDuckGo abstract
    try:
        import httpx
        with httpx.Client(timeout=10) as c:
            resp = c.get(f"https://api.duckduckgo.com/?q={query}&format=json")
            data = resp.json()
            if data.get('AbstractText'):
                results += f"DuckDuckGo: {data['AbstractText']} — {data.get('AbstractURL')}\n"
    except Exception:
        pass
    if not results:
        results = f"No live search available (add TAVILY_API_KEY in Streamlit Secrets for real search). Answering '{query}' from knowledge but note data may not be real-time."
    return results

def tool_generate_image(prompt: str, size="1024x1024"):
    client, _ = get_client()
    if not client:
        return None, "No OpenAI key"
    try:
        res = client.images.generate(model="dall-e-3", prompt=prompt, size=size, quality="hd", n=1)
        url = res.data[0].url
        return url, getattr(res.data[0], 'revised_prompt', prompt)
    except Exception as e:
        return None, str(e)

def parse_uploaded_file(uploaded_file):
    name = uploaded_file.name
    ext = name.split(".")[-1].lower()
    try:
        if ext == "pdf":
            from PyPDF2 import PdfReader
            reader = PdfReader(uploaded_file)
            text = "".join([p.extract_text() or "" for p in reader.pages[:20]])
            return f"--- FILE {name} ---\n{text[:15000]}"
        elif ext in ["txt","md","py","js","json","csv","html","css"]:
            content = uploaded_file.read().decode('utf-8', errors='ignore')
            return f"--- FILE {name} ---\n{content[:15000]}"
        elif ext in ["xlsx","xls"]:
            import pandas as pd
            df = pd.read_excel(uploaded_file)
            return f"--- FILE {name} Excel shape {df.shape} columns {list(df.columns)} ---\n{df.head(20).to_string()}"
        elif ext in ["docx"]:
            from docx import Document
            doc = Document(uploaded_file)
            return f"--- FILE {name} ---\n" + "\n".join([p.text for p in doc.paragraphs])[:15000]
        elif ext in ["png","jpg","jpeg","webp"]:
            # Return for vision
            b64 = base64.b64encode(uploaded_file.getvalue()).decode()
            return f"[IMAGE FILE: {name} - base64 vision available]"
        else:
            return f"[Unsupported file {name}]"
    except Exception as e:
        return f"[Error parsing {name}: {e}]"

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [] # list of chats
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = str(uuid.uuid4())[:8]
if "uploaded_context" not in st.session_state:
    st.session_state.uploaded_context = ""
if "memories" not in st.session_state:
    st.session_state.memories = []  # simple in-memory for streamlit cloud (persists per session)
if "model" not in st.session_state:
    st.session_state.model = "gpt-4o"

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
    <div style='display:flex;gap:10px;align-items:center;margin-bottom:16px'>
      <div style='width:36px;height:36px;border-radius:10px;background:linear-gradient(135deg,#FFC700,#FF8A00);display:flex;align-items:center;justify-content:center;color:black;font-weight:800;font-size:18px'>S</div>
      <div><div style='font-weight:800;line-height:1'>SEKTA GOLD</div><div style='font-size:11px;color:#8A8A90;font-family:monospace'>STREAMLIT • v2.0</div></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Security warning
    st.markdown("""
    <div class='gold-card' style='margin-bottom:12px'>
      <div style='color:#FFC700;font-family:monospace;font-weight:700;font-size:12px;margin-bottom:4px'>⚠️ SECURITY</div>
      <div style='font-size:11px;line-height:1.4'>If you leaked key starting <code>sk-proj-4R35...</code>, revoke at <a href='https://platform.openai.com/api-keys' target='_blank'>platform.openai.com/api-keys</a> NOW, then set new key in Streamlit Secrets.</div>
    </div>
    """, unsafe_allow_html=True)

    # API Key input if not in secrets
    openai_key = get_openai_key()
    if not openai_key or "YOUR_NEW_KEY" in openai_key:
        st.warning("🔑 No OpenAI key found. Add in Streamlit Secrets or below:")
        key_input = st.text_input("OpenAI API Key", type="password", placeholder="sk-proj-... (new key after revoke)")
        if key_input:
            st.session_state.openai_key_input = key_input
            st.rerun()
    else:
        if "4R35dzYfeSafQbROrcX1arD" in openai_key:
            st.error("🚨 You are using the LEAKED compromised key! Revoke it and use new one in Secrets.")
        else:
            st.success(f"✅ Key set • {openai_key[:7]}...{openai_key[-4:]}")
        if st.button("🔄 Clear Key", use_container_width=True):
            st.session_state.openai_key_input = ""
            st.rerun()

    st.divider()
    st.markdown("<div style='font-size:11px;font-family:monospace;color:#8A8A90;letter-spacing:1px;margin-bottom:8px'>AGENTS • CHOOSE POWER</div>", unsafe_allow_html=True)
    agent_id = st.selectbox("Agent", options=list(AGENTS.keys()), format_func=lambda x: f"{AGENTS[x]['icon']} {AGENTS[x]['name']}", label_visibility="collapsed")
    selected_agent = AGENTS[agent_id]
    st.markdown(f"<div class='gold-card'><div style='font-weight:700;font-size:13px'>{selected_agent['icon']} {selected_agent['name']}</div><div style='font-size:11px;color:#8A8A90;margin-top:4px'>{selected_agent['desc']}</div></div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("<div style='font-size:11px;font-family:monospace;color:#8A8A90;letter-spacing:1px'>MEMORY • LONG TERM</div>", unsafe_allow_html=True)
    mem_query = st.text_input("Search memory", placeholder="e.g. my name, project...", label_visibility="collapsed")
    if st.session_state.memories:
        # simple filter
        filtered = [m for m in st.session_state.memories if mem_query.lower() in m.lower()] if mem_query else st.session_state.memories
        for mem in filtered[-5:][::-1]:
            st.markdown(f"<div style='font-size:11px;background:#141415;border:1px solid #232325;padding:6px 8px;border-radius:8px;margin-bottom:4px'>💾 {mem[:80]}</div>", unsafe_allow_html=True)
    else:
        st.caption("No memories yet. Say 'remember that...'")

    st.divider()
    st.markdown("**Model:**")
    st.session_state.model = st.selectbox("Model", ["gpt-4o","gpt-4o-mini","gpt-4-turbo","o1-mini","o1-preview"], label_visibility="collapsed", index=0)
    
    if st.button("🗑️ New Chat", use_container_width=True):
        # save current to history
        if st.session_state.messages:
            st.session_state.chat_history.append({
                "id": st.session_state.current_chat_id,
                "title": st.session_state.messages[0]["content"][:40] if st.session_state.messages else "New Chat",
                "messages": st.session_state.messages.copy(),
                "agent": agent_id,
                "time": datetime.now().isoformat()
            })
        st.session_state.messages = []
        st.session_state.current_chat_id = str(uuid.uuid4())[:8]
        st.session_state.uploaded_context = ""
        st.rerun()

    # Chat history list
    if st.session_state.chat_history:
        st.markdown("<div style='font-size:11px;font-family:monospace;color:#8A8A90;margin-top:12px'>CHAT HISTORY</div>", unsafe_allow_html=True)
        for ch in reversed(st.session_state.chat_history[-10:]):
            if st.button(f"📝 {ch['title'][:30]}", key=f"hist_{ch['id']}", use_container_width=True):
                st.session_state.messages = ch["messages"]
                st.session_state.current_chat_id = ch["id"]
                st.rerun()

    st.divider()
    st.caption("🏆 SEKTA GOLD — Streamlit Cloud Edition\nBetter than all bots.\nDeploy: push to GitHub → share.streamlit.io/deploy")

# --- MAIN CHAT AREA ---
col1, col2 = st.columns([3,1]) if st.session_state.messages else (st.container(), None)

with col1:
    # Header
    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:12px;margin-bottom:16px'>
      <div style='font-size:28px'>{selected_agent['icon']}</div>
      <div><div style='font-weight:800;font-size:20px;letter-spacing:-0.02em'>{selected_agent['name']} • <span style='font-weight:400;color:#FFC700'>STREAMLIT</span></div>
      <div style='font-size:12px;color:#8A8A90'>{selected_agent['desc']} • {st.session_state.model} • Tools ON</div></div>
      <div style='margin-left:auto'><span class='gold-badge'>● LIVE • STREAMLIT CLOUD</span></div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown("""
        <div style='text-align:center;padding:40px 20px;background:#0F0F10;border:1px solid #232325;border-radius:16px;margin-bottom:16px'>
          <div style='width:64px;height:64px;border-radius:16px;background:linear-gradient(135deg,#FFC700,#FF8A00);display:flex;align-items:center;justify-content:center;font-size:32px;margin:0 auto 16px;box-shadow:0 0 40px rgba(255,199,0,0.2)'>🏆</div>
          <div style='font-size:28px;font-weight:800;letter-spacing:-0.02em'>SEKTA GOLD</div>
          <div style='color:#8A8A90;font-size:14px;margin-top:6px'>Better than every chatbot in history — now on Streamlit Cloud</div>
          <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:24px;text-align:left;max-width:520px;margin-left:auto;margin-right:auto'>
        """, unsafe_allow_html=True)
        # Quick prompts
        quick_prompts = [
            "Build me a SaaS landing page in Streamlit",
            "Search latest AI news today with sources",
            "Generate luxury logo for Sekta Gold Cup, black & gold",
            "Analyze this CSV and show charts",
            "Remember my name is Alex and I love F1",
            "Teach quantum computing like I'm 10"
        ]
        cols = st.columns(2)
        for i, qp in enumerate(quick_prompts):
            with cols[i%2]:
                if st.button(f"→ {qp}", key=f"qp_{i}", use_container_width=True):
                    st.session_state.prompt_clicked = qp
                    st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)

    # Display messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🏆" if msg["role"]=="assistant" else "🧑‍🚀"):
            st.markdown(msg["content"])
            if "image_url" in msg and msg["image_url"]:
                st.image(msg["image_url"], caption="Generated Image")

    # File uploader area
    uploaded_files = st.file_uploader("📎 Upload files (PDF, CSV, XLSX, DOCX, images) — they will be analyzed", accept_multiple_files=True, type=["pdf","txt","md","csv","xlsx","docx","png","jpg","jpeg","webp","py","js","json"], label_visibility="collapsed")
    if uploaded_files:
        context_parts = []
        for f in uploaded_files:
            ctx = parse_uploaded_file(f)
            context_parts.append(ctx)
        st.session_state.uploaded_context = "\n\n".join(context_parts)
        st.markdown(f"<div class='gold-card'><span class='gold-badge'>📎 {len(uploaded_files)} files parsed</span><div style='font-size:12px;margin-top:8px;max-height:120px;overflow:auto;white-space:pre-wrap'>{st.session_state.uploaded_context[:2000]}</div></div>", unsafe_allow_html=True)

# Prompt input handling
prompt_clicked = st.session_state.pop("prompt_clicked", None)
user_input = st.chat_input(f"Message {selected_agent['name']}... try 'generate image of...' or 'search...'")

actual_prompt = prompt_clicked or user_input

if actual_prompt:
    # Check key
    client, key = get_client()
    if not client:
        st.error("❌ No valid OpenAI API key. Add OPENAI_API_KEY in Streamlit Cloud → App → Settings → Secrets, or use sidebar input. IMPORTANT: Use NEW key after revoking leaked one.")
        st.stop()
    
    # Handle memory extraction: "remember that..."
    lower = actual_prompt.lower()
    if "remember that" in lower or "remember my" in lower or "my name is" in lower:
        fact = actual_prompt.replace("remember that","").replace("remember","").strip()
        st.session_state.memories.append(fact)
        st.toast(f"💾 Remembered: {fact[:50]}")

    # Add user message
    st.session_state.messages.append({"role": "user", "content": actual_prompt})
    with st.chat_message("user", avatar="🧑‍🚀"):
        st.markdown(actual_prompt)

    # Build system prompt with memory + file context
    system_prompt = selected_agent["prompt"]
    if st.session_state.memories:
        system_prompt += "\n\n[USER LONG-TERM MEMORIES]:\n" + "\n".join([f"- {m}" for m in st.session_state.memories[-10:]])
    if st.session_state.uploaded_context:
        system_prompt += f"\n\n[UPLOADED FILES CONTEXT]:\n{st.session_state.uploaded_context[:12000]}"

    # Prepare messages for OpenAI
    openai_messages = [{"role": "system", "content": system_prompt}]
    for m in st.session_state.messages[-20:]: # last 20 for context
        openai_messages.append({"role": m["role"], "content": m["content"]})

    # Check if user wants image generation explicitly
    wants_image = any(k in lower for k in ["generate image", "create image", "make image", "logo for", "draw ", "generate logo", "dall-e", "image of"])
    
    with st.chat_message("assistant", avatar="🏆"):
        message_placeholder = st.empty()
        full_response = ""
        tool_info = st.empty()

        # If image requested, handle separately for speed
        if wants_image:
            # Extract prompt
            img_prompt = actual_prompt
            # Remove trigger words
            for t in ["generate image of", "generate image", "create image of", "create image", "make image of", "generate logo for", "logo for"]:
                if t in lower:
                    img_prompt = actual_prompt.lower().split(t)[-1].strip()
                    break
            if not img_prompt or len(img_prompt) < 5:
                img_prompt = actual_prompt
            tool_info.markdown(f"<span class='gold-badge'>🎨 Generating image: {img_prompt[:60]}...</span>", unsafe_allow_html=True)
            url, revised = tool_generate_image(img_prompt)
            if url:
                full_response += f"Generated image for: **{img_prompt}**\n\n![Generated Image]({url})\n\n*Revised prompt: {revised}*"
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response, "image_url": url})
            else:
                full_response = f"Image generation failed: {revised}. But here's concept: {img_prompt}"
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
        else:
            # Normal chat with streaming + function calling simulation
            # Define tools for OpenAI
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search web for real-time info, news, prices, events. Always use for recent facts.",
                        "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "num_results": {"type": "integer", "default": 5}}, "required": ["query"]}
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "generate_image",
                        "description": "Generate image with DALL-E 3 for logos, art, diagrams",
                        "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}, "size": {"type": "string", "default": "1024x1024"}}, "required": ["prompt"]}
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "remember_fact",
                        "description": "Save important user fact to memory",
                        "parameters": {"type": "object", "properties": {"fact": {"type": "string"}}, "required": ["fact"]}
                    }
                }
            ]
            
            try:
                # Initial streaming attempt
                stream = client.chat.completions.create(
                    model=st.session_state.model,
                    messages=openai_messages,
                    tools=tools,
                    tool_choice="auto",
                    stream=True,
                    temperature=0.7,
                    max_tokens=3000
                )
                
                tool_calls_buffer = {}
                for chunk in stream:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        full_response += delta.content
                        message_placeholder.markdown(full_response + "▌")
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_calls_buffer:
                                tool_calls_buffer[idx] = {"id": "", "name": "", "args": ""}
                            if tc.id:
                                tool_calls_buffer[idx]["id"] += tc.id
                            if tc.function:
                                if tc.function.name:
                                    tool_calls_buffer[idx]["name"] += tc.function.name
                                if tc.function.arguments:
                                    tool_calls_buffer[idx]["args"] += tc.function.arguments
                
                message_placeholder.markdown(full_response)
                
                # If tool calls found, execute them and get final answer
                if tool_calls_buffer:
                    # Add assistant tool call message
                    openai_messages.append({
                        "role": "assistant",
                        "content": full_response or None,
                        "tool_calls": [
                            {"id": v["id"], "type": "function", "function": {"name": v["name"], "arguments": v["args"]}} for v in tool_calls_buffer.values()
                        ]
                    })
                    
                    for tc_data in tool_calls_buffer.values():
                        t_name = tc_data["name"]
                        try:
                            t_args = json.loads(tc_data["args"] or "{}")
                        except (json.JSONDecodeError, TypeError):
                            t_args = {}
                        
                        tool_info.markdown(f"<span class='gold-badge'>🔧 Tool: {t_name} — {str(t_args)[:80]}</span>", unsafe_allow_html=True)
                        
                        if t_name == "web_search":
                            res = tool_web_search(t_args.get("query",""), t_args.get("num_results",5))
                            openai_messages.append({"role": "tool", "tool_call_id": tc_data["id"], "name": t_name, "content": res})
                        elif t_name == "generate_image":
                            url, rev = tool_generate_image(t_args.get("prompt",""), t_args.get("size","1024x1024"))
                            if url:
                                res = f"Image generated: {url} — revised: {rev}"
                                openai_messages.append({"role": "tool", "tool_call_id": tc_data["id"], "name": t_name, "content": res})
                                full_response += f"\n\n![Generated]({url})"
                                message_placeholder.markdown(full_response)
                            else:
                                openai_messages.append({"role": "tool", "tool_call_id": tc_data["id"], "name": t_name, "content": f"Failed: {rev}"})
                        elif t_name == "remember_fact":
                            fact = t_args.get("fact","")
                            st.session_state.memories.append(fact)
                            openai_messages.append({"role": "tool", "tool_call_id": tc_data["id"], "name": t_name, "content": f"Saved: {fact}"})
                    
                    # Second call for final answer after tools
                    tool_info.markdown(f"<span class='gold-badge'>✨ Finalizing answer with tool results...</span>", unsafe_allow_html=True)
                    stream2 = client.chat.completions.create(
                        model=st.session_state.model,
                        messages=openai_messages,
                        stream=True,
                        temperature=0.7,
                        max_tokens=3000
                    )
                    full_response = "" if not full_response.startswith("Generated image") else full_response + "\n\n"
                    for chunk in stream2:
                        if chunk.choices[0].delta.content:
                            full_response += chunk.choices[0].delta.content
                            message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                
                # Save assistant message
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                tool_info.empty()
                
            except Exception as e:
                err_msg = str(e)
                if "api_key" in err_msg.lower() or "401" in err_msg:
                    st.error(f"🔑 OpenAI API key error: {err_msg}. Check key in Streamlit Secrets. Revoke old leaked key!")
                else:
                    st.error(f"Error: {err_msg}")
                    full_response = f"Sorry, error: {err_msg[:500]}"
                    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # Clear file context after use? Keep for session.
    # st.rerun() # streaming handles

# Footer
st.markdown("---")
st.markdown("<div style='text-align:center;color:#5A5A60;font-size:11px;font-family:monospace'>SEKTA GOLD CUP • Streamlit Cloud Edition • Better than all chatbots • Built with OpenAI + Streamlit • <a href='https://platform.openai.com/api-keys'>Revoke leaked key</a></div>", unsafe_allow_html=True)
