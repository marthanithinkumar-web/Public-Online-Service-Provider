import { readFile } from 'node:fs/promises';

const html=await readFile(new URL('./index.html',import.meta.url),'utf8');
const css=await readFile(new URL('./styles.css',import.meta.url),'utf8');
const robots=await readFile(new URL('./robots.txt',import.meta.url),'utf8');
const sitemap=await readFile(new URL('./sitemap.xml',import.meta.url),'utf8');
const required=[
  'MNK Technologies',
  'Public Online Service Provider',
  'https://pospindia.onrender.com',
  'FileWeave',
  'https://file-weave.vercel.app',
  'Nova',
  'Udyam-registered proprietorship',
  'https://mnktechnologies.onrender.com/',
  'h2xCzca3X9ymEzki4UvgyHf5LBSszj1hsDbXAJmTD3Q'
];
for(const value of required){if(!html.includes(value))throw new Error(`Missing required content: ${value}`)}
if(html.includes('MNK Technologies Pvt. Ltd.')||html.includes('MNK Technologies Limited'))throw new Error('Incorrect incorporated-company wording found');
if(!robots.includes('https://mnktechnologies.onrender.com/sitemap.xml'))throw new Error('robots.txt does not point to the official sitemap');
if(!sitemap.includes('<loc>https://mnktechnologies.onrender.com/</loc>'))throw new Error('sitemap does not use the official hostname');
const retiredHostname=['mnk','technologies.onrender.com'].join('-');
if(html.includes(retiredHostname)||robots.includes(retiredHostname)||sitemap.includes(retiredHostname))throw new Error('Retired hostname remains in public website files');
if(!css.includes('@media(max-width:680px)'))throw new Error('Mobile layout rule missing');
console.log('MNK Technologies company-site verification passed');
