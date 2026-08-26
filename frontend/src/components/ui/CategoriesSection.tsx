import React from 'react'
import { Link } from 'react-router-dom'

const categories = [
  {name:'Government Jobs', to:'/jobs', icon:'💼'},
  {name:'Scholarships', to:'/scholarships', icon:'🎓'},
  {name:'Certificates', to:'/certificates', icon:'📄'},
  {name:'MeeSeva', to:'/meeseva', icon:'🏛️'},
  {name:'Government Schemes', to:'/schemes', icon:'🏷️'},
]

export default function CategoriesSection(){
  return (
    <section className="content-section" id="services"><div className="section-header"><div><span className="eyebrow">Browse by category</span><h2>Find the Right Service Quickly</h2><p className="section-intro">Choose a category if you are not sure what to search for.</p></div></div>
      <div className="category-grid">
        {categories.map(c=>(
          <Link key={c.name} className="category-card" to={c.to}><span className="category-icon">{c.icon}</span><h3>{c.name}</h3><p>Explore {c.name} assistance and application guidance.</p></Link>
        ))}
      </div>
    </section>
  )
}
