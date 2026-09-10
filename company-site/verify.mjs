import { readFile } from 'node:fs/promises';

const html=await readFile(new URL('./index.html',import.meta.url),'utf8');
const css=await readFile(new URL('./styles.css',import.meta.url),'utf8');
const required=[
  'MNK Technologies',
  'Public Online Service Provider',
  'https://pospindia.onrender.com',
  'FileWeave',
  'https://file-weave.vercel.app',
  'Nova',
  'Udyam-registered proprietorship'
];
for(const value of required){if(!html.includes(value))throw new Error(`Missing required content: ${value}`)}
if(html.includes('MNK Technologies Pvt. Ltd.')||html.includes('MNK Technologies Limited'))throw new Error('Incorrect incorporated-company wording found');
if(!css.includes('@media(max-width:680px)'))throw new Error('Mobile layout rule missing');
console.log('MNK Technologies company-site verification passed');
