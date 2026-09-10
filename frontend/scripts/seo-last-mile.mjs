import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = path.dirname(fileURLToPath(import.meta.url))
const filename = path.resolve(scriptDir, '../dist/meeseva/index.html')

if (fs.existsSync(filename)) {
  let html = fs.readFileSync(filename, 'utf8')
  if (!html.includes('data-seo-meeseva-last-mile="true"')) {
    const paragraph = '<p data-seo-meeseva-last-mile="true">For services with time-sensitive records, obtain recent certificates or supporting documents when the responsible authority requires them. Review the final application preview carefully, preserve the official receipt, and use only the responsible department or portal for authoritative status, correction, appeal, or issuance information.</p>'
    html = html.replace('</article>', `${paragraph}</article>`)
    fs.writeFileSync(filename, html)
  }
}

console.log('Applied final MeeSeva SEO content check.')
