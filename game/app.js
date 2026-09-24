import {createWorld} from './world.js';

const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const token = $('meta[name="library-token"]').content;
const panel = $('#panel'), body = $('#panel-body');
const colors = ['#667d71','#92624f','#7b697d','#596e82','#9b8053','#936269'];
const categories = ['All books','Philosophy','Science','Literature','History','Politics','Religion'];
const roles = {editor:{name:'Margot',role:'The editor',desc:'A sharp pencil, a gentle touch. Bring her your sentences, tangles and all.',shirt:'#aa6e67',hair:'#6b392f'},researcher:{name:'Ada',role:'The researcher',desc:'Always following a footnote. She helps you trace claims back to the books.',shirt:'#87a7a0',hair:'#332c2a',skin:'#ba815c'},professor:{name:'Elias',role:'The professor',desc:'One more question, one more connection. Find the argument beneath your idea.',shirt:'#97826b',hair:'#d0c8b2'},publisher:{name:'Jules',role:'The publisher',desc:'Thinking about the reader on the other side. Find your audience and your next step.',shirt:'#8b88a0',hair:'#392f33'},friend:{name:'Noor',role:'Your first reader',desc:'Honest thoughts over a cup of coffee. A little perspective when you need it.',shirt:'#b99457',hair:'#3b2b2a',skin:'#bd8059'}};
const formatNames={corto:'Short article',medio:'Feature article',largo:'Long essay',paper:'Academic paper',tesis:'Thesis',libro:'Book',discusion:'Discussion'};
let db, state={bag:[],bookmarks:{},favorites:[],cups:0,treats:[],reader:{font:'serif',size:18,theme:'parchment'}}, world, view='world';
let search='',category='All books',catalogPage=0,catalogLanguage='',favoritesOnly=false;
let reading=null,readRequest=0,readPage=0,readFind='',readMatches=[],readMatchIndex=-1;
let draft={id:crypto.randomUUID().replaceAll('-',''),title:'Untitled manuscript',text:''}, draftDirty=false, draftVersion=0,saveChain=Promise.resolve(),saveTimer,stateTimer;
let brief='',format='corto',mode='guided',language='en',ideas=[],currentJob=null,jobTimer,chatRole='editor',chatResponse='',settingsDraft,preview=false;
let coffeeStart=0,coffeeFrame=0,coffeeRunning=false,soundContext=null,soundGain=null;

async function api(path,data){
  const response=await fetch('/api/'+path,{method:data===undefined?'GET':'POST',headers:{'X-Library-Token':token,...(data===undefined?{}:{'Content-Type':'application/json'})},body:data===undefined?undefined:JSON.stringify(data)});
  const result=await response.json();if(!response.ok)throw new Error(result.error||`Request failed (${response.status})`);return result;
}
let toastTimer;
function toast(message){$('#toast').textContent=message;$('#toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').hidden=true,4800);}
function showError(error){toast(error.message||String(error));}
function book(id){return [...db.books,...(db.archive_books||[])].find(b=>b.id===Number(id));}
function shelfBooks(){return state.collection==='archive'?(db.archive_books||[]):db.books;}
function selectCollection(collection){
  const previous=state.collection||'campaign';
  if(previous===collection)return;
  state.bags={...state.bags,[previous]:[...state.bag]};
  state.collection=collection;state.bag=(state.bags[collection]||[]).filter(id=>book(id));
  state.lastBook=null;ideas=[];search='';catalogPage=0;category='All books';remember();updateHome();
}
function tint(id){return colors[Math.abs(Number(id))%colors.length];}
function author(b){return b.authors.join(' · ')||'Anonymous';}
function portrait(role){const r=roles[role];return `<span class="portrait" style="--shirt:${r.shirt};--hair:${r.hair};--skin:${r.skin||'#e8b38c'}"><span class="pixel-person"></span></span>`;}
function words(text){return text.trim()?text.trim().split(/\s+/).length:0;}
function remember(){clearTimeout(stateTimer);stateTimer=setTimeout(()=>api('state',state).catch(showError),350);}
function updateHome(){
  $('#bag-count').textContent=state.bag.length;
  $('#side-bag').innerHTML=state.bag.length?state.bag.map(id=>{const b=book(id);return `<button class="bag-mini" data-action="read" data-id="${id}"><span class="mini-spine" style="--book:${tint(id)}"></span><span>${esc(b.title.slice(0,56))}</span></button>`;}).join(''):'<p>A good idea starts<br>with a little browsing.</p>';
  $('#book-total').textContent=(db.archive_books?.length||db.books.length).toLocaleString();$('#draft-total').textContent=db.documents.length;$('#coffee-total').textContent=state.cups;
  if(db.campaign){const c=db.campaign;$('#campaign-status').textContent=`${c.year} · ${c.place} · Day ${c.day} · ${c.money} coins · ${c.paper} paper · ${c.prestige} prestige · ${c.knowledge} research${c.completed?' · Campaign complete':''}`;$('.room-tag').textContent=`${c.year} · ${c.place}`;}
}
function shell(title,kicker='THE LAMPLIGHT LIBRARY'){$('#panel-title').textContent=title;$('#panel-kicker').textContent=kicker;}
function deskTabs(active){return `<div class="tabs">${[['computer','Writing desk'],['writer','Manuscript'],['usage','Usage & budget']].map(([key,title])=>`<button class="tab ${key===active?'selected':''}" data-view="${key}">${title}</button>`).join('')}</div>`;}
function open(next,arg){
  if(!db)return toast('The library is still opening.');
  if(next==='post')next='campaign';
  captureWriter();captureComputer();
  if(next==='archive'){selectCollection('archive');next='catalog';}
  if(next==='campaign')selectCollection('campaign');
  view=next;world.pause(next!=='world');
  document.querySelectorAll('.nav[data-view]').forEach(n=>n.classList.toggle('active',n.dataset.view===next));
  if(next==='world'){panel.close();return;}
  if(!panel.open)panel.showModal();
  body.scrollTop=0;panel.scrollTop=0;
  if(next==='catalog'){if(arg)category=arg;renderCatalog();}
  else if(next==='computer')renderComputer();
  else if(next==='writer')renderWriter();
  else if(next==='residents')renderResidents();
  else if(next==='chat'){if(arg)chatRole=arg;renderChat();}
  else if(next==='settings'){settingsDraft=structuredClone(db.settings);renderSettings();}
  else if(next==='usage')renderUsage();
  else if(next==='coffee')renderCoffee();
  else if(next==='help')renderHelp();
  else if(next==='campaign')renderCampaign();
}
function closePanel(){captureWriter();captureComputer();coffeeRunning=false;cancelAnimationFrame(coffeeFrame);view='world';world?.pause(false);document.querySelectorAll('.nav[data-view]').forEach(n=>n.classList.toggle('active',n.dataset.view==='world'));}
$('#close-panel').addEventListener('click',()=>panel.close());panel.addEventListener('close',closePanel);
panel.addEventListener('click',e=>{if(e.target===panel){const rect=panel.getBoundingClientRect();if(e.clientX<rect.left||e.clientX>rect.right||e.clientY<rect.top||e.clientY>rect.bottom)panel.close();}});
function renderCatalog(){
  const archive=state.collection==='archive';
  shell(archive?'A thousand doors to somewhere.':`The shelves of ${db.campaign.year}.`,archive?'THE ENGLISH BOOK LIBRARY':'PERIOD STUDY LIBRARY');
  body.innerHTML=`<p class="muted">${db.books.length.toLocaleString()} real books. Browse a shelf, take a book to your trolley, or settle in and read.</p><div class="toolbar"><input type="search" id="book-search" aria-label="Search books" placeholder="Find a title, author, subject, or idea…" value="${esc(search)}"><select id="book-language" aria-label="Filter language"><option value="">All languages</option><option value="en" ${catalogLanguage==='en'?'selected':''}>English</option></select><button class="secondary" data-action="favorites" aria-pressed="${favoritesOnly}">${favoritesOnly?'★ Favorites':'☆ Favorites'}</button></div><div class="tabs">${categories.map(c=>`<button class="tab ${c===category?'selected':''}" data-action="category" data-category="${c}">${c}</button>`).join('')}</div><div id="catalog-results"></div><p class="muted">Source: <a href="https://www.gutenberg.org/ebooks/offline_catalogs.html" target="_blank" rel="noreferrer">Project Gutenberg</a>. Each edition is marked public domain in the USA; rights elsewhere may differ. Full text downloads when opened and is then cached locally.</p>`;
  $('#book-search').addEventListener('input',e=>{search=e.target.value;catalogPage=0;renderBookResults();});
  body.querySelector('p').textContent=archive?`${db.archive_books.length.toLocaleString()} full English books. Read, search, and bring up to 12 books to the computer. This collection is available outside the historical campaign.`:`${db.books.length} original study notes on works known by ${db.campaign.year}. Later periods unlock more shelves. These are summaries, not complete books or historical quotations.`;
  if(!archive)body.querySelector('p:last-child').textContent='Period study notes stay within the campaign. Visit the English book library for the complete public-domain collection; its editions are not used as historical campaign sources.';
  if(archive){$('#book-language').innerHTML='<option value="en">English editions</option>';catalogLanguage='en';}else catalogLanguage='';
  body.insertAdjacentHTML('afterbegin',`<div class="tabs"><button class="tab ${archive?'selected':''}" data-action="collection" data-collection="archive">Full English books</button><button class="tab ${archive?'':'selected'}" data-action="collection" data-collection="campaign">Period study notes</button></div>`);
  $('#book-language').addEventListener('change',e=>{catalogLanguage=e.target.value;catalogPage=0;renderBookResults();});renderBookResults();
}
function renderBookResults(){
  const q=search.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
  const filtered=shelfBooks().filter(b=>(category==='All books'||b.categories.includes(category))&&(!catalogLanguage||b.languages.includes(catalogLanguage))&&(!favoritesOnly||state.favorites.includes(b.id))&&q.every(word=>(b.title+' '+author(b)+' '+b.subjects.join(' ')).toLocaleLowerCase().includes(word)));
  const pages=Math.max(1,Math.ceil(filtered.length/12));catalogPage=Math.min(catalogPage,pages-1);
  $('#catalog-results').innerHTML=(filtered.length?`<div class="book-grid">${filtered.slice(catalogPage*12,(catalogPage+1)*12).map(b=>`<article class="book-card"><button class="book-cover" style="--book:${tint(b.id)}" data-action="read" data-id="${b.id}" aria-label="Read ${esc(b.title)}"><span>✦</span><strong>${esc(b.title)}</strong></button><span class="category-label">${esc(b.categories[0])} · ${b.languages.join(' / ')}</span><h3>${esc(b.title)}</h3><p class="book-author">${esc(author(b))}</p><div class="book-actions"><button class="secondary" data-action="bag" data-id="${b.id}">${state.bag.includes(b.id)?'✓ On trolley':'+ Take book'}</button><button data-action="favorite" data-id="${b.id}" aria-label="${state.favorites.includes(b.id)?'Unfavorite':'Favorite'} ${esc(b.title)}">${state.favorites.includes(b.id)?'★':'☆'}</button></div></article>`).join('')}</div>`:'<div class="empty">No books on this shelf match yet.<br>Try another word or a different shelf.</div>')+`<div class="pagination"><span>${filtered.length.toLocaleString()} books · Page ${catalogPage+1} of ${pages}</span><div><button class="secondary" data-action="catalog-prev" ${catalogPage===0?'disabled':''}>← Previous</button> <button class="secondary" data-action="catalog-next" ${catalogPage===pages-1?'disabled':''}>Next →</button></div></div>`;
}
function toggleBag(id){
  if(state.bag.includes(id))state.bag=state.bag.filter(n=>n!==id);
  else {if(state.bag.length>=12)return toast('Your trolley holds 12 books. Return one to make a little room.');state.bag.push(id);toast('A new possibility, added to your trolley.');}
  remember();updateHome();if(view==='catalog')renderBookResults();if(view==='computer')renderComputer();if(view==='reader'&&reading)renderReader();if(view==='campaign')renderCampaign();
}
function paginate(text){
  const pages=[];let start=0;
  while(start<text.length){let end=Math.min(start+2200,text.length);if(end<text.length){const cut=text.lastIndexOf('\n\n',end);end=cut>start+1000?cut+2:text.lastIndexOf(' ',end)+1;if(end<=start)end=Math.min(start+2200,text.length);}pages.push({start,end,text:text.slice(start,end)});start=end;}
  return pages.length?pages:[{start:0,end:0,text:''}];
}
async function readBook(id){
  const selected=book(id);if(!selected)return;selectCollection(id>0?'archive':'campaign');open('reader');const request=++readRequest;
  shell(selected.title,'THE READING NOOK');body.innerHTML='<div class="loading">Bringing your book to the reading table…<p class="muted">The first visit downloads the full text. Later visits work offline.</p></div>';
  try {const result=await api(`book?id=${id}&collection=${id>0?'archive':'campaign'}`);if(request!==readRequest||view!=='reader')return;
    const pages=paginate(result.text);const chapters=[];const regex=/^\s*(?:chapter|book|part|volume|capítulo|capitulo|libro|canto|act)\s+(?:[ivxlcdm]+|\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b[^\n]{0,110}/gim;let m;
    while((m=regex.exec(result.text))&&chapters.length<350){chapters.push({title:m[0].trim(),page:Math.max(0,pages.findIndex(p=>p.end>m.index))});}
    reading={book:selected,text:result.text,pages,chapters};readFind='';readMatches=[];readMatchIndex=-1;readPage=Math.min(state.bookmarks[id]||0,pages.length-1);state.lastBook=id;remember();renderReader();
  }catch(error){if(request===readRequest&&view==='reader')body.innerHTML=`<div class="notice error-text">${esc(error.message)}</div><button class="secondary" data-action="read" data-id="${id}">Try again</button>`;}
}
function renderReader(){
  if(!reading)return;const b=reading.book;shell(b.title,'THE READING NOOK');
  body.innerHTML=`<div class="reader-meta"><div><p>${esc(author(b))}</p><p class="muted">${esc(b.rights)} · <a href="${esc(b.url)}" target="_blank" rel="noreferrer">Source & edition</a></p></div><button class="secondary" data-action="bag" data-id="${b.id}">${state.bag.includes(b.id)?'✓ On your trolley':'+ Bring to the computer'}</button></div><div class="reader-controls"><select id="reader-font" aria-label="Reading typography"><option value="serif">Bookish serif</option><option value="sans">Clear sans serif</option><option value="mono">Typewriter</option></select><select id="reader-size" aria-label="Font size">${[16,18,20,22,24].map(n=>`<option>${n}</option>`).join('')}</select><select id="reader-theme" aria-label="Reading theme"><option value="parchment">Parchment</option><option value="night">Night reading</option></select><select id="reader-chapter" aria-label="Jump to chapter"><option value="">Contents (${reading.chapters.length})</option>${reading.chapters.map(c=>`<option value="${c.page}">${esc(c.title.slice(0,90))}</option>`).join('')}</select><input id="reader-search" type="search" placeholder="Find in this book…" aria-label="Find in book" value="${esc(readFind)}"><button class="secondary" data-action="find-next">Find next</button></div><div id="reader-search-info" class="muted" role="status"></div><div class="reading-book ${state.reader.theme==='night'?'night':''}"><div class="reading-top">${esc(b.title.slice(0,90))}</div><div id="reading-text" class="reading-text"></div></div><div class="reading-footer"><button class="secondary" data-action="page-prev">← Previous page</button><span>Page <input id="page-number" type="number" min="1" max="${reading.pages.length}" aria-label="Page number" value="${readPage+1}"> of ${reading.pages.length} <span class="muted">· position saved</span></span><button class="secondary" data-action="page-next">Next page →</button></div><p class="muted">Reader pages are navigation positions, not the original edition’s page numbers. Contents are detected from chapter headings. This edition includes its original source and license notices.</p>`;
  $('#reader-font').value=state.reader.font;$('#reader-size').value=state.reader.size;$('#reader-theme').value=state.reader.theme;
  if(b.id<0)body.querySelector('p:last-child').textContent=`Historical work: ${b.year}. Citation marker: [B${Math.abs(b.id)}]. These are original English study notes, not a full edition or a historical quotation. Study this work at the time machine to earn research.`;
  for(const key of ['font','size','theme'])$('#reader-'+key).addEventListener('change',e=>{state.reader[key]=key==='size'?Number(e.target.value):e.target.value;remember();renderReader();});
  $('#reader-chapter').addEventListener('change',e=>{if(e.target.value!=='')setPage(Number(e.target.value));});
  $('#page-number').addEventListener('change',e=>setPage(Number(e.target.value)-1));
  $('#reader-search').addEventListener('input',e=>{readFind=e.target.value;readMatches=[];readMatchIndex=-1;});
  $('#reader-search').addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();findNext();}});drawPage();
}
function drawPage(){
  const element=$('#reading-text');if(!element)return;const p=reading.pages[readPage];let safe=esc(p.text);
  if(readFind){const escaped=esc(readFind).replace(/[.*+?^${}()|[\]\\]/g,'\\$&');safe=safe.replace(new RegExp(escaped,'gi'),m=>`<mark>${m}</mark>`);}
  element.innerHTML=safe;element.style.fontFamily={serif:'Georgia, serif',sans:'Segoe UI, sans-serif',mono:'Consolas, monospace'}[state.reader.font]||'Georgia, serif';element.style.fontSize=state.reader.size+'px';$('#page-number').value=readPage+1;
  $('[data-action="page-prev"]').disabled=readPage===0;$('[data-action="page-next"]').disabled=readPage===reading.pages.length-1;
  $('#reader-search-info').textContent=readFind?(readMatches.length?`Match ${readMatchIndex+1} of ${readMatches.length}`:'Press Find next to search the full book.') : '';
  element.scrollTop=0;
  const match=readMatches[readMatchIndex];
  if(match>=p.start&&match<p.end){const first=readMatches.findIndex(pos=>pos>=p.start);element.querySelectorAll('mark')[readMatchIndex-first]?.scrollIntoView({block:'nearest'});}
}
function setPage(value){readPage=Math.max(0,Math.min(reading.pages.length-1,Number.isFinite(value)?value:0));state.bookmarks[reading.book.id]=readPage;remember();drawPage();}
function findNext(){
  if(!readFind.trim())return;
  if(!readMatches.length){const text=reading.text.toLocaleLowerCase(),q=readFind.toLocaleLowerCase();let pos=-1;while((pos=text.indexOf(q,pos+1))>=0)readMatches.push(pos);}
  if(!readMatches.length){$('#reader-search-info').textContent='No matches in this book.';return;}
  readMatchIndex=(readMatchIndex+1)%readMatches.length;setPage(reading.pages.findIndex(p=>p.end>readMatches[readMatchIndex]));
}
function captureComputer(){if($('#brief')){brief=$('#brief').value;format=$('#format').value;mode=$('#mode').value;language=$('#language').value;}}
function renderComputer(){
  shell('A small machine. Endless possibilities.','THE LIBRARY COMPUTER');
  const spec=db.formats[format];
  body.innerHTML=deskTabs('computer')+`<div class="desk-layout"><section class="form-stack"><p class="muted">Feed the computer a few books. Follow a spark, shape it together, or let the writing pipeline carry it through.</p><label>WHAT’S ON YOUR MIND?<textarea id="brief" rows="3" maxlength="8000" placeholder="An idea, a question, or the title of something you want to write…">${esc(brief)}</textarea></label><div class="form-pair"><label>FORMAT<select id="format">${Object.entries(formatNames).map(([key,name])=>`<option value="${key}" ${key===format?'selected':''}>${name}</option>`).join('')}</select></label><label>HOW WOULD YOU LIKE TO WRITE?<select id="mode"><option value="guided" ${mode==='guided'?'selected':''}>Guided · make decisions together</option><option value="auto" ${mode==='auto'?'selected':''}>Automatic · take it from here</option><option value="manual" ${mode==='manual'?'selected':''}>Manual · just me and the page</option></select></label></div><div class="form-pair"><div class="notice" id="length-note">${spec.words[0].toLocaleString()}–${spec.words[1].toLocaleString()} words · existing pipeline format</div><label>WRITING LANGUAGE<select id="language"><option value="en" ${language==='en'?'selected':''}>English</option></select></label></div><div class="toolbar"><button class="secondary" data-action="ideas">✦ Find a few ideas</button><button class="primary" data-action="generate">${mode==='manual'?'Open the blank page':'Begin writing'} ↗</button></div><p class="muted">AI actions use your configured providers. Longer formats can take a while. Guided writing pauses for topic, outline, revision, and final decisions; manual writing uses no AI until you ask a resident.</p></section><aside><div class="card"><h3>Your source material</h3>${state.bag.length?state.bag.map(id=>`<div class="book-list-item"><span class="mini-spine" style="--book:${tint(id)}"></span><span>${esc(book(id).title)}</span><button data-action="bag" data-id="${id}" aria-label="Return ${esc(book(id).title)}">×</button></div>`).join(''):'<p class="muted">Your trolley is empty. Bring a book or two from the shelves.</p>'}<button class="text-button" data-view="catalog">+ Visit the bookshelves</button></div><div class="notice"><strong>${esc(db.settings.chain.join(' → '))}</strong><br>Writer: ${esc(db.settings.flash)}<br>Planner: ${esc(db.settings.pro)}<br><button class="text-button" data-view="settings">Adjust providers & models ↗</button></div></aside></div><div id="job-area"></div><div id="ideas-area">${ideas.map((idea,i)=>`<button class="idea" data-action="choose-idea" data-index="${i}"><span class="category-label">POSSIBILITY ${String(i+1).padStart(2,'0')}</span><p><strong>${esc(idea.title)}</strong></p><p>${esc(idea.hypothesis)}</p><span class="text-button">Follow this idea ↗</span></button>`).join('')}</div>`;
  body.insertAdjacentHTML('afterbegin',`<div class="notice">${state.collection==='archive'?'English library · write freely from full books, outside the historical campaign.':'Historical campaign · sources and residents follow your current period.'} <button class="text-button" data-view="${state.collection==='archive'?'campaign':'archive'}">${state.collection==='archive'?'Return to the campaign':'Visit the full English library'} ↗</button></div>`);
  $('#format').addEventListener('change',()=>{captureComputer();const s=db.formats[format];$('#length-note').textContent=`${s.words[0].toLocaleString()}–${s.words[1].toLocaleString()} words · existing pipeline format`;});
  $('#mode').addEventListener('change',()=>{captureComputer();renderComputer();});renderJob();
}
async function beginJob(kind){
  captureComputer();captureWriter();if(currentJob&&['running','waiting','cancelling'].includes(currentJob.status))return toast('The computer is still working on your current task.');
  if(kind==='generate'&&mode==='manual'){if(brief&&!draft.text){draft.title=brief.slice(0,300);markDraft();}open('writer');return;}
  const data={kind,books:state.bag,brief,format,mode,language,collection:state.collection||'campaign'};
  if(kind==='agent'){data.resident=chatRole;data.brief=$('#agent-request').value;data.text=draft.text;}
  const result=await api('job',data);currentJob={id:result.id,kind,status:'running',logs:[]};renderJob();pollJob();toast(kind==='agent'?`${roles[chatRole].name} is reading your request.`:'The computer is settling in to work.');
}
function renderJob(){
  const area=$('#job-area');if(!area||!currentJob)return;
  const job=currentJob;const active=['running','waiting','cancelling'].includes(job.status);
  const statuses={running:'The computer is working…',waiting:'A little decision for you',cancelling:'Stopping after the current provider call…',complete:'Something new for your desk',failed:'The computer needs your attention',cancelled:'Stopped safely',interrupted:'Interrupted by a server restart'};
  const focused=$('#job-answer');if(focused&&job.status==='waiting'&&area.dataset.question===job.question)return;
  area.dataset.question=job.question||'';
  area.innerHTML=`<section class="job-status"><h3>${statuses[job.status]||esc(job.status)}</h3>${job.logs?.length?`<div class="logs">${esc(job.logs.slice(-18).join('\n'))}</div>`:''}${job.error?`<p class="error-text">${esc(job.error)}</p>`:''}${job.status==='waiting'?`<div class="job-question"><label>${esc(job.question)}<textarea id="job-answer" rows="3" placeholder="Leave blank for the suggested answer: ${esc(job.default||'approve')}" maxlength="8000"></textarea></label><button class="primary" data-action="answer">Continue →</button></div>`:''}${active?`<p class="muted">Saved checkpoints stay on disk. You can browse or read while the computer works.</p><button class="text-button" data-action="cancel-job" ${job.status==='cancelling'?'disabled':''}>Stop at the next safe checkpoint</button>`:''}${job.result?.text&&job.kind==='generate'?'<button class="primary" data-action="load-result">Open generated manuscript ↗</button>':''}</section>`;
  const logs=area.querySelector('.logs');if(logs)logs.scrollTop=logs.scrollHeight;
}
async function pollJob(){
  clearTimeout(jobTimer);if(!currentJob)return;
  try {const previous=currentJob.status;currentJob=await api('job?id='+currentJob.id);
    if(currentJob.status==='complete'&&previous!=='complete'){
      if(currentJob.kind==='ideas'){ideas=currentJob.result.ideas;captureComputer();if(view==='computer')renderComputer();}
      if(currentJob.kind==='agent'){chatResponse=currentJob.result.text;chatRole=currentJob.result.resident;if(view==='chat')renderChat();}
      if(currentJob.kind==='letter'){db.campaign=await api('campaign');updateHome();if(view==='campaign')renderCampaign();}
      toast(currentJob.kind==='generate'?'Your manuscript is ready at the computer.':'There’s something new at the computer.');
    }renderJob();$('#connection').textContent=['running','waiting','cancelling'].includes(currentJob.status)?`Computer: ${currentJob.status}`:'All is quiet. All is saved.';
    if(['running','waiting','cancelling'].includes(currentJob.status))jobTimer=setTimeout(pollJob,1500);
  }catch(error){$('#connection').textContent='Reconnecting to the computer…';jobTimer=setTimeout(pollJob,4000);}
}
function localBackup(){try{localStorage.setItem('lamplight-draft',JSON.stringify(draft));}catch{toast('Browser backup is full. Save or export your manuscript.');}}
function markDraft(){draftDirty=true;draftVersion++;draft.updated=new Date().toISOString();localBackup();clearTimeout(saveTimer);saveTimer=setTimeout(()=>saveDraft().catch(showError),900);}
function captureWriter(){if($('#manuscript')){const text=$('#manuscript').value,title=$('#draft-title').value||'Untitled manuscript';if(text!==draft.text||title!==draft.title){draft={...draft,text,title};markDraft();}}}
function saveDraft(){
  captureWriter();if(!draftDirty)return saveChain;
  const snapshot={...draft},version=draftVersion;
  saveChain=saveChain.catch(()=>{}).then(async()=>{const saved=await api('document',snapshot);db.documents=db.documents.filter(d=>d.id!==saved.id).concat(saved);if(draft.id===saved.id&&version===draftVersion){draftDirty=false;if($('#save-state'))$('#save-state').textContent='Saved to your library';}updateHome();return saved;});return saveChain;
}
function renderWriter(){
  shell('Make a little room for your words.','YOUR MANUSCRIPT');
  body.innerHTML=deskTabs('writer')+`<div class="toolbar"><input id="draft-title" aria-label="Manuscript title" maxlength="300" value="${esc(draft.title)}" style="flex:1"><select id="draft-select" class="draft-selector" aria-label="Open saved manuscript"><option value="">Saved manuscripts (${db.documents.length})</option>${[...db.documents].reverse().map(d=>`<option value="${d.id}">${esc(d.title)}</option>`).join('')}</select><button class="secondary" data-action="new-draft">+ New</button></div><div class="writer-toolbar"><button data-action="format-text" data-format="bold" aria-label="Bold"><b>B</b></button><button data-action="format-text" data-format="italic" aria-label="Italic"><i>I</i></button><button data-action="format-text" data-format="heading" aria-label="Heading">H</button><button data-action="format-text" data-format="quote" aria-label="Block quote">❞</button><button data-action="preview">${preview?'Edit':'Preview'}</button><span id="word-count">${words(draft.text).toLocaleString()} words</span></div>${preview?`<article class="preview">${markdown(draft.text)}</article>`:`<textarea id="manuscript" class="manuscript" aria-label="Manuscript" placeholder="Every story begins somewhere. This one begins here…" spellcheck="true">${esc(draft.text)}</textarea>`}<div class="pagination"><span id="save-state">${draftDirty?'Saving…':'Saved locally · Markdown formatting'}</span><div><button class="secondary" data-action="save-draft">Save</button> <button class="secondary" data-action="export">Export .md ↓</button> <button class="primary" data-view="residents">Ask a regular ↗</button></div></div><div id="job-area"></div>`;
  $('#manuscript')?.addEventListener('input',()=>{draft.text=$('#manuscript').value;draft.title=$('#draft-title').value||'Untitled manuscript';markDraft();$('#word-count').textContent=words(draft.text).toLocaleString()+' words';$('#save-state').textContent='Saving…';});
  $('#draft-title').addEventListener('input',e=>{draft.title=e.target.value||'Untitled manuscript';markDraft();});
  $('#draft-select').addEventListener('change',async e=>{const id=e.target.value;if(!id)return;try{await saveDraft();draft={...db.documents.find(d=>d.id===id)};draftDirty=false;localBackup();renderWriter();}catch(error){showError(error);}});renderJob();
}
function markdown(text){
  return esc(text).split(/\n\n+/).map(block=>{const inline=block.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\*([^*]+)\*/g,'<em>$1</em>');if(/^#{1,3} /.test(inline)){const n=inline.match(/^#+/)[0].length;return `<h${n}>${inline.replace(/^#+ /,'')}</h${n}>`;}if(inline.startsWith('&gt; '))return `<blockquote>${inline.slice(5)}</blockquote>`;return `<p>${inline.replaceAll('\n','<br>')}</p>`;}).join('');
}
function formatText(type){const el=$('#manuscript');if(!el)return;const [a,b]=[el.selectionStart,el.selectionEnd],selection=el.value.slice(a,b)||'your words';const pair={bold:['**','**'],italic:['*','*'],heading:['\n## ',''],quote:['\n> ','']}[type];el.setRangeText(pair[0]+selection+pair[1],a,b,'select');el.dispatchEvent(new Event('input'));el.focus();}
function exportDraft(){captureWriter();const blob=new Blob([`# ${draft.title}\n\n${draft.text}`],{type:'text/markdown;charset=utf-8'});const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=draft.title.replace(/[^\p{L}\p{N}\s_-]/gu,'').slice(0,100)+'.md';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function renderResidents(){
  shell('Good company for a work in progress.','THE REGULARS');body.innerHTML=`<p class="muted">A small circle of AI readers, each with a different eye. They see your current manuscript and sampled passages from the books on your trolley.</p><div class="resident-grid">${Object.entries(roles).map(([key,r])=>`<button class="card resident-card" data-action="chat" data-role="${key}">${portrait(key)}<span class="role-pill">${r.role}</span><h3>${r.name}</h3><span class="muted">${r.desc}</span><span class="category-label">${esc(db.settings.agents[key]||db.settings.agent_model)}</span><span class="text-button">Pull up a chair ↗</span></button>`).join('')}</div><p class="muted">Shared resident model: ${esc(db.settings.agent_model)}. <button class="text-button" data-view="settings">Set a model for everyone or for each resident.</button></p>`;
}
function renderChat(){
  const r=roles[chatRole];shell(`A little time with ${r.name}.`,r.role.toUpperCase());
  const suggestions={editor:'Review this manuscript for clarity and structure. Quote the passages you would change and suggest precise fixes.',researcher:'Check my main claims against the selected books. What is supported, what needs evidence, and what should I read next?',professor:'Help me strengthen the argument. What concepts, counterarguments, or historical context am I missing?',publisher:'Who is this manuscript for? Suggest a title, a stronger opening, and the next editorial steps.',friend:'Be my first reader. What is interesting, what feels confusing, and what would you like to hear more about?'};
  body.innerHTML=`<div class="reader-meta"><div class="resident-small">${portrait(chatRole)}<div><strong>${r.name}</strong><small>${esc(db.settings.agents[chatRole]||db.settings.agent_model)} · AI resident</small></div></div><button class="text-button" data-view="residents">Meet the other regulars ↗</button></div><p class="muted">${r.desc}</p><div class="notice">On the table: <strong>${esc(draft.title)}</strong> · ${words(draft.text).toLocaleString()} words · ${state.bag.length} books. Resident feedback uses up to 60,000 manuscript characters and sampled book passages.</div><label>WHAT WOULD YOU LIKE TO TALK ABOUT?<textarea id="agent-request" rows="3" maxlength="8000">${esc(suggestions[chatRole])}</textarea></label><div class="toolbar" style="margin-top:15px"><button class="primary" data-action="ask-agent">Ask ${r.name} ↗</button><button class="secondary" data-view="writer">Back to manuscript</button></div><div id="job-area"></div>${chatResponse?`<div class="agent-response">${esc(chatResponse)}</div><button class="secondary" data-action="append-feedback">Add feedback to manuscript notes</button>`:''}`;renderJob();
}
function renderSettings(){
  const s=settingsDraft;shell('Make yourself at home.','SETTINGS');
  const models=[...new Set(Object.values(db.providers).flatMap(p=>p.models))];
  body.innerHTML=`<datalist id="model-options">${models.map(m=>`<option value="${esc(m)}"></option>`).join('')}</datalist><form id="settings-form"><section class="settings-section"><h3>The computer’s connections</h3><p class="muted">Uses the providers already configured in your .env and local CLIs. Model fields also accept exact IDs beyond the suggested catalog.</p><div class="form-stack"><label>PROVIDER CHAIN · FIRST CHOICE, THEN BACKUPS<input id="setting-chain" value="${esc(s.chain.join(', '))}" placeholder="hyper, go"></label><span class="muted">Available: ${esc(Object.keys(db.providers).join(', '))}</span><div class="form-pair"><label>PLANNER / REVIEWER (PRO)<input id="setting-pro" list="model-options" value="${esc(s.pro)}" required></label><label>WRITER (FLASH)<input id="setting-flash" list="model-options" value="${esc(s.flash)}" required></label></div><div class="form-pair"><label>DEFAULT WRITING LANGUAGE<select id="setting-language"><option value="en" ${s.language==='en'?'selected':''}>English</option></select></label><label>MONTHLY LOCAL CALL BUDGET · 0 MEANS UNLIMITED<input id="setting-budget" type="number" min="0" max="1000000" step="1" value="${s.monthly_calls}"></label></div></div></section><section class="settings-section"><h3>The regulars’ models</h3><label>SHARED MODEL FOR ALL RESIDENTS<input id="setting-agent" list="model-options" value="${esc(s.agent_model)}" required></label><div class="form-pair" style="margin-top:15px">${Object.entries(roles).map(([key,r])=>`<label>${r.name.toUpperCase()} · ${r.role.toUpperCase()}<input data-agent-model="${key}" list="model-options" placeholder="Use shared model" value="${esc(s.agents[key]||'')}"></label>`).join('')}</div></section><section class="settings-section"><h3>Custom OpenAI-compatible providers</h3><p class="muted">Add a chat-completions endpoint and its exact model IDs. Put its key in the named environment variable in .env, then restart the server. Keys stay out of the browser and each provider uses only its own key. A local server that needs no authentication can use a placeholder key.</p><div id="custom-providers">${s.custom.map((p,i)=>`<div class="card custom-provider" data-custom="${i}"><div class="form-pair"><label>PROVIDER ID<input data-field="id" value="${esc(p.id)}" placeholder="my-provider" required></label><label>API BASE URL<input data-field="base_url" type="url" value="${esc(p.base_url)}" placeholder="https://example.com/v1" required></label></div><label>API KEY ENVIRONMENT VARIABLE<input data-field="key_env" value="${esc(p.key_env)}" placeholder="MY_PROVIDER_API_KEY" required></label><div class="form-pair"><label>DEFAULT PRO MODEL<input data-field="pro" value="${esc(p.pro)}" required></label><label>DEFAULT FLASH MODEL<input data-field="flash" value="${esc(p.flash)}" required></label></div><button class="text-button" type="button" data-action="remove-provider" data-index="${i}">Remove custom provider</button></div>`).join('')}</div><button class="secondary" type="button" data-action="add-provider">+ Add custom provider</button></section><div class="toolbar"><button class="primary" type="submit">Save settings</button><button class="secondary" type="button" data-view="usage">Usage & budget ↗</button><span id="settings-status" role="status" class="muted"></span></div></form>`;
  $('#settings-form').addEventListener('submit',async e=>{e.preventDefault();try{captureSettings();await api('settings',settingsDraft);db=await api('bootstrap');language='en';$('#settings-status').textContent='Saved. The computer is ready.';toast('Your library, just the way you like it.');}catch(error){$('#settings-status').textContent=error.message;}});
}
function captureSettings(){
  if(!$('#setting-chain'))return;
  settingsDraft={chain:$('#setting-chain').value.split(',').map(v=>v.trim()).filter(Boolean),pro:$('#setting-pro').value.trim(),flash:$('#setting-flash').value.trim(),language:$('#setting-language').value,monthly_calls:Number($('#setting-budget').value),agent_model:$('#setting-agent').value.trim(),agents:Object.fromEntries([...document.querySelectorAll('[data-agent-model]')].map(e=>[e.dataset.agentModel,e.value.trim()])),custom:[...document.querySelectorAll('[data-custom]')].map(el=>Object.fromEntries([...el.querySelectorAll('[data-field]')].map(e=>[e.dataset.field,e.value.trim()])))};
}
async function renderUsage(){
  shell('A little look under the bonnet.','THE COMPUTER · USAGE');body.innerHTML=deskTabs('usage')+'<div class="loading">Checking your notebook…</div>';
  try{const u=await api('usage');if(view!=='usage')return;body.innerHTML=deskTabs('usage')+`<p class="muted">This calendar month · local activity from the library computer and its residents.</p><div class="metric-grid">${[['AI calls',u.calls,'logical requests'],['Estimated input',u.estimated_input,'tokens · estimate'],['Estimated output',u.estimated_output,'tokens · estimate'],['Local budget',u.budget?Math.max(0,u.budget-u.calls):'∞',u.budget?`calls left of ${u.budget}`:'no local limit set']].map(([title,val,sub])=>`<div class="card metric"><span class="category-label">${title}</span><strong>${typeof val==='number'?val.toLocaleString():val}</strong><small>${sub}</small></div>`).join('')}</div><div class="notice">${esc(u.note)} Failed logical calls: ${u.failed}. The local budget stops new calls when reached; it is not a provider billing limit.</div><button class="secondary" data-view="settings">Adjust your budget</button><div class="table-wrap"><table><thead><tr><th>Time</th><th>Requested model</th><th>Provider chain</th><th>Duration</th><th>Result</th></tr></thead><tbody>${u.recent.length?u.recent.map(e=>`<tr><td>${esc(new Date(e.at).toLocaleTimeString())}</td><td>${esc(e.model)}</td><td>${esc(e.chain.join(' → '))}</td><td>${e.seconds}s</td><td>${e.success?'Completed':'Failed'}</td></tr>`).join(''):'<tr><td colspan="5">No AI calls yet. A fresh page.</td></tr>'}</tbody></table></div>`;}catch(error){if(view==='usage')body.innerHTML=`<div class="notice">${esc(error.message)}</div>`;}
}

function renderCampaign(){
  const c=db.campaign, terms=c.commission;
  const delivered=c.letters.filter(l=>l.delivered&&l.era===c.era);
  shell(('Letters across time'),`${c.year} · ${(c.place)}`);
  body.innerHTML=`<div class="toolbar"><button class="secondary" data-action="campaign-language" data-lang="en" aria-pressed="${language==='en'}">English</button><span class="muted">${('Day')} ${c.day}</span></div>
    <p class="muted">${('You were an ordinary person in the 2020s. Now you have a laptop, an inexplicable LLM connection, and rent to pay in the wrong century. Write, research, and persuade your way to 1930. The laptop translates for you; local people do not know the future.')}</p>
    <div class="tabs">${c.years.map((y,i)=>`<span class="tab ${i===c.era?'selected':''}">${i<c.era?'✓ ':''}${y}</span>`).join('')}</div>
    <div class="metric-grid">${[[('Coins'),c.money],[('Paper'),c.paper],[('Prestige'),c.prestige],[('Research'),c.knowledge]].map(([label,n])=>`<div class="card metric"><span>${label}</span><strong>${n}</strong></div>`).join('')}</div>
    ${c.completed?`<div class="notice">${('Campaign complete. You built a literary and research career across three centuries. Your manuscripts and correspondence remain here.')}</div>`:''}
    <div class="notice">${('Capabilities')}: ${(c.capabilities).map(esc).join(' · ')}<br>${('The room is a stylised fictional setting; travel, economy and postal times are game rules, not historical measurements.')}</div>
    <div class="toolbar"><button class="secondary" data-action="campaign-work" ${c.completed?'disabled':''}>${('Copying shift')} (+${12+3*c.era} ◈, +1 ${('paper')}, 1 ${('day')})</button><button class="secondary" data-action="campaign-wait" ${c.completed?'disabled':''}>${('Wait one day')}</button><button class="secondary" data-view="computer">${('Open laptop')}</button></div>
    <h3>${('Study the period library')}</h3><div class="book-grid">${db.books.map(b=>`<article class="card"><span class="category-label">${b.year} · [B${Math.abs(b.id)}]</span><h3>${esc(b.title)}</h3><p class="muted">${esc(b.notes.en)}</p><div class="toolbar"><button class="secondary" data-action="campaign-study" data-id="${b.id}" ${c.studied.includes(b.id)||c.completed?'disabled':''}>${c.studied.includes(b.id)?('Studied'):('Study · 1 day')}</button><button class="text-button" data-action="bag" data-id="${b.id}">${state.bag.includes(b.id)?('Return'):('Take to desk')}</button></div></article>`).join('')}</div>
    <h3>${('The post desk')}</h3><p class="muted">${('Study a correspondent’s work, send a claim, and choose the challenge you want to explore. Replies take in-game days. These are curated fictional debates, not authentic letters or free-form AI impersonations. Your original claim stays in the envelope; replies draw only on the dated study notes.')}</p>
    <div class="form-pair"><label>${('Correspondent')}<select id="letter-figure">${c.figures.map(f=>`<option value="${f.id}">${esc(f.name)} · [B${Math.abs(f.book)}]</option>`).join('')}</select></label><label>${('Challenge')}<select id="letter-focus"><option value="evidence">${('Evidence')}</option><option value="counterargument">${('Strongest counterargument')}</option><option value="method">${('Method and falsification')}</option></select></label></div>
    <label>${('Continue a debate (optional)')}<select id="letter-parent"><option value="">${('New letter')}</option>${delivered.map(l=>`<option value="${l.id}" data-figure="${l.figure}">${esc(l.name)} · ${('day')} ${l.sent} · ${esc(l.text.slice(0,45))}</option>`).join('')}</select></label>
    <label>${('Your claim and question')}<textarea id="letter-text" rows="4" minlength="20" maxlength="3000" placeholder="${('What can we establish, and what remains uncertain?')}"></textarea></label><div class="toolbar"><button class="primary" data-action="campaign-letter" ${c.completed?'disabled':''}>${('Send letter')} · ${4+c.era} ◈ + 1 ${('paper')}</button><button class="secondary" data-action="campaign-ai-letter" ${c.completed?'disabled':''}>${('Send with AI-written reply')}</button></div>
    <p class="muted">${('Optional AI replies use the configured resident model and may consume provider credits. They receive only period notes and previous delivered correspondence, but can still make historical mistakes. Failed requests spend no game postage. Both reply modes use postal delivery.')}</p><div id="job-area"></div>
    ${c.letters.slice().reverse().map(l=>`<details class="card"><summary>${esc(l.name)} · ${c.years[l.era]} · ${l.delivered?('Delivered'):('Arrives day ')+l.due}</summary><p class="muted">${('Your letter')}: ${esc(l.text)}</p>${l.delivered?`<div class="agent-response">${esc(l.answer)}</div><p class="muted">${esc(l.simulation)} · [L${l.id}]</p><button class="secondary" data-action="campaign-note" data-letter="${l.id}">${('Add to manuscript notes')}</button>`:''}</details>`).join('')}
    <h3>${('A commission for this era')}</h3><p class="muted">${('Save a new manuscript with')} ${terms.words}+ ${('words, using')} ${terms.sources} ${('studied sources from your trolley, including a newly unlocked work. Credit them with [Bnumber] markers.')} ${terms.letter?('Address a delivered letter from this era and include its [Lid] marker.'):''}</p>
    <p class="notice">${('Payment')}: ${terms.payment} ◈ + ${terms.prestige} ${('prestige')} · ${('Cost')}: ${terms.paper} ${('paper and two days')}. ${('These are mechanical game checks, not an assessment of literary quality, historical accuracy or originality. No real publication or money is involved.')}</p>
    <label>${('Letter addressed in the manuscript')}<select id="commission-letter"><option value="">—</option>${delivered.map(l=>`<option value="${l.id}">${esc(l.name)} · ${l.sent}</option>`).join('')}</select></label>
    <p class="muted">${('Current manuscript')}: ${esc(draft.title)} · ${words(draft.text)} ${('words')}<br>${('Selected studied sources')}: ${state.bag.filter(id=>c.studied.includes(id)).map(id=>`[B${Math.abs(id)}]`).join(', ')||'—'}</p>
    <div class="toolbar"><button class="secondary" data-action="campaign-sources">${('Add source notes to manuscript')}</button><button class="secondary" data-view="writer">${('Edit manuscript')}</button><button class="primary" data-action="campaign-publish" ${c.completed?'disabled':''}>${('Submit current manuscript')}</button></div>
    <h3>${c.era===6?('Establish your legacy'):('Charge the time machine')}</h3>
    <ul>${Object.entries(c.requirements).map(([key,n])=>`<li>${esc({money:('Coins'),paper:('Paper'),prestige:('Prestige'),knowledge:('Research'),publications:('Publications this era')}[key])}: ${key==='publications'?c.era_publications:c[key]} / ${n}</li>`).join('')}</ul>
    <p class="muted">${('Coins and paper are spent; research, prestige, manuscripts and delivered mail travel with you. Collect pending letters before leaving.')}</p>
    <button class="primary" data-action="campaign-jump" ${!c.can_jump?'disabled':''}>${c.era===6?('Complete campaign'):('Jump to ')+c.years[c.era+1]}</button>`;
  $('#letter-parent').addEventListener('change',e=>{const option=e.target.selectedOptions[0];if(option.dataset.figure)$('#letter-figure').value=option.dataset.figure;});
  renderJob();
}
async function campaignAction(action, extra={}){
  db.campaign=await api('campaign',{action,...extra});
  if(action==='jump'){const fresh=await api('bootstrap');db.books=fresh.books;state.bag=state.bag.filter(id=>book(id));remember();}
  updateHome();renderCampaign();
}
function renderCoffee(){
  shell('But first, coffee.','A VERY IMPORTANT SIDE QUEST');body.innerHTML=`<section class="coffee-game"><div class="coffee-cup">☕</div><h2>A small ritual, just for you.</h2><p class="muted">Start pouring, then stop when the little marker reaches the green patch.<br>No hurry. There’s always another pot.</p><div class="coffee-track"><span class="coffee-zone"></span><span class="coffee-needle" id="coffee-needle"></span></div><button class="primary" data-action="brew" id="brew-button">Start pouring</button><p id="coffee-result" class="muted" role="status">${state.cups} lovely cups so far.</p></section>`;coffeeRunning=false;
}
function brew(){
  if(coffeeRunning){const pos=(performance.now()-coffeeStart)%1800/1800*100;coffeeRunning=false;cancelAnimationFrame(coffeeFrame);if(pos>=43&&pos<=60){state.cups++;remember();updateHome();$('#coffee-result').textContent='Just right. Warm hands, clearer thoughts. +1 lovely cup.';}else $('#coffee-result').textContent=pos<43?'A little light. Try another pour?':'A wonderfully strong cup. Try a gentler pour?';$('#brew-button').textContent='Pour another';return;}
  coffeeStart=performance.now();coffeeRunning=true;$('#brew-button').textContent='Stop pouring';
  const tick=()=>{if(!coffeeRunning||view!=='coffee')return;$('#coffee-needle').style.left=((performance.now()-coffeeStart)%1800/1800*100)+'%';coffeeFrame=requestAnimationFrame(tick);};tick();
}
function renderHelp(){shell('Settle in. You belong here.','A LITTLE FIELD GUIDE');body.innerHTML=`<ol class="help-list"><li>Walk with WASD or the arrow keys. Click a destination to find your way there.</li><li>Press E near a shelf, resident, or computer to interact. Clicking them walks you over.</li><li>Take up to 12 books on your trolley. Read, search inside, and pick your typography.</li><li>At the computer, choose a format and find ideas from your selected books.</li><li>Write automatically, make guided decisions, or work manually in the manuscript editor.</li><li>Ask the regulars for feedback. Their responses stay separate until you add them as notes.</li><li>Make a coffee. Visit Miso the cat. Look for three little treats around the room.</li></ol><p class="notice">Keyboard shortcuts: 1 library · 2 books · 3 computer · 4 manuscripts · 5 regulars. Escape closes a panel. Ctrl/Cmd+S saves your manuscript. All room interactions also have accessible navigation buttons.</p><div class="toolbar"><button class="secondary" data-view="coffee">Coffee break</button><button class="secondary" data-action="cat">Visit Miso</button>${['plant1','plant2','globe'].map((id,i)=>`<button class="secondary" data-action="find-treat" data-id="${id}">${['Inspect the west fern','Inspect the east fern','Inspect the globe'][i]}</button>`).join('')}</div>`;}
function visitCat(){if(state.treats.length===3){toast('Miso accepts your three treats and appoints you Assistant Head of Naps. Prrr.');state.catFriend=true;remember();}else toast(`Miso blinks slowly. A friend already. ${state.treats.length}/3 treats found near the ferns and globe.`);}
function findTreat(id){if(state.treats.includes(id))return toast('Just a happy plant and a pleasant little memory.');state.treats.push(id);remember();toast(`A tiny cat treat! ${state.treats.length}/3 found. Miso will be pleased.`);}
async function toggleSound(){
  if(!soundContext){soundContext=new AudioContext();soundGain=soundContext.createGain();soundGain.gain.value=.025;soundGain.connect(soundContext.destination);const length=soundContext.sampleRate*3,buffer=soundContext.createBuffer(1,length,soundContext.sampleRate),samples=buffer.getChannelData(0);let prev=0;for(let i=0;i<length;i++){prev=(prev+Math.random()*.04-.02)/1.02;samples[i]=prev*3;}const rain=soundContext.createBufferSource();rain.buffer=buffer;rain.loop=true;const filter=soundContext.createBiquadFilter();filter.type='lowpass';filter.frequency.value=1200;rain.connect(filter);filter.connect(soundGain);rain.start();for(const freq of [130.81,164.81,196,246.94]){const osc=soundContext.createOscillator(),gain=soundContext.createGain();osc.type='sine';osc.frequency.value=freq;gain.gain.value=.08;osc.connect(gain);gain.connect(soundGain);osc.start();}}else if(soundContext.state==='running')await soundContext.suspend();else await soundContext.resume();const on=soundContext.state==='running';$('#sound').setAttribute('aria-pressed',String(on));$('#sound span').textContent=on?'Rain & quiet':'Sound off';
}
$('#sound').addEventListener('click',()=>toggleSound().catch(showError));
document.addEventListener('click',async e=>{
  const el=e.target.closest('button[data-view],button[data-action]');if(!el||el.disabled)return;
  if(el.dataset.view){open(el.dataset.view);return;}
  const a=el.dataset.action,id=Number(el.dataset.id);
  try{
    if(a==='collection'){selectCollection(el.dataset.collection);renderCatalog();}
    else if(a==='campaign-language'){language=el.dataset.lang;renderCampaign();}
    else if(a==='campaign-work'||a==='campaign-wait'||a==='campaign-jump'){el.disabled=true;await campaignAction(a.slice(9));}
    else if(a==='campaign-study'){el.disabled=true;await campaignAction('study',{book:id});}
    else if(a==='campaign-letter'){el.disabled=true;await campaignAction('letter',{figure:$('#letter-figure').value,focus:$('#letter-focus').value,text:$('#letter-text').value,reply_to:$('#letter-parent').value||null,language});}
    else if(a==='campaign-ai-letter'){el.disabled=true;const result=await api('job',{kind:'letter',figure:$('#letter-figure').value,focus:$('#letter-focus').value,text:$('#letter-text').value,reply_to:$('#letter-parent').value||null,language});currentJob={id:result.id,kind:'letter',status:'running',logs:[]};renderJob();pollJob();}
    else if(a==='campaign-publish'){el.disabled=true;const letter=$('#commission-letter').value;await saveDraft();await campaignAction('publish',{document:draft.id,books:state.bag.filter(id=>db.campaign.studied.includes(id)),letter});}
    else if(a==='campaign-sources'){for(const id of state.bag.filter(id=>db.campaign.studied.includes(id))){const b=book(id);draft.text+=`\n\n[B${Math.abs(id)}] ${b.title}\n${b.notes.en}`;}markDraft();open('writer');}
    else if(a==='campaign-note'){const l=db.campaign.letters.find(l=>l.id===el.dataset.letter&&l.delivered);if(l){draft.text+=`\n\n[L${l.id}] ${('Fictional letter from')} ${l.name}\n${l.answer}`;markDraft();open('writer');}}
    else if(a==='help')open('help');
    else if(a==='category'){category=el.dataset.category;catalogPage=0;renderCatalog();}
    else if(a==='catalog-prev'||a==='catalog-next'){catalogPage+=a==='catalog-prev'?-1:1;renderBookResults();panel.scrollTop=0;}
    else if(a==='bag')toggleBag(id);
    else if(a==='read')await readBook(id);
    else if(a==='favorite'){state.favorites=state.favorites.includes(id)?state.favorites.filter(v=>v!==id):[...state.favorites,id];remember();renderBookResults();}
    else if(a==='favorites'){favoritesOnly=!favoritesOnly;catalogPage=0;renderCatalog();}
    else if(a==='page-prev')setPage(readPage-1);
    else if(a==='page-next')setPage(readPage+1);
    else if(a==='find-next')findNext();
    else if(a==='ideas'||a==='generate'||a==='ask-agent'){el.disabled=true;await beginJob(a==='ideas'?'ideas':a==='generate'?'generate':'agent');}
    else if(a==='choose-idea'){brief=ideas[Number(el.dataset.index)].title+'\n\n'+ideas[Number(el.dataset.index)].hypothesis;renderComputer();$('#brief').focus();}
    else if(a==='answer'){el.disabled=true;await api('answer',{id:currentJob.id,answer:$('#job-answer').value});currentJob.status='running';renderJob();}
    else if(a==='cancel-job'){await api('cancel',{id:currentJob.id});currentJob.status='cancelling';renderJob();}
    else if(a==='load-result'){await saveDraft();draft={id:currentJob.id,title:currentJob.result.title,text:currentJob.result.text};if(view==='writer')renderWriter();markDraft();await saveDraft();open('writer');}
    else if(a==='new-draft'){await saveDraft();draft={id:crypto.randomUUID().replaceAll('-',''),title:'Untitled manuscript',text:''};draftDirty=false;preview=false;localBackup();renderWriter();}
    else if(a==='save-draft'){await saveDraft();toast('Saved to your library.');}
    else if(a==='export')exportDraft();
    else if(a==='format-text')formatText(el.dataset.format);
    else if(a==='preview'){captureWriter();preview=!preview;renderWriter();}
    else if(a==='chat'){chatResponse='';open('chat',el.dataset.role);}
    else if(a==='append-feedback'){draft.text+='\n\n## Notes from '+roles[chatRole].name+'\n\n'+chatResponse;markDraft();open('writer');}
    else if(a==='add-provider'){captureSettings();settingsDraft.custom.push({id:'',base_url:'',key_env:'',pro:'',flash:''});renderSettings();}
    else if(a==='remove-provider'){captureSettings();settingsDraft.custom.splice(Number(el.dataset.index),1);renderSettings();}
    else if(a==='brew')brew();
    else if(a==='cat')visitCat();
    else if(a==='find-treat')findTreat(el.dataset.id);
  }catch(error){showError(error);}finally{if(el.isConnected)el.disabled=false;}
});
window.addEventListener('keydown',e=>{
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();saveDraft().then(()=>toast('Saved to your library.')).catch(showError);return;}
  if(panel.open||/INPUT|TEXTAREA|SELECT/.test(e.target.tagName)||e.ctrlKey||e.metaKey||e.altKey)return;
  const map={'1':'world','2':'catalog','3':'computer','4':'writer','5':'residents','6':'campaign'};if(map[e.key])open(map[e.key]);
});
window.addEventListener('beforeunload',e=>{captureWriter();if(draftDirty){e.preventDefault();e.returnValue='';}});
async function init(){
  try{db=await api('bootstrap');state={...state,...db.state,reader:{...state.reader,...db.state.reader}};state.bag=state.bag.filter(id=>book(id));state.favorites=state.favorites.filter(id=>book(id));language='en';
    const saved=[...db.documents].sort((a,b)=>b.updated.localeCompare(a.updated))[0];if(saved)draft={...saved};
    try{const backup=JSON.parse(localStorage.getItem('lamplight-draft'));if(backup&&typeof backup.text==='string'&&typeof backup.title==='string'&&/^[a-f0-9]{32}$/.test(backup.id)){const matching=db.documents.find(d=>d.id===backup.id);if(!matching||(backup.updated||'')>(matching.updated||'')){draft=backup;if(!matching||matching.text!==backup.text||matching.title!==backup.title)markDraft();}else draft={...matching};}}catch{toast('Could not restore the browser backup. Saved manuscripts remain available.');}
    $('#resident-row').innerHTML=['editor','researcher','friend'].map(key=>`<button class="resident-small" data-action="chat" data-role="${key}">${portrait(key)}<span><strong>${roles[key].name}</strong><small>${roles[key].role.replace('The ','')}</small></span></button>`).join('');
    updateHome();world=createWorld($('#world'),(id,arg)=>{if(roles[id]){chatResponse='';open('chat',id);}else if(id==='catalog')open('catalog',arg);else if(id==='reader'){state.lastBook?readBook(state.lastBook):open('catalog');}else if(id==='cat')visitCat();else if(['plant1','plant2','globe'].includes(id))findTreat(id);else if(id==='fire')toast('The fire crackles. For a moment, there’s nowhere else to be.');else if(id==='sofa')toast('You sit for a little while. Even unwritten words need room to breathe.');else if(id.startsWith('plant'))toast('New leaves. Slow growth is still growth.');else open(id);},position=>{state.position=position;remember();},state.position);
    currentJob=db.jobs.find(j=>['running','waiting','cancelling'].includes(j.status))||db.jobs[0]||null;
    if(currentJob?.kind==='ideas'&&currentJob.result)ideas=currentJob.result.ideas;
    if(currentJob&&['running','waiting','cancelling'].includes(currentJob.status))pollJob();
    $('#connection').textContent=`${db.books.length.toLocaleString()} books · Your library is open`;
    const updateClock=()=>$('#clock').textContent=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});updateClock();setInterval(updateClock,60000);
  }catch(error){$('#connection').textContent='Could not open the library';toast(error.message);body.innerHTML=`<div class="notice error-text">${esc(error.message)}</div><p class="muted">Run python game_server.py, then reload this page.</p>`;panel.showModal();}
}
init();
