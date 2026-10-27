// RibhLab Market Pulse: public GitHub issue comments are readable in-site.
// Writing a comment always requires authenticated GitHub; no local password store,
// no custom login form, no unmoderated anonymous POST endpoint.
(() => {
 const allowedLanguages=new Set(['ar','en','fr']);
 const threads=document.querySelectorAll('[data-market-comment-thread]');
 for(const section of threads){
  const issue=Number(section.dataset.marketCommentThread);
  const lang=allowedLanguages.has(section.dataset.marketCommentLang)?section.dataset.marketCommentLang:'en';
  if(!Number.isSafeInteger(issue)||issue<=0)continue;
  const button=section.querySelector('[data-comments-load]');
  const list=section.querySelector('[data-comments-list]');
  if(!button||!list)continue;
  const locale={ar:'ar-MA',en:'en-GB',fr:'fr-FR'}[lang];
  const state=text=>{list.replaceChildren();const item=document.createElement('p');item.className='market-comment-status';item.textContent=text;list.appendChild(item);};
  const api='https://api.github.com/repos/univcours/ribhlab-site/issues/'+issue+'/comments?per_page=30';
  button.addEventListener('click',async()=>{
   button.disabled=true;state(list.dataset.labelLoading||'Loading…');
   try{
    const response=await fetch(api,{headers:{Accept:'application/vnd.github+json'},credentials:'omit',cache:'no-store'});
    if(!response.ok)throw new Error('Public comments unavailable ('+response.status+')');
    const comments=await response.json();
    if(!Array.isArray(comments))throw new TypeError('Unexpected GitHub comment format');
    list.replaceChildren();
    if(!comments.length){state(list.dataset.labelEmpty||'No comments');return;}
    for(const item of comments.slice(0,30)){
     if(!item||typeof item.body!=='string'||typeof item.user?.login!=='string')continue;
     const article=document.createElement('article');
     article.className='market-reader-comment';
     const header=document.createElement('div');header.className='market-reader-comment-head';
     const login=document.createElement('strong');login.textContent=item.user.login.slice(0,80);
     header.appendChild(login);
     const date=document.createElement('time');
     const stamp=new Date(item.created_at);
     if(Number.isFinite(stamp.getTime())){
      date.dateTime=stamp.toISOString();
      date.textContent=new Intl.DateTimeFormat(locale,{year:'numeric',month:'short',day:'numeric'}).format(stamp);
     }
     header.appendChild(date);article.appendChild(header);
     const body=document.createElement('p');
     body.className='market-reader-comment-body';
     // Never inject HTML/Markdown from remote comments. This also stops XSS.
     body.textContent=item.body.slice(0,6000);
     article.appendChild(body);
     if(typeof item.html_url==='string'&&item.html_url.startsWith('https://github.com/univcours/ribhlab-site/issues/')){
      const link=document.createElement('a');
      link.href=item.html_url;
      link.rel='noopener noreferrer';
      link.target='_blank';
      link.textContent={ar:'فتح التعليق على GitHub',en:'View comment on GitHub',fr:'Voir le commentaire sur GitHub'}[lang];
      article.appendChild(link);
     }
     list.appendChild(article);
    }
    if(!list.children.length)state(list.dataset.labelEmpty||'No comments');
   }catch{
    state(list.dataset.labelFailed||'Could not load comments');
   }finally{button.disabled=false;}
  });
 }
})();
