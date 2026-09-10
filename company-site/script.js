if(location.hostname==='mnk-technologies.onrender.com'){
  const destination=`https://mnktechnologies.onrender.com${location.pathname}${location.search}${location.hash}`;
  location.replace(destination);
}

const menuButton=document.querySelector('.menu-button');
const nav=document.getElementById('primary-nav');
menuButton?.addEventListener('click',()=>{
  const open=menuButton.getAttribute('aria-expanded')==='true';
  menuButton.setAttribute('aria-expanded',String(!open));
  nav?.classList.toggle('open',!open);
});
nav?.querySelectorAll('a').forEach(link=>link.addEventListener('click',()=>{
  menuButton?.setAttribute('aria-expanded','false');
  nav?.classList.remove('open');
}));
const year=document.getElementById('year');
if(year)year.textContent=String(new Date().getFullYear());
