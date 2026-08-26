import React from 'react'

const steps = [
  {title: 'Find a Service', body: 'Search or browse, then review the requirements and transparent fee information.'},
  {title: 'Submit a Request', body: 'Sign in, provide only the required details, review everything and confirm.'},
  {title: 'Track Every Update', body: 'Use your reference ID and dashboard to follow progress and notifications.'},
]

export default function HowItWorks(){
  return (
    <section className="content-section" id="how-it-works"><div className="section-header"><div><span className="eyebrow">Simple request journey</span><h2>How It Works</h2></div></div>
      <div className="timeline-grid">
        {steps.map((s,i)=>(
          <div key={s.title} className="step-card timeline-item"><span className="step-number">{i+1}</span><h3>{s.title}</h3><p>{s.body}</p></div>
        ))}
      </div>
    </section>
  )
}
