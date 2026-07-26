# 🤖 SEKTA GOLD AI Chatbot

A Streamlit-ready AI chatbot with a black-and-gold interface, provider selection, file context, optional web context, and chat export.

## One-click Streamlit deploy

[![Deploy to Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=https://github.com/goldstarpalms-svg/Sekta-gold-cup&branch=arena/019f9bb4-sekta-gold-cup&mainModule=app.py)

Deployment settings:

- Repository: `https://github.com/goldstarpalms-svg/Sekta-gold-cup`
- Branch: `arena/019f9bb4-sekta-gold-cup`
- Main file path: `app.py`
- Python: `3.11`

## Features

- AI chat through Groq, OpenAI, or Gemini
- Demo mode so the app opens even before secrets are added
- Upload context from TXT, Markdown, CSV, Excel, PDF, DOCX, code, JSON, logs, and more
- Optional web context via Tavily when keyed, with a keyless DuckDuckGo/Wikipedia fallback
- Custom system instructions
- Export chat transcript as Markdown
- Streamlit Community Cloud deployment ready

## Required secrets

Add at least one provider key in **Streamlit Cloud → App settings → Secrets**:

```toml
GROQ_API_KEY = "your_groq_key"
OPENAI_API_KEY = "your_openai_key"
GEMINI_API_KEY = "your_gemini_key"
```

Optional:

```toml
TAVILY_API_KEY = "your_tavily_key"
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

For local secrets, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and add your keys.
