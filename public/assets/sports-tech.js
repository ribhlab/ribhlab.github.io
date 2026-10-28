/* Privacy-first: YouTube player is requested only after an explicit user click. */
document.querySelectorAll('[data-video-id]').forEach((button)=>{
 button.addEventListener('click',()=>{
   const id=button.getAttribute('data-video-id');
   if(!/^[A-Za-z0-9_-]{11}$/.test(id))return;
   const iframe=document.createElement('iframe');
   iframe.title=button.getAttribute('aria-label')||'Official video';
   iframe.src='https://www.youtube-nocookie.com/embed/'+id+'?autoplay=1';
   iframe.setAttribute('allow','autoplay; encrypted-media; picture-in-picture; fullscreen');
   iframe.setAttribute('allowfullscreen','');
   iframe.setAttribute('referrerpolicy','strict-origin-when-cross-origin');
   iframe.loading='eager';
   button.replaceWith(iframe);
 });
});
