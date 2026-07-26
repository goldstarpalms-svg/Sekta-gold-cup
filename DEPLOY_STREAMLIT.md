# Deploy SEKTA GOLD AI to Streamlit Community Cloud

## One-click deploy

[![Deploy to Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=https://github.com/goldstarpalms-svg/Sekta-gold-cup&branch=arena/019f9bb4-sekta-gold-cup&mainModule=app.py)

If Streamlit asks for settings, use:

- Repository: `https://github.com/goldstarpalms-svg/Sekta-gold-cup`
- Branch: `arena/019f9bb4-sekta-gold-cup`
- Main file path: `app.py`
- Python: `3.11`

## Add AI secrets

The app opens in demo mode without secrets. For real AI answers, add at least one key under **App settings → Secrets**:

```toml
GROQ_API_KEY = "your_groq_key"
OPENAI_API_KEY = "your_openai_key"
GEMINI_API_KEY = "your_gemini_key"
TAVILY_API_KEY = "optional_for_better_web_context"
```

Save, then reboot/redeploy the Streamlit app.
