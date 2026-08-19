import React from 'react'

const steps = [
  {title: 'Choose a Service', body: 'Find the service you need and review requirements.'},
  {title: 'Check Requirements', body: 'We explain documents and steps required.'},
  {title: 'Submit Your Request', body: 'Complete the form and upload supporting files.'},
  {title: 'Provider Reviews', body: 'Provider reviews your submission and proceeds.'},
  {title: 'Get Assistance', body: 'Receive guidance and next steps.'},
  {title: 'Track Your Request', body: 'Monitor progress from your dashboard.'},
]

export default function HowItWorks(){
  return (
    <section className="content-section"><div className="section-header"><div><span className="eyebrow">How it works</span><h2>How It Works</h2></div></div>
      <div className="timeline-grid">
        {steps.map((s,i)=>(
          <div key={s.title} className="step-card timeline-item"><span className="step-number">{i+1}</span><h3>{s.title}</h3><p>{s.body}</p></div>
        ))}
      </div>
    </section>
  )
}
