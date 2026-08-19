import React from 'react'
import { Shield, Users, Sparkle, Chart, Globe, Heart } from './Icons'

const items = [
  {title: 'Simple Process', text: 'Clear steps without unnecessary complexity.', Icon: Users},
  {title: 'Secure & Private', text: 'Responsible handling of submitted information.', Icon: Shield},
  {title: 'Citizen Focused', text: 'Designed around real public-service needs.', Icon: Heart},
  {title: 'Transparent', text: 'Clearly explain services and requirements.', Icon: Chart},
  {title: 'Easy Access', text: 'Use the platform anywhere.', Icon: Globe},
  {title: 'Personal Assistance', text: 'Get direct assistance when needed.', Icon: Sparkle},
]

export default function WhyChoose(){
  return (
    <section className="content-section"><div className="section-header"><div><span className="eyebrow">Why Choose Us</span><h2>Why Choose Public Online Service Provider?</h2></div></div>
      <div className="why-grid">
        {items.map(it=>{
          const Icon = it.Icon
          return <div key={it.title} className="step-card why-card"><div className="icon-wrap"><Icon/></div><h3>{it.title}</h3><p>{it.text}</p></div>
        })}
      </div>
    </section>
  )
}
