"""
SEKTA GOLD - Cyber Shield
=========================

A defensive security operations dashboard. DEFENSIVE USE ONLY - no offensive
tooling, scanning, exploitation, or attack capability is included or intended.

What it does (each is a standard blue-team control):
  * Slack alerting              - central notifier used by the other tools
  * Honeypot canary generator   - decoy files + a monitor script that alerts
                                  on access (host-side, you deploy it)
  * IP geolocation & threat map - enrich attacker IPs via ipapi.co
  * Fail2Ban config generator   - build jail + filter rules from log patterns
  * Cloudflare WAF rule builder - compose firewall expressions
  * File integrity monitor      - SHA-256 baselines + change detection
  * Encrypted backup generator  - tar + gpg backup script with retention
  * auth.log analyzer           - detect brute-force SSH attempts
  * AI security advisor         - LLM explains threats + recommends defensive
                                  actions (reads your dashboard context)
  * AI assistant                - general-purpose technical chat via Groq /
                                  Gemini / OpenAI (OpenAI-compatible API)

Design notes:
  * The Streamlit app is a GENERATOR + DASHBOARD. It never runs subprocess
    commands on the host. Scripts it produces are plain text that you read,
    review, and deploy on your own server.
  * Secrets (Slack webhook URL, ipapi key) are read from
    st.secrets / environment variables, never hardcoded, and masked in the UI.
"""

import os
import re
import io
import json
import time
import base64
import hashlib
import zipfile
from datetime import datetime, timezone
from collections import Counter, defaultdict

import pandas as pd
import streamlit as st

try:
    import httpx  # already in requirements.txt
    _HAS_HTTPX = True
except Exception:  # pragma: no cover - optional fallback
    _HAS_HTTPX = False

try:
    import plotly.express as px  # already in requirements.txt
    _HAS_PLOTLY = True
except Exception:  # pragma: no cover
    _HAS_PLOTLY = False


# --------------------------------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Sekta Gold - Cyber Shield",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif; }
.stApp { background: #0A0A0B; color: #E5E5E5; }
[data-testid="stSidebar"] { background: #0A0A0B; border-right: 1px solid #1f1f22; }
[data-testid="stHeader"] { background: rgba(10,10,11,0.85); backdrop-filter: blur(12px); }
h1, h2, h3 { color: #fff; letter-spacing: -0.02em; }
.kicker { color: #FFC700; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; font-size: 12px; }
.card { background: #141415; border: 1px solid #1f1f22; border-radius: 14px; padding: 18px; }
.mono { font-family: 'JetBrains Mono', monospace; }
code, pre { font-family: 'JetBrains Mono', monospace !important; }
.stButton > button { border-radius: 10px; font-weight: 500; }
a { color: #FFC700 !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stStatusWidget"] { display: none; }
.tag-ok    { color: #34d399; font-weight: 600; }
.tag-warn  { color: #fbbf24; font-weight: 600; }
.tag-bad   { color: #f87171; font-weight: 600; }
.defensive-banner { background: #14201a; border: 1px solid #1f3a2b; border-radius: 10px; padding: 10px 14px; color: #86efac; font-size: 13px; }
</style>
""",
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# SHARED UTILITIES
# --------------------------------------------------------------------------
def load_secret(name: str, default=None):
    """Read a secret from Streamlit secrets first, then environment."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)


def mask_secret(value: str, keep: int = 10) -> str:
    """Partially mask a secret for safe display."""
    if not value:
        return "(not set)"
    if len(value) <= keep:
        return "*" * len(value)
    return value[:keep] + "…" + "*" * 6


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def download_text(filename: str, text: str, label: str = "Download"):
    """Render a download button for a text payload."""
    st.download_button(
        label=label,
        data=text.encode("utf-8"),
        file_name=filename,
        mime="text/plain",
    )


def send_slack(message: str, webhook: str | None = None) -> tuple[bool, str]:
    """POST a message to a Slack incoming webhook. Returns (ok, detail).

    Purely outbound notification - no inbound capability.
    """
    webhook = webhook or load_secret("SLACK_WEBHOOK_URL")
    if not webhook:
        return False, "No Slack webhook configured. Set SLACK_WEBHOOK_URL in Streamlit secrets or .env."
    if not webhook.startswith("https://hooks.slack.com/"):
        return False, "Refusing to send: webhook does not look like a Slack incoming webhook URL."
    if not _HAS_HTTPX:
        return False, "httpx is not installed (add it to requirements.txt)."
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(webhook, json={"text": message})
        if r.status_code == 200 and r.text.strip() == "ok":
            return True, "Delivered to Slack."
        return False, f"Slack responded HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:  # noqa: BLE001
        return False, f"Request failed: {e}"


def geolocate_ip(ip: str, api_key: str | None = None) -> dict | None:
    """Look up one IP via ipapi.co. Returns parsed dict or None on failure."""
    ip = (ip or "").strip()
    if not ip:
        return None
    url = f"https://ipapi.co/{ip}/json/"
    params = {}
    if api_key:
        params["key"] = api_key
    if not _HAS_HTTPX:
        return None
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.get(url, params=params)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get("error"):
            return None
        return data
    except Exception:  # noqa: BLE001
        return None


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def kv_card(label: str, value, sub: str = ""):
    st.markdown(
        f"""<div class="card"><div class="kicker">{label}</div>
        <div style="font-size:26px;font-weight:700;color:#fff;margin-top:4px">{value}</div>
        <div style="color:#9ca3af;font-size:12px;margin-top:2px">{sub}</div></div>""",
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# AI PROVIDERS (OpenAI-compatible /chat/completions: Groq, Gemini, OpenAI)
# --------------------------------------------------------------------------
AI_PROVIDERS = {
    "Groq (Free)": {
        "icon": "⚡", "env_key": "GROQ_API_KEY", "signup": "console.groq.com/keys",
        "base_url": "https://api.groq.com/openai/v1",
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
        "default_model": "llama-3.3-70b-versatile",
    },
    "Gemini (Free)": {
        "icon": "💎", "env_key": "GEMINI_API_KEY", "signup": "aistudio.google.com/apikey",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "models": ["gemini-2.0-flash", "gemini-2.0-flash-lite"],
        "default_model": "gemini-2.0-flash",
    },
    "OpenAI": {
        "icon": "🧠", "env_key": "OPENAI_API_KEY", "signup": "platform.openai.com/api-keys",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini"],
        "default_model": "gpt-4o-mini",
    },
}


def ai_key_ok(provider_name: str) -> bool:
    return bool(load_secret(AI_PROVIDERS[provider_name]["env_key"]))


def ai_picker():
    """Render provider + model selectors. Returns (provider_name, model)."""
    cols = st.columns([1, 1])
    with cols[0]:
        provider_name = st.selectbox(
            "Model provider", list(AI_PROVIDERS.keys()),
            format_func=lambda n: f"{AI_PROVIDERS[n]['icon']} {n}", key="ai_provider",
        )
    prov = AI_PROVIDERS[provider_name]
    with cols[1]:
        model = st.selectbox("Model", prov["models"], key=f"ai_model_{provider_name}")
    if not ai_key_ok(provider_name):
        st.warning(
            f"No `{prov['env_key']}` set. Get a free key at **{prov['signup']}**, add it to "
            f"`.streamlit/secrets.toml` (or env), then reload."
        )
    return provider_name, model


def stream_chat(messages, provider_name: str, model: str, temperature: float = 0.4):
    """Stream an OpenAI-compatible chat completion. Yields text deltas.

    Works identically across Groq, Gemini (OpenAI-compat), and OpenAI.
    """
    prov = AI_PROVIDERS[provider_name]
    api_key = load_secret(prov["env_key"])
    if not api_key:
        yield "⚠️ No API key configured for this provider. Set it in Streamlit secrets."
        return
    if not _HAS_HTTPX:
        yield "⚠️ httpx is not installed (it's in requirements.txt)."
        return
    url = prov["base_url"].rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "stream": True, "temperature": temperature}
    try:
        with httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
            with client.stream("POST", url, headers=headers, json=payload) as r:
                if r.status_code != 200:
                    body = r.read().decode("utf-8", "ignore")[:400]
                    yield f"⚠️ API error HTTP {r.status_code}: {body}"
                    return
                for line in r.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        delta = json.loads(data)["choices"][0]["delta"].get("content")
                        if delta:
                            yield delta
                    except Exception:  # noqa: BLE001 - skip malformed keepalive chunks
                        continue
    except Exception as e:  # noqa: BLE001
        yield f"⚠️ Request failed: {e}"


# --------------------------------------------------------------------------
# SECTIONS
# --------------------------------------------------------------------------
def header(title: str, subtitle: str):
    st.markdown(f'<div class="kicker">🛡️ Sekta Gold · Cyber Shield</div>', unsafe_allow_html=True)
    st.markdown(f"## {title}")
    st.caption(subtitle)


def section_overview():
    header("Operations Overview", "Status of integrations and quick navigation.")

    slack_on = bool(load_secret("SLACK_WEBHOOK_URL"))
    ipapi_key = bool(load_secret("IPAPI_KEY"))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kv_card("Slack Alerting", "ON" if slack_on else "OFF", mask_secret(load_secret("SLACK_WEBHOOK_URL")))
    with c2:
        kv_card("ipapi.co Key", "SET" if ipapi_key else "FREE TIER", "Geolocation enrichment")
    with c3:
        kv_card("Mode", "Defensive", "No offensive capability")
    with c4:
        kv_card("Local Time", utcnow().split(" ")[1], "UTC")

    st.markdown('<div class="defensive-banner">🟢 <b>Defensive-only.</b> This dashboard generates detection, alerting, and hardening artifacts. It performs no scanning, exploitation, or attack against any system.</div>', unsafe_allow_html=True)

    st.markdown("### What each tool does")
    rows = [
        ("Slack Alerts", "Central notifier - test and verify your webhook before relying on it."),
        ("Honeypot Canaries", "Generate decoy files + a host monitor script that alerts Slack when touched."),
        ("IP Geolocation", "Enrich attacker IPs with city/country/ASN and plot them on a world map."),
        ("Fail2Ban Builder", "Generate jail.local + filter regex from a sample log line."),
        ("Cloudflare WAF", "Compose firewall expressions (block by IP/ASN/country/path)."),
        ("File Integrity", "SHA-256 baselines and change detection for important files."),
        ("Encrypted Backup", "Generate a tar + gpg backup script with retention policy."),
        ("auth.log Analyzer", "Detect brute-force SSH patterns and rank offending IPs."),
        ("AI Security Advisor", "LLM explains threats + recommends defensive actions from your dashboard data."),
        ("AI Assistant", "General-purpose technical chat — Groq, Gemini, or OpenAI."),
    ]
    st.table(pd.DataFrame(rows, columns=["Tool", "Purpose"]))


def section_alerts():
    header("Slack Alerting", "Central notifier used by the other tools. Test it here.")

    webhook = load_secret("SLACK_WEBHOOK_URL")
    st.markdown(f"**Configured webhook:** `{mask_secret(webhook)}`")
    if not webhook:
        st.info("No webhook set. Add `SLACK_WEBHOOK_URL` to `.streamlit/secrets.toml` (recommended) or `.env`, then reload. Create one at https://api.slack.com/messaging/webhooks")

    with st.form("slack_test"):
        msg = st.text_area("Message", value=f"🛡️ Cyber Shield test ping at {utcnow()}", height=80)
        col_a, col_b = st.columns([1, 3])
        with col_a:
            override = st.text_input("Override webhook (optional)", type="password", placeholder="https://hooks.slack.com/services/...")
        submitted = st.form_submit_button("Send test alert", type="primary")

    if submitted:
        with st.spinner("Sending…"):
            ok, detail = send_slack(msg, webhook=override or None)
        if ok:
            st.success(detail)
        else:
            st.error(detail)


def section_honeypot():
    header("Honeypot Canaries", "Decoy files that look tempting but are useless, plus a monitor that alerts Slack when touched.")

    st.markdown("Canaries are deployed on YOUR server. The monitor uses `inotifywait` to watch for access and fires a Slack alert. Generated canaries contain clearly-fake tokens so they're worthless if exfiltrated.")

    presets = {
        "aws_keys.txt": "# AWS CLI credentials (DECOY)\n[default]\naws_access_key_id = AKIAFAKECANARY000001\naws_secret_access_key = CANARY-please-report-this-access-0001\nregion = us-east-1\n",
        ".env.prod": "# Production environment (DECOY)\nDATABASE_URL=postgres://canary:NOT-REAL-PASSWORD@db.internal:5432/prod\nSTRIPE_SECRET_KEY=sk_live_CANARY_FAKE_0001\nADMIN_TOKEN=canary-token-do-not-use\n",
        "id_rsa": "-----BEGIN OPENSSH PRIVATE KEY-----\nDECOY CANARY KEY - REPORT ACCESS TO SECURITY - NOT A REAL KEY\n-----END OPENSSH PRIVATE KEY-----\n",
        "backup.sql.header": "-- MySQL dump (DECOY) -- canary file, report access\n",
    }

    chosen = st.multiselect("Canary files to generate", list(presets.keys()), default=list(presets.keys())[:2])
    deploy_dir = st.text_input("Deploy directory on your server", value="/opt/canary")

    webhook = load_secret("SLACK_WEBHOOK_URL")
    if not webhook:
        st.warning("No Slack webhook configured. The monitor script will still be generated, but alerts will fail until SLACK_WEBHOOK_URL is set.")

    # The monitor script - host-side, text only. Never executed by this app.
    monitor = f"""#!/usr/bin/env bash
# Canary honeypot monitor - DEPLOY ON YOUR SERVER.
# Requires: inotify-tools (apt-get install inotify-tools), curl.
# Alerts Slack whenever a canary file is read/opened.
set -u
CANARY_DIR="{deploy_dir}"
WEBHOOK="${{SLACK_WEBHOOK_URL:-{webhook or 'PUT_YOUR_SLACK_WEBHOOK_HERE'}}}"
HOST="$(hostname -s 2>/dev/null || echo host)"

[ -d "$CANARY_DIR" ] || {{ echo "Missing $CANARY_DIR" >&2; exit 1; }}
command -v inotifywait >/dev/null || {{ echo "Install inotify-tools" >&2; exit 1; }}

echo "Watching $CANARY_DIR for access…"
inotifywait -m -r -e open,access --format '%w%f %e %T' --timefmt '%H:%M:%S' "$CANARY_DIR" |
while read -r file events ts; do
  msg="🚨 CANARY TRIPPED on *$HOST* at $ts UTC\\nFile: \\\`$file\\\`\\nEvent: $events\\nLikely unauthorized access."
  curl -s -X POST -H 'Content-type: application/json' \\
    --data "$(printf '{{"text":"%s"}}' "$msg")" "$WEBHOOK" >/dev/null
  logger -t canary "tripped: $file $events"
done
"""

    st.markdown("#### Generated canary files")
    for name in chosen:
        with st.expander(name):
            st.code(presets[name], language="text")

    st.markdown("#### Monitor script (`canary-watch.sh`)")
    st.code(monitor, language="bash")

    # Bundle everything into a zip for easy download
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in chosen:
            z.writestr(f"canary/{name}", presets[name])
        z.writestr("canary/canary-watch.sh", monitor)
        z.writestr("canary/README.txt", "Canary honeypot pack generated by Sekta Gold Cyber Shield.\nDeploy the canary/ directory to your server and run canary-watch.sh.\nThese files are DECOYS containing fake tokens.\n")
    buf.seek(0)
    st.download_button("⬇️ Download canary pack (.zip)", buf, file_name="cyber_shield_canary_pack.zip", mime="application/zip")

    st.caption("Deploy tip: place canaries where an attacker who got in would naturally poke around (home dirs, /var/backups, app roots). Make permissions look real.")


def section_geo():
    header("IP Geolocation & Threat Map", "Enrich attacker IPs via ipapi.co and plot them on a world map.")
    st.caption("Free tier: ~30k requests/month. Leave the API key blank to use the free tier, or set IPAPI_KEY for higher limits.")

    ips_raw = st.text_area("IPs (one per line, or comma-separated)", height=120, placeholder="203.0.113.5\n198.51.100.10")
    ips = [x.strip() for x in re.split(r"[\n,]+", ips_raw) if x.strip()]
    api_key = load_secret("IPAPI_KEY")

    if st.button("Geolocate", type="primary", disabled=not ips):
        rows = []
        bar = st.progress(0.0, text="Looking up IPs…")
        for i, ip in enumerate(ips):
            data = geolocate_ip(ip, api_key=api_key)
            if data:
                rows.append({
                    "IP": ip,
                    "Country": data.get("country_name", "?"),
                    "Region": data.get("region", "?"),
                    "City": data.get("city", "?"),
                    "Org/ISP": data.get("org", "?"),
                    "ASN": data.get("asn", "?"),
                    "Lat": data.get("latitude"),
                    "Lon": data.get("longitude"),
                })
            else:
                rows.append({"IP": ip, "Country": "(lookup failed)", "Region": "?", "City": "?", "Org/ISP": "?", "ASN": "?", "Lat": None, "Lon": None})
            time.sleep(1.0)  # respect free-tier rate guidance
            bar.progress((i + 1) / len(ips))
        bar.empty()

        if not rows:
            st.warning("No results.")
            return

        st.session_state["geo_rows"] = rows

    rows = st.session_state.get("geo_rows")
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df.drop(columns=["Lat", "Lon"]), use_container_width=True, hide_index=True)
        if _HAS_PLOTLY:
            geo_df = df.dropna(subset=["Lat", "Lon"])
            if not geo_df.empty:
                fig = px.scatter_geo(
                    geo_df, lat="Lat", lon="Lon", hover_name="IP",
                    hover_data=["Country", "City", "Org/ISP"],
                    projection="natural earth", color_discrete_sequence=["#FFC700"],
                )
                fig.update_layout(
                    paper_bgcolor="#0A0A0B", geo=dict(bgcolor="#0A0A0B", showland=True, landcolor="#141415",
                    countrycolor="#27272a", lakecolor="#0A0A0B"),
                    margin=dict(l=0, r=0, t=0, b=0), height=460,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No plottable coordinates.")


def section_fail2ban():
    header("Fail2Ban Config Generator", "Build a jail + filter from a sample log line. Deploy on your server.")
    sample = st.text_input("Sample offending log line", value="Failed password for invalid user admin from 203.0.113.5 port 51022 ssh2")
    findtime = st.number_input("findtime (seconds)", value=600, step=60)
    maxretry = st.number_input("maxretry", value=5, min_value=1)
    bantime = st.number_input("bantime (seconds)", value=3600, step=300)

    # Heuristic regex builder from the sample - extract the IP via common pattern.
    # This only *generates* a filter; it does not inspect any system.
    ip_guess = re.search(r"\bfrom (\d{1,3}(?:\.\d{1,3}){3})\b", sample)
    base = sample
    if ip_guess:
        base = sample.replace(ip_guess.group(1), "<HOST>")
    base = re.escape(base).replace(re.escape("<HOST>"), "<HOST>")

    filt = f"""# /etc/fail2ban/filter.d/cybershield.conf
[INCLUDES]
before = common.conf

[Definition]
failregex = ^.*{base}.*$
ignoreregex =

# Generated by Sekta Gold Cyber Shield. Review before deploying.
"""

    jail = f"""# /etc/fail2ban/jail.local
[cybershield]
enabled  = true
filter   = cybershield
logpath  = /var/log/auth.log
backend  = systemd
port     = ssh
maxretry = {maxretry}
findtime = {findtime}
bantime  = {bantime}
action   = %(action_)s
"""

    st.markdown("#### Filter (`cybershield.conf`)")
    st.code(filt, language="ini")
    download_text("cybershield.conf", filt, "⬇️ Download filter")

    st.markdown("#### Jail (`jail.local` excerpt)")
    st.code(jail, language="ini")
    download_text("jail.local", jail, "⬇️ Download jail")

    st.caption("Tip: test with `fail2ban-regex /var/log/auth.log /etc/fail2ban/filter.d/cybershield.conf` before enabling.")


def section_waf():
    header("Cloudflare WAF Rule Builder", "Compose custom firewall expressions. Paste into Cloudflare > Security > WAF > Custom rules.")
    mode = st.radio("Build mode", ["Block by IP list", "Block by ASN", "Block by country", "Block by path pattern"])
    expr = ""
    if mode == "Block by IP list":
        ips = st.text_area("IPs (CIDR allowed, one per line)", placeholder="203.0.113.5\n198.51.100.0/24")
        parts = [f'(ip.src eq "{x.strip()}")' for x in ips.splitlines() if x.strip()]
        expr = " or ".join(parts)
    elif mode == "Block by ASN":
        asns = st.text_input("ASNs (comma separated)", placeholder="AS12345, AS67890")
        parts = [f'(ip.geoip.asnum eq {int(re.sub(r"[^0-9]", "", a))})' for a in asns.split(",") if re.sub(r"[^0-9]", "", a)]
        expr = " or ".join(parts)
    elif mode == "Block by country":
        cc = st.text_input("Country codes (comma separated)", placeholder="CN, RU")
        parts = [f'(ip.geoip.country eq "{a.strip().upper()}")' for a in cc.split(",") if a.strip()]
        expr = " or ".join(parts)
    elif mode == "Block by path pattern":
        pat = st.text_input("Path pattern (matches.lookup against raw URI)", placeholder="/.env")
        pat_safe = pat.replace('"', '\\"')
        expr = f'(http.request.uri.path contains "{pat_safe}")'

    action = st.selectbox("Action", ["Block", "Challenge", "Managed Challenge", "JS Challenge", "Log"])
    if expr:
        st.markdown("#### Expression")
        st.code(expr, language="sql")
        st.markdown(f"**Action:** `{action}`  — set this in the rule's 'Then take action' dropdown.")
        st.caption("Review against Cloudflare's expression reference before deploying.")


def section_fim():
    header("File Integrity Monitor", "SHA-256 baselines and change detection.")
    mode = st.radio("Mode", ["Build baseline", "Compare against baseline"], horizontal=True)

    if mode == "Build baseline":
        files = st.file_uploader("Upload files to baseline", accept_multiple_files=True)
        if files:
            baseline = {}
            for f in files:
                data = f.read()
                baseline[f.name] = {
                    "sha256": sha256_bytes(data),
                    "size": len(data),
                    "baseline_at": utcnow(),
                }
            blob = json.dumps(baseline, indent=2)
            st.code(blob, language="json")
            download_text("baseline.json", blob, "⬇️ Download baseline.json")
            st.caption("Store baseline.json securely (e.g., read-only or off-host). Re-run Compare with the same files to detect tampering.")
    else:
        baseline_file = st.file_uploader("Upload baseline.json", type=["json"])
        current_files = st.file_uploader("Upload current files to check", accept_multiple_files=True)
        if baseline_file and current_files:
            try:
                baseline = json.loads(baseline_file.read().decode("utf-8"))
            except Exception as e:  # noqa: BLE001
                st.error(f"Could not parse baseline.json: {e}")
                return
            findings = []
            for f in current_files:
                data = f.read()
                now_hash = sha256_bytes(data)
                rec = baseline.get(f.name)
                if rec is None:
                    findings.append((f.name, "NEW", "Not in baseline"))
                elif rec.get("sha256") == now_hash:
                    findings.append((f.name, "OK", "Matches baseline"))
                else:
                    findings.append((f.name, "CHANGED", f"Was {rec.get('sha256','?')[:12]}… now {now_hash[:12]}…"))
            missing = [n for n in baseline if n not in {f.name for f in current_files}]
            for n in missing:
                findings.append((n, "MISSING", "In baseline but not uploaded"))
            df = pd.DataFrame(findings, columns=["File", "Status", "Detail"])
            st.dataframe(df, use_container_width=True, hide_index=True)


def section_backup():
    header("Encrypted Backup Generator", "Generate a tar + gpg backup script with retention. Review and deploy on your server.")
    src = st.text_input("Directory to back up", value="/var/www")
    dest = st.text_input("Backup destination", value="/backups")
    keep = st.number_input("Retain last N backups", value=7, min_value=1)
    gpg_recipient = st.text_input("GPG recipient (-r), optional", placeholder="admin@example.com")

    enc = "gpg --batch --yes --symmetric"  # default symmetric passphrase
    if gpg_recipient.strip():
        enc = f"gpg --batch --yes --recipient {gpg_recipient.strip()} --encrypt"

    script = f"""#!/usr/bin/env bash
# Encrypted backup - DEPLOY ON YOUR SERVER. Requires tar + gpg.
set -euo pipefail
SRC="{src}"
DEST="{dest}"
KEEP={keep}
TS="$(date +%Y%m%d-%H%M%S)"
HOST="$(hostname -s)"

mkdir -p "$DEST"
OUT="$DEST/${{HOST}}-${{TS}}.tar.gz"
echo "Backing up $SRC -> $OUT"
tar -czf - -C "$(dirname "$SRC")" "$(basename "$SRC")" | {enc} > "$OUT.gpg"
chmod 600 "$OUT.gpg"
echo "Wrote $OUT.gpg"

# Retention: keep newest $KEEP encrypted backups
ls -1t "$DEST"/${{HOST}}-*.tar.gz.gpg 2>/dev/null | tail -n +$((KEEP + 1)) | while read -r old; do
  rm -f "$old"; echo "Pruned $old"
done
echo "Done."
"""
    st.code(script, language="bash")
    download_text("backup.sh", script, "⬇️ Download backup.sh")
    st.caption("Schedule with cron, e.g.: `0 3 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1`. Symmetric mode will prompt for a passphrase unless you supply it via gpg-agent or a passphrase file.")


SSH_FAIL_RE = re.compile(r"Failed password for (?:invalid user )?(?P<user>\S+) from (?P<ip>\d{1,3}(?:\.\d{1,3}){3})")
SSH_OK_RE = re.compile(r"Accepted (?:password|publickey) for (?P<user>\S+) from (?P<ip>\d{1,3}(?:\.\d{1,3}){3})")


def section_authlog():
    header("auth.log Analyzer", "Detect brute-force SSH attempts. Upload or paste your auth.log (client-side parse only).")
    src = st.radio("Source", ["Paste text", "Upload file"], horizontal=True)
    text = ""
    if src == "Paste text":
        text = st.text_area("auth.log contents", height=180, placeholder="Jan 1 12:00:00 host sshd[123]: Failed password for invalid user root from 203.0.113.5 port 51022 ssh2")
    else:
        up = st.file_uploader("Upload auth.log", type=["log", "txt", ""])
        if up:
            text = up.read().decode("utf-8", errors="ignore")

    if not text.strip():
        st.info("Provide auth.log data to analyze.")
        return

    failed_by_ip = Counter()
    failed_by_user = Counter()
    ok_by_ip = Counter()
    for line in text.splitlines():
        m = SSH_FAIL_RE.search(line)
        if m:
            failed_by_ip[m.group("ip")] += 1
            failed_by_user[m.group("user")] += 1
            continue
        m2 = SSH_OK_RE.search(line)
        if m2:
            ok_by_ip[m2.group("ip")] += 1

    total_fail = sum(failed_by_ip.values())
    bf_threshold = st.slider("Brute-force threshold (failures/IP)", min_value=3, max_value=100, value=10)
    brute = {ip: n for ip, n in failed_by_ip.items() if n >= bf_threshold}
    st.session_state["bf_findings"] = brute  # consumed by the AI Security Advisor

    c1, c2, c3 = st.columns(3)
    c1.metric("Failed attempts", total_fail)
    c2.metric("Unique offending IPs", len(failed_by_ip))
    c3.metric("Likely brute-force IPs", len(brute))

    if failed_by_ip:
        st.markdown("### Top offending IPs")
        top = pd.DataFrame(failed_by_ip.most_common(20), columns=["IP", "Failed attempts"])
        st.dataframe(top, use_container_width=True, hide_index=True)

    if failed_by_user:
        st.markdown("### Targeted usernames")
        st.dataframe(pd.DataFrame(failed_by_user.most_common(15), columns=["Username", "Attempts"]), use_container_width=True, hide_index=True)

    if brute:
        st.markdown("### 🚩 Brute-force IPs (consider banning)")
        bf_df = pd.DataFrame(sorted(brute.items(), key=lambda x: -x[1]), columns=["IP", "Failed attempts"])
        st.dataframe(bf_df, use_container_width=True, hide_index=True)
        ips = "\n".join(bf_df["IP"].tolist())
        st.text_area("Copy these to IP Geolocation or Fail2Ban", ips, height=120)

        if st.button("🔔 Send top brute-force summary to Slack", type="primary"):
            webhook = load_secret("SLACK_WEBHOOK_URL")
            if not webhook:
                st.error("Set SLACK_WEBHOOK_URL to enable Slack alerts.")
            else:
                msg = f"🛡️ Cyber Shield: {len(brute)} brute-force IP(s) detected.\n" + "\n".join(
                    f"• {ip} ({n} fails)" for ip, n in sorted(brute.items(), key=lambda x: -x[1])[:15]
                )
                ok, detail = send_slack(msg)
                (st.success if ok else st.error)(detail)
    else:
        st.success("No IPs crossed the brute-force threshold.")


# --------------------------------------------------------------------------
# AI SECTIONS
# --------------------------------------------------------------------------
ASSISTANT_SYSTEM = (
    "You are Sekta, a highly capable technical assistant, strong across software engineering, "
    "data & analytics, security, cloud/infrastructure, research, and writing. Be concise, accurate, "
    "and practical; use code blocks where helpful. Refuse requests to build offensive/attack tooling "
    "and steer toward legitimate, defensive use."
)

SUGGESTIONS = [
    "Explain OAuth2 vs. session cookies",
    "Write Python to dedupe a list of dicts by a key",
    "How do I harden an SSH server?",
    "Explain this regex: ^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$",
]


def section_ai_assistant():
    header("AI Assistant", "General-purpose technical assistant — Groq, Gemini, or OpenAI.")
    provider_name, model = ai_picker()

    if "ai_messages" not in st.session_state:
        st.session_state["ai_messages"] = []

    tcol1, tcol2 = st.columns([1, 5])
    with tcol1:
        if st.button("🗑️ Clear chat", use_container_width=True):
            st.session_state["ai_messages"] = []
            st.rerun()
    with tcol2:
        st.caption(f"Provider: **{AI_PROVIDERS[provider_name]['icon']} {provider_name}** · Model: `{model}`")

    for m in st.session_state["ai_messages"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Empty-state suggestion chips
    if not st.session_state["ai_messages"]:
        for i, s in enumerate(SUGGESTIONS):
            if st.button(s, key=f"sug_{i}"):
                st.session_state["pending_prompt"] = s
                st.rerun()

    prompt = st.chat_input("Ask anything — code, debug, explain, plan, analyze…") or \
        st.session_state.pop("pending_prompt", None)

    if prompt:
        st.session_state["ai_messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            history = st.session_state["ai_messages"][-20:]
            msgs = [{"role": "system", "content": ASSISTANT_SYSTEM}] + \
                [{"role": m["role"], "content": m["content"]} for m in history]
            placeholder = st.empty()
            collected = []
            with st.spinner("Thinking…"):
                for delta in stream_chat(msgs, provider_name, model):
                    collected.append(delta)
                    placeholder.markdown("".join(collected))
            answer = "".join(collected)
            placeholder.markdown(answer or "_(no response)_")
        st.session_state["ai_messages"].append({"role": "assistant", "content": answer})


ADVISOR_SYSTEM = (
    "You are Sekta Shield, a defensive security analyst. Using the context provided, explain what is "
    "happening in plain English, assess severity, and recommend ONLY legitimate, DEFENSIVE actions "
    "(e.g., Fail2Ban bans, Cloudflare WAF rules, patching, hardening, monitoring, isolation). Refuse "
    "any request that would facilitate attacks, exploitation, or unauthorized access. Use short "
    "sections: **Summary**, **Risk**, **Recommended actions**."
)


def _advisor_context() -> str:
    parts = []
    bf = st.session_state.get("bf_findings")
    if bf:
        lines = [f"- {ip} — {n} failed logins" for ip, n in sorted(bf.items(), key=lambda x: -x[1])[:15]]
        parts.append("Brute-force IPs detected (auth.log Analyzer tab):\n" + "\n".join(lines))
    geo = st.session_state.get("geo_rows")
    if geo:
        lines = [f"- {r.get('IP')} — {r.get('Country')}, {r.get('City')}, {r.get('Org/ISP')}" for r in geo[:15]]
        parts.append("Geolocated IPs (IP Geolocation tab):\n" + "\n".join(lines))
    return ("\nContext pulled from this dashboard:\n" + "\n".join(parts) + "\n\n") if parts else ""


def section_ai_advisor():
    header("AI Security Advisor", "Plain-English threat analysis + defensive recommendations.")
    provider_name, model = ai_picker()

    ctx = _advisor_context()
    situation = st.text_area(
        "Describe the situation or paste logs (auth.log lines, IPs, alerts)…",
        value=ctx, height=170, key="advisor_input",
    )
    ready = bool(situation.strip()) and ai_key_ok(provider_name)
    if st.button("Analyze", type="primary", disabled=not ready):
        msgs = [{"role": "system", "content": ADVISOR_SYSTEM}, {"role": "user", "content": situation}]
        with st.chat_message("assistant"):
            placeholder = st.empty()
            out = []
            with st.spinner("Analyzing…"):
                for delta in stream_chat(msgs, provider_name, model, temperature=0.2):
                    out.append(delta)
                    placeholder.markdown("".join(out))
            placeholder.markdown("".join(out) or "_(no response)_")


# --------------------------------------------------------------------------
# NAV
# --------------------------------------------------------------------------
NAV = {
    "📊 Overview": section_overview,
    "🔔 Slack Alerts": section_alerts,
    "🍯 Honeypot Canaries": section_honeypot,
    "🤖 AI Security Advisor": section_ai_advisor,
    "🌍 IP Geolocation": section_geo,
    "🚫 Fail2Ban Builder": section_fail2ban,
    "☁️ Cloudflare WAF": section_waf,
    "🔍 File Integrity": section_fim,
    "💾 Encrypted Backup": section_backup,
    "📜 auth.log Analyzer": section_authlog,
    "💬 AI Assistant": section_ai_assistant,
}


def main():
    with st.sidebar:
        st.markdown("### 🛡️ Cyber Shield")
        st.caption("Defensive operations console")
        choice = st.radio("Tool", list(NAV.keys()), label_visibility="collapsed")
        st.divider()
        st.caption("Defensive-only · no offensive capability")
        st.caption(f"UTC {utcnow()}")
    NAV[choice]()


if __name__ == "__main__":
    main()
