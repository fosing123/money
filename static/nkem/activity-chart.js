document.addEventListener("DOMContentLoaded",()=>{
 const root=document.querySelector("[data-activity-dashboard]");if(!root)return;
 const rows=[...root.querySelectorAll("[data-chart-row]")],tabs=[...root.querySelectorAll("[data-activity-period]")];
 const total=root.querySelector("[data-activity-total]"),incomeOut=root.querySelector("[data-activity-income]"),expenseOut=root.querySelector("[data-activity-expense]");
 const lineIn=root.querySelector('[data-chart-line="income"]'),lineOut=root.querySelector('[data-chart-line="expense"]'),areaIn=root.querySelector('[data-chart-area="income"]'),areaOut=root.querySelector('[data-chart-area="expense"]'),labels=root.querySelector("[data-chart-labels]"),note=root.querySelector("[data-chart-note]");
 const fmt=n=>Math.round(n).toLocaleString(undefined),incKinds=new Set(["income","refund","transfer_in"]),outKinds=new Set(["expense","transfer_out"]);
 const today=new Date();today.setHours(23,59,59,999);\n const dateLabels=[...root.querySelectorAll("[data-activity-date]")],localDate=d=>d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");\n const todayKey=localDate(new Date()),yesterday=new Date();yesterday.setDate(yesterday.getDate()-1);const yesterdayKey=localDate(yesterday);\n dateLabels.forEach(el=>{const key=el.dataset.activityDate;if(key===todayKey)el.textContent="Today";else if(key===yesterdayKey)el.textContent="Yesterday"});
 const startOf=(d,p)=>{const x=new Date(d);x.setHours(0,0,0,0);if(p==="week"){x.setDate(x.getDate()-((x.getDay()+6)%7));return x}if(p==="month"){x.setDate(1);return x}if(p==="year"){x.setMonth(0,1);return x}return x};
 function render(period){
  const end=new Date(today),start=startOf(end,period);
  const filtered=rows.map(el=>({kind:el.dataset.kind,amount:Number(el.dataset.amount)||0,date:new Date((el.dataset.date||"")+"T12:00:00"),created:new Date(el.dataset.created||el.dataset.date)})).filter(x=>Number.isFinite(x.date.getTime())&&x.date>=start&&x.date<=end);
  const count=period==="day"?24:period==="week"?7:period==="month"?Math.max(1,end.getDate()):12;
  const buckets=Array.from({length:count},()=>({income:0,expense:0,label:""}));
  filtered.forEach(x=>{let i=0;if(period==="day")i=Number.isFinite(x.created.getTime())?x.created.getHours():x.date.getHours();else if(period==="week")i=Math.max(0,Math.min(6,Math.floor((new Date(x.date.getFullYear(),x.date.getMonth(),x.date.getDate())-start)/86400000)));else if(period==="month")i=x.date.getDate()-1;else i=x.date.getMonth();if(incKinds.has(x.kind))buckets[i].income+=x.amount;else if(outKinds.has(x.kind))buckets[i].expense+=x.amount});
  buckets.forEach((b,i)=>{b.label=period==="day"?(i%6===0?(i===0?"12a":i+"h"):""):period==="week"?["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][i]:period==="month"?(i===0||i===count-1||(i+1)%5===0?String(i+1):""):["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][i]});
  const sumIn=filtered.filter(x=>incKinds.has(x.kind)).reduce((a,x)=>a+x.amount,0),sumOut=filtered.filter(x=>outKinds.has(x.kind)).reduce((a,x)=>a+x.amount,0);
  total.innerHTML=fmt(sumOut)+' <small>FCFA</small>';incomeOut.textContent=fmt(sumIn);expenseOut.textContent=fmt(sumOut);
  const max=Math.max(1,...buckets.map(b=>b.income),...buckets.map(b=>b.expense)),xAt=i=>10+(i/Math.max(1,count-1))*700,yAt=v=>220-(v/max)*178;
  const path=arr=>{if(!arr.length)return "";let d="M "+arr[0][0]+" "+arr[0][1];for(let i=0;i<arr.length-1;i++){const p0=arr[Math.max(0,i-1)],p1=arr[i],p2=arr[i+1],p3=arr[Math.min(arr.length-1,i+2)],c1=[p1[0]+(p2[0]-p0[0])/6,p1[1]+(p2[1]-p0[1])/6],c2=[p2[0]-(p3[0]-p1[0])/6,p2[1]-(p3[1]-p1[1])/6];d+=" C "+c1[0]+" "+c1[1]+", "+c2[0]+" "+c2[1]+", "+p2[0]+" "+p2[1]}return d};
  const make=k=>buckets.map((b,i)=>[xAt(i),yAt(b[k])]),a=make("income"),b=make("expense");
  lineIn.setAttribute("d",path(a));lineOut.setAttribute("d",path(b));areaIn.setAttribute("d",path(a)+" L 710 225 L 10 225 Z");areaOut.setAttribute("d",path(b)+" L 710 225 L 10 225 Z");
  labels.replaceChildren();const pick=[0,Math.floor((count-1)/4),Math.floor((count-1)/2),Math.floor((count-1)*3/4),count-1];[...new Set(pick)].forEach(i=>{const el=document.createElement("span");el.textContent=buckets[i]?.label||"";labels.append(el)});
  const idx=buckets.reduce((best,v,i)=>v.expense>buckets[best].expense?i:best,0),guide=root.querySelector("[data-chart-guide]"),pIn=root.querySelector('[data-chart-point="income"]'),pOut=root.querySelector('[data-chart-point="expense"]');
  guide.setAttribute("x1",xAt(idx));guide.setAttribute("x2",xAt(idx));guide.setAttribute("opacity",filtered.length?"1":"0");
  [[pIn,buckets[idx].income],[pOut,buckets[idx].expense]].forEach(pair=>{pair[0].setAttribute("cx",xAt(idx));pair[0].setAttribute("cy",yAt(pair[1]));pair[0].setAttribute("opacity",filtered.length?"1":"0")});
  note.textContent=filtered.length?filtered.length+" recorded transaction"+(filtered.length===1?"":"s")+" · "+({day:"today",week:"this week",month:"this month",year:"this year"}[period]):"No transactions recorded in this period yet.";
  tabs.forEach(t=>{const active=t.dataset.activityPeriod===period;t.classList.toggle("is-active",active);t.setAttribute("aria-pressed",active?"true":"false")});
 }
 tabs.forEach(t=>t.addEventListener("click",()=>render(t.dataset.activityPeriod)));render("week");
});