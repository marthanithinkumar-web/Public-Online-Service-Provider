import React from 'react'
import {Link} from 'react-router-dom'
import {PROVIDER} from '../../services/config'

export default function PublicInfoPage({eyebrow,title,intro,children}:{eyebrow:string,title:string,intro:string,children:React.ReactNode}){
  return <div className="public-info-page">
    <section className="public-info-hero"><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{intro}</p><div className="public-info-actions"><Link className="btn btn-primary" to="/#service-search">Search Services</Link><Link className="btn btn-secondary" to="/contact">Contact Us</Link></div></section>
    <div className="public-info-layout"><article className="public-info-content">{children}</article><aside className="public-info-aside"><strong>Need help?</strong><span>{PROVIDER.name}</span><a href={`tel:${PROVIDER.phone}`}>{PROVIDER.phone}</a><a href={`tel:${PROVIDER.phone2}`}>{PROVIDER.phone2}</a><a href={`mailto:${PROVIDER.email}`}>{PROVIDER.email}</a><p>Private assistance platform—not a government department or official portal.</p></aside></div>
  </div>
}
