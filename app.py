"""
SEKTA GOLD CUP — Production AI Platform
Free tools: Web Search, Image Gen, Code Interpreter, URL Reader,
Wikipedia, Charts, QR Codes, File Analysis, Voice
"""

import streamlit as st
import os, json, base64, time, uuid, re, io, sys, traceback, subprocess, tempfile
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Sekta AI", page_icon="⭐", layout="wide", initial_sidebar_state="expanded")

# --- CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
.stApp { background: #09090b; color: #e4e4e7; }
[data-testid="stSidebar"] { background: #09090b; border-right: 1px solid #27272a; }
[data-testid="stHeader"] { background: rgba(9,9,11,0.85); backdrop-filter: blur(12px); }
.stChatMessage { border-radius: 16px !important; }
div[data-testid="stChatMessage"]:nth-child(odd) { background: #18181b; border: 1px solid #27272a; }
div[data-testid="stChatMessage"]:nth-child(even) { background: #0f0f12; border: 1px solid #1e1e22; }
div[data-testid="stChatMessageAvatarUser"] { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; }
div[data-testid="stChatMessageAvatarAssistant"] { background: linear-gradient(135deg, #f59e0b, #f97316) !important; }
[data-testid="stChatInput"] { background: #18181b; border: 1px solid #27272a; border-radius: 16px; }
[data-testid="stChatInput"] textarea { color: #e4e4e7; }
[data-testid="stChatInput"] textarea::placeholder { color: #52525b; }
.stButton > button { border-radius: 10px; font-weight: 500; transition: all 0.2s; }
.stButton > button:hover { transform: translateY(-1px); }
.card { background: #18181b; border: 1px solid #27272a; border-radius: 12px; padding: 16px; }
a { color: #f59e0b !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stStatusWidget"] { display: none; }
.tool-bar { display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 0; }
.tool-chip { background: #18181b; border: 1px solid #27272a; border-radius: 10px; padding: 8px 14px; font-size: 12px; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 6px; }
.tool-chip:hover { border-color: #3f3f46; background: #1e1e22; }
.tool-chip .icon { font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# --- PROVIDERS ---
PROVIDERS = {
    "Groq (Free)": {"icon": "⚡", "base_url": "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        "default_model": "llama-3.3-70b-versatile", "signup": "console.groq.com", "env_key": "GROQ_API_KEY"},
    "Gemini (Free)": {"icon": "💎", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash"],
        "default_model": "gemini-2.0-flash", "signup": "aistudio.google.com/apikey", "env_key": "GEMINI_API_KEY"},
    "OpenAI (Paid)": {"icon": "🧠", "base_url": None,
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "default_model": "gpt-4o", "signup": "platform.openai.com", "env_key": "OPENAI_API_KEY"},
}

# --- AGENTS ---
AGENTS = {
    "sekta-omni": {"name": "Sekta Omni", "icon": "⭐", "color": "#f59e0b",
        "desc": "All-purpose assistant with tools",
        "prompt": "You are Sekta AI — a helpful, concise assistant. You have access to web search, image generation, code execution, Wikipedia, URL reading, and file analysis. When the user asks you to do something, USE your tools proactively. Be direct. Current date: 2026-07-25."},
    "code-titan": {"name": "Code Titan", "icon": "💻", "color": "#6366f1",
        "desc": "Engineer — writes & runs code",
        "prompt": "You are Code Titan — a Staff Engineer. Write production code. When asked to code, write it AND use the code runner to execute and test it. Show output. Fix bugs iteratively."},
    "research-oracle": {"name": "Research Oracle", "icon": "🔍", "color": "#10b981",
        "desc": "Deep research with sources",
        "prompt": "You are Research Oracle. For ANY factual question, use web search and Wikipedia. Cite sources [1](url). Structure: TL;DR → Key Findings → Deep Dive."},
    "creative-god": {"name": "Creative God", "icon": "🎨", "color": "#ec4899",
        "desc": "Content & visuals creator",
        "prompt": "You are Creative God — award-winning creative director. For images, use the image generator with detailed prompts. Give 3 variations: Safe, Bold, Unhinged."},
    "data-wizard": {"name": "Data Wizard", "icon": "📊", "color": "#8b5cf6",
        "desc": "Data analysis & charts",
        "prompt": "You are Data Wizard. When given data, generate Python code and run it. Create charts with matplotlib/plotly. Show insights, not just numbers."},
    "study-buddy": {"name": "Study Buddy", "icon": "📚", "color": "#06b6d4",
        "desc": "Feynman-style tutor",
        "prompt": "You are Study Buddy. Teach via Analogy → Simple → Example → Quiz. Use web search for facts. Make learning addictive."},
    "business-shark": {"name": "Business Shark", "icon": "🦈", "color": "#f97316",
        "desc": "Startup strategist",
        "prompt": "You are Business Shark. Evaluate ideas via Pain/Market/Moat/Money. Search for real market data. Be brutally honest with metrics."},
    "therapist-v2": {"name": "Therapist", "icon": "💛", "color": "#eab308",
        "desc": "Supportive listener",
        "prompt": "You are Therapist — warm, empathetic, non-judgmental. Validate feelings. If crisis, provide resources (US 988). AI disclaimer."},
}

# =====================================================================
# TOOLS — All free, no API keys required
# =====================================================================

def get_key(env_key):
    key = None
    try: key = st.secrets[env_key]
    except Exception: pass
    if not key: key = os.getenv(env_key, "")
    if not key: key = st.session_state.get("manual_key", "")
    return key

def get_client():
    prov = PROVIDERS[st.session_state.get("provider", "Groq (Free)")]
    key = get_key(prov["env_key"])
    if not key: return None
    from openai import OpenAI
    if prov["base_url"]:
        return OpenAI(api_key=key, base_url=prov["base_url"])
    return OpenAI(api_key=key)

def get_tavily_key():
    try: return st.secrets["TAVILY_API_KEY"]
    except Exception: return os.getenv("TAVILY_API_KEY", "")

# --- Tool 1: Web Search (DuckDuckGo free + Tavily optional) ---
def tool_web_search(query, num=5):
    # Try Tavily first (optional paid)
    tavily_key = get_tavily_key()
    if tavily_key:
        try:
            from tavily import TavilyClient
            res = TavilyClient(api_key=tavily_key).search(query, search_depth="advanced", max_results=num)
            out = ""
            for i, r in enumerate(res.get("results", [])[:num]):
                out += f"**[{i+1}] [{r.get('title')}]({r.get('url')})**\n{r.get('content','')[:400]}\n\n"
            if out: return out
        except Exception: pass

    # Free DuckDuckGo
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num))
            if results:
                out = f"🔍 **Web search results for:** *{query}*\n\n"
                for i, r in enumerate(results):
                    out += f"**[{i+1}] [{r.get('title','')}]({r.get('href','')})**\n{r.get('body','')[:300]}\n\n"
                return out
    except Exception as e:
        pass

    return f"No search results for '{query}'. Try adding TAVILY_API_KEY for better search."

# --- Tool 2: Image Generation (Pollinations.ai — 100% free, no key) ---
def tool_generate_image(prompt, size="1024x1024"):
    try:
        import httpx
        # Pollinations.ai — free, no API key, no signup
        encoded = prompt.replace(" ", "%20").replace("\n", "%20")
        w, h = size.split("x") if "x" in size else ("1024", "1024")
        url = f"https://image.pollinations.ai/prompt/{encoded}?width={w}&height={h}&nologo=true&seed={int(time.time())}"
        return url, prompt
    except Exception as e:
        return None, str(e)

# --- Tool 3: Code Interpreter (runs Python locally) ---
def tool_run_code(code, timeout=15):
    """Execute Python code in isolated subprocess, capture output."""
    # Safety: block dangerous operations
    blacklist = ["os.system", "subprocess.call", "subprocess.Popen", "shutil.rmtree",
                 "import socket", "open('/etc", "open('/proc", "__import__('os').system"]
    for b in blacklist:
        if b in code:
            return f"⛔ Blocked: `{b}` not allowed for safety."

    # Wrap code to capture output
    wrapped = f"""
import sys, io, math, json, random, datetime, collections, re, itertools
_old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    import pandas as pd
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
except:
    pass
try:
{chr(10).join('    ' + line for line in code.split(chr(10)))}
except Exception as e:
    import traceback
    traceback.print_exc()
output = sys.stdout.getvalue()
_old_stdout.write(output)
"""
    try:
        result = subprocess.run(
            ["python3", "-c", wrapped],
            capture_output=True, text=True, timeout=timeout,
            cwd=tempfile.mkdtemp()
        )
        out = result.stdout + result.stderr
        return out[:5000] if out.strip() else "✅ Code ran successfully (no output — use print() to see results)"
    except subprocess.TimeoutExpired:
        return f"⏱️ Code timed out after {timeout}s"
    except Exception as e:
        return f"❌ Error: {e}"

# --- Tool 4: URL Reader (fetch + extract text) ---
def tool_read_url(url):
    try:
        import httpx
        from bs4 import BeautifulSoup
        with httpx.Client(timeout=15, follow_redirects=True) as c:
            resp = c.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(resp.text, "lxml")
            # Remove scripts and styles
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            title = soup.title.string if soup.title else url
            return f"📄 **{title}**\n\n{text[:8000]}"
    except Exception as e:
        return f"❌ Could not read URL: {e}"

# --- Tool 5: Wikipedia ---
def tool_wikipedia(query):
    try:
        import wikipedia
        results = wikipedia.search(query, results=3)
        if not results:
            return f"No Wikipedia results for '{query}'"
        page = wikipedia.page(results[0], auto_suggest=False)
        summary = wikipedia.summary(results[0], sentences=5)
        return f"📖 **[{page.title}]({page.url})** (Wikipedia)\n\n{summary}\n\n*Full article: {page.url}*"
    except Exception as e:
        # Fallback to API
        try:
            import httpx
            with httpx.Client(timeout=10) as c:
                data = c.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ','_')}").json()
                if data.get("extract"):
                    return f"📖 **{data.get('title', query)}** (Wikipedia)\n\n{data['extract']}\n\n{data.get('content_urls',{}).get('desktop',{}).get('page','')}"
        except Exception: pass
        return f"No Wikipedia article found for '{query}'"

# --- Tool 6: QR Code Generator ---
def tool_qr_code(data):
    try:
        import qrcode
        img = qrcode.make(data)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        return None

# --- Tool 7: Chart Generator ---
def tool_make_chart(data_str, chart_type="bar", title="Chart"):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(8, 5))

        # Try to parse as JSON
        try:
            data = json.loads(data_str)
        except:
            data = {"data": data_str}

        if isinstance(data, dict):
            labels = list(data.keys())
            values = [float(v) if isinstance(v, (int, float)) else len(str(v)) for v in data.values()]
        else:
            return "Provide data as JSON: {\"label\": value, ...}"

        colors = ["#f59e0b", "#6366f1", "#10b981", "#ec4899", "#8b5cf6", "#06b6d4", "#f97316", "#eab308"]

        if chart_type == "bar":
            ax.bar(labels, values, color=colors[:len(labels)])
        elif chart_type == "pie":
            ax.pie(values, labels=labels, colors=colors[:len(labels)], autopct='%1.1f%%')
        elif chart_type == "line":
            ax.plot(labels, values, color="#f59e0b", marker='o', linewidth=2)

        ax.set_title(title, fontsize=14, fontweight='bold', color='#fafafa')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='#09090b')
        plt.close(fig)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/png;base64,{b64}"
    except Exception as e:
        return f"Chart error: {e}"

# --- Tool 8: File Analysis ---
def parse_file(f):
    name = f.name
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    try:
        if ext == "pdf":
            from PyPDF2 import PdfReader
            return "".join((p.extract_text() or "") for p in PdfReader(f).pages[:20])[:15000]
        elif ext in ("xlsx", "xls", "csv"):
            import pandas as pd
            df = pd.read_csv(f) if ext == "csv" else pd.read_excel(f)
            analysis = f"📊 **{name}** — {df.shape[0]} rows × {df.shape[1]} columns\n\n"
            analysis += f"**Columns:** {', '.join(df.columns.tolist())}\n\n"
            analysis += f"**Preview:**\n```\n{df.head(10).to_string()}\n```\n\n"
            analysis += f"**Stats:**\n```\n{df.describe().to_string()}\n```"
            return analysis
        elif ext == "docx":
            from docx import Document
            return "\n".join(p.text for p in Document(f).paragraphs)[:15000]
        elif ext in ("png", "jpg", "jpeg", "webp", "gif"):
            return "[IMAGE ATTACHED — describe what you see and answer questions about it]"
        else:
            return f.read().decode("utf-8", errors="ignore")[:15000]
    except Exception as e:
        return f"Error reading {name}: {e}"

# --- Tool Dispatcher (detects what user wants) ---
TOOLS_DESC = """Available tools:
- 🔍 **search** (query) — Web search via DuckDuckGo
- 🖼️ **image** (prompt) — Generate image via Pollinations AI (free)
- 💻 **code** (python) — Run Python code
- 🌐 **read_url** (url) — Read & extract any webpage
- 📖 **wiki** (query) — Wikipedia lookup
- 📊 **chart** (data, type) — Generate chart from JSON data
- 📎 **files** — Analyze uploaded files
- 🔳 **qr** (data) — Generate QR code"""

def detect_and_run_tool(user_msg, lower):
    """Check if user message triggers a tool, return (tool_name, result) or None."""
    # Web search triggers
    if any(k in lower for k in ["search for", "search the", "look up", "google", "find me", "what's the latest", "latest news", "what is happening"]):
        query = re.sub(r"(search for|search|look up|google|find me|what's the latest|latest news about|what is happening with)\s*", "", lower).strip()
        if query and len(query) > 2:
            return "🔍 Web Search", tool_web_search(query)

    # Wikipedia triggers
    if any(k in lower for k in ["wikipedia", "who is", "who was", "what is a ", "what are ", "define ", "tell me about"]):
        query = re.sub(r"(wikipedia|who is|who was|what is a|what are|define|tell me about)\s*", "", lower).strip()
        if query and len(query) > 2:
            return "📖 Wikipedia", tool_wikipedia(query)

    # URL reader triggers
    urls = re.findall(r'https?://[^\s]+', user_msg)
    if urls and any(k in lower for k in ["read", "summarize", "what's on", "open", "check this", "analyze url"]):
        return "🌐 URL Reader", tool_read_url(urls[0])

    # Code runner triggers
    code_match = re.search(r'```python\s*\n(.*?)```', user_msg, re.DOTALL)
    if code_match and any(k in lower for k in ["run", "execute", "test", "try this"]):
        return "💻 Code Runner", tool_run_code(code_match.group(1))

    # QR code triggers
    qr_match = re.search(r'(?:qr|qr code)\s+(?:for|of|code)\s+(.+)', lower)
    if qr_match:
        qr_data = tool_qr_code(qr_match.group(1).strip())
        if qr_data:
            return "🔳 QR Code", f"![QR Code]({qr_data})"

    # Chart triggers
    if any(k in lower for k in ["make a chart", "create a chart", "bar chart", "pie chart", "plot this"]):
        return "📊 Chart", "Provide data as JSON like: `{\"Jan\": 100, \"Feb\": 150, \"Mar\": 200}` and I'll generate a chart."

    return None, None

# =====================================================================
# SESSION STATE
# =====================================================================
for k, v in {
    "messages": [], "chat_history": [], "chat_id": str(uuid.uuid4())[:8],
    "file_ctx": "", "memories": [], "model": "llama-3.3-70b-versatile",
    "provider": "Groq (Free)", "agent": "sekta-omni", "manual_key": "",
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =====================================================================
# SIDEBAR
# =====================================================================
with st.sidebar:
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
        index=prov_names.index(st.session_state.provider), key="prov_radio")
    st.session_state.provider = prov
    p = PROVIDERS[prov]

    key = get_key(p["env_key"])
    if not key:
        st.markdown(f"<div class='card' style='margin:12px 0'><div style='font-size:12px;color:#f59e0b;font-weight:600;margin-bottom:6px'>🔑 API Key Required</div><div style='font-size:11px;color:#71717a'>Get free key → <b>{p['signup']}</b></div></div>", unsafe_allow_html=True)
        manual = st.text_input("API Key", type="password", placeholder="Paste key...", label_visibility="collapsed")
        if manual:
            st.session_state.manual_key = manual
            st.rerun()
    else:
        st.markdown(f"<div style='font-size:11px;color:#22c55e;margin:8px 0'>✓ Connected · <code style='color:#52525b;background:#1e1e22;padding:2px 6px;border-radius:4px'>{key[:6]}…{key[-4:]}</code></div>", unsafe_allow_html=True)

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
    m_idx = model_list.index(p["default_model"]) if p["default_model"] in model_list else 0
    st.session_state.model = st.selectbox("Model", model_list, index=m_idx, label_visibility="collapsed")

    st.markdown("<div style='height:1px;background:#27272a;margin:16px 0'></div>", unsafe_allow_html=True)

    # Tools info
    st.markdown("<div style='font-size:11px;font-weight:600;color:#52525b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px'>Built-in Tools</div>", unsafe_allow_html=True)
    tools_list = [
        ("🔍", "Web Search", "DuckDuckGo (free)"),
        ("🖼️", "Image Gen", "Pollinations AI (free)"),
        ("💻", "Code Runner", "Python sandbox"),
        ("🌐", "URL Reader", "Any webpage"),
        ("📖", "Wikipedia", "Knowledge base"),
        ("📊", "Charts", "Matplotlib"),
        ("📎", "File Analysis", "PDF, CSV, DOCX"),
        ("🔳", "QR Codes", "Instant generation"),
    ]
    for icon, name, desc in tools_list:
        st.markdown(f"<div style='display:flex;align-items:center;gap:8px;padding:4px 0'><span style='font-size:14px'>{icon}</span><span style='font-size:12px;color:#a1a1aa'>{name}</span><span style='font-size:10px;color:#3f3f46;margin-left:auto'>{desc}</span></div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1px;background:#27272a;margin:16px 0'></div>", unsafe_allow_html=True)

    # Memory
    if st.session_state.memories:
        st.markdown("<div style='font-size:11px;font-weight:600;color:#52525b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px'>Memory</div>", unsafe_allow_html=True)
        for m in st.session_state.memories[-3:][::-1]:
            st.markdown(f"<div style='font-size:11px;color:#71717a;padding:4px 0;border-bottom:1px solid #1e1e22'>💾 {m[:50]}</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1px;background:#27272a;margin:16px 0'></div>", unsafe_allow_html=True)

    # New chat
    if st.button("⭐  New Chat", use_container_width=True, type="primary"):
        if st.session_state.messages:
            st.session_state.chat_history.append({
                "id": st.session_state.chat_id,
                "title": st.session_state.messages[0]["content"][:40],
                "messages": st.session_state.messages.copy(),
                "agent": agent, "time": datetime.now().isoformat(),
            })
        st.session_state.messages = []
        st.session_state.chat_id = str(uuid.uuid4())[:8]
        st.session_state.file_ctx = ""
        st.rerun()

    if st.session_state.chat_history:
        st.markdown("<div style='font-size:11px;font-weight:600;color:#52525b;text-transform:uppercase;letter-spacing:0.08em;margin:12px 0 8px'>History</div>", unsafe_allow_html=True)
        for ch in st.session_state.chat_history[-5:][::-1]:
            if st.button(f"📝 {ch['title'][:25]}", key=f"h_{ch['id']}", use_container_width=True):
                st.session_state.messages = ch["messages"]
                st.session_state.chat_id = ch["id"]
                st.rerun()

# =====================================================================
# MAIN CHAT AREA
# =====================================================================
a = AGENTS[st.session_state.agent]
st.markdown(f"""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;padding:8px 0">
    <div style="width:36px;height:36px;border-radius:10px;background:{a['color']}15;border:1px solid {a['color']}30;display:flex;align-items:center;justify-content:center;font-size:18px">{a['icon']}</div>
    <div>
        <div style="font-size:15px;font-weight:600;color:#fafafa">{a['name']}</div>
        <div style="font-size:11px;color:#52525b">{st.session_state.model} · {st.session_state.provider.split(' (')[0]} · Tools Active</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Welcome screen
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center;padding:40px 20px 20px">
        <div style="width:64px;height:64px;border-radius:20px;background:linear-gradient(135deg,#f59e0b,#f97316);display:flex;align-items:center;justify-content:center;font-size:28px;margin:0 auto 20px;box-shadow:0 8px 32px rgba(245,158,11,0.2)">⭐</div>
        <h1 style="font-size:32px;font-weight:800;letter-spacing:-0.04em;color:#fafafa;margin:0">What can I help with?</h1>
        <p style="color:#52525b;font-size:14px;margin-top:8px">8 agents · web search · image gen · code runner · Wikipedia · charts</p>
    </div>
    """, unsafe_allow_html=True)

    prompts = [
        ("🔍", "Search latest AI news today"),
        ("🖼️", "Generate a luxury gold logo"),
        ("💻", "Run: print('Hello World')"),
        ("📖", "Who is Nikola Tesla?"),
        ("📊", "Make a bar chart: {Jan:100, Feb:150, Mar:200}"),
        ("🌐", "Summarize https://news.ycombinator.com"),
        ("🦈", "Evaluate my startup idea"),
        ("📚", "Explain quantum computing simply"),
        ("📎", "Analyze my CSV data"),
    ]
    cols = st.columns(3)
    for i, (icon, text) in enumerate(prompts):
        with cols[i % 3]:
            if st.button(f"{icon}  {text}", key=f"p_{i}", use_container_width=True):
                st.session_state["_prompt_clicked"] = text
                st.rerun()

# Display messages
for msg in st.session_state.messages:
    av = a["icon"] if msg["role"] == "assistant" else "👤"
    with st.chat_message(msg["role"], avatar=av):
        st.markdown(msg["content"])
        if msg.get("image_url"):
            st.image(msg["image_url"], use_container_width=True)

# File uploader
uploaded = st.file_uploader("📎 Attach files", type=["pdf","txt","md","csv","xlsx","docx","png","jpg","jpeg","py","js","json"],
    label_visibility="collapsed", accept_multiple_files=True)
if uploaded:
    ctx_parts = [f"### {f.name}\n{parse_file(f)}" for f in uploaded]
    st.session_state.file_ctx = "\n\n".join(ctx_parts)
    st.success(f"📎 {len(uploaded)} file(s) attached — ask anything about them!")

# Chat input
prompt = st.session_state.pop("_prompt_clicked", None) or st.chat_input(f"Message {a['name']}…")

if prompt:
    # Memory extraction
    low = prompt.lower()
    if any(k in low for k in ["remember that", "remember my", "my name is"]):
        st.session_state.memories.append(re.sub(r"(remember that|remember|my name is)\s*", "", low).strip())

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Try auto-tool detection first
    tool_name, tool_result = detect_and_run_tool(prompt, low)

    # Build system prompt
    system = a["prompt"] + f"\n\n{TOOLS_DESC}"
    if st.session_state.memories:
        system += "\n\n[User memories]:\n" + "\n".join(f"- {m}" for m in st.session_state.memories[-10:])
    if st.session_state.file_ctx:
        system += f"\n\n[Attached files]:\n{st.session_state.file_ctx[:12000]}"

    msgs = [{"role": "system", "content": system}]
    for m in st.session_state.messages[-20:]:
        msgs.append({"role": m["role"], "content": m["content"]})

    # If tool was triggered, add result as context
    if tool_result:
        msgs.append({"role": "system", "content": f"[Tool result from {tool_name}]:\n{tool_result[:4000]}"})

    client = get_client()
    if not client:
        st.error(f"🔑 No API key for **{st.session_state.provider}**. Add your key in the sidebar.")
        st.stop()

    with st.chat_message("assistant", avatar=a["icon"]):
        # Show tool badge if used
        if tool_name:
            st.markdown(f"<span style='background:#27272a;color:#f59e0b;padding:3px 10px;border-radius:100px;font-size:11px;font-family:JetBrains Mono,monospace'>{tool_name} ✓</span>", unsafe_allow_html=True)

        placeholder = st.empty()
        full = ""

        # If tool returned an image (QR code, chart, generated image)
        if tool_result and tool_result.startswith("data:image"):
            st.markdown(f"![Tool output]({tool_result})")
            full = f"Here's your result:\n\n![Generated]({tool_result})"
            st.session_state.messages.append({"role": "assistant", "content": full, "image_url": tool_result})
        elif tool_name == "🖼️ Image Gen" and tool_result and tool_result.startswith("http"):
            st.image(tool_result, use_container_width=True)
            full = f"Generated image for: **{prompt}**\n\n![Generated]({tool_result})"
            st.session_state.messages.append({"role": "assistant", "content": full, "image_url": tool_result})
        else:
            # Stream text response
            try:
                stream = client.chat.completions.create(
                    model=st.session_state.model, messages=msgs,
                    stream=True, temperature=0.7, max_tokens=4000,
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
                    st.error("⚠️ Rate limit hit. Try switching provider or wait a moment.")
                elif "401" in err or "api_key" in err.lower():
                    st.error("🔑 Invalid API key. Check your key in the sidebar.")
                else:
                    st.error(f"Error: {err[:300]}")
                st.session_state.messages.append({"role": "assistant", "content": f"⚠️ {err[:200]}"})

# Footer
st.markdown("<div style='height:1px;background:#1e1e22;margin-top:32px'></div>", unsafe_allow_html=True)
st.markdown("<div style='text-align:center;padding:16px 0;font-size:11px;color:#3f3f46;font-family:JetBrains Mono,monospace'>Sekta AI · 8 Tools · 3 Providers · Free · <a href='https://github.com/goldstarpalms-svg/Sekta-gold-cup' style='color:#52525b'>GitHub</a></div>", unsafe_allow_html=True)
