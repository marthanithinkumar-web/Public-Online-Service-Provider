import React from 'react'
import PublicInfoPage from '../components/ui/PublicInfoPage'

export default function PrivacyPolicy(){
  return <PublicInfoPage eyebrow="Privacy & safety" title="Your information stays private" intro="We collect and use only the information needed to provide account and service-request assistance.">
    <section><h2>Information we use</h2><p>Your account contact details, selected service information, application answers and documents are used to process and communicate about your requests.</p></section>
    <section><h2>Who can access it</h2><p>Backend ownership checks restrict client information to the account that submitted it. Authorized provider administrators may access the limited information required to process the request.</p></section>
    <section><h2>Information you must never provide</h2><ul><li>One-time passwords or OTPs</li><li>Account passwords, PINs or recovery codes</li><li>Banking-login credentials or card security codes</li></ul><p>When an official portal requires verification or payment, complete that step yourself on the official portal.</p></section>
    <section><h2>Account management</h2><p>You can update your contact details and security settings from your account. Protected account deletion requires password verification and an additional confirmation.</p></section>
  </PublicInfoPage>
}
