# 🔒 SECURITY NOTICE

## Your API Key Was Leaked!

You posted a key starting with: `sk-proj-4R35...YOrEA` (full key redacted for safety)
We detected leak and blocked it from git history.

This is a **SECRET**. Anyone with it can use your OpenAI account and charge you money.

### What To Do NOW (2 min):

1. Go to https://platform.openai.com/api-keys
2. Find key starting with `sk-proj-4R35...`
3. Click 🗑️ Delete / Revoke
4. Click "Create new secret key"
5. Copy new key
6. In this repo, do:
   ```
   cp .env.example .env
   nano .env   # paste new key
   ```

### What I Did:

- I did NOT save your leaked key anywhere in code or git
- I added detection in config.py that blocks that specific key prefix
- .env is gitignored
- Backend only reads key from env, never frontend

### Best Practices Going Forward:

- Never paste keys in chat, GitHub, email
- Use .env.example with placeholder
- Rotate keys every 90 days
- Set usage limits at https://platform.openai.com/account/limits

Stay gold, stay secure 🏆
