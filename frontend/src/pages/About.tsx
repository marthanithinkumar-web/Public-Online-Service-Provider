import React from 'react'
import PublicInfoPage from '../components/ui/PublicInfoPage'

export default function About(){
  return <PublicInfoPage eyebrow="About the platform" title="Public-service assistance made easier" intro="We help busy people understand, prepare and track requests for public and online services.">
    <section><h2>What we do</h2><p>Public Online Service Provider offers private assistance for certificates, government job and examination applications, scholarships, MeeSeva services, travel-related requests and other supported services.</p></section>
    <section><h2>How we help</h2><ul><li>Explain the service, requirements and next steps.</li><li>Collect only the information needed for the selected request.</li><li>Keep assistance fees separate from government or official charges.</li><li>Provide a reference ID, status tracking and meaningful notifications.</li></ul></section>
    <section className="public-info-notice"><h2>Independent private provider</h2><p>We are not a government department or official government portal. Official approvals, eligibility decisions and government fees remain with the relevant authority.</p></section>
  </PublicInfoPage>
}
