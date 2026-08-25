import React from 'react'
import {Link} from 'react-router-dom'
import '../../styles/auth.css'

export default function AuthLayout({title,eyebrow='Secure account access',children}:{title:string,eyebrow?:string,children:React.ReactNode}){
  return <div className="auth-screen">
    <section className="auth-banner" aria-labelledby="auth-page-title">
      <span>{eyebrow}</span><h1 id="auth-page-title">{title}</h1>
      <nav aria-label="Breadcrumb"><Link to="/">Home</Link><b aria-hidden="true">/</b><span>{title}</span></nav>
    </section>
    <div className="auth-page auth-page-centered">{children}</div>
  </div>
}
