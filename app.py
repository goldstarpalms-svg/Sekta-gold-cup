from __future__ import annotations

import io
import json
import os
import textwrap
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
except Exception:  # pragma: no cover
    httpx = None


APP_NAME = "SEKTA GOLD AI"
DEFAULT_SYSTEM_PROMPT = """
You are SEKTA GOLD AI, a fast, practical, and friendly AI chatbot.
Help with writing, coding, research, planning, analysis, business ideas, and everyday questions.
Be clear, useful, and honest. If uploaded files or web results are provided, use them as context.
If you are unsure, say so and suggest the next best step.
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


st.set_page_config(
    page_title="SEKTA GOLD AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
.stApp { background: radial-gradient(circle at top left, #191307 0, #08080A 38%, #050506 100%); color: #F5F5F5; }
[data-testid="stSidebar"] { background: #09090B; border-right: 1px solid rgba(255,199,0,0.20); }
[data-testid="stHeader"] { background: rgba(8,8,10,0.78); backdrop-filter: blur(14px); }
h1, h2, h3 { color: #FFFFFF; letter-spacing: -0.03em; }
a { color: #FFC700 !important; }
code, pre { font-family: 'JetBrains Mono', monospace !important; }
.gold { color: #FFC700; font-weight: 800; }
.hero {
    border: 1px solid rgba(255,199,0,0.22);
    border-radius: 22px;
    padding: 22px 24px;
    background: linear-gradient(135deg, rgba(255,199,0,0.12), rgba(20,20,22,0.85));
    box-shadow: 0 18px 70px rgba(0,0,0,0.28);
}
.subtle { color: #B8B8B8; }
.pill {
    display: inline-block;
    padding: 6px 10px;
    border: 1px solid rgba(255,199,0,0.26);
    border-radius: 999px;
    color: #FFC700;
    background: rgba(255,199,0,0.08);
    font-size: 12px;
    font-weight: 700;
    margin-right: 6px;
}
[data-testid="stChatMessage"] {
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(18,18,20,0.62);
}
.stButton > button { border-radius: 12px; font-weight: 700; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
</style>
""",
    unsafe_allow_html=True,
)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def load_secret(name: str, default: str = "") -> str:
    """Read from Streamlit secrets first, then environment variables."""
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


def provider_key(provider: str, override: str = "") -> str:
    if override:
        return override.strip()
    cfg = PROVIDERS[provider]
    return load_secret(cfg["secret"])


def available_provider_options() -> list[str]:
    options = ["demo"]
    for key, cfg in PROVIDERS.items():
        if load_secret(cfg["secret"]):
            options.append(key)
    # Always show providers so users can paste a key at runtime.
    for key in PROVIDERS:
        if key not in options:
            options.append(key)
    return options


def provider_label(provider: str) -> str:
    if provider == "demo":
        return "Demo mode (no API key)"
    cfg = PROVIDERS[provider]
    configured = "configured" if load_secret(cfg["secret"]) else "add key"
    return f"{cfg['label']} ({configured})"


def transcript_as_markdown(messages: list[dict[str, str]]) -> str:
    parts = [f"# {APP_NAME} Chat Transcript", "", f"Exported: {now_utc()}", ""]
    for msg in messages:
        role = "Assistant" if msg["role"] == "assistant" else "User"
        parts.extend([f"## {role}", "", msg["content"], ""])
    return "\n".join(parts)


def trim_text(text: str, limit: int = 12000) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n\n[Truncated to {limit:,} characters]"


def extract_uploaded_file(uploaded_file: Any) -> str:
    """Extract readable text/table preview from a Streamlit UploadedFile."""
    name = uploaded_file.name
    suffix = Path(name).suffix.lower()
    data = uploaded_file.getvalue()

    try:
        if suffix in {".txt", ".md", ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".json", ".toml", ".yaml", ".yml", ".log", ".csv"}:
            if suffix == ".csv":
                try:
                    df = pd.read_csv(io.BytesIO(data))
                    return f"File: {name}\nCSV shape: {df.shape}\nPreview:\n{df.head(25).to_csv(index=False)}"
                except Exception:
                    pass
            return f"File: {name}\n\n{data.decode('utf-8', errors='replace')}"

        if suffix in {".xlsx", ".xls"}:
            excel = pd.ExcelFile(io.BytesIO(data))
            chunks = [f"File: {name}", f"Sheets: {', '.join(excel.sheet_names)}"]
            for sheet in excel.sheet_names[:3]:
                df = pd.read_excel(excel, sheet_name=sheet, nrows=25)
                chunks.append(f"\nSheet: {sheet}\nShape preview: {df.shape}\n{df.to_csv(index=False)}")
            return "\n".join(chunks)

        if suffix == ".pdf":
            from PyPDF2 import PdfReader

            reader = PdfReader(io.BytesIO(data))
            pages = []
            for i, page in enumerate(reader.pages[:12], start=1):
                pages.append(f"\n--- Page {i} ---\n{page.extract_text() or ''}")
            return f"File: {name}\nPDF pages read: {min(len(reader.pages), 12)} of {len(reader.pages)}\n" + "\n".join(pages)

        if suffix == ".docx":
            import docx

            document = docx.Document(io.BytesIO(data))
            text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
            return f"File: {name}\n\n{text}"

        return f"File: {name}\nType: {suffix or 'unknown'}\nSize: {len(data):,} bytes\nI can see the file metadata, but this file type is not text-readable in the current app."
    except Exception as exc:
        return f"File: {name}\nCould not extract content: {exc}"


def build_file_context(files: list[Any]) -> str:
    if not files:
        return ""
    extracted = []
    for file in files[:5]:
        extracted.append(trim_text(extract_uploaded_file(file), 8000))
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


def lightweight_web_search(query: str) -> list[dict[str, str]]:
    if httpx is None:
        return []
    results: list[dict[str, str]] = []

    # DuckDuckGo Instant Answer API is lightweight and keyless.
    try:
        r = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            timeout=10,
        )
        data = r.json()
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
                        "title": topic.get("Text", "")[:80],
                        "url": topic.get("FirstURL", ""),
                        "content": topic.get("Text", ""),
                    }
                )
    except Exception:
        pass

    # Wikipedia summary fallback.
    if len(results) < 2:
        try:
            title = query.strip().replace(" ", "_")[:120]
            r = httpx.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}", timeout=10)
            if r.status_code == 200:
                data = r.json()
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
        results = lightweight_web_search(query)
    if not results:
        return "", []

    lines = ["Web search results. Use these only when relevant and cite the URLs:"]
    for i, item in enumerate(results, start=1):
        lines.append(
            f"[{i}] {item.get('title', 'Untitled')}\nURL: {item.get('url', '')}\nSnippet: {item.get('content', '')}"
        )
    return "\n\n".join(lines), results


def demo_response(prompt: str, file_context: str = "", search_context: str = "") -> str:
    """A no-key fallback so the deployed app is still usable for setup/testing."""
    pieces = [
        "I’m running in **Demo mode**, so I can’t call a live AI model yet.",
        "To unlock the real chatbot, add `GROQ_API_KEY`, `OPENAI_API_KEY`, or `GEMINI_API_KEY` in Streamlit Secrets.",
        "",
        "I received your message:",
        f"> {prompt}",
    ]
    if file_context:
        pieces.extend(["", "I also detected uploaded file context. Once an API key is added, I can analyze it in detail."])
    if search_context:
        pieces.extend(["", "Web context was collected. Once an API key is added, I can synthesize it into a sourced answer."])
    pieces.extend(
        [
            "",
            "Quick setup:",
            "```toml",
            'GROQ_API_KEY = "your_groq_key"',
            '# or OPENAI_API_KEY = "your_openai_key"',
            '# or GEMINI_API_KEY = "your_gemini_key"',
            "```",
        ]
    )
    return "\n".join(pieces)


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
        raise RuntimeError("The OpenAI Python package is not installed. Run `pip install -r requirements.txt`.") from exc

    cfg = PROVIDERS[provider]
    kwargs: dict[str, Any] = {"api_key": api_key}
    if cfg["base_url"]:
        kwargs["base_url"] = cfg["base_url"]
    client = OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def ensure_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello — I’m **SEKTA GOLD AI**. Ask me anything, or upload a file for me to analyze.",
            }
        ]


ensure_state()

with st.sidebar:
    st.markdown("# 🤖 SEKTA GOLD AI")
    st.caption("Streamlit AI chatbot")

    provider_options = available_provider_options()
    provider = st.selectbox(
        "AI provider",
        provider_options,
        index=0 if not any(load_secret(cfg["secret"]) for cfg in PROVIDERS.values()) else 1,
        format_func=provider_label,
    )

    pasted_key = ""
    model = ""
    if provider != "demo":
        cfg = PROVIDERS[provider]
        configured_key = load_secret(cfg["secret"])
        st.caption(f"Secret `{cfg['secret']}`: {mask_key(configured_key)}")
        pasted_key = st.text_input(
            "Temporary API key override",
            type="password",
            help="Optional. Use this for testing; it is not saved to the repo.",
        )
        model = st.text_input("Model", value=cfg["model"])
    else:
        st.info("Demo mode works without secrets, but real AI responses need an API key.")

    temperature = st.slider("Creativity", 0.0, 1.2, 0.7, 0.05)
    max_tokens = st.slider("Max response tokens", 256, 4096, 1400, 128)
    enable_web = st.toggle("🔍 Add web context", value=False)

    with st.expander("System instructions"):
        system_prompt = st.text_area("Assistant behavior", value=DEFAULT_SYSTEM_PROMPT, height=180)

    uploaded_files = st.file_uploader(
        "Upload files for context",
        type=["txt", "md", "csv", "xlsx", "xls", "pdf", "docx", "py", "js", "ts", "json", "html", "css", "log"],
        accept_multiple_files=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("New chat", use_container_width=True):
            st.session_state.messages = [
                {"role": "assistant", "content": "New chat started. What would you like to do?"}
            ]
            st.rerun()
    with c2:
        st.download_button(
            "Export",
            data=transcript_as_markdown(st.session_state.messages),
            file_name="sekta-gold-ai-chat.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.divider()
    st.caption("Streamlit secrets supported: `GROQ_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `TAVILY_API_KEY`.")

st.markdown(
    """
<div class="hero">
  <span class="pill">AI CHATBOT</span><span class="pill">STREAMLIT READY</span><span class="pill">FILES + WEB</span>
  <h1><span class="gold">SEKTA GOLD</span> AI Chatbot</h1>
  <p class="subtle">Ask questions, write content, debug code, analyze uploaded files, or add web context for current topics.</p>
</div>
""",
    unsafe_allow_html=True,
)

if uploaded_files:
    st.caption("Attached for the next message: " + ", ".join(file.name for file in uploaded_files[:5]))

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Message SEKTA GOLD AI…")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    file_context = build_file_context(uploaded_files or [])
    search_context = ""
    sources: list[dict[str, str]] = []
    if enable_web:
        with st.status("Searching the web…", expanded=False):
            search_context, sources = web_context(prompt)

    context_blocks = []
    if file_context:
        context_blocks.append("Uploaded file context:\n" + trim_text(file_context, 18000))
    if search_context:
        context_blocks.append(trim_text(search_context, 10000))

    user_content = prompt
    if context_blocks:
        user_content = (
            "Use the following context when relevant. If using web results, cite the URLs.\n\n"
            + "\n\n".join(context_blocks)
            + "\n\nUser question:\n"
            + prompt
        )

    model_messages = [{"role": "system", "content": system_prompt}]
    # Keep recent history compact for Streamlit/community model limits.
    model_messages.extend(st.session_state.messages[-12:-1])
    model_messages.append({"role": "user", "content": user_content})

    with st.chat_message("assistant"):
        try:
            if provider == "demo":
                answer = demo_response(prompt, file_context=file_context, search_context=search_context)
            else:
                key = provider_key(provider, pasted_key)
                if not key:
                    secret_name = PROVIDERS[provider]["secret"]
                    answer = (
                        f"I need `{secret_name}` to call {PROVIDERS[provider]['label']}. "
                        "Add it in Streamlit Secrets or paste a temporary key in the sidebar."
                    )
                else:
                    with st.spinner(f"Thinking with {PROVIDERS[provider]['label']}…"):
                        answer = call_chat_model(provider, key, model, model_messages, temperature, max_tokens)

            st.markdown(answer)
            if sources:
                with st.expander("Sources used for web context"):
                    for i, item in enumerate(sources, start=1):
                        st.markdown(f"{i}. [{item.get('title', 'Untitled')}]({item.get('url', '')})")
        except Exception as exc:
            answer = f"Sorry, I hit an error: `{exc}`"
            st.error(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
