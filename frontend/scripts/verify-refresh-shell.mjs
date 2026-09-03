import fs from 'node:fs'
import path from 'node:path'
import {fileURLToPath} from 'node:url'

const scriptDir=path.dirname(fileURLToPath(import.meta.url))
const distDir=path.resolve(scriptDir,'../dist')
const requiredPages=['index.html','jobs/index.html','services/apply-government-job/index.html']

for(const relative of requiredPages){
  const target=path.join(distDir,relative)
  if(!fs.existsSync(target)) throw new Error(`Missing refresh target: ${relative}`)
  const html=fs.readFileSync(target,'utf8')
  if(!html.includes('<script src="/app-boot.js"></script>')) throw new Error(`Missing CSP-safe app bootstrap in ${relative}`)
  if(html.includes("<script>document.documentElement.classList.add('js')</script>")) throw new Error(`Inline app bootstrap regressed in ${relative}`)
}

if(!fs.existsSync(path.join(distDir,'app-boot.js'))) throw new Error('app-boot.js was not copied to dist')
console.log('Verified refresh shell for homepage, jobs and service routes.')
