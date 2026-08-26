import React from 'react'
import PublicInfoPage from '../components/ui/PublicInfoPage'

export default function Terms(){
  return <PublicInfoPage eyebrow="Terms of assistance" title="Clear responsibilities and charges" intro="These terms explain the role of the private assistance provider and what clients should expect.">
    <section><h2>Assistance service</h2><p>We help clients understand requirements, prepare information and follow supported application or booking processes. We do not guarantee eligibility, approval, appointment availability, ticket availability or a government decision.</p></section>
    <section><h2>Fees</h2><p>Our assistance fee is shown before submission and is separate from every government, official, examination, ticket, payment-gateway or third-party charge. When an official fee is unknown, no final total is invented.</p></section>
    <section><h2>Client responsibilities</h2><ul><li>Provide accurate, lawful and relevant information.</li><li>Review the request and fee summary before confirming.</li><li>Complete OTP, password, PIN and payment steps personally on official portals.</li><li>Respond to legitimate document or information requests through the secure client workspace.</li></ul></section>
    <section><h2>Cancellations and closed requests</h2><p>Available cancellation, grievance or support options depend on the request’s current processing stage and any work already completed.</p></section>
  </PublicInfoPage>
}
