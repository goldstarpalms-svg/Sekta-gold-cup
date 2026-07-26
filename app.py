from __future__ import annotations

import io
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

try:
    import httpx
except Exception:  # pragma: no cover - optional at runtime
    httpx = None


APP_NAME = "SEKTA GOLD AI"
APP_VERSION = "Chatbot Dashboard v2"
DEFAULT_SYSTEM_PROMPT = """
You are SEKTA GOLD AI, a premium AI chatbot inside a Streamlit dashboard.
Help with writing, coding, business, research, analysis, planning, documents, and everyday questions.
Be direct, practical, friendly, and useful. If uploaded files or web results are provided, use them as context.
If you do not know something, say so and suggest the best next step.
""".strip()

PROVIDERS: dict[str, dict[str, str]] = {
    "groq": {
        "label": "Groq",
        "secret": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
    },
    "openai": {
        "label": "OpenAI",
        "secret": "OPENAI_API_KEY",
        "base_url": "",
        "model": "gpt-4o-mini",
    },
    "gemini": {
        "label": "Gemini",
        "secret": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-1.5-flash",
    },
}

SAMPLE_PROMPTS = [
    "Create a professional business plan for my idea.",
    "Review this text and make it sound more premium.",
    "Explain this code and improve it.",
    "Give me a step-by-step marketing strategy.",
]


st.set_page_config(
    page_title="SEKTA GOLD AI Chatbot",
    page_icon="⚜️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
  --gold: #FFC700;
  --gold-2: #E8A900;
  --bg: #050506;
  --panel: rgba(17, 17, 20, 0.82);
  --panel-2: rgba(255, 199, 0, 0.08);
  --line: rgba(255, 199, 0, 0.22);
  --muted: #A8A8AF;
}

html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
.stApp {
  color: #F7F7F8;
  background:
    radial-gradient(circle at 10% 8%, rgba(255, 199, 0, 0.22), transparent 28%),
    radial-gradient(circle at 88% 18%, rgba(232, 169, 0, 0.12), transparent 28%),
    linear-gradient(135deg, #050506 0%, #08080A 48%, #11100A 100%);
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #050506 0%, #0E0E10 100%);
  border-right: 1px solid var(--line);
}
[data-testid="stHeader"] { background: rgba(5,5,6,0.72); backdrop-filter: blur(18px); }
.block-container { padding-top: 1.4rem; max-width: 1420px; }
h1, h2, h3 { color: white; letter-spacing: -0.04em; }
a { color: var(--gold) !important; }
code, pre { font-family: 'JetBrains Mono', monospace !important; }

.top-shell {
  border: 1px solid rgba(255,199,0,0.30);
  border-radius: 30px;
  padding: 30px;
  background:
    linear-gradient(135deg, rgba(255,199,0,0.18), rgba(255,199,0,0.04) 34%, rgba(11,11,13,0.86)),
    radial-gradient(circle at 92% 18%, rgba(255,199,0,0.16), transparent 32%);
  box-shadow: 0 24px 90px rgba(0,0,0,0.42);
  margin-bottom: 18px;
}
.logo-row { display:flex; align-items:center; gap:12px; margin-bottom:12px; }
.logo-mark {
  width: 46px; height: 46px; border-radius: 16px;
  display:flex; align-items:center; justify-content:center;
  background: linear-gradient(135deg, #FFC700, #8A6200);
  color:#050506; font-size:26px; font-weight:900;
  box-shadow: 0 12px 34px rgba(255,199,0,0.22);
}
.kicker { color: var(--gold); font-weight: 900; font-size: 12px; letter-spacing: 0.20em; text-transform: uppercase; }
.hero-title { font-size: clamp(38px, 6vw, 76px); line-height: 0.92; font-weight: 900; margin: 0; }
.hero-subtitle { color: #D5D5D8; font-size: 18px; max-width: 860px; margin-top: 14px; }
.gold-gradient {
  background: linear-gradient(90deg, #FFF4B0 0%, #FFC700 42%, #B98200 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.status-grid { display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin: 18px 0; }
.status-card {
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(15,15,18,0.70);
  border-radius: 20px;
  padding: 16px;
}
.status-card b { display:block; font-size: 22px; color:#fff; margin-top:6px; }
.status-card span { color: var(--muted); font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: .12em; }

.prompt-card {
  border: 1px solid rgba(255,199,0,0.20);
  background: rgba(255,199,0,0.055);
  border-radius: 18px;
  padding: 14px 16px;
  min-height: 92px;
}
.prompt-card h4 { margin: 0 0 7px 0; color: #fff; }
.prompt-card p { color: #BEBEC5; margin: 0; font-size: 13px; }

.chat-frame {
  border: 1px solid rgba(255,199,0,0.18);
  border-radius: 26px;
  padding: 18px;
  background: rgba(7,7,9,0.58);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
}
[data-testid="stChatMessage"] {
  border: 1px solid rgba(255,255,255,0.09);
  background: rgba(18,18,22,0.74);
  border-radius: 20px;
  padding: 10px;
}
.stButton > button, .stDownloadButton > button {
  border-radius: 14px;
  font-weight: 800;
  border: 1px solid rgba(255,199,0,0.26);
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: rgba(255,199,0,0.70);
  color: var(--gold);
}
.small-note { color: var(--muted); font-size: 13px; }
.sidebar-title { font-size: 26px; font-weight: 900; color: #fff; margin: 0; }
.sidebar-badge {
  display:inline-block; padding: 5px 9px; border-radius:999px;
  background: rgba(255,199,0,0.10); border: 1px solid rgba(255,199,0,0.24);
  color: var(--gold); font-weight: 900; font-size: 11px; letter-spacing:.12em;
}
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

@media (max-width: 900px) {
  .status-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .top-shell { padding: 22px; border-radius: 24px; }
}
</style>
""",
    unsafe_allow_html=True,
)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def load_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(name, default) or default


def mask_key(value: str) -> str:
    if not value:
        return "not set"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}…{value[-4:]}"


def configured_providers() -> list[str]:
    return [key for key, cfg in PROVIDERS.items() if load_secret(cfg["secret"])]


def provider_options() -> list[str]:
    options = ["demo"]
    for key in configured_providers():
        if key not in options:
            options.append(key)
    for key in PROVIDERS:
        if key not in options:
            options.append(key)
    return options


def provider_display(provider: str) -> str:
    if provider == "demo":
        return "Demo mode — no key needed"
    cfg = PROVIDERS[provider]
    return f"{cfg['label']} — {'ready' if load_secret(cfg['secret']) else 'needs key'}"


def provider_api_key(provider: str, override: str = "") -> str:
    if override.strip():
        return override.strip()
    return load_secret(PROVIDERS[provider]["secret"])


def trim_text(text: str, limit: int = 12000) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n\n[Truncated to {limit:,} characters]"


def transcript_as_markdown(messages: list[dict[str, str]]) -> str:
    lines = [f"# {APP_NAME} Transcript", "", f"Exported: {now_utc()}", ""]
    for message in messages:
        label = "Assistant" if message["role"] == "assistant" else "User"
        lines.extend([f"## {label}", "", message["content"], ""])
    return "\n".join(lines)


def extract_uploaded_file(uploaded_file: Any) -> str:
    name = uploaded_file.name
    suffix = Path(name).suffix.lower()
    data = uploaded_file.getvalue()

    try:
        if suffix == ".csv":
            df = pd.read_csv(io.BytesIO(data))
            return f"File: {name}\nCSV shape: {df.shape}\nPreview:\n{df.head(30).to_csv(index=False)}"

        if suffix in {".xlsx", ".xls"}:
            excel = pd.ExcelFile(io.BytesIO(data))
            chunks = [f"File: {name}", f"Sheets: {', '.join(excel.sheet_names)}"]
            for sheet in excel.sheet_names[:4]:
                df = pd.read_excel(excel, sheet_name=sheet, nrows=30)
                chunks.append(f"\nSheet: {sheet}\nPreview shape: {df.shape}\n{df.to_csv(index=False)}")
            return "\n".join(chunks)

        if suffix == ".pdf":
            from PyPDF2 import PdfReader

            reader = PdfReader(io.BytesIO(data))
            pages = []
            for page_number, page in enumerate(reader.pages[:12], start=1):
                pages.append(f"\n--- Page {page_number} ---\n{page.extract_text() or ''}")
            return f"File: {name}\nPDF pages read: {min(len(reader.pages), 12)} of {len(reader.pages)}\n" + "\n".join(pages)

        if suffix == ".docx":
            import docx

            document = docx.Document(io.BytesIO(data))
            text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
            return f"File: {name}\n\n{text}"

        readable = {
            ".txt", ".md", ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css",
            ".json", ".toml", ".yaml", ".yml", ".log", ".sql", ".xml",
        }
        if suffix in readable or not suffix:
            return f"File: {name}\n\n{data.decode('utf-8', errors='replace')}"

        return f"File: {name}\nType: {suffix or 'unknown'}\nSize: {len(data):,} bytes\nThis file type is not text-readable here, but the metadata is available."
    except Exception as exc:
        return f"File: {name}\nCould not extract content: {exc}"


def build_file_context(files: list[Any]) -> str:
    if not files:
        return ""
    extracted = [trim_text(extract_uploaded_file(file), 9000) for file in files[:6]]
    return "\n\n".join(extracted)


def tavily_search(query: str, api_key: str) -> list[dict[str, str]]:
    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, search_depth="basic", max_results=5)
        return [
            {
                "title": item.get("title", "Untitled"),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            }
            for item in response.get("results", [])
        ]
    except Exception:
        return []


def keyless_search(query: str) -> list[dict[str, str]]:
    if httpx is None:
        return []

    results: list[dict[str, str]] = []
    try:
        response = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=10,
        )
        data = response.json()
        if data.get("AbstractText"):
            results.append(
                {
                    "title": data.get("Heading") or "DuckDuckGo result",
                    "url": data.get("AbstractURL") or "https://duckduckgo.com/",
                    "content": data.get("AbstractText", ""),
                }
            )
        for topic in data.get("RelatedTopics", [])[:4]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(
                    {
                        "title": topic.get("Text", "")[:90],
                        "url": topic.get("FirstURL", ""),
                        "content": topic.get("Text", ""),
                    }
                )
    except Exception:
        pass

    if len(results) < 2:
        try:
            title = query.strip().replace(" ", "_")[:120]
            response = httpx.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("extract"):
                    results.append(
                        {
                            "title": data.get("title", "Wikipedia"),
                            "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                            "content": data.get("extract", ""),
                        }
                    )
        except Exception:
            pass

    return results[:5]


def web_context(query: str) -> tuple[str, list[dict[str, str]]]:
    tavily_key = load_secret("TAVILY_API_KEY")
    results = tavily_search(query, tavily_key) if tavily_key else []
    if not results:
        results = keyless_search(query)
    if not results:
        return "", []

    lines = ["Web context. Use when relevant and cite the URLs:"]
    for index, item in enumerate(results, start=1):
        lines.append(
            f"[{index}] {item.get('title', 'Untitled')}\nURL: {item.get('url', '')}\nSnippet: {item.get('content', '')}"
        )
    return "\n\n".join(lines), results


def call_chat_model(
    provider: str,
    api_key: str,
    model: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> str:
    try:
        from openai import OpenAI
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("The OpenAI package is missing. Install requirements.txt and redeploy.") from exc

    cfg = PROVIDERS[provider]
    client_kwargs: dict[str, Any] = {"api_key": api_key}
    if cfg["base_url"]:
        client_kwargs["base_url"] = cfg["base_url"]

    client = OpenAI(**client_kwargs)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def demo_response(prompt: str, file_context: str, search_context: str) -> str:
    response = [
        "I’m online in **Demo mode**, so the dashboard is working but no live AI provider is connected yet.",
        "",
        "To turn this into the real chatbot, add one of these secrets in Streamlit Cloud:",
        "```toml",
        'GROQ_API_KEY = "your_key"',
        '# or OPENAI_API_KEY = "your_key"',
        '# or GEMINI_API_KEY = "your_key"',
        "```",
        "",
        "Your message was:",
        f"> {prompt}",
    ]
    if file_context:
        response.append("\nI also received uploaded file context. Add an AI key and I can analyze it fully.")
    if search_context:
        response.append("\nWeb context was collected. Add an AI key and I can summarize it with citations.")
    return "\n".join(response)


def ensure_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Welcome to **SEKTA GOLD AI**. I’m ready for chat, files, code, research, and strategy.",
            }
        ]
    if "pending_prompt" not in st.session_state:
        st.session_state.pending_prompt = ""


def queue_prompt(prompt: str) -> None:
    st.session_state.pending_prompt = prompt


ensure_state()

configured = configured_providers()
default_options = provider_options()
default_index = 1 if configured else 0

with st.sidebar:
    st.markdown('<div class="sidebar-badge">SEKTA GOLD</div>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-title">AI Control</p>', unsafe_allow_html=True)
    st.caption(APP_VERSION)

    provider = st.selectbox(
        "Provider",
        default_options,
        index=min(default_index, len(default_options) - 1),
        format_func=provider_display,
    )

    pasted_key = ""
    model = "demo"
    if provider == "demo":
        st.info("Demo mode confirms the dashboard loads. Add a provider key for real AI answers.")
    else:
        cfg = PROVIDERS[provider]
        secret_value = load_secret(cfg["secret"])
        st.caption(f"Secret `{cfg['secret']}`: {mask_key(secret_value)}")
        pasted_key = st.text_input("Temporary API key override", type="password")
        model = st.text_input("Model", value=cfg["model"])

    st.divider()
    temperature = st.slider("Creativity", 0.0, 1.2, 0.65, 0.05)
    max_tokens = st.slider("Max response tokens", 256, 4096, 1400, 128)
    enable_web = st.toggle("Add web context", value=False)

    with st.expander("System prompt", expanded=False):
        system_prompt = st.text_area("Instructions", value=DEFAULT_SYSTEM_PROMPT, height=190)

    uploaded_files = st.file_uploader(
        "Attach files",
        type=[
            "txt", "md", "csv", "xlsx", "xls", "pdf", "docx", "py", "js", "ts", "tsx", "jsx",
            "json", "html", "css", "log", "sql", "xml", "yaml", "yml", "toml",
        ],
        accept_multiple_files=True,
    )

    left, right = st.columns(2)
    with left:
        if st.button("New", use_container_width=True):
            st.session_state.messages = [
                {"role": "assistant", "content": "Fresh chat started. What should we build or solve?"}
            ]
            st.session_state.pending_prompt = ""
            st.rerun()
    with right:
        st.download_button(
            "Export",
            data=transcript_as_markdown(st.session_state.messages),
            file_name="sekta-gold-ai-chat.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.markdown('<p class="small-note">Secrets supported: GROQ_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, TAVILY_API_KEY.</p>', unsafe_allow_html=True)

provider_name = "Demo" if provider == "demo" else PROVIDERS[provider]["label"]
provider_state = "Ready" if provider != "demo" and provider_api_key(provider, pasted_key) else ("Demo" if provider == "demo" else "Needs key")
file_count = len(uploaded_files or [])
message_count = len(st.session_state.messages)
web_state = "On" if enable_web else "Off"

st.markdown(
    f"""
<div class="top-shell">
  <div class="logo-row">
    <div class="logo-mark">⚜️</div>
    <div>
      <div class="kicker">{APP_VERSION}</div>
      <div style="color:#B8B8BF; font-weight:700;">Premium Streamlit AI assistant</div>
    </div>
  </div>
  <h1 class="hero-title"><span class="gold-gradient">SEKTA GOLD</span><br/>AI Command Center</h1>
  <div class="hero-subtitle">A completely redesigned chatbot dashboard for conversations, file analysis, code help, research, and strategy.</div>
</div>
<div class="status-grid">
  <div class="status-card"><span>Provider</span><b>{provider_name}</b></div>
  <div class="status-card"><span>Status</span><b>{provider_state}</b></div>
  <div class="status-card"><span>Files</span><b>{file_count}</b></div>
  <div class="status-card"><span>Messages</span><b>{message_count}</b></div>
</div>
""",
    unsafe_allow_html=True,
)

quick_cols = st.columns(4)
for col, sample in zip(quick_cols, SAMPLE_PROMPTS):
    with col:
        st.markdown(
            f"""
<div class="prompt-card">
  <h4>{sample.split('.')[0]}</h4>
  <p>Click below to start this workflow.</p>
</div>
""",
            unsafe_allow_html=True,
        )
        if st.button("Use prompt", key=f"sample_{sample}", use_container_width=True):
            queue_prompt(sample)
            st.rerun()

if uploaded_files:
    st.success("Attached for the next message: " + ", ".join(file.name for file in uploaded_files[:6]))

st.markdown('<div class="chat-frame">', unsafe_allow_html=True)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
st.markdown('</div>', unsafe_allow_html=True)

chat_prompt = st.chat_input("Message SEKTA GOLD AI...")
prompt = st.session_state.pending_prompt or chat_prompt
st.session_state.pending_prompt = ""

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    file_context = build_file_context(uploaded_files or [])
    search_context = ""
    sources: list[dict[str, str]] = []

    if enable_web:
        with st.status("Collecting web context...", expanded=False):
            search_context, sources = web_context(prompt)

    context_blocks = []
    if file_context:
        context_blocks.append("Uploaded file context:\n" + trim_text(file_context, 20000))
    if search_context:
        context_blocks.append(trim_text(search_context, 10000))

    enriched_prompt = prompt
    if context_blocks:
        enriched_prompt = (
            "Use this context when relevant. If using web context, cite the provided URLs.\n\n"
            + "\n\n".join(context_blocks)
            + "\n\nUser question:\n"
            + prompt
        )

    model_messages = [{"role": "system", "content": system_prompt}]
    model_messages.extend(st.session_state.messages[-12:-1])
    model_messages.append({"role": "user", "content": enriched_prompt})

    with st.chat_message("assistant"):
        try:
            if provider == "demo":
                answer = demo_response(prompt, file_context, search_context)
            else:
                api_key = provider_api_key(provider, pasted_key)
                if not api_key:
                    secret_name = PROVIDERS[provider]["secret"]
                    answer = (
                        f"I need `{secret_name}` to call {PROVIDERS[provider]['label']}. "
                        "Add it in Streamlit Secrets or paste a temporary key in the sidebar."
                    )
                else:
                    with st.spinner(f"Thinking with {PROVIDERS[provider]['label']}..."):
                        answer = call_chat_model(
                            provider=provider,
                            api_key=api_key,
                            model=model,
                            messages=model_messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        )

            st.markdown(answer)
            if sources:
                with st.expander("Web sources"):
                    for index, item in enumerate(sources, start=1):
                        st.markdown(f"{index}. [{item.get('title', 'Untitled')}]({item.get('url', '')})")
        except Exception as exc:
            answer = f"Sorry, I hit an error: `{exc}`"
            st.error(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
