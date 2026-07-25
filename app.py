"""
SEKTA GOLD CUP — Streamlit Cloud Edition
Production-ready AI chatbot with multiple free providers.
"""

import streamlit as st
import os
import json
import base64
import time
import uuid
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Sekta AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
.stApp { background: #09090b; color: #e4e4e7; }

/* Sidebar */
[data-testid="stSidebar"] { background: #09090b; border-right: 1px solid #27272a; }
[data-testid="stSidebar"] [data-testid="stMarkdown"] { color: #a1a1aa; }

/* Header bar */
[data-testid="stHeader"] { background: rgba(9,9,11,0.85); backdrop-filter: blur(12px); }

/* Chat messages */
.stChatMessage { border-radius: 16px !important; }
div[data-testid="stChatMessage"]:nth-child(odd) { background: #18181b; border: 1px solid #27272a; }
div[data-testid="stChatMessage"]:nth-child(even) { background: #0f0f12; border: 1px solid #1e1e22; }
div[data-testid="stChatMessageAvatarUser"] { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; }
div[data-testid="stChatMessageAvatarAssistant"] { background: linear-gradient(135deg, #f59e0b, #f97316) !important; }

/* Input */
[data-testid="stChatInput"] { background: #18181b; border: 1px solid #27272a; border-radius: 16px; }
[data-testid="stChatInput"] textarea { color: #e4e4e7; }
[data-testid="stChatInput"] textarea::placeholder { color: #52525b; }

/* Buttons */
.stButton > button { border-radius: 10px; font-weight: 500; transition: all 0.2s; }
.stButton > button:hover { transform: translateY(-1px); }

/* Cards */
.card { background: #18181b; border: 1px solid #27272a; border-radius: 12px; padding: 16px; }
.card-highlight { background: rgba(245,158,11,0.06); border: 1px solid rgba(245,158,11,0.2); border-radius: 12px; padding: 16px; }
.badge { display: inline-block; background: #27272a; color: #a1a1aa; padding: 3px 10px; border-radius: 100px; font-size: 11px; font-weight: 500; font-family: 'JetBrains Mono'; }
.badge-gold { background: rgba(245,158,11,0.1); color: #f59e0b; border: 1px solid rgba(245,158,11,0.2); }
.badge-green { background: rgba(34,197,94,0.1); color: #22c55e; border: 1px solid rgba(34,197,94,0.2); }
.badge-purple { background: rgba(139,92,246,0.1); color: #a78bfa; border: 1px solid rgba(139,92,246,0.2); }

/* Quick prompts */
.prompt-card { background: #18181b; border: 1px solid #27272a; border-radius: 12px; padding: 14px 16px; cursor: pointer; transition: all 0.2s; }
.prompt-card:hover { border-color: #3f3f46; background: #1e1e22; }

/* Misc */
a { color: #f59e0b !important; }
div[data-testid="stSelectbox"] { background: #18181b; border-radius: 10px; }
div[data-testid="stExpander"] { background: #18181b; border: 1px solid #27272a; border-radius: 12px; }

/* Hide Streamlit branding */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stStatusWidget"] { display: none; }
</style>
""", unsafe_allow_html=True)

# --- PROVIDERS ---
PROVIDERS = {
    "Groq (Free)": {
        "icon": "⚡",
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        "default_model": "llama-3.3-70b-versatile",
        "signup": "console.groq.com",
        "env_key": "GROQ_API_KEY",
        "features": ["Chat", "Fast"],
    },
    "Gemini (Free)": {
        "icon": "💎",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash"],
        "default_model": "gemini-2.0-flash",
        "signup": "aistudio.google.com/apikey",
        "env_key": "GEMINI_API_KEY",
        "features": ["Chat", "Vision"],
    },
    "OpenAI (Paid)": {
        "icon": "🧠",
        "base_url": None,
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "default_model": "gpt-4o",
        "signup": "platform.openai.com",
        "env_key": "OPENAI_API_KEY",
        "features": ["Chat", "Tools", "Vision", "Image Gen"],
    },
}

# --- AGENTS ---
AGENTS = {
    "sekta-omni": {
        "name": "Sekta Omni", "icon": "✦", "color": "#f59e0b",
        "desc": "All-purpose assistant",
        "prompt": "You are Sekta AI — a helpful, concise, and capable AI assistant. Use markdown formatting. Be direct and thorough. Current date: 2026-07-25.",
    },
    "code-titan": {
        "name": "Code Titan", "icon": "💻", "color": "#6366f1",
        "desc": "Senior engineer — builds apps",
        "prompt": "You are Code Titan — a Staff Engineer. Write production-ready code with error handling. Build full features, not tutorials. Include file structure and setup instructions.",
    },
    "research-oracle": {
        "name": "Research Oracle", "icon": "🔍", "color": "#10b981",
        "desc": "Deep research with sources",
        "prompt": "You are Research Oracle — a precise researcher. Structure: TL;DR → Key Findings → Deep Dive. Cite sources with [1](url). Distinguish fact from opinion.",
    },
    "creative-god": {
        "name": "Creative God", "icon": "🎨", "color": "#ec4899",
        "desc": "Content & creative director",
        "prompt": "You are Creative God — an award-winning creative director. Give 3 variations: Safe, Bold, Unhinged. Make everything memorable and shareable.",
    },
    "data-wizard": {
        "name": "Data Wizard", "icon": "📊", "color": "#8b5cf6",
        "desc": "Data analysis & charts",
        "prompt": "You are Data Wizard — a data scientist. When given data, do EDA: shape, columns, missing values, stats, insights. Write pandas code. Give actionable recommendations.",
    },
    "study-buddy": {
        "name": "Study Buddy", "icon": "📚", "color": "#06b6d4",
        "desc": "Feynman-style tutor",
        "prompt": "You are Study Buddy — the best tutor. Teach via Analogy → Simple Explanation → Example → Quiz. Adapt to user level. Make learning addictive.",
    },
    "business-shark": {
        "name": "Business Shark", "icon": "🦈", "color": "#f97316",
        "desc": "Startup & growth strategist",
        "prompt": "You are Business Shark — built 3 unicorns. Evaluate ideas via Pain/Market/Moat/Money. Be brutally honest. Give actionable advice with metrics.",
    },
    "therapist-v2": {
        "name": "Therapist V2", "icon": "💛", "color": "#eab308",
        "desc": "Supportive listener",
        "prompt": "You are Therapist V2 — warm, empathetic, non-judgmental. Validate feelings, ask open questions, use CBT tools. If self-harm mentioned, provide crisis resources (US 988). You are an AI, not a professional.",
    },
}

# --- HELPERS ---
def get_key(env_key):
    key = None
    try:
        key = st.secrets[env_key]
    except Exception:
        pass
    if not key:
        key = os.getenv(env_key, "")
    if not key:
        key = st.session_state.get("manual_key", "")
    return key

def get_client():
    prov = PROVIDERS[st.session_state.get("provider", "Groq (Free)")]
    key = get_key(prov["env_key"])
    if not key:
        return None, None
    from openai import OpenAI
    if prov["base_url"]:
        return OpenAI(api_key=key, base_url=prov["base_url"]), key
    return OpenAI(api_key=key), key

def get_tavily_key():
    try:
        return st.secrets["TAVILY_API_KEY"]
    except Exception:
        return os.getenv("TAVILY_API_KEY", "")

def web_search(query, num=5):
    key = get_tavily_key()
    if key:
        try:
            from tavily import TavilyClient
            res = TavilyClient(api_key=key).search(query, search_depth="advanced", max_results=num)
            out = ""
            for i, r in enumerate(res.get("results", [])[:num]):
                out += f"[{i+1}] {r.get('title')} — {r.get('url')}\n{r.get('content','')[:500]}\n\n"
            return out or "No results found."
        except Exception as e:
            return f"Search error: {e}"
    try:
        import httpx
        with httpx.Client(timeout=10) as c:
            data = c.get(f"https://api.duckduckgo.com/?q={query}&format=json").json()
            if data.get("AbstractText"):
                return f"{data['AbstractText']} — {data.get('AbstractURL','')}"
    except Exception:
        pass
    return "No search available. Add TAVILY_API_KEY for web search."

def gen_image(prompt, size="1024x1024"):
    key = get_key("OPENAI_API_KEY")
    if not key:
        return None, "Requires OpenAI API key for DALL-E image generation."
    try:
        from openai import OpenAI
        res = OpenAI(api_key=key).images.generate(model="dall-e-3", prompt=prompt, size=size, quality="hd", n=1)
        return res.data[0].url, getattr(res.data[0], "revised_prompt", prompt)
    except Exception as e:
        return None, str(e)

def parse_file(f):
    name = f.name
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    try:
        if ext == "pdf":
            from PyPDF2 import PdfReader
            return "".join((p.extract_text() or "") for p in PdfReader(f).pages[:20])[:15000]
        elif ext in ("xlsx", "xls"):
            import pandas as pd
            df = pd.read_excel(f)
            return f"Shape: {df.shape}\nColumns: {list(df.columns)}\n\n{df.head(20).to_string()}"
        elif ext == "docx":
            from docx import Document
            return "\n".join(p.text for p in Document(f).paragraphs)[:15000]
        elif ext in ("png", "jpg", "jpeg", "webp"):
            return "[IMAGE — describe what you see]"
        else:
            return f.read().decode("utf-8", errors="ignore")[:15000]
    except Exception as e:
        return f"Error reading {name}: {e}"

# --- SESSION STATE ---
for k, v in {
    "messages": [], "chat_history": [], "chat_id": str(uuid.uuid4())[:8],
    "file_ctx": "", "memories": [], "model": "llama-3.3-70b-versatile",
    "provider": "Groq (Free)", "agent": "sekta-omni", "manual_key": "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- SIDEBAR ---
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:24px;padding:4px 0">
        <div style="width:40px;height:40px;border-radius:12px;background:linear-gradient(135deg,#f59e0b,#f97316);display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:800;color:#000">S</div>
        <div>
            <div style="font-size:18px;font-weight:700;letter-spacing:-0.03em;color:#fafafa">Sekta AI</div>
            <div style="font-size:11px;color:#52525b;font-family:'JetBrains Mono';margin-top:-2px">v2.0 · Cloud</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Provider
    st.markdown("<div style='font-size:11px;font-weight:600;color:#52525b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px'>Provider</div>", unsafe_allow_html=True)
    prov_names = list(PROVIDERS.keys())
    prov = st.radio("Provider", prov_names, label_visibility="collapsed",
        format_func=lambda x: f"{PROVIDERS[x]['icon']}  {x}",
        index=prov_names.index(st.session_state.provider),
        key="prov_radio")
    st.session_state.provider = prov
    p = PROVIDERS[prov]

    # Key status
    key = get_key(p["env_key"])
    if not key:
        st.markdown(f"<div class='card' style='margin:12px 0'><div style='font-size:12px;color:#f59e0b;font-weight:600;margin-bottom:6px'>🔑 API Key Required</div><div style='font-size:11px;color:#71717a'>Get free key at <b>{p['signup']}</b></div></div>", unsafe_allow_html=True)
        manual = st.text_input("API Key", type="password", placeholder="Paste your key here...", label_visibility="collapsed")
        if manual:
            st.session_state.manual_key = manual
            st.rerun()
    else:
        masked = f"{key[:6]}…{key[-4:]}"
        st.markdown(f"<div style='font-size:11px;color:#22c55e;margin:8px 0'>✓ Connected · <code style='color:#52525b;background:#1e1e22;padding:2px 6px;border-radius:4px'>{masked}</code></div>", unsafe_allow_html=True)

    st.markdown(f"<div style='font-size:10px;color:#3f3f46;margin:4px 0'>Models: {', '.join(p['models'][:2])}…</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1px;background:#27272a;margin:16px 0'></div>", unsafe_allow_html=True)

    # Agent
    st.markdown("<div style='font-size:11px;font-weight:600;color:#52525b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px'>Agent</div>", unsafe_allow_html=True)
    agent_options = list(AGENTS.keys())
    agent_idx = agent_options.index(st.session_state.agent) if st.session_state.agent in agent_options else 0
    agent = st.selectbox("Agent", agent_options, index=agent_idx, label_visibility="collapsed",
        format_func=lambda x: f"{AGENTS[x]['icon']}  {AGENTS[x]['name']}")
    st.session_state.agent = agent
    a = AGENTS[agent]
    st.markdown(f"<div class='card'><div style='font-weight:600;font-size:13px;color:#fafafa'>{a['icon']} {a['name']}</div><div style='font-size:12px;color:#71717a;margin-top:4px'>{a['desc']}</div></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1px;background:#27272a;margin:16px 0'></div>", unsafe_allow_html=True)

    # Model
    st.markdown("<div style='font-size:11px;font-weight:600;color:#52525b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px'>Model</div>", unsafe_allow_html=True)
    model_list = p["models"]
    default_m = p["default_model"]
    m_idx = model_list.index(default_m) if default_m in model_list else 0
    st.session_state.model = st.selectbox("Model", model_list, index=m_idx, label_visibility="collapsed")

    st.markdown("<div style='height:1px;background:#27272a;margin:16px 0'></div>", unsafe_allow_html=True)

    # Memory
    st.markdown("<div style='font-size:11px;font-weight:600;color:#52525b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px'>Memory</div>", unsafe_allow_html=True)
    if st.session_state.memories:
        for m in st.session_state.memories[-5:][::-1]:
            st.markdown(f"<div style='font-size:11px;color:#a1a1aa;padding:6px 0;border-bottom:1px solid #1e1e22'>💾 {m[:60]}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-size:11px;color:#3f3f46;padding:8px 0'>Say \"remember that…\" to save facts</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1px;background:#27272a;margin:16px 0'></div>", unsafe_allow_html=True)

    # New chat
    if st.button("✦  New Chat", use_container_width=True, type="primary"):
        if st.session_state.messages:
            st.session_state.chat_history.append({
                "id": st.session_state.chat_id,
                "title": st.session_state.messages[0]["content"][:40] if st.session_state.messages else "Chat",
                "messages": st.session_state.messages.copy(),
                "agent": agent,
                "time": datetime.now().isoformat(),
            })
        st.session_state.messages = []
        st.session_state.chat_id = str(uuid.uuid4())[:8]
        st.session_state.file_ctx = ""
        st.rerun()

    # History
    if st.session_state.chat_history:
        st.markdown("<div style='font-size:11px;font-weight:600;color:#52525b;text-transform:uppercase;letter-spacing:0.08em;margin:16px 0 8px'>History</div>", unsafe_allow_html=True)
        for ch in st.session_state.chat_history[-8:][::-1]:
            if st.button(f"{'📝'} {ch['title'][:28]}", key=f"h_{ch['id']}", use_container_width=True):
                st.session_state.messages = ch["messages"]
                st.session_state.chat_id = ch["id"]
                st.rerun()

# --- MAIN AREA ---
# Header
a = AGENTS[st.session_state.agent]
st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;padding:8px 0">
    <div style="width:36px;height:36px;border-radius:10px;background:{a['color']}15;border:1px solid {a['color']}30;display:flex;align-items:center;justify-content:center;font-size:18px">{a['icon']}</div>
    <div>
        <div style="font-size:15px;font-weight:600;color:#fafafa">{a['name']}</div>
        <div style="font-size:11px;color:#52525b">{st.session_state.model} · {st.session_state.provider.split(' (')[0]}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Quick prompts (when empty)
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px 40px">
        <div style="width:64px;height:64px;border-radius:20px;background:linear-gradient(135deg,#f59e0b,#f97316);display:flex;align-items:center;justify-content:center;font-size:28px;margin:0 auto 20px;box-shadow:0 8px 32px rgba(245,158,11,0.2)">✦</div>
        <h1 style="font-size:32px;font-weight:800;letter-spacing:-0.04em;color:#fafafa;margin:0">What can I help with?</h1>
        <p style="color:#52525b;font-size:14px;margin-top:8px">Choose an agent and start chatting</p>
    </div>
    """, unsafe_allow_html=True)

    prompts = [
        ("💡", "Explain quantum computing", "like I'm 10"),
        ("🔍", "Latest AI news today", "with sources"),
        ("💻", "Build a Python REST API", "with FastAPI"),
        ("📊", "Analyze this data", "upload CSV below"),
        ("🎨", "Write viral tweets", "about startups"),
        ("🦈", "Evaluate my startup idea", "be brutally honest"),
    ]
    cols = st.columns(3)
    for i, (icon, main, sub) in enumerate(prompts):
        with cols[i % 3]:
            if st.button(f"{icon}  {main}", key=f"p_{i}", use_container_width=True):
                st.session_state["_prompt_clicked"] = f"{main} {sub}"
                st.rerun()

# Display messages
for msg in st.session_state.messages:
    avatar = a["icon"] if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg.get("image_url"):
            st.image(msg["image_url"])

# File uploader
uploaded = st.file_uploader("📎 Attach files", type=["pdf","txt","md","csv","xlsx","docx","png","jpg","jpeg","py","js","json"],
    label_visibility="collapsed", accept_multiple_files=True)
if uploaded:
    ctx_parts = []
    for f in uploaded:
        ctx_parts.append(f"### {f.name}\n{parse_file(f)}")
    st.session_state.file_ctx = "\n\n".join(ctx_parts)
    st.success(f"📎 {len(uploaded)} file(s) attached — ask me anything about them!")

# Chat input
prompt = st.session_state.pop("_prompt_clicked", None) or st.chat_input(f"Message {a['name']}…")

if prompt:
    # Memory extraction
    low = prompt.lower()
    if any(k in low for k in ["remember that", "remember my", "my name is", "i like", "i work at"]):
        st.session_state.memories.append(prompt.replace("remember that", "").replace("remember", "").strip())

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Build context
    system = a["prompt"]
    if st.session_state.memories:
        system += "\n\n[User memories]:\n" + "\n".join(f"- {m}" for m in st.session_state.memories[-10:])
    if st.session_state.file_ctx:
        system += f"\n\n[Attached files]:\n{st.session_state.file_ctx[:12000]}"

    msgs = [{"role": "system", "content": system}]
    for m in st.session_state.messages[-20:]:
        msgs.append({"role": m["role"], "content": m["content"]})

    client, _ = get_client()
    if not client:
        st.error(f"🔑 No API key for **{st.session_state.provider}**. Add your key in the sidebar.")
        st.stop()

    with st.chat_message("assistant", avatar=a["icon"]):
        placeholder = st.empty()
        full = ""
        try:
            stream = client.chat.completions.create(
                model=st.session_state.model,
                messages=msgs,
                stream=True,
                temperature=0.7,
                max_tokens=4000,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full += chunk.choices[0].delta.content
                    placeholder.markdown(full + "▌")
            placeholder.markdown(full)
            st.session_state.messages.append({"role": "assistant", "content": full})
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower():
                st.error("⚠️ Rate limit or quota exceeded. Try switching provider or adding credits.")
            elif "401" in err or "api_key" in err.lower():
                st.error("🔑 Invalid API key. Check your key in the sidebar.")
            else:
                st.error(f"Error: {err[:300]}")
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ Error: {err[:200]}"})

# Footer
st.markdown("<div style='height:1px;background:#1e1e22;margin-top:32px'></div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;padding:16px 0;font-size:11px;color:#3f3f46;font-family:JetBrains Mono,monospace'>Sekta AI · Built with Streamlit · <a href='https://github.com/goldstarpalms-svg/Sekta-gold-cup' style='color:#52525b'>GitHub</a></div>", unsafe_allow_html=True)
