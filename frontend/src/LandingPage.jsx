import { useEffect, useRef, useState } from 'react'

const AGENTS_SHOWCASE = [
  { id: 'sekta-omni', name: 'SEKTA OMNI', icon: '🏆', description: 'The ultimate generalist — better than all bots combined, picks the right tool for any job.' },
  { id: 'code-titan', name: 'CODE TITAN', icon: '💻', description: 'Senior-engineer level. Ships full apps, debugs gnarly code, explains as it goes.' },
  { id: 'research-oracle', name: 'RESEARCH ORACLE', icon: '🔍', description: 'Deep, cited research. Live web search built in — no stale answers.' },
  { id: 'creative-god', name: 'CREATIVE GOD', icon: '🎨', description: 'Viral copy, stunning visuals, brand voice that actually lands.' },
  { id: 'data-wizard', name: 'DATA WIZARD', icon: '📊', description: 'Drop a CSV or PDF, get charts, trends, and plain-English insight.' },
  { id: 'study-buddy', name: 'STUDY BUDDY', icon: '📚', description: 'Explains anything simply — from quantum physics to tax law.' },
  { id: 'business-shark', name: 'BUSINESS SHARK', icon: '🦈', description: 'Pitch decks, growth loops, and hard truths about your idea.' },
  { id: 'therapist-v2', name: 'THERAPIST V2', icon: '💛', description: 'A calm, supportive space to think out loud. No judgment.' },
]

const CAPABILITIES = [
  { icon: '⚡', label: 'Real-time streaming', desc: 'Tokens appear as they\u2019re generated — no waiting on a spinner.' },
  { icon: '🌐', label: 'Live web search', desc: 'Cited, up-to-date answers via Tavily, Wikipedia & DuckDuckGo.' },
  { icon: '🖼️', label: 'Image generation', desc: 'DALL·E 3 built in — logos, art, mockups, on demand.' },
  { icon: '🧠', label: 'Long-term memory', desc: 'Remembers who you are and what you care about, across chats.' },
  { icon: '👁️', label: 'Vision & files', desc: 'Understands screenshots, PDFs, spreadsheets, and Word docs.' },
  { icon: '🎙️', label: 'Voice in & out', desc: 'Whisper transcription and natural text-to-speech.' },
  { icon: '📎', label: 'File analysis', desc: 'CSV, XLSX, DOCX, PDF, images — parsed and understood instantly.' },
  { icon: '🧩', label: 'Live code canvas', desc: 'Preview HTML/React artifacts the AI builds, right in the sidebar.' },
]

const STATS = [
  { value: '8', label: 'Specialist agents' },
  { value: '5+', label: 'Native tool integrations' },
  { value: '0', label: 'Setup steps to start chatting' },
  { value: '24/7', label: 'Streaming availability' },
]

function Reveal({ children, className = '', delay = 0 }) {
  const ref = useRef(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            setVisible(true)
            obs.unobserve(e.target)
          }
        })
      },
      { threshold: 0.15 }
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  return (
    <div
      ref={ref}
      className={`transition-all duration-700 ease-out ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'} ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  )
}

export default function LandingPage({ onEnter }) {
  const [typed, setTyped] = useState('')
  const fullText = 'better than every chatbot you\u2019ve tried.'

  useEffect(() => {
    let i = 0
    const id = setInterval(() => {
      i++
      setTyped(fullText.slice(0, i))
      if (i >= fullText.length) clearInterval(id)
    }, 28)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="relative min-h-screen bg-[#0A0A0B] text-white overflow-x-hidden">
      {/* animated ambient blobs */}
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="blob blob-a" />
        <div className="blob blob-b" />
        <div className="blob blob-c" />
      </div>

      {/* NAV */}
      <nav className="sticky top-0 z-20 backdrop-blur-md bg-[#0A0A0B]/70 border-b border-[#1c1c1e]">
        <div className="max-w-[1100px] mx-auto flex items-center justify-between px-5 py-3.5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#FFC700] to-[#FF8A00] flex items-center justify-center text-black font-bold text-sm">S</div>
            <span className="font-bold tracking-tight text-[15px]">SEKTA GOLD</span>
            <span className="hidden sm:inline text-[10px] font-mono text-[#8A8A90] border border-[#232325] rounded-full px-2 py-0.5">v2.0</span>
          </div>
          <div className="flex items-center gap-3">
            <a href="#agents" className="hidden md:block text-[13px] text-zinc-400 hover:text-white transition">Agents</a>
            <a href="#capabilities" className="hidden md:block text-[13px] text-zinc-400 hover:text-white transition">Capabilities</a>
            <button onClick={onEnter} className="text-[13px] font-semibold bg-white text-black rounded-full px-4 py-1.5 hover:bg-zinc-100 transition">
              Launch App →
            </button>
          </div>
        </div>
      </nav>

      {/* HERO */}
      <section className="relative max-w-[900px] mx-auto text-center px-5 pt-20 pb-16">
        <Reveal>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#141415] border border-[#232325] text-[11px] font-mono text-[#FFC700] mb-7">
            <span className="w-1.5 h-1.5 bg-[#FFC700] rounded-full animate-pulse" /> 8 AGENTS · ONE GOLD STANDARD
          </div>
        </Reveal>
        <Reveal delay={80}>
          <h1 className="text-[42px] md:text-[64px] leading-[1.05] font-bold tracking-tight">
            <span className="bg-clip-text text-transparent bg-gradient-to-b from-white to-zinc-400">The AI chatbot</span>
            <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-[#FFC700] via-[#FFE066] to-[#FF8A00]">that does it all</span>
          </h1>
        </Reveal>
        <Reveal delay={160}>
          <p className="mt-6 text-zinc-400 text-[16px] md:text-[18px] max-w-[560px] mx-auto min-h-[28px]">
            {typed}<span className="animate-pulse">▍</span>
          </p>
        </Reveal>
        <Reveal delay={240}>
          <div className="mt-9 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button onClick={onEnter} className="w-full sm:w-auto px-7 py-3 rounded-full bg-gradient-to-r from-[#FFC700] to-[#FF8A00] text-black font-bold text-[15px] hover:brightness-105 transition shadow-[0_0_40px_rgba(255,199,0,0.25)]">
              Start Chatting Free
            </button>
            <a href="#agents" className="w-full sm:w-auto px-7 py-3 rounded-full border border-[#232325] text-[15px] text-zinc-300 hover:text-white hover:border-[#333] transition text-center">
              Meet the 8 agents
            </a>
          </div>
        </Reveal>

        {/* stats row */}
        <Reveal delay={320}>
          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-[720px] mx-auto">
            {STATS.map((s, i) => (
              <div key={i} className="rounded-2xl border border-[#1c1c1e] bg-[#101011] py-5">
                <div className="text-[26px] md:text-[30px] font-bold bg-clip-text text-transparent bg-gradient-to-r from-[#FFC700] to-[#FF8A00]">{s.value}</div>
                <div className="text-[11px] text-zinc-500 mt-1 font-mono uppercase tracking-wide">{s.label}</div>
              </div>
            ))}
          </div>
        </Reveal>
      </section>

      {/* AGENTS SHOWCASE */}
      <section id="agents" className="max-w-[1100px] mx-auto px-5 py-20">
        <Reveal className="text-center mb-12">
          <div className="text-[11px] font-mono text-[#FFC700] uppercase tracking-widest mb-3">Choose your power</div>
          <h2 className="text-[28px] md:text-[36px] font-bold tracking-tight">8 specialist agents, one chat window</h2>
          <p className="text-zinc-400 mt-3 max-w-[520px] mx-auto text-[14px]">Switch instantly — every agent shares your files, memory, and chat history.</p>
        </Reveal>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {AGENTS_SHOWCASE.map((a, i) => (
            <Reveal key={a.id} delay={i * 60}>
              <div className="group h-full rounded-2xl border border-[#1c1c1e] bg-[#101011] p-5 hover:border-[#FFC700]/30 hover:-translate-y-1 transition-all duration-300 hover:shadow-[0_10px_40px_rgba(255,199,0,0.08)]">
                <div className="text-[28px] mb-3 group-hover:scale-110 transition-transform">{a.icon}</div>
                <div className="font-semibold text-[13px] tracking-tight">{a.name}</div>
                <div className="text-[12px] text-zinc-500 mt-1.5 leading-relaxed">{a.description}</div>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* CAPABILITIES */}
      <section id="capabilities" className="max-w-[1100px] mx-auto px-5 py-20">
        <Reveal className="text-center mb-12">
          <div className="text-[11px] font-mono text-[#FFC700] uppercase tracking-widest mb-3">Under the hood</div>
          <h2 className="text-[28px] md:text-[36px] font-bold tracking-tight">Every superpower, built in</h2>
        </Reveal>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {CAPABILITIES.map((c, i) => (
            <Reveal key={i} delay={i * 50}>
              <div className="h-full rounded-2xl border border-[#1c1c1e] bg-gradient-to-b from-[#141415] to-[#0F0F10] p-5 hover:border-[#232325] transition">
                <div className="text-[24px] mb-3">{c.icon}</div>
                <div className="font-semibold text-[13px]">{c.label}</div>
                <div className="text-[12px] text-zinc-500 mt-1.5 leading-relaxed">{c.desc}</div>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* PROVIDER BADGES */}
      <section className="max-w-[1100px] mx-auto px-5 pb-16">
        <Reveal className="text-center">
          <div className="text-[11px] font-mono text-zinc-600 uppercase tracking-widest mb-4">Runs on your choice of model</div>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {['⚡ Groq', '💎 Gemini', '🧠 OpenAI', '🔍 Tavily'].map((p, i) => (
              <span key={i} className="px-4 py-2 rounded-full border border-[#1c1c1e] bg-[#101011] text-[13px] text-zinc-300">{p}</span>
            ))}
          </div>
        </Reveal>
      </section>

      {/* FINAL CTA */}
      <section className="relative max-w-[820px] mx-auto px-5 pb-24">
        <Reveal>
          <div className="relative rounded-3xl border border-[#232325] bg-gradient-to-br from-[#141415] to-[#0A0A0B] p-10 md:p-14 text-center overflow-hidden">
            <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full bg-[#FFC700]/10 blur-[80px]" />
            <h3 className="text-[26px] md:text-[34px] font-bold tracking-tight relative z-10">Ready to go gold?</h3>
            <p className="text-zinc-400 mt-3 text-[14px] relative z-10">No signup wall. No credit card. Just start typing.</p>
            <button onClick={onEnter} className="mt-7 px-8 py-3 rounded-full bg-white text-black font-bold text-[15px] hover:bg-zinc-100 transition relative z-10">
              Enter Sekta Gold →
            </button>
          </div>
        </Reveal>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-[#1c1c1e] py-8 text-center">
        <div className="text-[12px] text-zinc-600">🏆 Sekta Gold Cup · Built for demos, defensive tooling, and everyday work · {new Date().getFullYear()}</div>
      </footer>
    </div>
  )
}
