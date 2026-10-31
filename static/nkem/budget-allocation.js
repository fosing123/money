document.addEventListener("DOMContentLoaded",()=>{
 const root=document.querySelector("[data-budget-dashboard]");if(!root)return;
 const cards=[...root.querySelectorAll("[data-budget-item]")],donut=root.querySelector("[data-budget-donut]"),legend=root.querySelector("[data-budget-legend]");
 const style=getComputedStyle(document.body),tokens=["--budget-segment-a","--budget-segment-b","--budget-segment-c","--budget-segment-d","--budget-segment-e"].map(k=>style.getPropertyValue(k).trim()||style.getPropertyValue("--brand-primary").trim());
 const fmt=n=>Math.round(n).toLocaleString(undefined),currency=document.querySelector(".budget-donut-hole>span")?.textContent||"FCFA";
 const data=cards.map(c=>({name:c.dataset.budgetName||"Other",amount:Number(c.dataset.budgetAmount)||0,spent:Number(c.dataset.budgetSpent)||0})).filter(x=>x.amount>0);
 const total=data.reduce((s,x)=>s+x.amount,0),spent=data.reduce((s,x)=>s+x.spent,0);
 root.querySelector("[data-budget-total]").textContent=fmt(total);root.querySelector("[data-budget-spent]").textContent=fmt(spent)+" spent";
 root.querySelector("[data-budget-planned]").textContent=fmt(total)+" "+currency;root.querySelector("[data-budget-actual]").textContent=fmt(spent)+" "+currency;
 if(!data.length){donut.style.background="conic-gradient(var(--brand-soft) 0 100%)";legend.replaceChildren();const msg=document.createElement("p");msg.className="budget-legend-placeholder";msg.textContent="Create a budget to see how your plan is allocated.";legend.append(msg);return}
 let cursor=0;const segments=data.map((item,i)=>{const begin=cursor;cursor+=item.amount/total*100;return tokens[i%tokens.length]+" "+begin+"% "+cursor+"%"});donut.style.background="conic-gradient("+segments.join(",")+")";
 legend.replaceChildren();data.slice(0,7).forEach((item,i)=>{const row=document.createElement("div");row.className="budget-legend-item";const dot=document.createElement("i");dot.className="budget-legend-dot";dot.style.setProperty("--slice-color",tokens[i%tokens.length]);const name=document.createElement("span");name.className="budget-legend-name";name.textContent=item.name;const amount=document.createElement("strong");amount.className="budget-legend-amount";amount.textContent=fmt(item.amount);row.append(dot,name,amount);legend.append(row)});
});