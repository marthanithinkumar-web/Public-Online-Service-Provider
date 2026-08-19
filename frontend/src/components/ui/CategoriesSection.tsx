import React from 'react'
import { Link } from 'react-router-dom'

const categories = [
  {name:'Government Jobs', to:'/jobs', icon:'💼'},
  {name:'Scholarships', to:'/scholarships', icon:'🎓'},
  {name:'Certificates', to:'/certificates', icon:'📄'},
  {name:'MeeSeva', to:'/meeseva', icon:'🏛️'},
  {name:'Government Schemes', to:'/schemes', icon:'🏷️'},
  {name:'Public Services', to:'/', icon:'🔎'},
]

export default function CategoriesSection(){
  return (
    <section className="content-section"><div className="section-header"><div><span className="eyebrow">Popular Categories</span><h2>Popular Categories</h2></div></div>
      <div className="category-grid">
        {categories.map(c=>(
          <Link key={c.name} className="category-card" to={c.to}><span className="category-icon">{c.icon}</span><h3>{c.name}</h3><p>Explore {c.name} assistance and application guidance.</p></Link>
        ))}
      </div>
    </section>
  )
}
