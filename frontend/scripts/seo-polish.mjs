import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { siteUrl } from './seo-catalog.mjs'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const distDir = path.resolve(scriptDir, '../dist')
const logoUrl = `${siteUrl}/logo.svg`

const pageCopy = {
  '/': {
    title: 'Public Online Service Provider — Application Assistance',
    extra: `<section><h2>How Public Online Service Provider helps</h2><p>Public Online Service Provider is an independent private assistance platform for people who need help understanding and completing eligible online public-service processes in India. The website brings together service guidance, government recruitment notices, scholarship information, certificates, schemes, MeeSeva-related assistance and request tracking in one place.</p><p>Before sending a request, clients can review the purpose of a service, available requirements, assistance fees and the next step. Official eligibility, government charges, approval decisions and deadlines remain governed by the responsible authority. Where the website links to an official notice or portal, clients should use that authoritative source for the final rules.</p><h2>Find the right service</h2><p>Use the service search or browse the dedicated jobs, scholarships, certificates, schemes and MeeSeva sections. Recruitment and scholarship pages are refreshed from approved sources and are designed to keep official links visible. Public Online Service Provider does not represent a government department and does not guarantee approval, selection or benefit eligibility.</p><h2>Safer application assistance</h2><p>Clients can submit an assistance request, review fees, track progress and receive updates through their account. Never share an OTP, password, PIN, CVV or banking-login credential with the platform or with anyone claiming to act on its behalf.</p></section>`
  },
  '/scholarships': {
    title: 'Scholarships & Application Assistance | POSP India',
    extra: `<section><h2>Using the scholarship directory</h2><p>Review the scholarship provider, study level, region, category, academic year, eligibility information and deadline shown for each available opportunity. Scholarship rules can change, so the linked official or verified source remains authoritative for current eligibility, documents, award value and application dates.</p><p>Public Online Service Provider offers independent application assistance where supported. It does not award scholarships or guarantee selection. Check identity, academic, income, category, domicile and bank-document requirements before requesting help, and keep copies of submitted documents and acknowledgement details.</p></section>`
  },
  '/meeseva': {
    title: 'MeeSeva & Public Service Assistance | POSP India',
    extra: `<section><h2>Before requesting MeeSeva assistance</h2><p>Choose the service that matches the certificate, record, registration or public-service task you need. Review the listed purpose and document guidance first, then confirm the current official eligibility, government fee and processing rules for your location. Some services may be available only through a responsible department or an official state portal.</p><p>Public Online Service Provider is an independent private assistance provider, not MeeSeva or a government department. Assistance fees are shown separately from official charges. Approval, rejection, processing time and document issuance remain with the responsible authority.</p></section>`
  },
  '/government-services': {
    title: 'Government Service Assistance | POSP India',
    extra: `<section><h2>Choose a service with confidence</h2><p>Browse available public-service assistance by purpose, then open the relevant service page to review requirements and the request process. Government rules, eligibility, official charges, processing times and approval decisions are controlled by the responsible authority and may change.</p><p>This website provides independent private assistance and clear navigation. It is not a government department or official portal. Always use the linked official source when a service requires final confirmation of eligibility, documents, fees or deadlines.</p></section>`
  },
  '/certificates': {
    title: 'Certificate Application Assistance | POSP India',
    extra: `<section><h2>Prepare before applying</h2><p>Certificate applications commonly depend on identity, address, family, income, birth, residence, community or other supporting records. Open the relevant service page to review the available guidance and confirm the latest official requirements before submission.</p><p>Public Online Service Provider provides independent application assistance only. The responsible government authority decides eligibility, verification, processing time, approval and issuance of every official certificate.</p></section>`
  },
  '/schemes': {
    title: 'Government Scheme Assistance | POSP India',
    extra: `<section><h2>Check scheme eligibility carefully</h2><p>Government schemes can have income, age, residence, occupation, category, family or other eligibility conditions. Review the service information and use the responsible official source to confirm the latest rules, benefit details, documents and deadlines before requesting assistance.</p><p>Public Online Service Provider is an independent private assistance platform. It does not decide scheme eligibility, sanction benefits or guarantee approval.</p></section>`
  },
  '/jobs': {
    title: 'Government Jobs & Recruitment Notices | POSP India',
    extra: ''
  }
}

function fileForRoute(route) {
  return route === '/' ? path.join(distDir, 'index.html') : path.join(distDir, route.slice(1), 'index.html')
}

function replaceTitle(html, title) {
  const escaped = title.replace(/&/g, '&amp;')
  return html
    .replace(/<title>.*?<\/title>/s, `<title>${escaped}</title>`)
    .replace(/<meta property="og:title"[^>]*>/, `<meta property="og:title" content="${escaped}" />`)
    .replace(/<meta name="twitter:title"[^>]*>/, `<meta name="twitter:title" content="${escaped}" />`)
}

for (const [route, config] of Object.entries(pageCopy)) {
  const filename = fileForRoute(route)
  if (!fs.existsSync(filename)) continue
  let html = fs.readFileSync(filename, 'utf8')
  html = replaceTitle(html, config.title)
  if (config.extra && !html.includes('data-seo-polish="true"')) {
    html = html.replace('</article>', `${config.extra.replace('<section>', '<section data-seo-polish="true">')}</article>`)
  }
  if (route === '/') {
    html = html.replace(/<link rel="icon"[^>]*>/, '<link rel="icon" href="/logo.svg" type="image/svg+xml" />')
    html = html.replace(
      /<script id="structured-data" type="application\/ld\+json">.*?<\/script>/s,
      `<script id="structured-data" type="application/ld+json">${JSON.stringify([
        {
          '@context': 'https://schema.org',
          '@type': 'WebSite',
          name: 'Public Online Service Provider',
          url: `${siteUrl}/`,
          description: 'Independent assistance for public-service applications.'
        },
        {
          '@context': 'https://schema.org',
          '@type': 'Organization',
          name: 'Public Online Service Provider',
          url: `${siteUrl}/`,
          logo: logoUrl,
          description: 'Independent private assistance provider for public-service applications.'
        }
      ]).replace(/</g, '\\u003c')}</script>`
    )
  }
  fs.writeFileSync(filename, html)
}

console.log('Applied final on-page SEO polish to priority public pages.')
