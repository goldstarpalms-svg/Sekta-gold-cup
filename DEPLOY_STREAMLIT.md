# 🚀 Deploy SEKTA GOLD to Streamlit Cloud (1-Click)

You wanted "streamitt" — here's Streamlit Cloud deployment, 2 minutes.

### What You Get
- **Single file deploy**: `app.py` is the whole ultimate chatbot
- **Same gold UI**, 8 agents, streaming, image gen, web search, files, memory
- **Works on Streamlit Community Cloud (free)**

---

### Step 1: Push to GitHub (Already Done)

Your branch `arena/019f96ed-sekta-gold-cup` already has `app.py`.

### Step 2: Revoke Leaked Key (CRITICAL)

Your old key `sk-proj-4R35...` is compromised.

1. Go to https://platform.openai.com/api-keys
2. Delete old key
3. Create new key → copy it

### Step 3: Deploy to Streamlit

1. Go to https://share.streamlit.io/deploy
2. Or direct: https://share.streamlit.io → New app → From existing repo
3. Select:
   - **Repository**: `goldstarpalms-svg/Sekta-gold-cup`
   - **Branch**: `arena/019f96ed-sekta-gold-cup`
   - **Main file path**: `app.py`
   - **Python version**: 3.11

4. **Advanced Settings → Secrets** paste:

```toml
OPENAI_API_KEY = "sk-proj-YOUR_NEW_KEY_AFTER_REVOKE"
TAVILY_API_KEY = "tvly-... optional get free at tavily.com for real web search"
```

5. Click **Deploy** — 2 min build, you get URL like `https://sekta-gold-cup.streamlit.app`

### Step 4: Test

- Chat: "Generate luxury logo for Sekta Gold Cup black & gold"
- "Search latest Tesla news with sources"
- Upload PDF/CSV and ask questions
- Say "remember my name is Alex" → check sidebar memory

---

### Local Streamlit Test

```bash
pip install -r requirements.txt
streamlit run app.py --server.port 8501
# → http://localhost:8501
```

Set key locally:
- Create `.streamlit/secrets.toml` from example
- Put new key there

### Full Stack vs Streamlit

- **Full Stack** (`backend/` + `frontend/`): Production, scalable, separate FE/BE, fast, customizable — use for Vercel/Render/VPS
- **Streamlit** (`app.py`): 1-file, fastest deploy, perfect for Streamlit Cloud, demos, sharing link

Both use same OpenAI key and same 8 agents. Streamlit version is simplified but still better than ChatGPT.

### Troubleshooting

- **Error 401 / invalid key**: You used leaked key. Revoke and use new one.
- **No search results**: Add TAVILY_API_KEY free from tavily.com to Secrets
- **Build fails**: Check Python 3.11, requirements.txt exists at root (we have it)
- **Images not showing**: Check OpenAI billing, DALL-E 3 requires credits

Gold standard deployed 🏆
