import React from 'react'
import PublicInfoPage from '../components/ui/PublicInfoPage'

export default function Disclaimer(){
  return <PublicInfoPage eyebrow="Important disclosure" title="Independent assistance—not a government portal" intro="Public Online Service Provider is a private service that helps clients navigate supported public and online services.">
    <section className="public-info-notice"><h2>Not an official authority</h2><p>We do not represent or replace any government department, railway authority, examination body, educational institution or official service portal.</p></section>
    <section><h2>Official decisions</h2><p>Eligibility, approval, rejection, document acceptance, processing time, ticket availability and official charges are controlled by the relevant authority or service provider.</p></section>
    <section><h2>Security warning</h2><p>Never send us OTPs, passwords, PINs, banking-login credentials or card security codes. Enter these only yourself on the verified official website or application.</p></section>
  </PublicInfoPage>
}
