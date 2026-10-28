
(function(){
'use strict';
var STORE='student-money-experience-v2', PROFILE='student-money-profile-v2', TOUR='student-money-tour-v2';
var app=document.getElementById('app'),overlay=document.getElementById('overlay-root'),toastRoot=document.getElementById('toast-root');
var state=loadState(),profile=loadProfile(),page='dashboard',onStep=1,introStep=0,selectedGoals=[],selectedPersona='student',allowanceCadence='weekly',budgetPreset='balanced',tourStep=0,chatMessages=[],activityFilter='all',activitySearch='';
var goalOptions=[
 {id:'emergency',emoji:'🛟',title:'Build a safety cushion',detail:'Feel ready for surprises',target:30000,color:'mint'},
 {id:'school',emoji:'🎓',title:'Pay school fees',detail:'Plan ahead for school',target:150000,color:'blue'},
 {id:'laptop',emoji:'💻',title:'Buy a laptop',detail:'Invest in your learning',target:250000,color:'purple'},
 {id:'business',emoji:'🚀',title:'Start a side hustle',detail:'Turn an idea into income',target:50000,color:'peach'},
 {id:'travel',emoji:'✈️',title:'Save for a trip',detail:'Make a memory',target:100000,color:'pink'},
 {id:'freedom',emoji:'🌱',title:'Feel financially free',detail:'Build better money habits',target:50000,color:'yellow'}
];
var goalCategories=[
 {id:'education',label:'Education & career',emoji:'🎓',hint:'Fees, books, certifications, exam prep'},
 {id:'tech',label:'Tech & creative work',emoji:'💻',hint:'Laptop, phone, software, creative tools'},
 {id:'business',label:'Business & side hustle',emoji:'🚀',hint:'Stock, equipment, first customers'},
 {id:'health',label:'Health & wellbeing',emoji:'🌿',hint:'Health needs, fitness, personal care'},
 {id:'independence',label:'Independence & home',emoji:'🏡',hint:'Rent, furniture, moving out'},
 {id:'family',label:'Family & community',emoji:'🤝',hint:'Support loved ones and community'},
 {id:'travel',label:'Travel & experiences',emoji:'✈️',hint:'Trips, events, memorable experiences'},
 {id:'safety',label:'Safety & peace of mind',emoji:'🛟',hint:'Emergency fund and unexpected costs'},
 {id:'personal',label:'Personal dream',emoji:'✨',hint:'Anything meaningful to you'}
];
var goalIdeas=[
 {id:'fees',category:'education',name:'School fees',emoji:'🎓',target:150000},
 {id:'cert',category:'education',name:'Certification or exam',emoji:'📜',target:50000},
 {id:'books',category:'education',name:'Books and study materials',emoji:'📚',target:30000},
 {id:'laptop',category:'tech',name:'Laptop for my future',emoji:'💻',target:250000},
 {id:'phone',category:'tech',name:'Phone or creative gear',emoji:'📱',target:120000},
 {id:'portfolio',category:'tech',name:'Creative tools and portfolio',emoji:'🎨',target:50000},
 {id:'business-stock',category:'business',name:'First business stock',emoji:'🛍️',target:75000},
 {id:'business-tools',category:'business',name:'Tools for my side hustle',emoji:'🧰',target:100000},
 {id:'business-launch',category:'business',name:'Launch my idea',emoji:'🚀',target:50000},
 {id:'health',category:'health',name:'Health and wellbeing',emoji:'🌿',target:30000},
 {id:'rent',category:'independence',name:'Moving out / rent fund',emoji:'🏡',target:200000},
 {id:'home',category:'independence',name:'Room essentials',emoji:'🪴',target:80000},
 {id:'family',category:'family',name:'Support my family',emoji:'🤝',target:50000},
 {id:'trip',category:'travel',name:'My next trip',emoji:'✈️',target:100000},
 {id:'emergency',category:'safety',name:'Emergency cushion',emoji:'🛟',target:30000},
 {id:'dream',category:'personal',name:'My own big dream',emoji:'✨',target:50000}
];
var palettes=[
 {id:'violet',name:'Dreamy violet',desc:'Creative, confident, modern',colors:['#6658e8','#b8a7ff','#f0edff','#292448']},
 {id:'ocean',name:'Ocean calm',desc:'Clear, cool, focused',colors:['#087e8b','#5bc0be','#e2f6f5','#143b4a']},
 {id:'sunset',name:'Sunset glow',desc:'Warm, bold, optimistic',colors:['#e76f51','#f4a261','#fff0df','#5d2d25']},
 {id:'forest',name:'Forest fresh',desc:'Grounded, peaceful, natural',colors:['#26845b','#7cc8a3','#e4f7ec','#183d2c']},
 {id:'rose',name:'Rose studio',desc:'Soft, expressive, stylish',colors:['#c45183','#f0a6ca','#fff0f6','#54263f']},
 {id:'midnight',name:'Midnight neon',desc:'Esports energy, deep and electric',colors:['#8a5cf6','#36d6c5','#17172c','#f4f1ff']}
];
var categoryDefaults={Food:5000,Transport:2400,'Airtime & data':3000,School:5000,Housing:10000,Other:3000};
var categoryInfo={
 'Food':{emoji:'🍲',color:'#ffe7d8',ink:'#cf6e43'},'Transport':{emoji:'🛵',color:'#e2edff',ink:'#3976cf'},
 'Airtime & data':{emoji:'📱',color:'#e8e2ff',ink:'#6c5de3'},'School':{emoji:'📚',color:'#fff1c8',ink:'#b27e1d'},
 'Housing':{emoji:'🏠',color:'#dff7e9',ink:'#26885f'},'Other':{emoji:'✨',color:'#ffe2f1',ink:'#bd5089'},
 'Income':{emoji:'💚',color:'#dff7e9',ink:'#26885f'}
};
function loadState(){try{var o=JSON.parse(localStorage.getItem(STORE)||'null');return o&&typeof o==='object'?o:{onboarded:false,balance:5000,allowance:10000,budget:Object.assign({},categoryDefaults),transactions:[],goals:[],savingsTarget:2000,cadence:'weekly',notifications:[]};}catch(e){return {onboarded:false,balance:5000,allowance:10000,budget:Object.assign({},categoryDefaults),transactions:[],goals:[],savingsTarget:2000,cadence:'weekly',notifications:[]};}}
function loadProfile(){try{return JSON.parse(localStorage.getItem(PROFILE)||'{}')}catch(e){return {};}}
function persist(){try{localStorage.setItem(STORE,JSON.stringify(state));localStorage.setItem(PROFILE,JSON.stringify(profile));return true;}catch(e){showToast('Your browser could not save this change. Export your records as a backup.');return false;}}
function fmt(n){return new Intl.NumberFormat('fr-FR',{maximumFractionDigits:0}).format(Math.round(Number(n)||0))+' FCFA';}
function shortMoney(n){n=Number(n)||0;if(n>=1000000)return (n/1000000).toFixed(1)+'M';if(n>=10000)return Math.round(n/1000)+'k';if(n>=1000)return (n/1000).toFixed(1)+'k';return String(Math.round(n));}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function nowDate(){return new Date().toLocaleDateString('en-GB',{day:'numeric',month:'short'});}
function greeting(){var h=new Date().getHours();return h<12?'Good morning':h<17?'Good afternoon':'Good evening';}
function iconInfo(cat){return categoryInfo[cat]||categoryInfo.Other;}
function totals(){var income=0,spent=0;state.transactions.forEach(function(t){var amount=Math.max(0,Number(t.amount)||0);if(t.type==='income')income+=amount;else if(t.type==='expense')spent+=amount;});return {income:income,spent:spent};}
function weekStartTimestamp(date){
 var d=date?new Date(date):new Date();d.setHours(0,0,0,0);d.setDate(d.getDate()-((d.getDay()+6)%7));return d.getTime();
}
function transactionsBetween(start,end){
 return (Array.isArray(state.transactions)?state.transactions:[]).filter(function(t){var at=Number(t.createdAt)||0;return at>=start&&at<end;});
}
function sumTransactions(records,type){
 return (records||[]).reduce(function(sum,t){return sum+(t.type===type?Math.max(0,Number(t.amount)||0):0);},0);
}
function transactionMatchesFilter(t,filter){
 return filter==='all'||(filter==='savings'?t.type==='transfer':t.type===filter);
}
function weeklyAllowance(){if(state.cadence==='monthly')return Math.round(state.allowance/4.33);if(state.cadence==='irregular')return state.allowance;return state.allowance;}
function categoryFor(text){
 var s=String(text||'').toLowerCase();
 if(/food|lunch|dinner|breakfast|bread|meal|restaurant|chop|snack|drink|nourriture|repas|déjeuner|dejeuner|dîner|diner|petit-déjeuner|pain|beignet|boisson|manger/.test(s))return 'Food';
 if(/taxi|transport|bus|bike|ride|fuel|car|moto|mototaxi|essence|carburant|trajet|déplacement|deplacement/.test(s))return 'Transport';
 if(/airtime|data bundle|internet|mtn|orange money|wifi|megabyte|forfait|connexion|crédit téléphonique|credit telephonique|méga|mega/.test(s))return 'Airtime & data';
 if(/school|book|print|exam|course|tuition|photocopy|note|école|ecole|scolarité|scolarite|cahier|livre|impression|photocopie|examen|frais scolaires|frais de scolarité/.test(s))return 'School';
 if(/rent|room|house|water|electricity|light bill|loyer|chambre|logement|eau|électricité|electricite|facture/.test(s))return 'Housing';
 return 'Other';
}
function extractAmount(text){
 var source=String(text||'').replace(/\u00a0/g,' ');
 var match=source.match(/(?:^|[^\d])(\d{1,3}(?:[ .,,'’]\d{3})+|\d+)(?:\s*(?:fcfa|xaf|frs))?/i);
 if(!match)return 0;
 var amount=Number(String(match[1]).replace(/\D/g,''));
 return Number.isFinite(amount)?Math.round(amount):0;
}
function brand(){return '<div class="brand"><div class="brand-symbol brand-symbol-tiana">T<span aria-hidden="true">.</span></div><div>TIANA<small>SMART MONEY. BRIGHTER YOU.</small></div></div>';}
function launchConfetti(){var colors=['#6558ed','#ff9c72','#5dce9c','#ffc95d','#e975ad'];for(var i=0;i<26;i++){var el=document.createElement('i');el.className='confetti';el.style.left=(Math.random()*100)+'vw';el.style.background=colors[i%colors.length];el.style.animationDelay=(Math.random()*.55)+'s';el.style.transform='rotate('+(Math.random()*120)+'deg)';document.body.appendChild(el);setTimeout(function(x){x.remove();},1800,el);}}
function showToast(text){toastRoot.innerHTML='<div class="toast" role="status">'+esc(text)+'</div>';setTimeout(function(){toastRoot.innerHTML='';},2800);}
function appNavItems(){return [['dashboard','⌂','Home'],['budgets','▤','Budgets'],['goals','◎','Goals'],['coach','✳','Money Coach'],['more','•••','More']];}
function navBtn(item,active){return '<button class="'+(active===item[0]?'active':'')+'" data-page="'+item[0]+'"><span class="nav-emoji">'+item[1]+'</span><span class="nav-label">'+item[2]+'</span></button>';}
function productFooter(){return '<footer class="footer"><div class="footer-brand"><div class="brand-symbol" style="width:32px;height:32px;border-radius:11px;font-size:16px">✳</div><div>Money, made clearer.<small>Spend smart. Save steadily.</small></div></div><div class="product-links"><button class="'+(page==='dashboard'?'active':'')+'" data-page="dashboard">💜 Money</button><button class="'+(page==='marketplace'?'active':'')+'" data-page="marketplace">🛍️ Marketplace</button><button class="'+(page==='invest'?'active':'')+'" data-page="invest">🌱 Discover business</button></div><div class="footer-meta"><span>Prototype · FCFA · Designed for students in Cameroon</span><span>Your demo entries stay in this browser on this device.</span></div></footer>';}
function txHtml(t){var moved=t.type==='transfer',inf=moved?{emoji:'🎯',color:'#e8f8ef',ink:'#238b5b'}:iconInfo(t.category);var amountClass=(t.type==='income'||moved)?'positive':'negative',sign=t.type==='income'?'+':(moved?'↗':'−');return '<div class="tx"><div class="tx-icon" style="background:'+inf.color+';color:'+inf.ink+'">'+inf.emoji+'</div><div class="tx-copy"><b>'+esc(t.title)+'</b><small>'+esc(moved?'Savings transfer':t.category)+' · '+esc(t.date||nowDate())+'</small></div><div class="tx-amount '+amountClass+'">'+sign+fmt(t.amount)+'</div></div>';}
function pageHead(eyebrow,title,sub){return '<div class="page-head screen"><div class="eyebrow">'+eyebrow+'</div><h1>'+title+'</h1><p>'+sub+'</p></div>';}
function budgetTotal(){return Object.keys(state.budget).reduce(function(s,k){return s+(Number(state.budget[k])||0);},0);}
function budgetSpent(cat){var start=weekStartTimestamp(),now=Date.now();return transactionsBetween(start,now).filter(function(t){return t.type==='expense'&&t.category===cat;}).reduce(function(s,t){return s+Math.max(0,Number(t.amount)||0);},0);}
function dashboardPage(){
 var t=totals(),weekStart=weekStartTimestamp(),weekRecords=transactionsBetween(weekStart,Date.now()),spent=sumTransactions(weekRecords,'expense'),planned=budgetTotal(),remaining=Math.max(0,planned-spent);
 var entries=Object.keys(state.budget).map(function(c){return {name:c,total:budgetSpent(c),limit:Number(state.budget[c])||0,info:iconInfo(c)};});
 var colors={Food:'#ff825f',Transport:'#38b6ee','Airtime & data':'#8b68f5',School:'#f2bd45',Housing:'#38bf91',Other:'#e977b1'};
 var active=entries.filter(function(x){return x.total>0;}).sort(function(a,b){return b.total-a.total;});
 var legend=active.slice(0,5).map(function(x){return '<div class="spend-legend-row"><span class="legend-dot" style="background:'+colors[x.name]+'"></span><span>'+esc(x.name)+'</span><b>'+Math.round(x.total/Math.max(1,spent)*100)+'%</b></div>';}).join('');
 var stops=[],cursor=0;
 if(spent>0){active.forEach(function(x){var pct=x.total/spent*100;stops.push(colors[x.name]+' '+cursor+'% '+(cursor+pct)+'%');cursor+=pct;});}
 var donutStyle=spent>0?'conic-gradient('+stops.join(',')+')':'conic-gradient(#ebeafa 0 28%,#d7f4e3 28% 50%,#fff0c9 50% 74%,#e3efff 74% 100%)';
 var goal=state.goals[0];
 var goalRows=state.goals.slice(0,2).map(function(g){var pct=Math.min(100,Math.round(g.saved/Math.max(1,g.target)*100));return '<div class="goal-mini-row"><div class="goal-mini-emoji">'+esc(g.emoji||'🎯')+'</div><div class="goal-mini-copy"><b>'+esc(g.name)+'</b><small>'+fmt(g.saved)+' of '+fmt(g.target)+'</small><div class="bar"><i style="width:'+pct+'%;background:#6758ed"></i></div></div><div class="goal-mini-value">'+pct+'%</div></div>';}).join('');
 var tip=active.length?'You’ve spent the most on '+active[0].name.toLowerCase()+'. Check your budget before your next purchase.':'Start by recording a few expenses. Your money coach will help you spot patterns.';
 return '<section class="welcome screen"><div><div class="eyebrow">'+greeting().toUpperCase()+' · '+new Date().toLocaleDateString('en-GB',{weekday:'long',day:'numeric',month:'short'}).toUpperCase()+'</div><h1>Hey, '+esc(profile.name||'Student')+' 👋<br><span>you’ve got this.</span></h1></div><div class="welcome-side"><span class="pill"><span class="dot"></span> FCFA money space</span><button class="button secondary small" data-action="start-tour">Quick tour ↗</button></div></section>'+
 '<section class="balance-card screen" data-tour-target="balance"><div class="balance-info"><div class="balance-label">AVAILABLE BALANCE <span style="font-size:12px;opacity:.9">◉</span></div><div class="balance-number">'+fmt(state.balance)+'</div><div class="balance-sub">Your recorded money · Update anytime</div></div><div class="balance-metrics"><div><span>↙ Money in</span><strong>'+fmt(t.income)+'</strong><small>Recorded income</small></div><div><span>↗ Expenses</span><strong>'+fmt(t.spent)+'</strong><small>Recorded spending</small></div></div></section>'+
 '<section class="quick-actions screen" data-tour-target="quick"><button class="quick-action" data-action="add-tx" data-type="income"><span class="iconbox mint">＋</span><span><b>Add income</b><small>Allowance, gig, gift</small></span></button><button class="quick-action" data-action="add-tx" data-type="expense"><span class="iconbox peach">−</span><span><b>Add expense</b><small>Everyday spending</small></span></button><button class="quick-action" data-action="scan-receipt"><span class="iconbox yellow">🧾</span><span><b>Scan receipt</b><small>Coming soon</small></span></button><button class="quick-action" data-page="coach"><span class="iconbox purple">✳</span><span><b>Money coach</b><small>Get guidance</small></span></button></section>'+
 '<div class="dashboard-grid screen"><section class="panel"><div class="panel-head"><div><div class="mini-label">YOUR MONEY, IN MOTION</div><h2>Recent transactions</h2></div><button class="text-button" data-page="activity">See all →</button></div><div class="tx-list">'+(state.transactions.slice(0,5).map(txHtml).join('')||'<div class="empty-state"><div class="emoji">🌱</div><b>Your story starts here.</b><br>Add your first entry to see it here.</div>')+'</div><button class="bottom-link" data-action="add-tx" data-type="expense">＋ Add a transaction</button></section>'+
 '<section style="display:grid;gap:14px"><section class="panel spending-panel"><div class="panel-head"><div><div class="mini-label">YOUR SPENDING OVERVIEW</div><h2>Where it goes</h2></div><span class="pill">This week</span></div><div class="donut-layout"><div class="donut-chart" style="background:'+donutStyle+'"><div class="donut-hole"><small>THIS WEEK</small><b>'+shortMoney(spent)+'</b><span>FCFA</span></div></div><div class="spend-legend">'+(legend||'<p class="sub">Your categories will appear after you add expenses.</p>')+'</div></div></section>'+
 '<section class="panel"><div class="panel-head"><div><div class="mini-label">FUTURE YOU</div><h2>Savings goals</h2></div><button class="text-button" data-page="goals">See all →</button></div><div class="goal-mini">'+(goalRows||'<div class="empty-state">Choose a goal and start small.</div>')+'</div><button class="bottom-link" data-page="goals">＋ Add a new goal</button></section></section></div>'+
 disciplinePanel()+'<section class="ai-tip screen"><img src="./assets/money-coach.svg" alt=""><div><div class="mini-label">A LITTLE MONEY TIP ✨</div><b>'+esc(tip)+'</b><p>Small steps count. You’re doing great by keeping track.</p></div><button class="button secondary small" data-page="coach">Ask coach →</button></section>';
}
function activityPage(){
 var items=state.transactions.filter(function(t){var match=transactionMatchesFilter(t,activityFilter);var text=(t.title+' '+t.category+' '+(t.type==='transfer'?'savings':'' )).toLowerCase();return match&&text.indexOf(activitySearch.toLowerCase())>=0;});
 return pageHead('TRANSACTIONS','Income & expenses.','Search or filter your entries.')+'<section class="panel"><div class="toolbar"><input class="search" id="activity-search" value="'+esc(activitySearch)+'" placeholder="Search transactions…"><button class="button small" data-action="add-tx" data-type="expense">＋ Add entry</button></div><div class="filter-row">'+[['all','Everything'],['income','Money in'],['expense','Money out'],['savings','Saved']].map(function(v){return '<button class="filter '+(activityFilter===v[0]?'active':'')+'" data-filter="'+v[0]+'">'+v[1]+'</button>';}).join('')+'</div><div class="tx-list">'+(items.map(txHtml).join('')||'<div class="empty-state"><div class="emoji">🔎</div><b>No matching transactions.</b><br>Try another search or add your first entry.</div>')+'</div></section><div class="note" style="margin-top:14px">🔒 These are manually recorded demo entries, not live bank or Mobile Money transactions.</div>';
}
function budgetsPage(){
 var cats=Object.keys(state.budget).map(function(c){var inf=iconInfo(c),used=budgetSpent(c),limit=Number(state.budget[c])||0;var pct=limit?Math.min(100,Math.round(used/limit*100)):0;return '<section class="panel budget-card"><div class="budget-title"><span class="iconbox" style="background:'+inf.color+';color:'+inf.ink+'">'+inf.emoji+'</span><span><b>'+esc(c)+'</b><small>Weekly spending limit</small></span></div><div class="budget-number">'+fmt(used)+' <span style="font:600 9px DM Sans;color:#9597ab">of '+fmt(limit)+'</span></div><div class="bar"><i style="width:'+pct+'%;background:'+inf.ink+'"></i></div><div class="budget-details"><span>'+pct+'% used</span><span>'+fmt(Math.max(0,limit-used))+' left</span></div></section>';}).join('');
 return pageHead('FLEXIBLE BUDGET','Plan your spending.','Set limits that fit your life.')+'<div class="toolbar"><span class="pill">🗓️ Weekly plan · '+fmt(budgetTotal())+'</span><button class="button small" data-action="edit-budget">✎ Edit limits</button></div><div class="budget-grid">'+cats+'</div><div class="note" style="margin-top:15px">💡 Tip: start by covering food, transport, school and data. It’s okay if your budget changes when life does.</div>';
}
function goalsPage(){
 var activeCategory=window.__goalCategory||'education';
 var categories=goalCategories.map(function(c){return '<button class="goal-category-chip '+(activeCategory===c.id?'active':'')+'" data-goal-category="'+c.id+'"><span>'+c.emoji+'</span><b>'+esc(c.label)+'</b></button>';}).join('');
 var ideas=goalIdeas.filter(function(g){return g.category===activeCategory;}).map(function(g){
  var exists=state.goals.some(function(x){return x.ideaId===g.id||x.name===g.name;});
  return '<button class="goal-idea-card" data-goal-idea="'+g.id+'"><span class="goal-idea-emoji">'+g.emoji+'</span><span class="goal-idea-copy"><b>'+esc(g.name)+'</b><small>Suggested target · '+fmt(g.target)+'</small></span><span class="goal-idea-add">'+(exists?'✓':'＋')+'</span></button>';
 }).join('');
 var cards=state.goals.map(function(g){
  var pct=Math.min(100,Math.round((Number(g.saved)||0)/Math.max(1,Number(g.target)||1)*100));
  var category=goalCategories.find(function(c){return c.id===g.category;});
  return '<section class="panel goal-card premium-goal-card"><div class="goal-card-head"><div class="goal-card-icon">'+esc(g.emoji||'🎯')+'</div><button class="text-button" data-action="goal-menu" data-id="'+esc(g.id)+'">•••</button></div><div class="goal-personal-tag">'+esc(category?category.label:(g.category||'Personal dream'))+'</div><h3>'+esc(g.name)+'</h3><p>'+esc(g.note||'Your dream, your pace. Every small step counts.')+'</p><div class="goal-saved">'+fmt(g.saved)+' <small>of '+fmt(g.target)+'</small></div><div class="bar"><i style="width:'+pct+'%;background:linear-gradient(90deg,var(--purple),var(--accent-2))"></i></div><div class="goal-bottom"><span>'+pct+'% there</span><span>'+fmt(Math.max(0,g.target-g.saved))+' to go</span></div><button class="button secondary full small" style="margin-top:16px" data-action="add-saving" data-id="'+esc(g.id)+'">＋ Add savings</button></section>';
 }).join('');
 return pageHead('YOUR LIFE, YOUR GOALS','Build a future that feels like yours.','Different dreams. Different paths. One plan shaped around you.')+
 '<section class="goal-hero-panel"><div><div class="goal-hero-kicker">A LITTLE CLOSER, EVERY WEEK ✨</div><h2>What matters to <em>you?</em></h2><p>Choose a career, a personal milestone, or a dream nobody else needs to understand. Your goals should fit your life—not a template.</p><button class="button light" data-action="new-goal">＋ Create a personal goal</button></div><div class="goal-hero-orbit"><span>🎓</span><span>💻</span><span>🚀</span><span>🏡</span><div>YOUR<br>FUTURE</div></div></section>'+
 '<div class="goal-section-heading"><div><div class="mini-label">MADE FOR DIFFERENT JOURNEYS</div><h2>Explore goal paths</h2></div><span class="pill">'+goalIdeas.length+' ideas to get you started</span></div>'+
 '<div class="goal-category-rail">'+categories+'</div><div class="goal-ideas-grid">'+(ideas||'<div class="empty-state">Your ideas are on the way.</div>')+'</div>'+
 '<div class="goal-section-heading"><div><div class="mini-label">YOUR PERSONAL ROADMAP</div><h2>Goals you’re growing</h2></div><span class="pill">'+state.goals.length+' goals</span></div>'+
 '<div class="goal-grid-app">'+(cards||'<div class="goal-empty-premium"><span>🌱</span><h3>Your next chapter starts here.</h3><p>Choose an idea above or create a goal that is completely your own.</p></div>')+'</div>';
}
function coachPage(){
 if(!chatMessages.length)chatMessages=[{role:'assistant',text:'Hey '+(profile.name||'friend')+'! 👋 I’m your Money Coach preview. You can tell me about a spend, ask if you can afford something, or get help planning your allowance.'}];
 var prompts=['Spent 1,200 FCFA on lunch','Can I afford 3,000 FCFA shoes?','Help me plan my allowance','Where does most of my money go?'];
 return pageHead('YOUR MONEY COACH','Your money, your next move.','Goal-based tips and small daily habits.')+coachGuidancePanel()+'<div class="chat-layout"><section class="panel chat-panel"><header class="chat-head"><img src="./assets/money-coach.svg" alt=""><div><b>Money Coach <span style="color:#8b82ed">✦</span></b><small><span class="online"></span> Interactive preview · Always kind, never judgemental</small></div><span class="pill" style="margin-left:auto">FCFA</span></header><div class="messages" id="messages">'+chatMessages.map(chatHtml).join('')+'</div><div class="chat-compose"><form id="chat-form"><div class="chat-input-row"><input id="chat-text" maxlength="500" autocomplete="off" placeholder="Tell me what’s on your mind…"><button class="send-btn" type="submit" aria-label="Send message">➤</button></div></form><p class="chat-disclaimer">This version uses simple on-device rules, not a connected AI model. Your message stays in this browser. No financial advice or live account access.</p></div></section><aside class="panel suggest-panel"><div class="mini-label">NEED A STARTER?</div><h3>Try asking…</h3><p>Tap one to start a conversation.</p><div class="prompt-list">'+prompts.map(function(p){return '<button data-prompt="'+esc(p)+'">✦ &nbsp;'+esc(p)+'</button>';}).join('')+'</div><div class="tip-card">💛 <b>Quick reminder</b><br>A budget is a guide, not a test.</div></aside></div>';
}
function marketplacePage(){
 var categories=['All','Books & supplies','Tech & gadgets','Tutoring','Creative services','Repairs','Food','Other services'];
 var items=[
 {id:'m-books',name:'Study notes & textbooks',category:'Books & supplies',price:2500,emoji:'📚',desc:'Student-to-student textbooks and revision materials. Confirm edition and condition with the seller before meeting.',seller:'Campus student seller',place:'Local pickup · agree in chat'},
 {id:'m-design',name:'Flyer & social media design',category:'Creative services',price:5000,emoji:'🎨',desc:'A starter design service for student clubs, small businesses and campus events. Share your brief before agreeing a price.',seller:'Independent student creator',place:'Digital delivery'},
 {id:'m-tutor',name:'Peer tutoring session',category:'Tutoring',price:3000,emoji:'🧠',desc:'One-to-one revision support. Agree subject, duration and meeting place with the provider first.',seller:'Student tutor',place:'Campus / online by agreement'},
 {id:'m-repair',name:'Phone & laptop troubleshooting',category:'Repairs',price:2000,emoji:'🛠️',desc:'Initial diagnostic service. Parts and repair costs are not included unless explicitly agreed.',seller:'Independent repair provider',place:'Confirm location first'},
 {id:'m-food',name:'Campus snack pre-order',category:'Food',price:1000,emoji:'🥪',desc:'Example listing for a local student vendor. Confirm ingredients, availability and collection time before paying.',seller:'Student vendor',place:'Pickup by arrangement'},
 {id:'m-tech',name:'Laptop setup & software help',category:'Tech & gadgets',price:2500,emoji:'💻',desc:'Basic device setup and study-tool guidance. Never share passwords or account recovery codes.',seller:'Student tech helper',place:'In person by agreement'}
 ];
 var saved=state.marketSaved||[],q=(window.__marketQuery||'').toLowerCase(),cat=window.__marketCategory||'All';
 var shown=items.filter(function(x){return (cat==='All'||x.category===cat)&&(!q||(x.name+' '+x.category+' '+x.desc).toLowerCase().indexOf(q)>=0);});
 return pageHead('TIANA CAMPUS MARKETPLACE','Good finds. Real student hustle.','Explore useful student services and sample offers. Listings marked as examples are not verified live offers; confirm identity, price and availability independently.')+
 '<section class="market-hero"><div><span class="eyebrow">BUY · SELL · BUILD</span><h2>Your next useful find is closer.</h2><p>Discover student-friendly services, save ideas and register interest. This preview does not process payments.</p><button class="button" data-action="seller-listing">＋ Draft a listing</button></div><img src="./assets/marketplace.svg" alt="Illustration of a shopping bag"></section>'+
 '<div class="market-controls"><label class="market-search">⌕ <input id="market-search" value="'+esc(window.__marketQuery||'')+'" placeholder="Search books, tutoring, repairs…" aria-label="Search marketplace"></label><div class="market-categories">'+categories.map(function(c){return '<button class="filter '+(cat===c?'active':'')+'" data-market-category="'+esc(c)+'">'+esc(c)+'</button>';}).join('')+'</div></div>'+
 '<div class="market-trust-note">ⓘ <span><b>Community preview</b> · Prices and providers below are illustrative examples, not verified offers. Arrange safe public meetups and never prepay a stranger.</span></div>'+
 '<div class="market-listing-grid">'+shown.map(function(x){return '<article class="market-listing"><div class="market-listing-art"><span>'+x.emoji+'</span><button class="save-listing '+(saved.indexOf(x.id)>=0?'saved':'')+'" data-market-save="'+x.id+'" aria-label="Save '+esc(x.name)+'">'+(saved.indexOf(x.id)>=0?'♥':'♡')+'</button></div><div class="market-listing-body"><span class="listing-category">'+esc(x.category)+'</span><h3>'+esc(x.name)+'</h3><p>'+esc(x.desc)+'</p><div class="listing-provider">'+esc(x.seller)+'<small>'+esc(x.place)+'</small></div><div class="listing-footer"><b>'+fmt(x.price)+'</b><button class="button secondary small" data-market-detail="'+x.id+'">View details</button></div></div></article>';}).join('')+'</div>'+(shown.length?'':'<div class="empty-state">No matches yet. Try another search or category.</div>')+
 '<p class="market-footnote">Sample catalogue only. Seller accounts, server-side listing persistence, payments, verified reviews and moderation require a secure backend before public launch.</p>';
}
function investPage(){
 var opportunities=[
 {id:'o-campus',name:'Campus printing service',sector:'Campus services',emoji:'🖨️',summary:'A concept profile for a student-run printing and document service.',stage:'Idea profile',status:'Example · not an offer'},
 {id:'o-creative',name:'Student creative studio',sector:'Creative ventures',emoji:'🎨',summary:'A concept profile for a small design and content studio serving local businesses.',stage:'Idea profile',status:'Example · not an offer'},
 {id:'o-tech',name:'Device repair & learning lab',sector:'Technology',emoji:'🧰',summary:'A concept profile for device support and practical digital-skills workshops.',stage:'Idea profile',status:'Example · not an offer'}
 ];
 var saved=state.savedOpportunities||[];
 return pageHead('STUDENT BUSINESS DISCOVERY','Find ideas worth learning about.','Explore student-business concepts and register interest in future verified profiles—without pretending funding is available today.')+
 '<section class="opportunity-hero"><div><span class="eyebrow">GROWTH WITH YOUR EYES OPEN</span><h2>Back student ambition with better information.</h2><p>Learn how businesses work, compare risks and discover local ventures. This is discovery and education only; no investment is being offered or accepted.</p><div class="opportunity-pills"><span>✓ No deposits</span><span>✓ No promised returns</span><span>✓ Risk-first education</span></div></div><img src="./assets/invest.svg" alt="Plant and coins illustration"></section>'+
 '<div class="goal-section-heading"><div><div class="mini-label">DISCOVERY EXAMPLES</div><h2>Student business ideas</h2></div><button class="button secondary small" data-action="submit-opportunity">＋ Suggest a business</button></div>'+
 '<div class="opportunity-grid">'+opportunities.map(function(o){return '<article class="opportunity-card"><div class="opportunity-art">'+o.emoji+'<span>ILLUSTRATIVE PROFILE</span></div><div class="opportunity-body"><span class="listing-category">'+esc(o.sector)+'</span><h3>'+esc(o.name)+'</h3><p>'+esc(o.summary)+'</p><div class="opportunity-status">'+esc(o.status)+'</div><div class="listing-footer"><small>'+esc(o.stage)+'</small><button class="button secondary small" data-opportunity-interest="'+o.id+'">'+(saved.indexOf(o.id)>=0?'Interest saved':'Register interest')+'</button></div></div></article>';}).join('')+'</div>'+
 '<section class="risk-education"><div class="iconbox mint">🌱</div><div><h3>Before you put money into any business</h3><p>Investments can lose some or all of their value. Returns are not guaranteed; money may be locked in; and a business profile is not proof of performance or regulatory approval. Verify owners, financial records, written terms and applicable authorization independently.</p><p><b>TIANA does not accept investment funds in this version.</b> No funding progress, minimum contribution, returns or verification status are being claimed.</p></div></section>'+
 '<p class="market-footnote">Real opportunities require owner identity checks, moderation, evidence-backed information, privacy controls and legal review. Any future financial execution needs appropriate authorization and a compliant provider.</p>';
}
function comingPage(which){
 var market=which==='marketplace',title=market?'Campus life, with fewer hassles.':'A thoughtful future for student business.',subtitle=market?'Buy, sell, find local services.':'Discover business opportunities.',art=market?'./assets/marketplace.svg':'./assets/invest.svg';
 return '<section class="coming-layout screen"><div class="coming-copy"><div class="coming-status"><span></span> A NEW CHAPTER IS GROWING</div><div class="eyebrow">'+(market?'CAMPUS MARKETPLACE':'STUDENT BUSINESS FUNDING')+'</div><h1>'+ (market?'Your campus.':'Business funding, carefully.')+' <span>'+(market?'One easier place.':'The right way.')+'</span></h1><p>'+subtitle+'</p><button class="button" data-action="interest" data-product="'+which+'">♧ &nbsp; Notify me when it’s ready</button><div class="coming-footnote">'+(market?'Planned: textbooks · gadgets · services · campus deals':'No funds are accepted and no investments or returns are being offered in this preview.')+'</div></div><img class="coming-art" src="'+art+'" alt="'+(market?'Shopping bag illustration':'Growing plant and coins illustration')+'"></section>';
}
function insightsPage(){
 var now=Date.now(),start=weekStartTimestamp(),records=transactionsBetween(start,now+1);
 var dayCount=Math.max(1,Math.min(7,Math.floor((now-start)/86400000)+1));
 var previousStart=start-7*86400000,previousEnd=previousStart+dayCount*86400000;
 var previous=transactionsBetween(previousStart,previousEnd);
 var spent=sumTransactions(records,'expense'),income=sumTransactions(records,'income'),previousSpent=sumTransactions(previous,'expense');
 var difference=previousSpent?Math.round((spent-previousSpent)/previousSpent*100):null;
 var budget=budgetTotal(),left=budget-spent;
 var categories=Object.keys(state.budget||{}).map(function(c){
  var val=records.filter(function(t){return t.type==='expense'&&t.category===c;}).reduce(function(s,t){return s+Number(t.amount||0);},0);
  var limit=Math.max(0,Number(state.budget[c])||0);
  return {name:c,amount:val,limit:limit,left:limit-val,pct:limit?Math.round(val/limit*100):0};
 }).sort(function(a,b){return b.amount-a.amount;});
 var maximum=Math.max(1,...categories.map(function(c){return c.amount;}));
 var categoryRows=categories.map(function(c){
  var info=iconInfo(c.name),w=Math.round(c.amount/maximum*100);
  return '<div class="insight-category"><div class="insight-category-title"><span class="iconbox" style="background:'+info.color+';color:'+info.ink+'">'+info.emoji+'</span><span><b>'+esc(c.name)+'</b><small>'+fmt(c.amount)+(c.limit?' of '+fmt(c.limit):' recorded')+'</small></span><strong>'+c.pct+'%</strong></div><div class="bar"><i style="width:'+w+'%;background:'+info.ink+'"></i></div><div class="insight-category-foot"><span>'+ (c.limit?(c.left>=0?fmt(c.left)+' left':fmt(Math.abs(c.left))+' over'):'No limit set')+'</span><span>'+c.pct+'% of limit</span></div></div>';
 }).join('');
 var dayNames=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],dayRows='';
 for(var d=0;d<7;d++){
  var dayStart=start+d*86400000,dayEnd=dayStart+86400000;
  var val=transactionsBetween(dayStart,dayEnd).filter(function(t){return t.type==='expense';}).reduce(function(s,t){return s+Number(t.amount||0);},0);
  var height=spent?Math.max(val?5:2,Math.round(val/Math.max(1,spent)*100)):2;
  var label=new Date(dayStart).toLocaleDateString('en-GB',{day:'numeric',month:'short'});
  dayRows+='<div class="insight-day"><div class="insight-day-value">'+(val?shortMoney(val):'—')+'</div><div class="insight-day-track"><i style="height:'+height+'%"></i></div><b>'+dayNames[d]+'</b><small>'+label+'</small></div>';
 }
 var goalCards=(state.goals||[]).map(function(g){
  var target=Math.max(0,Number(g.target)||0),saved=Math.max(0,Number(g.saved)||0),remaining=Math.max(0,target-saved);
  var pct=target?Math.min(100,Math.round(saved/target*100)):0;
  var weekly=Math.max(0,Number(state.savingsTarget)||0),eta=weekly?Math.ceil(remaining/weekly):null;
  return '<div class="insight-goal"><div class="insight-goal-icon">'+esc(g.emoji||'🎯')+'</div><div class="insight-goal-main"><div class="insight-goal-title"><b>'+esc(g.name)+'</b><strong>'+pct+'%</strong></div><div class="bar"><i style="width:'+pct+'%;background:linear-gradient(90deg,#6558ed,#36c591)"></i></div><small>'+fmt(saved)+' saved · '+fmt(remaining)+' to go'+(eta!==null?' · about '+eta+' week'+(eta===1?'':'s'):'')+'</small></div></div>';
 }).join('');
 var advice=moneyAdviceSnapshot();
 var comparison=difference===null
  ?(spent?'You are starting a spending baseline. Keep recording this week.':'Add a few transactions to unlock your first comparison.')
  :(difference>0?'Recorded spending is up '+difference+'% versus the same number of days last week. Check essentials and optional purchases before payday.':difference<0?'Recorded spending is down '+Math.abs(difference)+'% versus the same number of days last week. Keep the habits that helped.':'Spending matches the same number of days last week. Look at your category mix for your next improvement.');
 var tone=difference!==null&&difference>0?'watch':'good';
 return pageHead('INSIGHTS & PATTERNS','Learn from your money.','No judgement. Just one useful next step.')+
 '<div class="insight-metrics"><section class="insight-metric"><span class="insight-metric-icon">↗</span><small>SPENT THIS WEEK</small><b>'+fmt(spent)+'</b><span>'+records.filter(function(t){return t.type==='expense';}).length+' recorded expenses</span></section><section class="insight-metric"><span class="insight-metric-icon green">＋</span><small>INCOME THIS WEEK</small><b>'+fmt(income)+'</b><span>Recorded money in</span></section><section class="insight-metric"><span class="insight-metric-icon amber">◷</span><small>BUDGET LEFT</small><b class="'+(left<0?'text-danger':'')+'">'+fmt(left)+'</b><span>'+(left<0?'Over your weekly limits':'Across your weekly categories')+'</span></section><section class="insight-metric"><span class="insight-metric-icon lilac">🎯</span><small>WEEKLY SAVING PLAN</small><b>'+fmt(state.savingsTarget||0)+'</b><span>'+(Number(state.savingsTarget)>0?fmt(Number(state.savingsTarget)*52)+' over a year':'Set a repeatable amount')+'</span></section></div>'+
 '<div class="insights-layout"><section class="panel insight-panel"><div class="panel-head"><div><div class="mini-label">YOUR WEEK</div><h2>Daily spending</h2></div><span class="pill">Monday → Sunday</span></div><div class="insight-week-chart">'+dayRows+'</div><div class="insight-note '+tone+'"><span>'+(tone==='watch'?'👀':'✨')+'</span><div><b>'+ (tone==='watch'?'A pattern worth checking':'Your money check-in')+'</b><p>'+esc(comparison)+'</p></div></div></section>'+
 '<section class="panel insight-panel"><div class="panel-head"><div><div class="mini-label">PERSONALIZED NEXT STEP</div><h2>What to do next</h2></div><span class="pill">Money Coach</span></div><div class="insight-advice"><div class="insight-advice-icon">🧭</div><div><b>'+esc(advice.goalName)+'</b><p>'+esc(advice.focus)+'</p><div class="insight-next"><small>TRY THIS</small>'+esc(advice.nextAction)+'</div></div></div><button class="button full" data-page="coach">Talk it through with your coach →</button></section></div>'+
 '<div class="insights-layout"><section class="panel insight-panel"><div class="panel-head"><div><div class="mini-label">WHERE IT GOES</div><h2>Category check</h2></div><button class="text-button" data-page="budgets">Edit budgets →</button></div><div class="insight-category-list">'+(categoryRows||'<div class="empty-state">Add expenses to see your categories.</div>')+'</div></section>'+
 '<section class="panel insight-panel"><div class="panel-head"><div><div class="mini-label">FUTURE YOU</div><h2>Goal progress</h2></div><button class="text-button" data-page="goals">Manage goals →</button></div><div class="insight-goal-list">'+(goalCards||'<div class="empty-state">Choose one thing you want to save for.</div>')+'</div><div class="insight-save-note">💡 Your goal timeline assumes you keep saving '+fmt(state.savingsTarget||0)+' every week. Change the target whenever your real budget changes.</div></section></div>'+
 '<div class="insight-disclaimer">Insights are calculated from entries you recorded in this browser. They are estimates, not connected bank data.</div>';
}
function morePage(){
 return pageHead('MORE FOR YOUR MONEY','Your next move starts here.','Campus life, useful tools and future opportunities.')+
 '<div class="more-grid"><button class="more-product marketplace-tile" data-page="marketplace"><span class="more-product-icon">🛍️</span><span class="soon">COMING SOON</span><h2>Marketplace</h2><p>Buy, sell and find campus services.</p><img src="./assets/marketplace.svg" alt=""></button><button class="more-product invest-tile" data-page="invest"><span class="more-product-icon">🌱</span><span class="soon">COMING SOON</span><h2>Invest</h2><p>Explore business funding, built with care.</p><img src="./assets/invest.svg" alt=""></button></div>'+
 '<section class="panel more-list"><button data-page="insights"><span class="iconbox purple">📊</span><span><b>Insights & patterns</b><small>See trends and get your next step</small></span><strong>›</strong></button><button data-action="start-tour"><span class="iconbox purple">🧭</span><span><b>App tutorial</b><small>Take a quick guided tour</small></span><strong>›</strong></button><button data-page="settings"><span class="iconbox blue">⚙️</span><span><b>Settings</b><small>Export data or reset the demo</small></span><strong>›</strong></button><button data-action="help"><span class="iconbox mint">💬</span><span><b>Help & support</b><small>Learn how this preview works</small></span><strong>›</strong></button><button data-action="about"><span class="iconbox yellow">ⓘ</span><span><b>About</b><small>Prototype v0.2 · Cameroon</small></span><strong>›</strong></button></section>';
}
function settingsPage(){
 var selected=state.palette||'violet';
 var paletteCards=palettes.map(function(p){return '<button class="palette-card '+(selected===p.id?'selected':'')+'" data-palette="'+p.id+'" aria-pressed="'+(selected===p.id?'true':'false')+'"><span class="palette-swatches">'+p.colors.map(function(c){return '<i style="background:'+c+'"></i>';}).join('')+'</span><span class="palette-card-name">'+esc(p.name)+'</span><small>'+esc(p.desc)+'</small><span class="palette-check">'+(selected===p.id?'✓ Selected':'Choose palette')+'</span></button>';}).join('');
 return pageHead('YOUR SPACE, YOUR STYLE','Make it feel like you.','Your goals, your colours, your pace.')+
 '<section class="palette-feature"><div><div class="goal-hero-kicker">A SMALL SPACE THAT FEELS LIKE YOURS</div><h2>Choose your colour story.</h2><p>Pick a palette that feels right. The app updates its accents, buttons, highlights and soft backgrounds while keeping text readable.</p></div><div class="palette-preview"><span>YOUR MONEY SPACE</span><b>Dream in colour.</b><button class="palette-preview-button">Your next move ↗</button></div></section>'+
 '<div class="palette-grid">'+paletteCards+'</div>'+
 '<div class="settings-grid" style="margin-top:20px"><section class="panel settings-card"><div class="iconbox purple">🔒</div><h3>Your privacy</h3><p>Your records stay on this device. Save a full backup before clearing browser data or changing phones.</p><div class="settings-actions"><button class="button secondary small" data-action="export-backup">Download full backup (JSON)</button><button class="button secondary small" data-action="import-backup">Restore a backup</button><button class="button ghost small" data-action="export">Export transactions (CSV)</button><input id="backup-file" class="hide" type="file" accept="application/json,.json"></div></section><section class="panel settings-card"><div class="iconbox mint">🧹</div><h3>Start fresh</h3><p>Clear this browser’s demo money records and return to the setup experience.</p><button class="button secondary small" data-action="reset">Reset local data</button></section><section class="panel settings-card"><div class="iconbox peach">🧪</div><h3>About this preview</h3><p>No real AI API, account login, bank/mobile-money connection, advertising network or payment processing is connected yet.</p><span class="pill">Prototype v0.3</span></section><section class="panel settings-card"><div class="iconbox yellow">🪄</div><h3>Need a refresher?</h3><p>Take a quick guided tour of your money dashboard and the main features.</p><button class="button small" data-action="start-tour">Start the tour →</button></section></div><div class="note" style="margin-top:15px">🛡️ This is a budgeting tool, not a bank, wallet, investment service or financial adviser. Your displayed balance is what you enter manually.</div>';
}
function chatHtml(m){var user=m.role==='user';return '<div class="message-row '+(user?'user':'assistant')+'">'+(!user?'<img class="message-avatar" src="./assets/money-coach.svg" alt="">':'')+'<div class="bubble">'+esc(m.text)+'</div></div>';}
function renderApp(){
 document.body.dataset.palette=state.palette||'violet';
 if(!state.onboarded){renderOnboarding();return;}
 var pages={dashboard:dashboardPage,activity:activityPage,budgets:budgetsPage,goals:goalsPage,coach:coachPage,insights:insightsPage,more:morePage,marketplace:marketplacePage,invest:investPage,settings:settingsPage};
 var title=({dashboard:'Your money, in focus',activity:'Transactions',budgets:'Budgets',goals:'Savings goals',coach:'Money Coach',insights:'Insights',more:'More',marketplace:'Campus Marketplace',invest:'Student Business Funding',settings:'Settings'})[page]||'Overview';
 var nav=appNavItems();
 app.innerHTML='<div class="app-shell"><aside class="sidebar">'+brand()+'<div class="side-label">YOUR MONEY SPACE</div><nav class="nav">'+nav.map(function(n){return navBtn(n,page);}).join('')+'<button class="'+(page==='activity'?'active':'')+'" data-page="activity"><span class="nav-emoji">↔</span><span class="nav-label">Transactions</span></button><button class="'+(page==='settings'?'active':'')+'" data-page="settings"><span class="nav-emoji">⚙️</span><span class="nav-label">Settings & help</span></button></nav><div class="sidebar-bottom"><section class="sidebar-goal"><b>🌈 Small steps add up.</b><p>There’s no perfect budget. Just a plan that helps you feel more in control.</p><button class="text-button" data-page="goals">Choose a goal →</button></section><div class="sidebar-meta">🇨🇲 &nbsp; Cameroon · FCFA<br><span style="display:inline-block;margin-top:5px">'+esc(profile.name||'Student')+'</span></div></div></aside><main class="main"><header class="topbar"><div class="crumb">Money space / <b>'+title+'</b></div><div class="top-right"><span class="currency-pill">🇨🇲 &nbsp; FCFA</span><div class="avatar">'+esc((profile.name||'S').charAt(0).toUpperCase())+'</div></div></header><div class="content"><div class="screen" key="'+page+'">'+(pages[page]||dashboardPage)()+'</div>'+productFooter()+'</div></main></div><nav class="mobile-nav">'+nav.map(function(n){return '<button class="'+(page===n[0]?'active':'')+'" data-page="'+n[0]+'"><span class="mi">'+n[1]+'</span><span>'+({'dashboard':'Home','activity':'Activity','budgets':'Budget','goals':'Goals','coach':'Coach','more':'More'})[n[0]]+'</span></button>';}).join('')+'</nav>';
 bindApp();
}
function bindApp(){
 document.querySelectorAll('[data-action="habit-toggle"]').forEach(function(b){b.addEventListener('click',function(){toggleMoneyHabit(b.dataset.habit);});});
 document.querySelectorAll('[data-page]').forEach(function(b){b.addEventListener('click',function(){page=b.dataset.page;renderApp();window.scrollTo({top:0,behavior:'smooth'});});});
 document.querySelectorAll('[data-action="add-tx"]').forEach(function(b){b.addEventListener('click',function(){openTx(b.dataset.type||'expense');});});
 document.querySelectorAll('[data-action="scan-receipt"]').forEach(function(b){b.addEventListener('click',function(){showToast('Receipt scanning is coming soon. Add the total manually for now.');});});
 document.querySelectorAll('[data-action="help"]').forEach(function(b){b.onclick=function(){openModal('<button class="modal-close" data-close>✕</button><div class="eyebrow">HELP & SUPPORT</div><h2>Need a hand?</h2><p>This preview stores entries in your browser. Add income or expenses manually, edit your budget, and use Money Coach for simple guidance. Real accounts, AI and notifications are not connected yet.</p><button class="button full" data-close>Got it</button>');};});
 document.querySelectorAll('[data-action="about"]').forEach(function(b){b.onclick=function(){openModal('<button class="modal-close" data-close>✕</button><div class="eyebrow">ABOUT THIS PREVIEW</div><h2>Money, made clearer.</h2><p>A student money-management concept for Cameroon. Built around FCFA budgeting, savings goals, a future campus marketplace and a future regulated business-funding experience.</p><div class="note">Prototype v0.2 · Local browser data · No payments accepted</div><button class="button full" data-close>Close</button>');};});
 document.querySelectorAll('[data-action="edit-budget"]').forEach(function(b){b.onclick=editBudget;});
 document.querySelectorAll('[data-palette]').forEach(function(b){b.onclick=function(){state.palette=b.dataset.palette;persist();renderApp();showToast('Palette updated. Your space, your style. 🎨');};});
 document.querySelectorAll('[data-action="new-goal"]').forEach(function(b){b.onclick=function(){newGoal();};});
 document.querySelectorAll('[data-goal-category]').forEach(function(b){b.onclick=function(){window.__goalCategory=b.dataset.goalCategory;renderApp();};});
 document.querySelectorAll('[data-goal-idea]').forEach(function(b){b.onclick=function(){var idea=goalIdeas.find(function(g){return g.id===b.dataset.goalIdea;});if(idea)newGoal(idea);};});
 document.querySelectorAll('[data-action="add-saving"]').forEach(function(b){b.onclick=function(){addSaving(b.dataset.id);};});
 document.querySelectorAll('[data-action="goal-menu"]').forEach(function(b){b.onclick=function(){goalMenu(b.dataset.id);};});
 document.querySelectorAll('[data-action="export"]').forEach(function(b){b.onclick=exportCSV;});
 document.querySelectorAll('[data-action="export-backup"]').forEach(function(b){b.onclick=exportBackup;});
 document.querySelectorAll('[data-action="import-backup"]').forEach(function(b){b.onclick=function(){var input=document.getElementById("backup-file");if(input)input.click();};});
 var backupInput=document.getElementById("backup-file");if(backupInput)backupInput.addEventListener("change",function(){var file=backupInput.files&&backupInput.files[0];if(file)restoreBackupFile(file);backupInput.value="";});
 document.querySelectorAll('[data-action="reset"]').forEach(function(b){b.onclick=resetData;});
 document.querySelectorAll('[data-action="start-tour"]').forEach(function(b){b.onclick=function(){tourStep=0;renderTour();};});
 document.querySelectorAll('[data-market-category]').forEach(function(b){b.onclick=function(){window.__marketCategory=b.dataset.marketCategory;renderApp();};});
 var marketSearch=document.getElementById('market-search');if(marketSearch)marketSearch.addEventListener('input',function(){window.__marketQuery=marketSearch.value;var pos=marketSearch.selectionStart;renderApp();var next=document.getElementById('market-search');if(next){next.focus();next.setSelectionRange(pos,pos);}});
 document.querySelectorAll('[data-market-save]').forEach(function(b){b.onclick=function(){state.marketSaved=state.marketSaved||[];var id=b.dataset.marketSave,at=state.marketSaved.indexOf(id);if(at>=0)state.marketSaved.splice(at,1);else state.marketSaved.push(id);persist();renderApp();showToast(at>=0?'Removed from saved listings.':'Listing saved on this device.');};});
 document.querySelectorAll('[data-market-detail]').forEach(function(b){b.onclick=function(){var id=b.dataset.marketDetail;var all=[['m-books','Study notes & textbooks','Books & supplies',2500,'📚','Student-to-student textbooks and revision materials. Confirm edition and condition before meeting.'],['m-design','Flyer & social media design','Creative services',5000,'🎨','Starter design service for student clubs and small businesses. Agree the scope before work begins.'],['m-tutor','Peer tutoring session','Tutoring',3000,'🧠','Peer revision support. Agree subject, duration and location first.'],['m-repair','Phone & laptop troubleshooting','Repairs',2000,'🛠️','Initial diagnostic service; parts and repairs are extra unless agreed.'],['m-food','Campus snack pre-order','Food',1000,'🥪','Illustrative local vendor listing. Confirm ingredients and availability.'],['m-tech','Laptop setup & software help','Tech & gadgets',2500,'💻','Basic setup guidance. Never share passwords or recovery codes.']];var x=all.find(function(v){return v[0]===id;});if(!x)return;openModal('<button class="modal-close" data-close>✕</button><div class="eyebrow">SAMPLE LISTING · NOT VERIFIED</div><div class="detail-emoji">'+x[4]+'</div><h2>'+esc(x[1])+'</h2><p>'+esc(x[5])+'</p><div class="note">'+esc(x[2])+' · '+fmt(x[3])+'</div><p>Provider identity, stock and availability are not verified in this prototype. Contact or payment services are not connected. Meet safely and do not send advance payments to unknown people.</p><button class="button full" data-action="market-request" data-id="'+id+'">Register interest</button>');overlay.querySelector('[data-action="market-request"]').onclick=function(){state.marketRequests=state.marketRequests||[];if(state.marketRequests.indexOf(id)<0)state.marketRequests.push(id);persist();closeModal();showToast('Interest saved locally; no seller has been contacted.');};};});
 document.querySelectorAll('[data-action="seller-listing"]').forEach(function(b){b.onclick=function(){openModal('<button class="modal-close" data-close>✕</button><div class="eyebrow">SELLER WORKSPACE</div><h2>Draft a student listing</h2><p>This saves a private draft on this device. Publishing and buyer contact need a backend.</p><form id="seller-listing-form" class="modal-form"><label>Listing title<input id="seller-title" required maxlength="80" placeholder="e.g. Maths tutoring"></label><label>Category<select id="seller-category"><option>Books & supplies</option><option>Tech & gadgets</option><option>Tutoring</option><option>Creative services</option><option>Repairs</option><option>Food</option><option>Other services</option></select></label><label>Price (FCFA)<input id="seller-price" type="number" min="0" max="100000000" required></label><label>Description<textarea id="seller-desc" maxlength="500" required placeholder="Describe what you offer and any conditions"></textarea></label><button class="button full" type="submit">Save private draft</button></form>');overlay.querySelector('#seller-listing-form').onsubmit=function(e){e.preventDefault();state.sellerDrafts=state.sellerDrafts||[];state.sellerDrafts.push({id:String(Date.now()),title:overlay.querySelector('#seller-title').value.trim(),category:overlay.querySelector('#seller-category').value,price:Math.round(Number(overlay.querySelector('#seller-price').value)),description:overlay.querySelector('#seller-desc').value.trim(),status:'draft',createdAt:Date.now()});persist();closeModal();showToast('Private draft saved on this device; not published.');};};});
 document.querySelectorAll('[data-opportunity-interest]').forEach(function(b){b.onclick=function(){state.savedOpportunities=state.savedOpportunities||[];var id=b.dataset.opportunityInterest;if(state.savedOpportunities.indexOf(id)<0)state.savedOpportunities.push(id);persist();renderApp();showToast('Interest saved locally; no funding or investment has taken place.');};});
 document.querySelectorAll('[data-action="submit-opportunity"]').forEach(function(b){b.onclick=function(){openModal('<button class="modal-close" data-close>✕</button><div class="eyebrow">COMMUNITY DISCOVERY</div><h2>Suggest a student business</h2><p>This submits a local draft only. It is not published or verified.</p><form id="opportunity-form" class="modal-form"><label>Business name<input id="opp-name" maxlength="90" required></label><label>Sector<select id="opp-sector"><option>Campus services</option><option>Creative ventures</option><option>Technology</option><option>Retail</option><option>Food</option><option>Other</option></select></label><label>What does it do?<textarea id="opp-description" maxlength="600" required></textarea></label><button class="button full" type="submit">Save suggestion</button></form>');overlay.querySelector('#opportunity-form').onsubmit=function(e){e.preventDefault();state.opportunityDrafts=state.opportunityDrafts||[];state.opportunityDrafts.push({name:overlay.querySelector('#opp-name').value.trim(),sector:overlay.querySelector('#opp-sector').value,description:overlay.querySelector('#opp-description').value.trim(),status:'local draft',createdAt:Date.now()});persist();closeModal();showToast('Suggestion saved privately on this device.');};};});
 document.querySelectorAll('[data-action="interest"]').forEach(function(b){b.onclick=function(){var p=b.dataset.product;state.notifications=state.notifications||[];if(state.notifications.indexOf(p)<0)state.notifications.push(p);persist();showToast('Interest saved on this device. No notification service is connected yet.');};});
 document.querySelectorAll('[data-filter]').forEach(function(b){b.onclick=function(){activityFilter=b.dataset.filter;renderApp();};});
 var search=document.getElementById('activity-search');if(search)search.addEventListener('input',function(){activitySearch=search.value;var pos=search.selectionStart;var value=search.value;var matches=state.transactions.filter(function(t){return transactionMatchesFilter(t,activityFilter)&&(t.title+' '+t.category+' '+(t.type==='transfer'?'savings':'')).toLowerCase().indexOf(value.toLowerCase())>=0;});var list=document.querySelector('.panel .tx-list');if(list)list.innerHTML=matches.map(txHtml).join('')||'<div class="empty-state">No matching transactions.</div>';});
 document.getElementById('chat-form')?.addEventListener('submit',function(e){e.preventDefault();sendMessage();});
 document.querySelectorAll('[data-prompt]').forEach(function(b){b.onclick=function(){sendMessage(b.dataset.prompt);};});
}
function openModal(content){overlay.innerHTML='<section class="modal">'+content+'</section>';overlay.style.display='grid';overlay.onclick=function(e){if(e.target===overlay)closeModal();};overlay.querySelectorAll('[data-close]').forEach(function(b){b.addEventListener('click',closeModal);});}
function closeModal(){overlay.innerHTML='';overlay.style.display='none';}
function openTx(type){
 var chosen=type||'expense';
 openModal('<button class="modal-close" data-close>✕</button><div class="eyebrow">KEEP YOUR MONEY STORY UP TO DATE</div><h2>Add a transaction</h2><p>Add a quick entry.</p><div class="filter-row"><button class="filter '+(chosen==='income'?'':'active')+'" data-type-choice="expense">↗ Money out</button><button class="filter '+(chosen==='income'?'active':'')+'" data-type-choice="income">↙ Money in</button></div><form id="tx-form" class="modal-form"><label>What was it for?<input id="tx-title" maxlength="100" required placeholder="'+(chosen==='income'?'e.g. Weekly allowance':'e.g. Lunch at campus')+'"></label><label>How much? (FCFA)<input id="tx-amount" type="number" inputmode="numeric" min="1" max="100000000" required placeholder="1500"></label><label>Category<select id="tx-category">'+Object.keys(categoryInfo).map(function(c){return '<option value="'+esc(c)+'" '+(c===(chosen==='income'?'Income':'Food')?'selected':'')+'>'+esc(categoryInfo[c].emoji+' '+c)+'</option>';}).join('')+'</select></label><div class="note">💛 These are manual records only. This will not move money in your Orange Money or MTN MoMo account.</div><button class="button full" type="submit">Save this entry ✓</button></form>');
 var typeButtons=overlay.querySelectorAll('[data-type-choice]');typeButtons.forEach(function(b){b.onclick=function(){closeModal();openTx(b.dataset.typeChoice);};});
 overlay.querySelector('#tx-form').onsubmit=function(e){e.preventDefault();var title=overlay.querySelector('#tx-title').value.trim(),amount=Number(overlay.querySelector('#tx-amount').value),cat=overlay.querySelector('#tx-category').value;addTransaction(title,amount,chosen,cat);closeModal();renderApp();};
}
function addTransaction(title,amount,type,cat){
 amount=Math.round(Number(amount));if(!title||!Number.isFinite(amount)||amount<=0){showToast('Add a description and a valid amount.');return;}
 state.transactions.unshift({id:Date.now(),title:title,amount:amount,type:type,category:type==='income'?'Income':(cat==='Income'?categoryFor(title):cat),date:nowDate(),createdAt:Date.now()});
 state.balance=Number(state.balance||0)+(type==='income'?amount:-amount);persist();showToast(type==='income'?'Money in recorded. Nice! ✨':'Expense recorded. One small step. ✅');
}
function editBudget(){
 var fields=Object.keys(state.budget).map(function(k){var inf=iconInfo(k);return '<label><span>'+inf.emoji+' '+esc(k)+'</span><input data-bval="'+esc(k)+'" type="number" min="0" max="100000000" value="'+Number(state.budget[k]||0)+'"></label>';}).join('');
 openModal('<button class="modal-close" data-close>✕</button><div class="eyebrow">A FLEXIBLE PLAN</div><h2>Shape your weekly budget.</h2><p>These are spending limits to guide you. Change them whenever real life changes.</p><form class="modal-form" id="budget-form">'+fields+'<button class="button full" type="submit">Save my budget</button></form>');
 overlay.querySelector('#budget-form').onsubmit=function(e){e.preventDefault();overlay.querySelectorAll('[data-bval]').forEach(function(i){state.budget[i.dataset.bval]=Math.max(0,Number(i.value)||0);});persist();closeModal();renderApp();showToast('Budget updated. You’ve got this. 🌈');};
}
function newGoal(prefill){
 var preset=prefill||{},category=preset.category||'personal';
 openModal('<button class="modal-close" data-close>✕</button><div class="eyebrow">YOUR DREAM, YOUR RULES</div><h2>Make it personal.</h2><p>Pick a path, name what matters, and set a target that feels realistic for your life.</p><form class="modal-form" id="new-goal-form"><label>Goal path<select id="goal-category">'+goalCategories.map(function(c){return '<option value="'+c.id+'" '+(c.id===category?'selected':'')+'>'+c.emoji+' '+esc(c.label)+'</option>';}).join('')+'</select></label><label>Goal name<input id="goal-name" required maxlength="70" value="'+esc(preset.name||'')+'" placeholder="e.g. Laptop for my engineering studies"></label><label>Why does this matter? (optional)<input id="goal-note" maxlength="160" placeholder="e.g. So I can practise coding and freelance"></label><label>Target amount (FCFA)<input id="goal-target" type="number" min="100" max="100000000" required value="'+(Number(preset.target)||'')+'" placeholder="150000"></label><label>Already saved (FCFA)<input id="goal-saved" type="number" min="0" max="100000000" value="0"></label><button class="button full" type="submit">Create my roadmap ✨</button></form>');
 overlay.querySelector('#new-goal-form').onsubmit=function(e){e.preventDefault();var name=overlay.querySelector('#goal-name').value.trim(),target=Math.round(Number(overlay.querySelector('#goal-target').value)),saved=Math.max(0,Math.round(Number(overlay.querySelector('#goal-saved').value)||0)),cat=overlay.querySelector('#goal-category').value;if(!name||!Number.isFinite(target)||target<100){showToast('Add a goal name and a valid target.');return;}state.goals.push({id:String(Date.now()),ideaId:preset.id||null,name:name,target:target,saved:Math.min(saved,target),emoji:(goalCategories.find(function(c){return c.id===cat;})||{}).emoji||'✨',category:cat,note:overlay.querySelector('#goal-note').value.trim()});persist();closeModal();page='goals';renderApp();showToast('Your personal goal is ready. One step at a time. ✨');};
}
function addSaving(id){
 var goal=state.goals.find(function(g){return String(g.id)===String(id);});if(!goal)return;
 var need=Math.max(0,Number(goal.target||0)-Number(goal.saved||0));
 if(need<=0){showToast('You already reached this goal. Set a new target to keep going.');return;}
 openModal('<button class="modal-close" data-close>✕</button><div class="eyebrow">ONE STEP CLOSER</div><h2>Set money aside.</h2><p>'+esc(goal.name)+' · '+fmt(goal.saved)+' saved of '+fmt(goal.target)+'.</p><div class="note">Available balance: <b>'+fmt(state.balance)+'</b>. Saving moves money out of your spendable balance and into this goal.</div><form id="saving-form" class="modal-form"><label>Amount to set aside (FCFA)<input id="saving-amount" type="number" min="1" max="100000000" required placeholder="'+Math.min(1000,need)+'"></label><button class="button full" type="submit">Move into this goal ✓</button></form>');
 overlay.querySelector('#saving-form').onsubmit=function(e){
  e.preventDefault();var asked=Math.round(Number(overlay.querySelector('#saving-amount').value));
  if(!Number.isFinite(asked)||asked<=0){showToast('Enter a valid amount.');return;}
  if(asked>Number(state.balance||0)){showToast('That is more than your recorded available balance.');return;}
  if(need<=0){closeModal();showToast('You already reached this goal. Set a new target to keep going.');return;}
  var moved=Math.min(asked,need);
  state.balance=Math.max(0,Number(state.balance||0)-moved);goal.saved=Math.min(Number(goal.target)||0,Number(goal.saved||0)+moved);
  state.transactions.unshift({id:Date.now(),title:'Set aside for '+goal.name,amount:moved,type:'transfer',category:'Savings',date:nowDate(),createdAt:Date.now()});
  var habits=todaysMoneyHabits();habits.goal=true;
  persist();closeModal();renderApp();
  showToast(moved<asked?'Moved '+fmt(moved)+'. Your goal is now fully funded! 🎉':'Money set aside. One promise kept. 🌱');
 };
}
function goalMenu(id){var g=state.goals.find(function(x){return String(x.id)===String(id);});if(!g)return;openModal('<button class="modal-close" data-close>✕</button><div class="eyebrow">GOAL OPTIONS</div><h2>'+esc(g.name)+'</h2><p>Edit the target or remove this goal.</p><form id="goal-edit-form" class="modal-form"><label>Target amount (FCFA)<input id="goal-edit-target" type="number" min="1" value="'+g.target+'"></label><div class="modal-actions"><button class="button secondary" type="button" id="goal-delete">Remove goal</button><button class="button" type="submit">Save target</button></div></form>');overlay.querySelector('#goal-edit-form').onsubmit=function(e){e.preventDefault();g.target=Math.max(1,Number(overlay.querySelector('#goal-edit-target').value)||g.target);persist();closeModal();renderApp();};overlay.querySelector('#goal-delete').onclick=function(){state.goals=state.goals.filter(function(x){return String(x.id)!==String(id);});persist();closeModal();renderApp();showToast('Goal removed. You can always add a new one.');};}
function sendMessage(preset){
 var input=document.getElementById('chat-text'),text=String(preset||(input&&input.value)||'').trim();if(!text)return;
 chatMessages.push({role:'user',text:text});var reply=moneyReply(text);chatMessages.push({role:'assistant',text:reply});if(chatMessages.length>28)chatMessages=chatMessages.slice(-28);page='coach';renderApp();var box=document.getElementById('messages');if(box)box.scrollTop=box.scrollHeight;
}
function basicMoneyReply(text){
 var s=String(text||'').toLowerCase(),amount=extractAmount(text);
 if(amount&&/\b(spent|paid|bought|used|cost me|expense|lunch|taxi|food|data bundle)\b/.test(s)){var cat=categoryFor(text);addTransaction(text,amount,'expense',cat);return 'Got it — I added '+fmt(amount)+' to '+cat+'. Please check the entry in Activity if the description or category needs changing. Small steps help your money picture stay honest. ✅';}
 if(amount&&/\b(received|earned|allowance|salary|got paid|sold|income|made)\b/.test(s)){addTransaction(text,amount,'income','Income');return 'Nice! I recorded '+fmt(amount)+' as money in. 🎉 You can now see it in your balance and recent activity.';}
 if(/\b(afford|buy|purchase|should i get|can i get)\b/.test(s)){
  if(!amount)return 'Tell me the price in FCFA and I’ll compare it with the balance you’ve recorded. We can also leave room for food, transport and other essentials.';
  var after=state.balance-amount,buffer=3000;if(after<0)return 'That purchase is '+fmt(amount)+' while your recorded balance is '+fmt(state.balance)+'. It would put your plan '+fmt(Math.abs(after))+' below zero. Consider waiting, saving towards it, or checking whether you have other money not recorded here.';
  if(after<buffer)return 'You could technically cover '+fmt(amount)+', but that would leave '+fmt(after)+'. That’s below the 3,000 FCFA example buffer, so check food, transport, data and upcoming bills before deciding. 💛';
  return 'Based on the balance you entered, buying it would leave about '+fmt(after)+'. That looks possible on paper, but first make sure your upcoming essentials are covered. Estimate only — not live account data.';
 }
 if(/\b(where|most|spend|spending|category|eating|goes|expense|expenses)\b/.test(s)){
  var totalsBy=Object.keys(state.budget).map(function(c){return {name:c,total:budgetSpent(c)};}).sort(function(a,b){return b.total-a.total;});var top=totalsBy[0];return top&&top.total?'Your biggest recorded category is '+top.name+' at '+fmt(top.total)+'. Next is '+(totalsBy[1]&&totalsBy[1].total?totalsBy[1].name+' at '+fmt(totalsBy[1].total):'no second category yet')+'. Only recorded entries are included.':'I don’t have expense entries yet. Add a few — even small ones — and I can help spot patterns in what you record.';
 }
 if(/\b(save|saving|goal|laptop|school fees|target)\b/.test(s)){
  var g=state.goals[0];return g?'Your first goal is “'+g.name+'”. You’ve recorded '+fmt(g.saved)+' of '+fmt(g.target)+' so far. That leaves '+fmt(Math.max(0,g.target-g.saved))+'. A small repeatable amount is usually easier to stick to than an ambitious target that makes the week stressful. 🌱':'Create a savings goal first, then we can work backwards from your target and the time you have.';
 }
 if(/\b(plan|allowance|week|budget|money left|left until)\b/.test(s)){
  var b=budgetTotal(),left=b-totals().spent;return 'Here’s your current snapshot: balance '+fmt(state.balance)+', recorded spending '+fmt(totals().spent)+', and budget remaining '+fmt(left)+'. Your planned allowance is '+fmt(state.allowance)+' '+(state.cadence==='monthly'?'per month':state.cadence==='irregular'?'when it comes in':'per week')+'. Start with essentials, set aside a little for the goal you care about, then leave a flexible amount for real life. Want to record an expense or adjust your budget?';
 }
 return 'I can help you review your recorded spending, plan your allowance, and think through a purchase. Try “Spent 1,200 FCFA on lunch”, “Can I afford 3,000 FCFA shoes?”, or “Where does most of my money go?”. 🌈\\n\\nThis is a smart-rule preview, not a live AI model yet.';
}
function renderTour(){
 var steps=[
  {icon:'💜',title:'Welcome to your money space!',body:'This is your starting point. Your balance is the amount you entered during setup — it is not connected to a bank or Mobile Money account.',image:'./assets/student-hero-3d.webp',label:'1 / 3'},
  {icon:'✨',title:'Every small move has a place.',body:'Use Add income or Add expense to keep your records current. Budgets and savings goals help you decide what to do next.',image:'./assets/marketplace.svg',label:'2 / 3'},
  {icon:'🤖',title:'You don’t have to figure it all out alone.',body:'Ask Money Coach about spending, planning an allowance or saving for a goal. Demo assistant · Real AI comes later.',image:'./assets/money-coach.svg',label:'3 / 3'}
 ];var s=steps[tourStep];
 overlay.innerHTML='<section class="modal"><button class="modal-close" data-action="tour-skip">✕</button><div class="eyebrow">QUICK TOUR · '+s.label+'</div><div class="tour-visual"><img src="'+s.image+'" alt=""></div><h2>'+s.icon+' '+s.title+'</h2><p>'+s.body+'</p><div class="tour-steps">'+steps.map(function(_,i){return '<i class="'+(i===tourStep?'active':'')+'"></i>';}).join('')+'</div><div class="modal-actions"><button class="button secondary" data-action="tour-skip">Skip tour</button><button class="button" data-action="tour-next">'+(tourStep===2?'Let’s do this ✓':'Next tip →')+'</button></div></section>';
 overlay.style.display='grid';overlay.onclick=function(e){if(e.target===overlay)finishTour();};
 overlay.querySelectorAll('[data-action="tour-skip"]').forEach(function(b){b.onclick=finishTour;});overlay.querySelector('[data-action="tour-next"]').onclick=function(){if(tourStep<2){tourStep++;renderTour();}else finishTour();};
}
function finishTour(){state.tutorialDone=true;persist();overlay.innerHTML='';overlay.style.display='none';}
function exportBackup(){
 var payload={format:'student-money-backup',version:1,exportedAt:new Date().toISOString(),app:'Student Money',state:state,profile:profile};
 var blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');
 a.href=url;a.download='student-money-backup-'+localDateKey()+'.json';document.body.appendChild(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(url);},1000);
 showToast('Full backup downloaded. Keep it somewhere safe. ✅');
}
function restoreBackupFile(file){
 if(file.size>5*1024*1024){showToast('That backup is too large to import (5 MB maximum).');return;}
 var reader=new FileReader();
 reader.onerror=function(){showToast('The backup file could not be read.');};
 reader.onload=function(){
  var payload;
  try{payload=JSON.parse(String(reader.result||''));}catch(e){showToast('This file is not valid JSON. Choose a Student Money backup.');return;}
  if(!payload||payload.format!=='student-money-backup'||!payload.state||typeof payload.state!=='object'||Array.isArray(payload.state)||!Array.isArray(payload.state.transactions)||!Array.isArray(payload.state.goals)){
   showToast('This is not a valid Student Money backup. Nothing was changed.');return;
  }
  if(!confirm('Restore this backup and replace the money records currently saved on this device? Export your current records first if you need to keep them.'))return;
  var previousState=state,previousProfile=profile;
  state=payload.state;profile=payload.profile&&typeof payload.profile==='object'&&!Array.isArray(payload.profile)?payload.profile:{};
  state.budget=state.budget&&typeof state.budget==='object'&&!Array.isArray(state.budget)?state.budget:Object.assign({},categoryDefaults);
  state.transactions=Array.isArray(state.transactions)?state.transactions:[];state.goals=Array.isArray(state.goals)?state.goals:[];
  if(!persist()){state=previousState;profile=previousProfile;renderApp();return;}
  page='dashboard';renderApp();showToast('Backup restored on this device. Your records are back. ✅');
 };
 reader.readAsText(file);
}
function exportCSV(){
 var rows=[['Description','Category','Type','Amount FCFA','Date']].concat(state.transactions.map(function(t){return [t.title,t.category,t.type,t.amount,t.date];}));
 var csv=rows.map(function(r){return r.map(function(v){return '"'+String(v).replace(/"/g,'""')+'"';}).join(',');}).join('\r\n');
 var a=document.createElement('a'),url=URL.createObjectURL(new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'}));a.href=url;a.download='student-money-records.csv';a.click();URL.revokeObjectURL(url);showToast('Your CSV export is ready.');
}
function resetData(){if(!confirm('Clear all money records and show the new onboarding again? This cannot be undone.'))return;chatMessages=[];activityFilter='all';activitySearch='';localStorage.removeItem(STORE);localStorage.removeItem(PROFILE);localStorage.removeItem(TOUR);state=loadState();profile={};onStep=0;onboardingStep=0;selectedGoals=['emergency','school'];selectedPersona='student';allowanceCadence='weekly';payday='Tuesday';selectedSources=['cash','orange','mtn'];weeklyNeeds={'Food':5000,'Transport':2400,'Airtime & data':3500,'School / personal':1000,'Other':0,'Debt owed':0};planValues={'Food':3500,'Transport':1500,'Airtime & data':1000,'School / personal':1000,'Emergency buffer':1000};page='dashboard';closeModal();renderOnboarding();}


function localDateKey(d){
 d=d||new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
}
function todaysMoneyHabits(){
 state.habitLog=state.habitLog&&typeof state.habitLog==='object'?state.habitLog:{};
 var key=localDateKey(),defaults={track:false,pause:false,goal:false};
 if(!state.habitLog[key])state.habitLog[key]=Object.assign({},defaults);
 return state.habitLog[key];
}
function isCompleteHabitDay(key){var x=state.habitLog&&state.habitLog[key];return !!(x&&x.track&&x.pause&&x.goal);}
function moneyHabitStreak(){
 var today=new Date(),key=localDateKey(today),streak=0;
 if(!isCompleteHabitDay(key))today.setDate(today.getDate()-1);
 for(var i=0;i<366;i++){if(!isCompleteHabitDay(localDateKey(today)))break;streak++;today.setDate(today.getDate()-1);}
 return streak;
}
function toggleMoneyHabit(key){
 if(['track','pause','goal'].indexOf(key)<0)return;
 var habits=todaysMoneyHabits();habits[key]=!habits[key];persist();renderApp();
}
function moneyAdviceSnapshot(){
 var goals=Array.isArray(state.goals)?state.goals:[],goal=goals[0]||null;
 var weeklyIncome=Math.max(0,Number(weeklyAllowance())||0),savingsTarget=Math.max(0,Number(state.savingsTarget)||0);
 var tx=Array.isArray(state.transactions)?state.transactions:[],since=weekStartTimestamp();
 var recent=tx.filter(function(t){return t.type==='expense'&&Number(t.amount)>0&&Number(t.createdAt||0)>=since;});
 var categorySpent={};recent.forEach(function(t){var cat=t.category||'Other';categorySpent[cat]=(categorySpent[cat]||0)+Number(t.amount||0);});
 var limits=state.budget||{},overs=[];
 Object.keys(categorySpent).forEach(function(cat){var limit=Number(limits[cat]||0),used=categorySpent[cat];if(limit>0&&used>limit)overs.push({category:cat,used:used,limit:limit,over:used-limit});});
 overs.sort(function(a,b){return b.over-a.over;});
 var top=Object.keys(categorySpent).map(function(k){return {category:k,amount:categorySpent[k]};}).sort(function(a,b){return b.amount-a.amount;})[0]||null;
 var debt=Number((state.weeklyNeeds&&state.weeklyNeeds['Debt owed'])||(profile.weeklyNeeds&&profile.weeklyNeeds['Debt owed'])||0);
 var payday=state.payday||profile.payday||'Tuesday',goalName=goal?goal.name:'Build a safety cushion',goalId=goal?goal.id:'emergency';
 var remaining=goal?Math.max(0,Number(goal.target||0)-Number(goal.saved||0)):30000,weeksToGoal=savingsTarget>0?Math.ceil(remaining/savingsTarget):null;
 var goalAdvice={
  emergency:'Protect a starter emergency buffer before spending on non-essentials. Even 500 FCFA set aside consistently helps build the habit.',
  school:'Treat school fees as a deadline goal: divide the amount still needed by the paydays left, then set that amount aside before optional spending.',
  laptop:'Keep a separate laptop target. Compare prices before buying, and choose a weekly amount you can repeat without sacrificing food, transport or school needs.',
  business:'Keep business money separate from personal spending. Test a small idea, write down every cost and sale, and only grow it when the numbers make sense.',
  travel:'Give travel its own savings pot and pay for essentials first. Avoid borrowing for a trip that can wait.',
  freedom:'Build financial freedom through repeatable habits: record spending, protect essentials, save on payday and review the plan once a week.'
 };
 var focus='',nextAction='';
 if(debt>0){focus='You’ve reported '+fmt(debt)+' in outstanding debt. Keep this separate from weekly spending, list each due date, and don’t promise the same money to both debt and savings.';nextAction='Write down the next debt due date and minimum payment before setting optional spending.';}
 else if(overs.length){focus='Your recent recorded '+overs[0].category.toLowerCase()+' spending is '+fmt(overs[0].over)+' above its budget limit. That is a signal to adjust the plan—not a reason to feel guilty.';nextAction='Pause non-essential spending in '+overs[0].category.toLowerCase()+' for today and review the remaining limit.';}
 else if(!recent.length){focus='The first discipline habit is visibility. Record every expense today—even a small snack or airtime purchase—so your plan is based on reality.';nextAction='Log each purchase today, then check your balance before your next non-essential buy.';}
 else if(top){focus='Your largest recorded spending category this week is '+top.category+' at '+fmt(top.amount)+'. Review it once before your next purchase and compare it with your budget.';nextAction='Check '+top.category.toLowerCase()+' before you spend again. Small pauses prevent surprise totals.';}
 else{focus='Keep your plan light and repeatable. Review money in, money out and your next goal once a day.';nextAction='Record today’s spending and review your next goal.';}
 var weeklyGoalText=savingsTarget?fmt(savingsTarget)+' each week':'choose a savings amount that feels realistic';
 var goalAdviceText=goalAdvice[goalId]||goalAdvice.emergency;
 if(goal&&remaining===0){goalAdviceText='You have reached the target you set for '+goal.name+'. Celebrate that progress, then choose whether to maintain the habit or set a new goal.';}
 else if(goal&&savingsTarget>0){goalAdviceText+=' At '+weeklyGoalText+', the remaining '+fmt(remaining)+' would take about '+weeksToGoal+' week'+(weeksToGoal===1?'':'s')+', assuming you can save that amount consistently.';}
 return {goal:goal,goalName:goalName,goalId:goalId,goalAdvice:goalAdviceText,focus:focus,nextAction:nextAction,weeklyIncome:weeklyIncome,savingsTarget:savingsTarget,balance:Math.max(0,Number(state.balance)||0),payday:payday,debt:debt,overs:overs,top:top,recentCount:recent.length,habits:todaysMoneyHabits(),streak:moneyHabitStreak()};
}
function disciplinePanel(){
 var a=moneyAdviceSnapshot(),habits=a.habits;
 var definitions=[['track','📝','Record every expense','Log it the same day, however small.'],['pause','⏳','Pause before impulse buys','Wait 24 hours on non-essential purchases.'],['goal','🎯','Reconnect with your goal','Take one small step towards '+esc(a.goalName.toLowerCase())+'.']];
 var completed=definitions.filter(function(x){return !!habits[x[0]];}).length;
 return '<section class="discipline-panel screen"><div class="discipline-head"><div><div class="mini-label">YOUR DAILY MONEY ROUTINE</div><h2>Build discipline, one day at a time.</h2><p>Small actions beat perfect plans.</p></div><div class="streak-pill"><span>🔥</span><b>'+a.streak+'</b><small>day streak</small></div></div>'+
 '<div class="discipline-focus"><div class="focus-icon">🧭</div><div><span class="focus-label">YOUR FOCUS · '+esc(a.goalName.toUpperCase())+'</span><p>'+esc(a.focus)+'</p></div></div>'+
 '<div class="discipline-progress"><span>'+completed+' of 3 habits completed</span><div class="bar"><i style="width:'+(completed/3*100)+'%"></i></div></div>'+
 '<div class="habit-checklist">'+definitions.map(function(x){return '<button type="button" class="habit-row '+(habits[x[0]]?'done':'')+'" data-action="habit-toggle" data-habit="'+x[0]+'" aria-pressed="'+(habits[x[0]]?'true':'false')+'"><span class="habit-check">'+(habits[x[0]]?'✓':x[1])+'</span><span class="habit-copy"><b>'+x[2]+'</b><small>'+x[3]+'</small></span><span class="habit-state">'+(habits[x[0]]?'Done':'Mark done')+'</span></button>';}).join('')+'</div>'+
 '<div class="discipline-footer"><div><b>One move for today</b><small>'+esc(a.nextAction)+'</small></div><button type="button" class="button small secondary" data-page="coach">Get guidance →</button></div></section>';
}
function coachGuidancePanel(){
 var a=moneyAdviceSnapshot(),prompts=['Help me stay disciplined this week','Help me reach my '+a.goalName.toLowerCase()+' goal','Plan my allowance around payday'];
 return '<section class="coach-guidance"><div class="coach-guidance-top"><div><div class="mini-label">YOUR PERSONAL MONEY PLAN</div><h2>Advice for your real life.</h2></div><span class="pill">Goal-based</span></div><div class="coach-guidance-grid"><div class="coach-guidance-card"><span class="coach-card-icon">🧭</span><div class="mini-label">TODAY’S FOCUS</div><p>'+esc(a.focus)+'</p></div><div class="coach-guidance-card goal-advice"><span class="coach-card-icon">🎯</span><div class="mini-label">YOUR GOAL · '+esc(a.goalName.toUpperCase())+'</div><p>'+esc(a.goalAdvice)+'</p></div></div><div class="coach-prompt-row">'+prompts.map(function(p){return '<button type="button" data-prompt="'+esc(p)+'">✦ '+esc(p)+'</button>';}).join('')+'</div><div class="coach-rule-note">Personalized from your saved goals, budget and recorded spending. This prototype uses local rules, not a connected AI model.</div></section>';
}
function moneyReply(text){
 var s=String(text||'').toLowerCase(),a=moneyAdviceSnapshot(),amount=extractAmount(text);
 var frenchExpense=/j['’ ]?ai\s+(?:dépens|depens|payé|paye|acheté|achete|pris|commandé|commande)|(?:dépensé|depense|dépense|payé|payee|acheté)\s+\d+/.test(s);
 var frenchIncome=/j['’ ]?ai\s+(?:reçu|recu|gagné|gagne|encaissé|encaisse|vendu)|argent de poche|salaire|allocation|revenu reçu|paiement reçu/.test(s);
 if(amount&&frenchExpense){
  var cat=categoryFor(text);addTransaction(text,amount,'expense',cat);
  return 'C’est noté : '+fmt(amount)+' enregistrés dans « '+cat+' ». ✅ Continue à noter tes petites dépenses aussi — c’est comme ça que ton budget devient utile.';
 }
 if(amount&&frenchIncome){
  addTransaction(text,amount,'income','Income');
  return 'Bien joué ! J’ai enregistré '+fmt(amount)+' comme argent reçu. 🎉 Ton solde et ton activité sont à jour.';
 }
 if(/discipline|habitude|routine|gaspill|dépenser moins|depense moins|maîtriser mon argent|maitriser mon argent|mieux gérer|mieux gerer|achat impulsif|motivation|conseil/.test(s)){
  return 'On va rendre la discipline simple. 💛 '+a.focus+'\n\nTon objectif principal est « '+a.goalName+' ». '+a.goalAdvice+'\n\nPour aujourd’hui : note chaque dépense, attends 24 heures avant un achat non essentiel, puis vérifie ton objectif ce soir. Ton objectif d’épargne est de '+fmt(a.savingsTarget)+' par semaine. La régularité compte plus que la perfection.';
 }
 if(amount&&/est-ce que je peux|puis-je|je peux me permettre|je peux acheter|acheter|achat|abordable|ça vaut|ca vaut|devrais-je/.test(s)){
  var after=Number(state.balance||0)-amount,buffer=3000;
  if(after<0)return 'Tu veux acheter quelque chose à '+fmt(amount)+', mais ton solde enregistré est de '+fmt(state.balance)+'. Il manquerait '+fmt(Math.abs(after))+'. Le choix le plus prudent est d’attendre, d’épargner ou de vérifier si tu as d’autres fonds non enregistrés.';
  if(after<buffer)return 'C’est peut-être possible, mais il ne resterait que '+fmt(after)+'. C’est moins que la réserve indicative de 3 000 FCFA. Vérifie d’abord nourriture, transport, internet et les paiements qui arrivent. 💛';
  return 'Après cet achat, il resterait environ '+fmt(after)+'. Sur le papier, ça semble possible ; vérifie quand même que tes besoins essentiels et tes paiements à venir sont couverts. C’est une estimation basée sur ton solde saisi.';
 }
 if(/où va|ou va|où part|ou part|dépense|depense|dépenses|depenses|argent part|catégorie|categorie|mes dépenses|mes depenses/.test(s)){
  var frTotals=Object.keys(state.budget).map(function(c){return {name:c,total:budgetSpent(c)};}).sort(function(x,y){return y.total-x.total;}),frTop=frTotals[0];
  return frTop&&frTop.total?'Ta catégorie la plus dépensière cette semaine est '+frTop.name+' avec '+fmt(frTop.total)+'. Compare ce montant à ta limite et décide d’un petit ajustement pour les prochains jours.':'Je n’ai pas encore de dépenses enregistrées cette semaine. Note quelques achats, même petits, et je t’aiderai à repérer les tendances.';
 }
 if(/épargn|epargn|économis|economis|objectif|ordinateur|frais de scolarité|frais scolaires|fonds d'urgence|fonds d’urgence|voyage|entreprise/.test(s)){
  var frGoal=state.goals[0];
  if(frGoal)return 'On avance vers « '+frGoal.name+' ». '+a.goalAdvice+'\n\nTon objectif d’épargne est de '+fmt(a.savingsTarget)+' par semaine. Protège d’abord nourriture, transport, école et paiements dus ; baisse temporairement l’objectif si la semaine devient trop serrée.';
  return 'Crée d’abord un objectif, puis on calculera le montant hebdomadaire à mettre de côté.';
 }
 if(/planifier|plan de la semaine|budget|allocation|argent de poche|jour de paie|prochaine paie|semaine prochaine|comment organiser mon argent/.test(s)){
  return 'Voici une routine simple pour le jour de paie ('+a.payday+') : 1) couvre les besoins essentiels et les dettes dues, 2) mets de côté les '+fmt(a.savingsTarget)+' prévus seulement si c’est raisonnable, 3) répartis le reste dans tes limites hebdomadaires, 4) vérifie ton plan avant la prochaine paie. Solde enregistré : '+fmt(a.balance)+'. Aucun transfert automatique n’est connecté.';
 }
 if(/\b(disciplin|habit|routine|stay on track|motivat|daily plan|challenge|stop wasting|control my spending|what should i do|personalized advice|advic|feel overwhelmed|impulse)\b/.test(s)){
  return 'Let’s make discipline practical, '+(profile.name||'friend')+'. 💛 '+a.focus+'\n\nYour main goal is “'+a.goalName+'”. '+a.goalAdvice+'\n\nFor today: (1) record every spend, (2) pause 24 hours before a non-essential purchase, and (3) check your goal before bedtime. Your savings target is '+fmt(a.savingsTarget)+' per week, and your usual payday is '+a.payday+'. Aim for consistency, not perfection.';
 }
 if(/\b(reach|achieve|goal|save more|spend less|save for|savings plan|laptop|school fees|emergency fund|start a business|travel fund)\b/.test(s)&&/\b(how|help|plan|save|goal|reach|achieve|should|advice|target|for|more|less)\b/.test(s)){
  return 'Let’s work towards “'+a.goalName+'”. '+a.goalAdvice+'\n\nYour planned weekly savings amount is '+fmt(a.savingsTarget)+'. Keep food, transport, school and due payments covered first; if that target makes the week too tight, lower it and stay consistent.';
 }
 if(/\b(plan my allowance|plan my week|payday routine|weekly plan|what should i do today)\b/.test(s)){
  return 'Here is your simple payday routine for '+a.payday+': first cover essentials and due bills; second, set aside the '+fmt(a.savingsTarget)+' you planned only if it is affordable; third, split the remainder across your weekly limits; and fourth, review the plan before the next payday. Your recorded balance is '+fmt(a.balance)+'. Remember, this preview does not move money automatically.';
 }
 return basicMoneyReply(text);
}

/* Focused, personalized onboarding override */
var onboardingStep=0;
selectedGoals=['emergency','school'];
selectedPersona='student';
allowanceCadence='weekly';
var payday='Tuesday';
var selectedSources=['cash','orange','mtn'];
var weeklyNeeds={'Food':5000,'Transport':2400,'Airtime & data':3500,'School / personal':1000,'Other':0,'Debt owed':0};
var planValues={'Food':3500,'Transport':1500,'Airtime & data':1000,'School / personal':1000,'Emergency buffer':1000};

function onboardingIncomeWeekly(){var amount=Math.max(0,Number(state.allowance)||0);return allowanceCadence==='monthly'?Math.round(amount/4.33):amount;}
function renderOnboarding(){
 var shellStart='<main class="onboarding"><header class="ob-top">'+brand()+'<button class="button ghost small" data-action="ob-skip">Skip setup</button></header>';
 var shellEnd='<footer class="ob-bottom"><span>YOUR MONEY. YOUR NEXT MOVE.</span><span>FCFA · PRIVATE BY DEFAULT</span></footer></main>';
 if(onboardingStep===0.5){
  var intro='<main class="onboarding tiana-onboarding"><section class="tiana-intro screen" aria-label="Take control of your money"><div class="tiana-intro-photo"><img src="./assets/student-onboarding-photo.png" alt="Student wearing headphones and using a phone on campus"></div><div class="tiana-intro-fade" aria-hidden="true"></div><div class="tiana-intro-status" aria-hidden="true"><span>9:41</span><span class="tiana-status-icons"><svg viewBox="0 0 40 20"><path d="M2 17h4V11H2zM10 17h4V7h-4zM18 17h4V3h-4zM26 17h4V0h-4z" fill="currentColor"/></svg><svg viewBox="0 0 24 20"><path d="M2 7.4C7.7 2.2 16.3 2.2 22 7.4L12 18z" fill="currentColor"/></svg><svg viewBox="0 0 32 18"><rect x="1" y="2" width="26" height="14" rx="3" fill="none" stroke="currentColor" stroke-width="1.8"/><rect x="3.5" y="4.5" width="20" height="9" rx="1.5" fill="currentColor"/><path d="M29 6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></span></div><button type="button" class="tiana-intro-back" data-action="ob-intro-back" aria-label="Back to welcome"><svg viewBox="0 0 24 24"><path d="m15 18-6-6 6-6" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg></button><div class="tiana-intro-content"><h1>Take control<br>of your money</h1><p class="tiana-intro-copy">Track, plan, save and achieve your goals — all in one place.</p><div class="tiana-benefits"><article class="tiana-benefit tiana-benefit-green"><span class="tiana-benefit-icon"><svg viewBox="0 0 32 32"><path d="M5 26V18h5v8M14 26V11h5v15M23 26V5h5v21" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/><path d="m5 12 7-5 6 1 8-5" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg></span><b>Track<br>expenses</b></article><article class="tiana-benefit tiana-benefit-pink"><span class="tiana-benefit-icon"><svg viewBox="0 0 32 32"><circle cx="16" cy="16" r="11" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="16" cy="16" r="5" fill="none" stroke="currentColor" stroke-width="3"/><path d="M18 14 27 5M22 5h5v5" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg></span><b>Reach<br>your goals</b></article><article class="tiana-benefit tiana-benefit-blue"><span class="tiana-benefit-icon"><svg viewBox="0 0 32 32"><path d="M16 3 27 7v8c0 7-5 11-11 14C10 26 5 22 5 15V7z" fill="currentColor"/><path d="m11 16 3 3 7-8" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg></span><b>Build<br>better habits</b></article></div><div class="tiana-intro-footer"><div class="tiana-intro-dots" aria-label="Onboarding page 1 of 4"><span class="active"></span><span></span><span></span><span></span></div><button type="button" class="tiana-intro-next" data-action="ob-intro-next" aria-label="Next onboarding page"><svg viewBox="0 0 24 24"><path d="M4 12h15M13 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg></button></div></div></section></main>';
  app.innerHTML=intro;bindOnboarding();return;
 }
 if(onboardingStep===0){
  var welcome='<main class="onboarding tiana-onboarding"><section class="tiana-welcome screen" aria-label="Welcome to TIANA"><div class="tiana-welcome-art"><img src="./assets/student-onboarding-photo.png" alt="A smiling student in a blue hoodie using his phone on campus"></div><div class="tiana-welcome-shade" aria-hidden="true"></div><div class="tiana-status" aria-hidden="true"><span>9:41</span><span class="tiana-status-icons"><svg viewBox="0 0 40 20"><path d="M2 17h4V11H2zM10 17h4V7h-4zM18 17h4V3h-4zM26 17h4V0h-4z" fill="currentColor"/></svg><svg viewBox="0 0 24 20"><path d="M2 7.4C7.7 2.2 16.3 2.2 22 7.4L12 18z" fill="currentColor"/><path d="M6 11c3.4-3 8.6-3 12 0l-6 7z" fill="#101710"/></svg><svg viewBox="0 0 32 18"><rect x="1" y="2" width="26" height="14" rx="3" fill="none" stroke="currentColor" stroke-width="1.8"/><rect x="3.5" y="4.5" width="20" height="9" rx="1.5" fill="currentColor"/><path d="M29 6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></span></div><button type="button" class="tiana-back" data-action="ob-welcome-back" aria-label="Go back"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg></button><div class="tiana-brand-block"><div class="tiana-wordmark">TIANA</div><p>Smart Money. Brighter You.</p></div><div class="tiana-bottom-stack"><p class="tiana-promise">For students. For a better tomorrow.</p><button class="tiana-cta" type="button" data-action="ob-start"><span>Get Started</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15M13 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg></button></div></section></main>';
  app.innerHTML=welcome;bindOnboarding();return;
 }
 var totalSteps=7;
 var incomeAmount=Math.max(0,Number(state.allowance)||0);var income=onboardingIncomeWeekly();
 var savings=Math.max(0,Number(state.savingsTarget===undefined?2000:state.savingsTarget)||0);
 var balance=Math.max(0,Number(state.balance)||0);
 var weeklySpend=Number(weeklyNeeds.Food||0)+Number(weeklyNeeds.Transport||0)+Number(weeklyNeeds['Airtime & data']||0)+Number(weeklyNeeds['School / personal']||0)+Number(weeklyNeeds.Other||0);
 var spendAfterSavings=Math.max(0,income-savings);
 var gap=Math.max(0,weeklySpend-spendAfterSavings);
 var percent=income?Math.round(savings/income*100):0;
 var stepTitle='',stepCopy='',stepBody='';
 var progress=Math.min(100,Math.round(onboardingStep/totalSteps*100));
 if(onboardingStep===1){
  stepTitle='Tell us about you';
  stepCopy='We’ll make your money space fit your life.';
  stepBody='<label class="field">YOUR FIRST NAME <small>OPTIONAL</small><input id="ob-name" maxlength="40" value="'+esc(profile.name||'')+'" placeholder="e.g. Alex"></label><div class="field-label-static">WHICH DESCRIBES YOU BEST?</div><div class="choice-list">'+[
   ['student','🎓','University student','I’m studying right now.'],
   ['hustler','💻','Student + side hustle','I study and earn too.'],
   ['young-pro','💼','Young professional','I work and earn regularly.'],
   ['entrepreneur','🚀','Student entrepreneur','I’m building a business.']
  ].map(function(p){return '<button class="choice '+(selectedPersona===p[0]?'selected':'')+'" data-persona="'+p[0]+'"><span class="choice-icon">'+p[1]+'</span><span class="choice-copy"><b>'+p[2]+'</b><small>'+p[3]+'</small></span><span class="checkmark">✓</span></button>';}).join('')+'</div>';
 }else if(onboardingStep===2){
  stepTitle='What are your goals?';
  stepCopy='Choose up to 3. You can change them later.';
  stepBody='<div class="goal-grid">'+goalOptions.map(function(g){var sel=selectedGoals.indexOf(g.id)>=0;return '<button class="goal-choice '+(sel?'selected':'')+'" data-goal="'+g.id+'"><span class="checkmark">'+(sel?'✓':'')+'</span><span class="g-emoji">'+g.emoji+'</span><b>'+g.title+'</b><small>'+g.detail+'</small></button>';}).join('')+'</div><div class="hint">Pick the goals that matter most to you right now.</div>';
 }else if(onboardingStep===3){
  stepTitle='How do you receive money?';
  stepCopy='We’ll plan around your real payday.';
  stepBody='<div class="field-label-static">HOW OFTEN?</div><div class="cadence-options">'+[['weekly','Every week'],['monthly','Every month'],['irregular','It varies']].map(function(v){return '<button type="button" class="'+(allowanceCadence===v[0]?'cadence-selected':'')+'" data-cadence="'+v[0]+'">'+v[1]+'</button>';}).join('')+'</div><label class="field">TYPICAL INCOME / ALLOWANCE<div class="onboard-amount"><input id="ob-allowance" type="number" min="0" max="100000000" step="500" value="'+incomeAmount+'" inputmode="numeric"><span>FCFA</span></div></label><div class="field-label-static">'+(allowanceCadence==='weekly'?'WHICH DAY DOES IT ARRIVE?':'WHICH DAY SHOULD WE USE FOR REMINDERS?')+'</div><div class="weekday-grid">'+['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'].map(function(d){return '<button type="button" class="'+(payday===d?'active':'')+'" data-payday="'+d+'">'+d.slice(0,3)+'</button>';}).join('')+'</div><div class="info-strip">📅 <span>We’ll use <b>'+esc(payday)+'</b> for your payday plan and reminder settings.</span></div>';
 }else if(onboardingStep===4){
  stepTitle='How much do you have now?';
  stepCopy='Add everything you can access. Estimates are okay.';
  var sourceDefs=[['cash','💵','Cash'],['orange','🟠','Orange Money'],['mtn','🟡','MTN MoMo'],['bank','🏦','Bank account']];
  stepBody='<div class="balance-entry"><div class="mini-label">TOTAL AVAILABLE MONEY</div><div class="onboard-amount big"><input id="ob-balance" type="number" min="0" max="100000000" step="100" value="'+balance+'" inputmode="numeric"><span>FCFA</span></div><div class="quick-amounts">'+[0,5000,10000,25000].map(function(v){return '<button type="button" data-balance-preset="'+v+'">'+(v===0?'0':shortMoney(v))+'</button>';}).join('')+'</div></div><div class="field-label-static">WHERE DO YOU KEEP YOUR MONEY?</div><div class="source-grid">'+sourceDefs.map(function(s){var yes=selectedSources.indexOf(s[0])>=0;return '<button type="button" class="source-choice '+(yes?'selected':'')+'" data-source="'+s[0]+'"><span>'+s[1]+'</span><b>'+s[2]+'</b><i>'+(yes?'✓':'+')+'</i></button>';}).join('')+'</div><div class="hint">We’ll record your total for now. No wallet or bank account is connected.</div>';
 }else if(onboardingStep===5){
  stepTitle='How much do you want to save?';
  stepCopy='Start small. Consistency wins.';
  var target=state.savingsTarget===undefined?2000:Number(state.savingsTarget);
  stepBody='<div class="savings-hero"><div class="mini-label">WEEKLY SAVINGS GOAL</div><div class="range-value"><span id="ob-save-value">'+fmt(target)+'</span></div><input id="ob-savings" type="range" min="0" max="10000" step="500" value="'+target+'"><div class="range-labels"><span>0 FCFA</span><span>10,000 FCFA</span></div><div class="savings-presets">'+[500,1000,2000,3000,5000].map(function(v){return '<button type="button" class="'+(target===v?'active':'')+'" data-saving-preset="'+v+'">'+shortMoney(v)+'</button>';}).join('')+'</div></div><div class="savings-feedback" id="savings-feedback"><span>🎯</span><div><b>'+percent+'% of your income</b><small>'+(percent<=20?'A steady goal that leaves more room for weekly needs.':'A bigger target. We’ll check if it fits your weekly expenses.')+'</small></div></div><div class="info-strip">💡 <span>At <b id="savings-year-target">'+fmt(target)+'</b> per week, you’d save about <b id="savings-year-total">'+fmt(target*52)+'</b> in a year.</span></div>';
 }else if(onboardingStep===6){
  stepTitle='What do you usually need?';
  stepCopy='Let’s use your real costs, not guesses.';
  var needRows=[
   ['Food','🍲','Food / week','Based on your estimate'],['Transport','🚌','Transport / week','Getting around'],['Airtime & data','📱','Internet & airtime / week','Based on 1,000 FCFA every 2 days'],['School / personal','📚','School & personal / week','Starter estimate · edit anytime'],['Other','✨','Other costs / week','Regular extras'],['Debt owed','🧾','Total debts you owe','Outstanding total, not weekly spending']
  ];
  stepBody='<div class="needs-grid">'+needRows.map(function(n){var val=Number(weeklyNeeds[n[0]]||0);return '<label class="need-field"><span class="need-icon">'+n[1]+'</span><span class="need-label"><b>'+n[2]+'</b><small>'+n[3]+'</small></span><span class="need-input-wrap"><input type="number" min="0" max="100000000" step="100" inputmode="numeric" data-need="'+n[0]+'" value="'+val+'"><small>FCFA</small></span></label>';}).join('')+'</div><div class="needs-summary"><span>Estimated weekly needs</span><b>'+fmt(weeklySpend)+'</b></div><div class="needs-alert '+(gap?'warning':'good')+'"><span>'+(gap?'⚠️':'✅')+'</span><div><b>'+(gap?'Your current estimate is above your target.':'Your weekly target looks workable.')+'</b><small>'+(gap?'After saving '+fmt(savings)+', your spending target is '+fmt(spendAfterSavings)+'. The numbers entered are '+fmt(gap)+' above that, before debt repayments. We’ll create an adjustable plan next.':'Your entered weekly needs fit within the money available after savings.')+'</small></div></div>';
 }else{
  stepTitle='Here’s your first budget plan';
  stepCopy='A starting point. Adjust any amount.';
  var planItems=[
   ['Food','🍲','Food and meals'],['Transport','🚌','Getting around'],['Airtime & data','📱','Internet & airtime'],['School / personal','📚','School and personal'],['Emergency buffer','🛟','Keep a little aside']
  ];
  var planTotal=planItems.reduce(function(sum,p){return sum+Number(planValues[p[0]]||0);},0);
  var over=Math.max(0,planTotal+savings-income),left=income-planTotal-savings,needsGap=Math.max(0,weeklySpend-planTotal);
  stepBody='<div class="plan-summary-top"><div><small>WEEKLY INCOME</small><b>'+fmt(income)+'</b></div><div><small>SAVINGS GOAL</small><b>'+fmt(savings)+'</b></div></div><div class="plan-list">'+planItems.map(function(p){return '<label class="plan-row"><span class="plan-icon">'+p[1]+'</span><span class="plan-label"><b>'+p[0]+'</b><small>'+p[2]+'</small></span><span class="plan-value"><input type="number" min="0" max="100000000" step="100" inputmode="numeric" data-plan="'+p[0]+'" value="'+Number(planValues[p[0]]||0)+'"><small>FCFA</small></span></label>';}).join('')+'</div><div class="plan-total"><span>Planned spending</span><b id="plan-total">'+fmt(planTotal)+'</b></div><div class="plan-total savings"><span>Weekly savings</span><b>'+fmt(savings)+'</b></div><div class="plan-total final"><span>Total allocated</span><b id="plan-allocated">'+fmt(planTotal+savings)+'</b></div><div class="needs-alert '+((over||needsGap)?'warning':'good')+'" id="plan-balance-alert"><span>'+(over||needsGap?'⚠️':'✅')+'</span><div><b>'+(over?'This plan is over your income.':needsGap?'Your needs exceed this plan.':'Your plan balances.')+'</b><small id="plan-balance-copy">'+(over?'Reduce allocations by '+fmt(over)+' or adjust the savings target only if essentials remain covered.':needsGap?'Your entered needs are '+fmt(needsGap)+' above planned spending. Review the amounts honestly before accepting this plan.':fmt(Math.max(0,left))+' left unallocated. Keep it for flexibility or add it to a category.')+'</small></div></div><div class="info-strip">🧠 <span>Your estimated needs are <b>'+fmt(weeklySpend)+'/week</b>. This is a suggested target, not a promise that every cost will fit.</span></div>';
 }
 if(onboardingStep===6){
  stepBody=stepBody.replace('<b>'+fmt(weeklySpend)+'</b>','<b id="needs-weekly-total">'+fmt(weeklySpend)+'</b>');
  stepBody=stepBody.replace('class="needs-alert '+(gap?'warning':'good')+'"','class="needs-alert '+(gap?'warning':'good')+'" id="needs-alert-box"');
  stepBody=stepBody.replace('<span>'+(gap?'⚠️':'✅')+'</span>','<span id="needs-alert-icon">'+(gap?'⚠️':'✅')+'</span>');
  stepBody=stepBody.replace('<b>'+(gap?'Your current estimate is above your target.':'Your weekly target looks workable.')+'</b>','<b id="needs-alert-title">'+(gap?'Your current estimate is above your target.':'Your weekly target looks workable.')+'</b>');
  stepBody=stepBody.replace('<small>'+(gap?'After saving '+fmt(savings)+', your spending target is '+fmt(spendAfterSavings)+'. The numbers entered are '+fmt(gap)+' above that, before debt repayments. We’ll create an adjustable plan next.':'Your entered weekly needs fit within the money available after savings.')+'</small>','<small id="needs-alert-copy">'+(gap?'After saving '+fmt(savings)+', your spending target is '+fmt(spendAfterSavings)+'. The numbers entered are '+fmt(gap)+' above that, before debt repayments. We’ll create an adjustable plan next.':'Your entered weekly needs fit within the money available after savings.')+'</small>');
 }
 var sideTitle=onboardingStep===1?'Let’s make this yours.':onboardingStep===2?'Make room for what matters.':onboardingStep===3?'Plan around payday.':onboardingStep===4?'Know what you have.':onboardingStep===5?'Small steps build freedom.':onboardingStep===6?'Real numbers. Better plans.':'Your first plan, made for you.';
 var sideCopy=onboardingStep===6?'We’ll compare what you need with what comes in.':onboardingStep===7?'Your plan stays editable as life changes.':'A money space that fits student life in Cameroon.';
 var sideMetrics='<div class="on-side-metrics"><div><small>WEEKLY INCOME</small><b>'+fmt(income)+'</b></div><div><small>SAVINGS GOAL</small><b>'+fmt(savings)+'</b></div></div>';
 var setup='<div class="ob-body screen"><section class="ob-photo-panel"><img src="./assets/student-onboarding-photo.webp" alt="University student using a phone on campus"><div class="ob-photo-overlay"><span class="ob-photo-tag">YOUR MONEY, YOUR FUTURE</span><h2>'+sideTitle+'</h2><p>'+sideCopy+'</p>'+sideMetrics+'</div></section><section class="ob-card" id="ob-card"><div class="ob-progress-top"><span>SET UP YOUR MONEY</span><strong>'+onboardingStep+' / '+totalSteps+'</strong></div><div class="progress-track"><i style="width:'+progress+'%"></i></div><div class="ob-step-icon">'+({1:'👋🏽',2:'🎯',3:'🗓️',4:'💸',5:'🌱',6:'🧾',7:'✨'})[onboardingStep]+'</div><h2>'+stepTitle+'</h2><p class="ob-sub">'+stepCopy+'</p>'+stepBody+'<div class="ob-footer"><button class="button ghost" data-action="ob-back">← Back</button><div class="step-dots">'+['Profile','Goals','Income','Balance','Savings','Needs','Plan'].map(function(_,i){return '<span class="'+(i+1===onboardingStep?'active':'')+'"></span>';}).join('')+'</div><button class="button" data-action="'+(onboardingStep===7?'ob-finish':'ob-next')+'">'+(onboardingStep===7?'Create my plan':'Continue')+' →</button></div><div class="ob-privacy">🔒 Saved in this browser for this preview.</div></section></div>';
 app.innerHTML=shellStart+setup+shellEnd;
 bindOnboarding();
}
function bindOnboarding(){
 var welcomeBack=document.querySelector('[data-action="ob-welcome-back"]');
 if(welcomeBack)welcomeBack.onclick=function(){if(window.history.length>1)window.history.back();};
 var skip=document.querySelector('[data-action="ob-skip"]');
 if(skip)skip.onclick=function(){saveOnboardingFields();finishOnboarding(true);};
 var start=document.querySelector('[data-action="ob-start"]');
 if(start)start.onclick=function(){onboardingStep=0.5;renderOnboarding();};
 var introBack=document.querySelector('[data-action="ob-intro-back"]');
 if(introBack)introBack.onclick=function(){onboardingStep=0;renderOnboarding();};
 var introNext=document.querySelector('[data-action="ob-intro-next"]');
 if(introNext)introNext.onclick=function(){onboardingStep=1;renderOnboarding();};
 var card=document.getElementById('ob-card');if(!card)return;
 card.querySelectorAll('[data-persona]').forEach(function(b){b.onclick=function(){saveOnboardingFields();selectedPersona=b.dataset.persona;renderOnboarding();};});
 card.querySelectorAll('[data-goal]').forEach(function(b){b.onclick=function(){saveOnboardingFields();var id=b.dataset.goal;var i=selectedGoals.indexOf(id);if(i>=0)selectedGoals.splice(i,1);else if(selectedGoals.length<3)selectedGoals.push(id);else showToast('Choose up to 3 goals.');renderOnboarding();};});
 card.querySelectorAll('[data-cadence]').forEach(function(b){b.onclick=function(){saveOnboardingFields();allowanceCadence=b.dataset.cadence;renderOnboarding();};});
 card.querySelectorAll('[data-payday]').forEach(function(b){b.onclick=function(){saveOnboardingFields();payday=b.dataset.payday;renderOnboarding();};});
 card.querySelectorAll('[data-source]').forEach(function(b){b.onclick=function(){saveOnboardingFields();var id=b.dataset.source;var i=selectedSources.indexOf(id);if(i>=0)selectedSources.splice(i,1);else selectedSources.push(id);renderOnboarding();};});
 card.querySelectorAll('[data-balance-preset]').forEach(function(b){b.onclick=function(){saveOnboardingFields();state.balance=Number(b.dataset.balancePreset);renderOnboarding();};});
 card.querySelectorAll('[data-saving-preset]').forEach(function(b){b.onclick=function(){saveOnboardingFields();state.savingsTarget=Number(b.dataset.savingPreset);renderOnboarding();};});
 card.querySelector('[data-action="ob-next"]')?.addEventListener('click',nextOnboarding);
 card.querySelector('[data-action="ob-back"]')?.addEventListener('click',function(){saveOnboardingFields();onboardingStep=Math.max(0,onboardingStep-1);renderOnboarding();});
 card.querySelector('[data-action="ob-finish"]')?.addEventListener('click',function(){saveOnboardingFields();finishOnboarding(false);});
 card.querySelector('#ob-savings')?.addEventListener('input',function(e){state.savingsTarget=Math.max(0,Number(e.target.value)||0);var v=document.getElementById('ob-save-value');if(v)v.textContent=fmt(state.savingsTarget);updateSavingsFeedback();});
 card.querySelectorAll('[data-plan]').forEach(function(inp){inp.addEventListener('input',updatePlanSummary);});
 card.querySelectorAll('[data-need]').forEach(function(inp){inp.addEventListener('input',updateNeedsSummary);});
}
function saveOnboardingFields(){
 var name=document.getElementById('ob-name');if(name)profile.name=name.value.trim();
 var bal=document.getElementById('ob-balance');if(bal)state.balance=Math.max(0,Number(bal.value)||0);
 var allowance=document.getElementById('ob-allowance');if(allowance)state.allowance=Math.max(0,Number(allowance.value)||0);
 var savings=document.getElementById('ob-savings');if(savings)state.savingsTarget=Math.max(0,Number(savings.value)||0);
 document.querySelectorAll('[data-need]').forEach(function(el){weeklyNeeds[el.dataset.need]=Math.max(0,Number(el.value)||0);});
 document.querySelectorAll('[data-plan]').forEach(function(el){planValues[el.dataset.plan]=Math.max(0,Number(el.value)||0);});
}
function nextOnboarding(){
 saveOnboardingFields();
 if(onboardingStep===1){if(!(profile.name||'').trim())profile.name='Student';onboardingStep=2;renderOnboarding();return;}
 if(onboardingStep===2){if(!selectedGoals.length){showToast('Choose at least one goal.');return;}onboardingStep=3;renderOnboarding();return;}
 if(onboardingStep===3){onboardingStep=4;renderOnboarding();return;}
 if(onboardingStep===4){onboardingStep=5;renderOnboarding();return;}
 if(onboardingStep===5){onboardingStep=6;renderOnboarding();return;}
 if(onboardingStep===6){onboardingStep=7;renderOnboarding();return;}
 finishOnboarding(false);
}
function updateSavingsFeedback(){
 var el=document.getElementById('savings-feedback');if(!el)return;
 var income=onboardingIncomeWeekly(),s=Math.max(0,Number(state.savingsTarget)||0),p=income?Math.round(s/income*100):0;
 el.innerHTML='<span>🎯</span><div><b>'+p+'% of your income</b><small>'+(p<=20?'A steady goal that leaves more room for weekly needs.':'A bigger target. We’ll check if it fits your weekly expenses.')+'</small></div>';var yr=document.getElementById('savings-year-target'),yrTotal=document.getElementById('savings-year-total');if(yr)yr.textContent=fmt(s);if(yrTotal)yrTotal.textContent=fmt(s*52);
}
function updateNeedsSummary(){
 var keys=['Food','Transport','Airtime & data','School / personal','Other'];
 keys.forEach(function(k){var el=document.querySelector('[data-need="'+k+'"]');if(el)weeklyNeeds[k]=Math.max(0,Number(el.value)||0);});
 var total=keys.reduce(function(s,k){return s+Number(weeklyNeeds[k]||0);},0);
 var income=onboardingIncomeWeekly(),savings=Math.max(0,Number(state.savingsTarget)||0),spendLimit=Math.max(0,income-savings),gap=Math.max(0,total-spendLimit);
 var totalEl=document.getElementById('needs-weekly-total'),box=document.getElementById('needs-alert-box'),ico=document.getElementById('needs-alert-icon'),title=document.getElementById('needs-alert-title'),copy=document.getElementById('needs-alert-copy');
 if(totalEl)totalEl.textContent=fmt(total);
 if(box)box.className='needs-alert '+(gap?'warning':'good');
 if(ico)ico.textContent=gap?'⚠️':'✅';
 if(title)title.textContent=gap?'Your current estimate is above your target.':'Your weekly target looks workable.';
 if(copy)copy.textContent=gap?'After saving '+fmt(savings)+', your spending target is '+fmt(spendLimit)+'. Your entered needs are '+fmt(gap)+' above that, before debt repayments. We’ll create an adjustable plan next.':'Your entered weekly needs fit within the money available after savings.';
}
function updatePlanSummary(){
 var total=0;document.querySelectorAll('[data-plan]').forEach(function(el){var n=Math.max(0,Number(el.value)||0);planValues[el.dataset.plan]=n;total+=n;});
 var needKeys=['Food','Transport','Airtime & data','School / personal','Other'];
 var needsTotal=needKeys.reduce(function(sum,key){return sum+Math.max(0,Number(weeklyNeeds[key])||0);},0);
 var savings=Math.max(0,Number(state.savingsTarget)||0),income=onboardingIncomeWeekly(),allocated=total+savings,left=income-allocated,over=Math.max(0,-left),needsGap=Math.max(0,needsTotal-total);
 var t=document.getElementById('plan-total'),a=document.getElementById('plan-allocated'),box=document.getElementById('plan-balance-alert'),copy=document.getElementById('plan-balance-copy');
 if(t)t.textContent=fmt(total);if(a)a.textContent=fmt(allocated);
 if(box){
  box.className='needs-alert '+((over||needsGap)?'warning':'good');
  box.querySelector('span').textContent=(over||needsGap)?'⚠️':'✅';
  box.querySelector('b').textContent=over?'This plan is over your income.':needsGap?'Your needs exceed this plan.':'Your plan balances.';
 }
 if(copy)copy.textContent=over?'Your allocations exceed income by '+fmt(over)+'. Prioritize essentials and review your planned savings.':needsGap?'Your entered needs are '+fmt(needsGap)+' above planned spending. Review the amounts honestly before accepting this plan.':fmt(left)+' left unallocated. Keep it for flexibility or add it to a category.';
}
function finishOnboarding(skip){
 saveOnboardingFields();
 if(!profile.name)profile.name='Student';
 profile.persona=selectedPersona;profile.payday=payday;profile.moneySources=selectedSources.slice();
 profile.weeklyNeeds=Object.assign({},weeklyNeeds);
 profile.weeklyIncome=onboardingIncomeWeekly();
 profile.weeklySavingsGoal=Math.max(0,Number(state.savingsTarget)||0);
 if(!selectedGoals.length)selectedGoals=['emergency'];
 state.cadence=allowanceCadence;state.payday=payday;
 state.savingsTarget=Math.max(0,Number(state.savingsTarget)||0);
 state.weeklyNeeds=Object.assign({},weeklyNeeds);
 state.weeklyPlan=Object.assign({},planValues);
 state.budget={
  Food:Number(planValues.Food)||0,
  Transport:Number(planValues.Transport)||0,
  'Airtime & data':Number(planValues['Airtime & data'])||0,
  School:Number(planValues['School / personal'])||0,
  Housing:0,
  Other:Number(planValues['Emergency buffer'])||0
 };
 state.budgetPeriod='weekly';
 state.goals=selectedGoals.map(function(id){var g=goalOptions.find(function(x){return x.id===id;})||goalOptions[0];return {id:id,name:g.title.replace('Build a safety cushion','Emergency cushion'),target:g.target,saved:0,emoji:g.emoji};});
 state.onboarded=true;state.tutorialDone=false;persist();
 app.classList.add('celebrate');launchConfetti();page='dashboard';renderApp();if(!skip){tourStep=0;renderTour();}else{state.tutorialDone=true;persist();}
}

if(state.onboarded){page='dashboard';renderApp();if(!state.tutorialDone){tourStep=0;renderTour();}}else{state.balance=state.balance||5000;state.allowance=state.allowance||10000;state.budget=state.budget||Object.assign({},categoryDefaults);if(!Array.isArray(selectedGoals)||!selectedGoals.length)selectedGoals=['emergency','school'];renderOnboarding();}
if('serviceWorker' in navigator && location.protocol.indexOf('http')===0){navigator.serviceWorker.register('./sw.js').catch(function(){});}
})();
