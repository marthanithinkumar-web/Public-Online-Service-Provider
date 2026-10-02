import React,{useEffect,useState} from 'react'
import {fetchAiOperationsOverview,chatWithAiOperations,runAiJobSync} from '../../services/admin'

type Message={role:'admin'|'ai';text:string}

export default function AiOperations(){
  const [overview,setOverview]=useState<any>(null)
  const [messages,setMessages]=useState<Message[]>([])
  const [input,setInput]=useState('')
  const [loading,setLoading]=useState(false)
  const [actionLoading,setActionLoading]=useState(false)
  const [error,setError]=useState('')

  async function refresh(){
    try{setError('');setOverview(await fetchAiOperationsOverview())}
    catch(e:any){setError(e?.response?.data?.error||'Could not load POSP AI operations.')}
  }
  useEffect(()=>{refresh()},[])

  async function ask(text=input){
    const message=text.trim()
    if(!message||loading)return
    setInput('')
    setMessages(prev=>[...prev,{role:'admin',text:message}])
    setLoading(true);setError('')
    try{
      const res=await chatWithAiOperations(message)
      if(res.answer)setMessages(prev=>[...prev,{role:'ai',text:res.answer}])
      else if(res.message)setMessages(prev=>[...prev,{role:'ai',text:res.message}])
    }catch(e:any){
      setError(e?.response?.data?.error||e?.response?.data?.message||'AI request failed.')
    }finally{setLoading(false)}
  }

  async function syncJobs(){
    if(actionLoading)return
    setActionLoading(true);setError('')
    try{
      const res=await runAiJobSync()
      setMessages(prev=>[...prev,{role:'ai',text:res.message||'Job synchronization completed.'}])
      await refresh()
    }catch(e:any){setError(e?.response?.data?.error||'Job synchronization failed.')}
    finally{setActionLoading(false)}
  }

  const sourceHealth=overview?.scholarships?.source_health||[]
  return <section className="admin-section">
    <div className="section-header">
      <div><span className="eyebrow">POSP AI</span><h2>AI Operations</h2><p>One place to understand jobs, scholarships, source health and runtime issues.</p></div>
      <button className="btn btn-secondary" onClick={refresh}>Refresh checks</button>
    </div>
    {error&&<div className="admin-alert">{error}</div>}

    <div className="admin-grid admin-grid-3">
      <article className="admin-card"><strong>Jobs</strong><p>Published: {overview?.jobs?.published ?? '—'}</p><p>Needs review: {overview?.jobs?.needs_review ?? '—'}</p><p>Expired: {overview?.jobs?.expired ?? '—'}</p></article>
      <article className="admin-card"><strong>Scholarships</strong><p>Active: {overview?.scholarships?.count ?? '—'}</p><p>Official: {overview?.scholarships?.official_count ?? '—'}</p><p>Stale sources: {overview?.scholarships?.stale_source_count ?? '—'}</p></article>
      <article className="admin-card"><strong>Runtime</strong><p>Database: {overview?.runtime?.database ? 'Healthy' : 'Unavailable'}</p><p>Checked: {overview?.checked_at ? new Date(overview.checked_at).toLocaleString() : '—'}</p></article>
    </div>

    <article className="admin-card" style={{marginTop:16}}>
      <div className="section-header"><div><strong>Scholarship source health</strong><p>Read-only view of the approved daily discovery sources.</p></div></div>
      <div style={{display:'grid',gap:8}}>
        {sourceHealth.length?sourceHealth.map((source:any)=><div key={source.key} style={{display:'flex',justifyContent:'space-between',gap:12,padding:'10px 12px',border:'1px solid var(--border-color,#ddd)',borderRadius:8}}>
          <span>{source.source_name}</span><span>{source.ok?'Healthy':'Needs attention'} · {source.count} found</span>
        </div>):<span>No scholarship source-health data is available yet.</span>}
      </div>
    </article>

    <article className="admin-card" style={{marginTop:16}}>
      <div className="section-header"><div><strong>AI health findings</strong><p>Read-only checks that tell you what needs attention before any change is made.</p></div></div>
      <div style={{display:'grid',gap:8}}>
        {(overview?.findings||[]).length===0?<div>✓ No current findings from the available operational checks.</div>:
          (overview?.findings||[]).map((finding:any,i:number)=><div key={i} style={{padding:'10px 12px',border:'1px solid var(--border-color,#ddd)',borderRadius:8}}>
            <strong>{String(finding.severity||'info').toUpperCase()}</strong> · {finding.area}<div>{finding.message}</div>
          </div>)}
      </div>
    </article>

    <article className="admin-card" style={{marginTop:16}}>
      <div className="section-header"><div><strong>AI status</strong><p>Client AI can be enabled separately; this screen never exposes API credentials.</p></div></div>
      <div style={{display:'flex',gap:16,flexWrap:'wrap'}}>
        <span>Operations AI: {overview?.ai?.operations_ai_configured?'Configured':'Not configured'}</span>
        <span>Client AI: {overview?.ai?.client_ai_enabled?'Enabled':'Disabled'}</span>
      </div>
    </article>

    <article className="admin-card" style={{marginTop:16}}>
      <div className="section-header"><div><strong>Ask POSP AI</strong><p>Ask what changed, what is failing, what needs review, or what should be checked next.</p></div></div>
      <div style={{display:'flex',flexWrap:'wrap',gap:8,marginBottom:12}}>
        {['What needs attention right now?','Check job and scholarship source health.','Summarize the current POSP operational status.'].map(q=><button key={q} className="btn btn-secondary" onClick={()=>ask(q)}>{q}</button>)}
        <button className="btn btn-secondary" disabled={actionLoading} onClick={syncJobs}>{actionLoading?'Syncing jobs…':'Run approved job sync'}</button>
      </div>
      <div style={{minHeight:160,maxHeight:420,overflowY:'auto',display:'grid',gap:10,padding:12,background:'var(--surface-muted,#f7f7f7)',borderRadius:10}}>
        {messages.length===0?<p>Start with a question above. POSP AI only receives operational context and does not receive client documents or credentials.</p>:messages.map((m,i)=><div key={i} style={{justifySelf:m.role==='admin'?'end':'start',maxWidth:'90%',padding:'10px 12px',borderRadius:10,background:m.role==='admin'?'var(--surface,#fff)':'var(--surface-strong,#eef6ff)'}}><strong>{m.role==='admin'?'You':'POSP AI'}</strong><div style={{whiteSpace:'pre-wrap',marginTop:4}}>{m.text}</div></div>)}
        {loading&&<div>POSP AI is checking the current operational context…</div>}
      </div>
      <form onSubmit={e=>{e.preventDefault();ask()}} style={{display:'flex',gap:8,marginTop:12}}>
        <input aria-label="Ask POSP AI" value={input} onChange={e=>setInput(e.target.value)} placeholder="Ask about jobs, scholarships, errors, source health…" style={{flex:1}}/>
        <button className="btn btn-primary" disabled={loading||!input.trim()}>{loading?'Checking…':'Ask AI'}</button>
      </form>
    </article>
  </section>
}
