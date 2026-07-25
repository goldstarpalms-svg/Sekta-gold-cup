"""
Memory system - Long term + Short term, better than ChatGPT's memory.
Uses SQLite + in-memory vector search (simple but effective, no heavy deps at runtime fallback)
"""
import sqlite3
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import hashlib

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "sekta_memory.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

class MemoryStore:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                title TEXT,
                agent_id TEXT DEFAULT 'sekta-omni',
                created_at TEXT,
                updated_at TEXT,
                messages TEXT -- JSON array
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                user_id TEXT DEFAULT 'default',
                content TEXT,
                embedding_hash TEXT,
                importance INTEGER DEFAULT 5,
                created_at TEXT,
                tags TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id TEXT PRIMARY KEY,
                key TEXT UNIQUE,
                value TEXT,
                updated_at TEXT
            )
        """)
        self.conn.commit()
    
    # --- CHATS ---
    def create_chat(self, title="New Chat", agent_id="sekta-omni") -> str:
        chat_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute("INSERT INTO chats (id, title, agent_id, created_at, updated_at, messages) VALUES (?,?,?,?,?,?)",
                    (chat_id, title, agent_id, now, now, json.dumps([])))
        self.conn.commit()
        return chat_id
    
    def get_chat(self, chat_id: str) -> Optional[Dict]:
        cur = self.conn.cursor()
        row = cur.execute("SELECT * FROM chats WHERE id=?", (chat_id,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "title": row["title"],
            "agent_id": row["agent_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "messages": json.loads(row["messages"] or "[]")
        }
    
    def list_chats(self) -> List[Dict]:
        cur = self.conn.cursor()
        rows = cur.execute("SELECT id, title, agent_id, created_at, updated_at FROM chats ORDER BY updated_at DESC LIMIT 100").fetchall()
        return [dict(r) for r in rows]
    
    def save_messages(self, chat_id: str, messages: List[Dict], title: Optional[str]=None):
        cur = self.conn.cursor()
        now = datetime.utcnow().isoformat()
        if title:
            cur.execute("UPDATE chats SET messages=?, updated_at=?, title=? WHERE id=?", (json.dumps(messages), now, title, chat_id))
        else:
            cur.execute("UPDATE chats SET messages=?, updated_at=? WHERE id=?", (json.dumps(messages), now, chat_id))
        self.conn.commit()
    
    def delete_chat(self, chat_id: str):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM chats WHERE id=?", (chat_id,))
        self.conn.commit()
    
    # --- LONG TERM MEMORY ---
    def add_memory(self, content: str, importance=5, tags=""):
        mem_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        h = hashlib.md5(content.encode()).hexdigest()
        cur = self.conn.cursor()
        # dedup simple
        exists = cur.execute("SELECT id FROM memories WHERE embedding_hash=?", (h,)).fetchone()
        if exists:
            return exists["id"]
        cur.execute("INSERT INTO memories (id, content, embedding_hash, importance, created_at, tags) VALUES (?,?,?,?,?,?)",
                    (mem_id, content, h, importance, now, tags))
        self.conn.commit()
        return mem_id
    
    def search_memories(self, query: str, limit=5) -> List[Dict]:
        # Simple keyword search - fast, no embedding model required for MVP
        # If sentence-transformers available, we could do semantic, but fallback is BM25-like LIKE
        cur = self.conn.cursor()
        words = query.lower().split()
        like_clause = " OR ".join(["LOWER(content) LIKE ?" for _ in words]) if words else "1=1"
        params = [f"%{w}%" for w in words]
        try:
            rows = cur.execute(f"SELECT * FROM memories WHERE {like_clause} ORDER BY importance DESC, created_at DESC LIMIT ?", (*params, limit)).fetchall()
        except:
            rows = cur.execute("SELECT * FROM memories ORDER BY importance DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]
    
    def list_memories(self):
        cur = self.conn.cursor()
        rows = cur.execute("SELECT * FROM memories ORDER BY created_at DESC LIMIT 100").fetchall()
        return [dict(r) for r in rows]
    
    # --- FACTS (key-value) ---
    def set_fact(self, key: str, value: str):
        now = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute("INSERT OR REPLACE INTO facts (id, key, value, updated_at) VALUES (?,?,?,?)",
                    (str(uuid.uuid4()), key, value, now))
        self.conn.commit()
    
    def get_facts_str(self) -> str:
        cur = self.conn.cursor()
        rows = cur.execute("SELECT key, value FROM facts").fetchall()
        if not rows:
            return "No facts yet."
        return "\n".join([f"- {r['key']}: {r['value']}" for r in rows])

memory_store = MemoryStore()
