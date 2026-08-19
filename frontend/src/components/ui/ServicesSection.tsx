import React from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight } from './Icons'

const services = [
  { key: 'jobs', title: 'Government Jobs', desc: 'Assistance with government job opportunities and applications.', to: '/jobs' },
  { key: 'scholarships', title: 'Scholarships', desc: 'Find scholarship opportunities and understand eligibility.', to: '/scholarships' },
  { key: 'certificates', title: 'Certificates', desc: 'Get assistance understanding certificate applications.', to: '/certificates' },
  { key: 'meeseva', title: 'MeeSeva Services', desc: 'Get guidance for common public-service applications.', to: '/meeseva' },
  { key: 'schemes', title: 'Government Schemes', desc: 'Explore schemes and understand eligibility.', to: '/schemes' },
]

export default function ServicesSection(){
  return (
    <section className="content-section services-section">
      <div className="section-header"><div><span className="eyebrow">Everything you need</span><h2>Everything You Need, In One Place</h2></div></div>
      <div className="service-list-grid">
        {services.map(s=> (
          <article key={s.key} className="service-card premium">
            <div className="service-card-top"><span className="service-badge">{s.title}</span><span className="service-price">&nbsp;</span></div>
            <h3>{s.title}</h3>
            <p>{s.desc}</p>
            <div className="service-actions"><Link to={s.to} className="text-link">Learn More</Link><Link to={s.to} className="btn btn-secondary small">{<ArrowRight/>}</Link></div>
          </article>
        ))}
      </div>
    </section>
  )
}
