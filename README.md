# 🛡️ SEKTA GOLD — Cyber Shield

A **defensive security operations dashboard** built with Streamlit. It generates
detection, alerting, and hardening artifacts for your own servers and edge.

> 🟢 **Defensive-only.** This dashboard performs **no scanning, exploitation, or
> attack** against any system. It builds configs and analyzes logs you provide.

---

## What it does

| Tool | Purpose |
|------|---------|
| 🔔 **Slack Alerts** | Central notifier — test/verify your webhook before relying on it. |
| 🍯 **Honeypot Canaries** | Generate decoy files + a host monitor script (`inotifywait`) that alerts Slack when a canary is touched. |
| 🌍 **IP Geolocation** | Enrich attacker IPs via [ipapi.co](https://ipapi.co) (city/country/ASN) and plot them on a world map. |
| 🚫 **Fail2Ban Builder** | Generate `jail.local` + a filter regex from a sample log line. |
| ☁️ **Cloudflare WAF** | Compose custom firewall expressions (block by IP / ASN / country / path). |
| 🔍 **File Integrity** | SHA-256 baselines + change detection for important files. |
| 💾 **Encrypted Backup** | Generate a `tar` + `gpg` backup script with a retention policy. |
| 📜 **auth.log Analyzer** | Detect brute-force SSH attempts and rank offending IPs; send a Slack summary. |
| 🤖 **AI Security Advisor** | LLM reads your dashboard context (brute-force IPs, geolocations) and writes plain-English analysis + defensive recommendations. |
| 💬 **AI Assistant** | General-purpose technical chat — strong across coding, research, writing, data — via Groq / Gemini / OpenAI (you pick per session). |

**Architecture note:** the Streamlit app is a *generator + dashboard*. It never
runs subprocess commands on the host it runs on. Scripts it produces (canary
monitor, backup, Fail2Ban configs) are plain text that **you** read, review, and
deploy on your own server.

---

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Python 3.11+. Dependencies (`streamlit`, `pandas`, `plotly`, `httpx`) are all
listed in `requirements.txt`.

## Secrets

Put sensitive values in `.streamlit/secrets.toml` (see
`.streamlit/secrets.toml.example`), or as environment variables / in `.env`.

| Key | Required | Notes |
|-----|----------|-------|
| `SLACK_WEBHOOK_URL` | For alerting | Create at https://api.slack.com/messaging/webhooks |
| `IPAPI_KEY` | Optional | Higher ipapi.co limits; free tier works without it |
| `GROQ_API_KEY` | For AI (any one) | Free: console.groq.com/keys |
| `GEMINI_API_KEY` | For AI (any one) | Free: aistudio.google.com/apikey |
| `OPENAI_API_KEY` | For AI (any one) | Paid: platform.openai.com/api-keys |

Webhook URLs are masked in the UI and never hardcoded. The AI tabs work with
**any one** provider key; blank ones are skipped gracefully.

## Deploy

See [`DEPLOY_STREAMLIT.md`](DEPLOY_STREAMLIT.md) for Streamlit Cloud. The app
redeploys automatically when `main` is updated. Add your secrets under
**Streamlit Cloud → App settings → Secrets**.

---

## Safety & scope

This project is strictly defensive. It contains no offensive tooling and is
intended for protecting systems you own or are authorized to harden. See
[`SECURITY.md`](SECURITY.md).
