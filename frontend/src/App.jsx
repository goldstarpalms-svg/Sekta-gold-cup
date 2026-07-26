import { useState, useEffect, useRef } from 'react'

const AGENTS_FALLBACK = [
  { id: 'sekta-omni', name: 'SEKTA GOLD OMNI', icon: '🏆', description: 'Ultimate - better than all bots combined' },
  { id: 'code-titan', name: 'CODE TITAN', icon: '💻', description: 'Senior engineer, builds anything' },
  { id: 'research-oracle', name: 'RESEARCH ORACLE', icon: '🔍', description: 'Deep research with citations' },
  { id: 'creative-god', name: 'CREATIVE GOD', icon: '🎨', description: 'Viral content & stunning visuals' },
  { id: 'data-wizard', name: 'DATA WIZARD', icon: '📊', description: 'CSV analysis & charts' },
  { id: 'study-buddy', name: 'STUDY BUDDY', icon: '📚', description: 'Teaches anything simply' },
  { id: 'business-shark', name: 'BUSINESS SHARK', icon: '🦈', description: 'Pitch & growth hacker' },
  { id: 'therapist-v2', name: 'THERAPIST V2', icon: '💛', description: 'Supportive listener' },
]

function MarkdownLite({ content }) {
  // Super lightweight markdown renderer without heavy deps for MVP
  // Handles **bold**, `code`, ```blocks```, [links], images, lists
  if (!content) return null
  
  const parts = []
  let lastIndex = 0
  const regex = /(```[\s\S]*?```|`[^`]+`|\*\*[^*]+\*\*|!\[.*?\]\(.*?\)|\[.*?\]\(.*?\)|\n)/g
  let match
  
  // For full rendering we use innerHTML with simple transforms (safe-ish for this app, content is AI)
  // Better: split by code blocks first
  const blockParts = content.split(/(```[\w]*\n[\s\S]*?```)/g)
  
  return (
    <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-p:my-2">
      {blockParts.map((block, bi) => {
        if (block.startsWith('```')) {
          const langMatch = block.match(/```(\w*)\n/)
          const lang = langMatch ? langMatch[1] : ''
          const code = block.replace(/```\w*\n/, '').replace(/```$/, '')
          
          // Check for artifact marker
          const isArtifact = lang === 'html' && code.includes('<') || lang === 'react' || block.includes('artifact')
          if (isArtifact) {
            return (
              <div key={bi} className="my-4 border border-[#FFC700]/30 rounded-xl overflow-hidden">
                <div className="bg-[#FFC700]/10 px-3 py-1.5 text-xs font-mono flex items-center justify-between">
                  <span>◼ ARTIFACT • LIVE PREVIEW</span>
                  <button onClick={() => navigator.clipboard.writeText(code)} className="text-[10px] opacity-70 hover:opacity-100">COPY</button>
                </div>
                <div className="bg-white p-0">
                  <iframe srcDoc={code} className="w-full h-[340px] border-0" sandbox="allow-scripts" />
                </div>
                <details className="bg-[#141415] px-3 py-2">
                  <summary className="text-xs text-zinc-400 cursor-pointer">Show code</summary>
                  <pre className="text-xs mt-2 overflow-auto bg-[#0A0A0B] p-3 rounded"><code>{code}</code></pre>
                </details>
              </div>
            )
          }
          
          return (
            <pre key={bi} className="bg-[#141415] border border-[#232325] rounded-lg p-3 overflow-auto my-3 text-[13px] font-mono">
              <div className="flex justify-between items-center mb-2 text-[11px] text-zinc-500">
                <span>{lang || 'code'}</span>
                <button onClick={() => navigator.clipboard.writeText(code)} className="hover:text-white">Copy</button>
              </div>
              <code>{code}</code>
            </pre>
          )
        } else {
          // Inline formatting
          let html = block
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
            .replace(/`([^`]+)`/g, '<code class="bg-[#1E1E20] px-1.5 py-0.5 rounded text-[13px] border border-[#232325]">$1</code>')
            .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="rounded-xl my-3 max-w-full border border-[#232325]" />')
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-[#FFC700] underline underline-offset-2">$1</a>')
            .replace(/\n- /g, '<br/>• ')
            .replace(/\n\d+\. /g, '<br/>• ')
            .replace(/\n/g, '<br/>')
          
          return <div key={bi} dangerouslySetInnerHTML={{ __html: html }} className="leading-relaxed" />
        }
      })}
    </div>
  )
}

export default function App() {
  const [agents, setAgents] = useState(AGENTS_FALLBACK)
  const [selectedAgent, setSelectedAgent] = useState(AGENTS_FALLBACK[0])
  const [chats, setChats] = useState([])
  const [currentChatId, setCurrentChatId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamContent, setStreamContent] = useState('')
  const [filesContext, setFilesContext] = useState('')
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [showCanvas, setShowCanvas] = useState(false)
  const [canvasContent, setCanvasContent] = useState('')
  const [toolStatus, setToolStatus] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)
  const textareaRef = useRef(null)
  
  // Load initial data
  useEffect(() => {
    fetch('/api/agents').then(r => r.json()).then(d => { if(Array.isArray(d) && d.length) setAgents(d) }).catch(()=>{})
    fetch('/api/chats').then(r => r.json()).then(setChats).catch(()=>{})
  }, [])
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamContent])
  
  const createNewChat = async () => {
    try {
      const res = await fetch(`/api/chats?title=New+Chat&agent_id=${selectedAgent.id}`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        const newChat = { id: data.chat_id, title: data.title || 'New Chat', agent_id: data.agent_id || selectedAgent.id, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }
        setChats(prev => [newChat, ...prev])
        setCurrentChatId(data.chat_id)
        setMessages([])
        return data.chat_id
      }
    } catch {}
    // fallback local only if backend unreachable
    const id = Date.now().toString(36)
    const newChat = { id, title: 'New Chat', agent_id: selectedAgent.id, created_at: new Date().toISOString(), updated_at: new Date().toISOString() }
    setChats(prev => [newChat, ...prev])
    setCurrentChatId(id)
    setMessages([])
    return id
  }
  
  const loadChat = async (chatId) => {
    setCurrentChatId(chatId)
    try {
      const res = await fetch(`/api/chats/${chatId}`)
      if (res.ok) {
        const data = await res.json()
        if (data.messages && data.messages.length > 0) {
          setMessages(data.messages)
        }
        const ag = agents.find(a => a.id === data.agent_id)
        if (ag) setSelectedAgent(ag)
      }
    } catch {
      // Chat may only exist locally, that's ok
    }
  }
  
  const handleFileUpload = async (e) => {
    const files = e.target.files
    if (!files.length) return
    setUploadedFiles([...files])
    setToolStatus('📎 Analyzing files...')
    const formData = new FormData()
    for (let f of files) formData.append('files', f)
    try {
      const res = await fetch('/api/files/analyze', { method: 'POST', body: formData })
      const data = await res.json()
      setFilesContext(data.files_context)
      setToolStatus(`✅ ${files.length} file(s) ready`)
      setTimeout(()=>setToolStatus(''), 2000)
    } catch (err) {
      setToolStatus('❌ File analyze failed')
    }
  }
  
  const handleSend = async () => {
    if (!input.trim() && !filesContext) return
    if (isStreaming) return
    
    let chatId = currentChatId
    if (!chatId) {
      chatId = await createNewChat()
    }
    
    const userMsg = { role: 'user', content: input, files: uploadedFiles.map(f=>f.name) }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setInput('')
    setIsStreaming(true)
    setStreamContent('')
    setToolStatus('✨ Thinking...')
    
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: newMessages.map(m => ({ role: m.role, content: m.content })),
          chat_id: chatId,
          agent_id: selectedAgent.id,
          stream: true,
          use_memory: true,
          use_web_search: true,
          files_context: filesContext
        })
      })
      
      if (!response.ok) {
        const err = await response.text()
        throw new Error(err)
      }
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let full = ''
      let buffer = ''
      let streamDone = false
      
      while (!streamDone) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (streamDone) break
          if (!line.startsWith('data: ')) continue
          const dataStr = line.slice(6)
          if (dataStr === '[DONE]') { streamDone = true; break }
          try {
            const data = JSON.parse(dataStr)
            if (data.type === 'content') {
              full += data.content
              setStreamContent(full)
            } else if (data.type === 'tool_start') {
              setToolStatus(`🔧 ${data.tool}: ${JSON.stringify(data.args).slice(0,60)}...`)
            } else if (data.type === 'tool_result') {
              setToolStatus(`✅ Done: ${data.tool}`)
              if (data.tool === 'generate_image' && data.result.includes('http')) {
                const urlMatch = data.result.match(/https:\/\/[^\s]+/)
                if (urlMatch) {
                  full += `\n\n![Generated](${urlMatch[0]})\n`
                  setStreamContent(full)
                }
              }
            } else if (data.type === 'error') {
              full += `\n\n**Error:** ${data.error}`
              setStreamContent(full)
            } else if (data.type === 'done') {
              // Use backend's final content only if we didn't accumulate anything
              if (!full && data.full_content) {
                full = data.full_content
              }
              setStreamContent(full)
            }
          } catch (e) {
            // ignore parse errors
          }
        }
      }
      
      // Save final
      if (full) {
        setMessages([...newMessages, { role: 'assistant', content: full }])
        // Update chat title from latest user message
        const firstUserMsg = newMessages.find(m => m.role === 'user')?.content || 'Chat'
        setChats(prev => prev.map(c => c.id === chatId ? { ...c, title: firstUserMsg.slice(0,40), updated_at: new Date().toISOString() } : c))
      }
      
    } catch (err) {
      setMessages([...newMessages, { role: 'assistant', content: `⚠️ Error: ${err.message}\n\nCheck your .env OPENAI_API_KEY. If you pasted a leaked key, revoke it first at platform.openai.com/api-keys and use a new one.` }])
    } finally {
      setIsStreaming(false)
      setStreamContent('')
      setToolStatus('')
      setFilesContext('')
      setUploadedFiles([])
    }
  }
  
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }
  
  return (
    <div className="flex h-screen bg-[#0A0A0B] text-white overflow-hidden">
      {/* SIDEBAR */}
      <div className="w-[300px] bg-[#0F0F10] border-r border-[#232325] flex flex-col hidden md:flex">
        <div className="p-4 border-b border-[#232325]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#FFC700] to-[#FF8A00] flex items-center justify-center text-black font-bold">S</div>
            <div>
              <div className="font-bold tracking-tight">SEKTA GOLD</div>
              <div className="text-[11px] text-[#8A8A90] -mt-1">ULTIMATE • v2.0</div>
            </div>
          </div>
          <button onClick={createNewChat} className="mt-4 w-full bg-white text-black rounded-lg py-2.5 text-sm font-semibold hover:bg-zinc-100 transition flex items-center justify-center gap-2">
            <span className="text-lg leading-none">+</span> New Chat
          </button>
        </div>
        
        <div className="p-3 flex-1 overflow-auto">
          <div className="text-[11px] font-mono text-[#8A8A90] uppercase tracking-widest mb-2 px-2">Agents • Choose Power</div>
          <div className="space-y-1.5 mb-6">
            {agents.map(agent => (
              <button key={agent.id} onClick={() => setSelectedAgent(agent)}
                className={`w-full text-left p-2.5 rounded-lg border transition flex gap-2.5 items-start ${selectedAgent.id === agent.id ? 'bg-[#FFC700]/10 border-[#FFC700]/30' : 'bg-[#141415] border-transparent hover:border-[#232325]'}`}>
                <span className="text-lg leading-none mt-0.5">{agent.icon}</span>
                <div className="min-w-0 flex-1">
                  <div className="text-[13px] font-semibold truncate">{agent.name}</div>
                  <div className="text-[11px] text-[#8A8A90] leading-tight truncate">{agent.description}</div>
                </div>
                {selectedAgent.id === agent.id && <div className="w-1.5 h-1.5 bg-[#FFC700] rounded-full mt-2 animate-pulse" />}
              </button>
            ))}
          </div>
          
          <div className="text-[11px] font-mono text-[#8A8A90] uppercase tracking-widest mb-2 px-2 flex items-center justify-between">
            <span>Chats</span>
            <span className="text-[10px] bg-[#1E1E20] px-1.5 py-0.5 rounded">{chats.length}</span>
          </div>
          <div className="space-y-1">
            {chats.map(chat => (
              <button key={chat.id} onClick={() => loadChat(chat.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-[13px] truncate border ${currentChatId === chat.id ? 'bg-[#1E1E20] border-[#333] text-white' : 'border-transparent text-zinc-400 hover:text-white hover:bg-[#141415]'}`}>
                <div className="truncate">{chat.title}</div>
                <div className="text-[10px] text-zinc-500">{new Date(chat.updated_at).toLocaleDateString()} • {chat.agent_id}</div>
              </button>
            ))}
            {chats.length === 0 && <div className="text-xs text-zinc-600 px-2 py-4 text-center">No chats yet. Start one →</div>}
          </div>
        </div>
        
        <div className="p-3 border-t border-[#232325] text-[11px] text-zinc-500">
          <div className="bg-[#141415] rounded-lg p-3 border border-[#232325]">
            <div className="text-[#FFC700] font-mono font-bold mb-1">🏆 GOLD STANDARD</div>
            <div className="leading-snug">Better than ChatGPT + Claude + Gemini + Perplexity. Streaming, tools, memory, vision, image gen, voice, files.</div>
            <div className="mt-2 text-[10px] text-zinc-600">⚠️ Revoke leaked key at platform.openai.com/api-keys</div>
          </div>
        </div>
      </div>
      
      {/* MAIN */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        {/* HEADER */}
        <div className="h-[56px] border-b border-[#232325] flex items-center justify-between px-4 bg-[#0A0A0B]/80 backdrop-blur">
          <div className="flex items-center gap-3">
            <div className="md:hidden w-8 h-8 rounded bg-gradient-to-br from-[#FFC700] to-[#FF8A00] flex items-center justify-center text-black font-bold">S</div>
            <div className="flex items-center gap-2">
              <span className="text-lg">{selectedAgent.icon}</span>
              <span className="font-semibold text-sm">{selectedAgent.name}</span>
              <span className="text-[11px] bg-[#1E1E20] border border-[#232325] px-2 py-0.5 rounded-full text-zinc-400">{selectedAgent.id}</span>
            </div>
            {toolStatus && <div className="ml-3 text-xs bg-[#FFC700]/10 border border-[#FFC700]/20 text-[#FFC700] px-2.5 py-1 rounded-full animate-pulse">{toolStatus}</div>}
          </div>
          <div className="flex items-center gap-2">
            <button onClick={()=>setShowCanvas(v=>!v)} className="text-xs bg-[#141415] border border-[#232325] px-3 py-1.5 rounded-full hover:bg-[#1E1E20]">Canvas {showCanvas ? '• ON' : ''}</button>
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.5)]" title="Backend online if green" />
          </div>
        </div>
        
        {/* MESSAGES */}
        <div className="flex-1 overflow-auto px-2 md:px-0">
          <div className="max-w-[760px] mx-auto w-full py-6">
            {messages.length === 0 && !isStreaming && (
              <div className="relative text-center py-16 md:py-20 overflow-hidden">
                {/* ambient glow backdrop */}
                <div className="pointer-events-none absolute inset-0 -z-10 flex items-start justify-center">
                  <div className="w-[560px] h-[560px] rounded-full bg-[#FFC700]/10 blur-[120px]" />
                </div>

                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#141415] border border-[#232325] text-[11px] font-mono text-[#FFC700] mb-6">
                  <span className="w-1.5 h-1.5 bg-[#FFC700] rounded-full animate-pulse" /> 8 SUPER AGENTS · ONE CHAT
                </div>

                <h1 className="text-[40px] md:text-[56px] leading-[1.05] font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white to-zinc-400">
                  Experience the
                </h1>
                <h1 className="text-[40px] md:text-[56px] leading-[1.05] font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-[#FFC700] via-[#FFE066] to-[#FF8A00] mt-0.5">
                  gold standard
                </h1>
                <p className="text-zinc-400 mt-4 text-[15px] max-w-[480px] mx-auto">
                  One box. Code, research, design, data, and more — powered by {selectedAgent.name.toLowerCase()} and 7 other specialists.
                </p>

                {/* Arena-style quick action chips */}
                <div className="flex flex-wrap items-center justify-center gap-2 mt-8 max-w-[680px] mx-auto">
                  {[
                    { icon: '🎨', label: 'Create a landing page', prompt: 'Create a sleek, modern landing page for my product with a hero section, features grid, and pricing', agent: 'creative-god' },
                    { icon: '📊', label: 'Build a dashboard', prompt: 'Turn this data into an interactive dashboard with charts', agent: 'data-wizard' },
                    { icon: '🕹️', label: 'Make a game', prompt: 'Build a simple playable browser game, single HTML file', agent: 'code-titan' },
                    { icon: '🔍', label: 'Research a topic', prompt: 'Do deep research on the latest AI trends this week, with sources', agent: 'research-oracle' },
                    { icon: '🧮', label: 'Analyze data', prompt: 'Analyze this CSV/PDF and summarize the key insights (drag & drop a file)', agent: 'data-wizard' },
                    { icon: '🦈', label: 'Write a pitch', prompt: 'Write an investor pitch for my startup idea', agent: 'business-shark' },
                  ].map((c, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        const ag = agents.find(a => a.id === c.agent)
                        if (ag) setSelectedAgent(ag)
                        setInput(c.prompt)
                        textareaRef.current?.focus()
                      }}
                      className="group flex items-center gap-1.5 px-3.5 py-2 rounded-full bg-[#141415] border border-[#232325] hover:border-[#FFC700]/40 hover:bg-[#1A1A1C] text-[13px] text-zinc-300 hover:text-white transition"
                    >
                      <span className="text-[14px]">{c.icon}</span> {c.label}
                    </button>
                  ))}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-6 text-left max-w-[560px] mx-auto">
                  {[
                    "Generate a luxury logo for Sekta Gold Cup, black & gold",
                    "Search latest AI news today with sources",
                    "Remember that my name is Alex and I love F1",
                    "Teach me quantum computing like I'm 10",
                  ].map((s,i)=>(
                    <button key={i} onClick={()=>{setInput(s); textareaRef.current?.focus()}} className="p-3 rounded-xl bg-[#101011] border border-[#1c1c1e] hover:border-[#333] text-[13px] text-zinc-400 hover:text-zinc-200 text-left transition">
                      <span className="text-[#FFC700] mr-1">→</span> {s}
                    </button>
                  ))}
                </div>

                <div className="mt-8 flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-[11px] text-zinc-600 font-mono">
                  <span>⚡ streaming</span><span>·</span><span>🌐 web search</span><span>·</span>
                  <span>🖼️ image gen</span><span>·</span><span>🧠 memory</span><span>·</span>
                  <span>👁️ vision</span><span>·</span><span>📎 files</span><span>·</span><span>🎙️ voice</span>
                </div>
              </div>
            )}
            
            <div className="space-y-6 px-4 md:px-2">
              {messages.map((m,i)=>(
                <div key={i} className={`flex gap-3 ${m.role==='user' ? 'justify-end' : 'justify-start'}`}>
                  {m.role !== 'user' && (
                    <div className="w-7 h-7 rounded-full bg-[#1E1E20] border border-[#232325] flex items-center justify-center text-[12px] shrink-0 mt-1">{selectedAgent.icon}</div>
                  )}
                  <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-[14px] ${m.role==='user' ? 'bg-white text-black rounded-br-md' : 'bg-[#141415] border border-[#232325] rounded-bl-md'}`}>
                    {m.role === 'user' ? (
                      <div className="whitespace-pre-wrap">{m.content}{m.files?.length ? <div className="mt-2 text-[11px] opacity-70">📎 {m.files.join(', ')}</div> : null}</div>
                    ) : (
                      <MarkdownLite content={m.content} />
                    )}
                  </div>
                </div>
              ))}
              
              {isStreaming && (
                <div className="flex gap-3">
                  <div className="w-7 h-7 rounded-full bg-[#1E1E20] border border-[#232325] flex items-center justify-center text-[12px] shrink-0 mt-1 animate-pulse">{selectedAgent.icon}</div>
                  <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-[#141415] border border-[#232325] rounded-bl-md min-h-[40px]">
                    {streamContent ? <MarkdownLite content={streamContent} /> : <div className="flex gap-1 py-1"><div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce"/><div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce [animation-delay:0.1s]"/><div className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce [animation-delay:0.2s]"/></div>}
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </div>
        </div>
        
        {/* INPUT */}
        <div className="p-3 md:p-4 bg-gradient-to-t from-[#0A0A0B] to-transparent">
          <div className="max-w-[760px] mx-auto">
            {uploadedFiles.length > 0 && (
              <div className="mb-2 flex flex-wrap gap-2">
                {uploadedFiles.map((f,i)=>(
                  <div key={i} className="text-[11px] bg-[#1E1E20] border border-[#232325] px-2.5 py-1 rounded-full flex items-center gap-1.5">
                    <span>📎</span>{f.name} <span className="opacity-50">{(f.size/1024).toFixed(0)}KB</span>
                  </div>
                ))}
                <button onClick={()=>{setUploadedFiles([]); setFilesContext('')}} className="text-[11px] text-zinc-500 hover:text-white">Clear</button>
              </div>
            )}
            <div className="relative bg-[#141415] border border-[#232325] rounded-2xl focus-within:border-[#FFC700]/30 transition flex items-end gap-2 p-2 shadow-[0_0_0_1px_rgba(255,255,255,0.02)]">
              <button onClick={()=>fileInputRef.current?.click()} className="w-9 h-9 rounded-xl bg-[#0A0A0B] border border-[#232325] flex items-center justify-center hover:bg-[#1E1E20] transition shrink-0">📎</button>
              <input ref={fileInputRef} type="file" multiple hidden onChange={handleFileUpload} accept=".pdf,.txt,.md,.docx,.csv,.xlsx,.png,.jpg,.jpeg,.webp,.py,.js,.json" />
              
              <textarea
                ref={textareaRef}
                value={input}
                onChange={e=>setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={`Message ${selectedAgent.name}... (Enter to send, Shift+Enter for new line) — try "generate image of..." or "search..."`}
                className="flex-1 bg-transparent resize-none outline-none text-[14px] max-h-[160px] min-h-[36px] py-2 placeholder:text-zinc-500"
                rows={1}
              />
              
              <button onClick={handleSend} disabled={isStreaming || (!input.trim() && !filesContext)} className="w-9 h-9 rounded-xl bg-white text-black flex items-center justify-center font-bold hover:bg-zinc-100 disabled:opacity-30 disabled:cursor-not-allowed shrink-0 transition">
                {isStreaming ? '◼' : '↑'}
              </button>
            </div>
            <div className="flex items-center justify-between mt-2 px-1">
              <div className="text-[11px] text-zinc-500 font-mono">SEKTA GOLD • {selectedAgent.id} • Streaming • Tools ON</div>
              <div className="text-[10px] text-zinc-600">⚠️ Revoke leaked key immediately</div>
            </div>
          </div>
        </div>
        
        {/* CANVAS */}
        {showCanvas && (
          <div className="absolute right-0 top-[56px] bottom-0 w-[420px] bg-[#0F0F10] border-l border-[#232325] hidden lg:flex flex-col">
            <div className="p-3 border-b border-[#232325] flex items-center justify-between">
              <div className="text-xs font-mono font-bold">CANVAS • LIVE ARTIFACT</div>
              <button onClick={()=>setShowCanvas(false)} className="text-xs text-zinc-500 hover:text-white">✕</button>
            </div>
            <div className="flex-1 overflow-auto p-3">
              {canvasContent ? (
                <iframe srcDoc={canvasContent} className="w-full h-full bg-white rounded-xl border-0" />
              ) : (
                <div className="text-center py-20 text-zinc-600 text-sm">
                  Canvas shows HTML/React artifacts from AI.<br/>Ask: "Build me a landing page"<br/>or code with artifact block.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
