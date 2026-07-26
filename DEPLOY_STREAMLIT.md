# Deploy to Streamlit Community Cloud

## One-click deploy

Use this direct Streamlit deploy link:

[![Deploy to Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/deploy?repository=https://github.com/goldstarpalms-svg/Sekta-gold-cup&branch=arena/019f9bb4-sekta-gold-cup&mainModule=app.py)

If Streamlit asks for settings, use:

- Repository: `https://github.com/goldstarpalms-svg/Sekta-gold-cup`
- Branch: `arena/019f9bb4-sekta-gold-cup`
- Main file path: `app.py`
- Python: `3.11`

This repository is now structured as a Streamlit app. The entry point is:

```text
app.py
```

## 1. Push to GitHub

Commit and push the repository to GitHub.

## 2. Create the Streamlit app

1. Go to <https://share.streamlit.io/>.
2. Choose this GitHub repository.
3. Set the main file path to `app.py`.
4. Use Python 3.11+.
5. Deploy.

Streamlit Cloud will install packages from `requirements.txt`.

## 3. Add secrets if needed

The app runs without secrets for local CSV analysis. Add these only if you want live odds/provider integrations:

```toml
THE_ODDS_API_KEY = "your_key_here"
PINNACLE_USERNAME = ""
PINNACLE_PASSWORD = ""
BETFAIR_APP_KEY = ""
BETFAIR_SESSION_TOKEN = ""
```

In Streamlit Cloud, paste them under **App settings → Secrets**. Do not commit real secrets.

## 4. Data and models

- Historical CSV data is included in `data/`.
- Trained `.joblib`/`.pkl` models are ignored by Git because they can be regenerated from the ML Lab or scripts.
