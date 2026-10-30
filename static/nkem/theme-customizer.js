document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("[data-theme-customizer]");
  if (!form) return;
  const select = form.querySelector("[data-palette-select]");
  const fields = Object.fromEntries(Array.from(form.querySelectorAll("[data-palette-field]")).map(input => [input.dataset.paletteField, input]));
  const root = document.documentElement;
  const swatches = Array.from(form.querySelectorAll("[data-preset]"));
  const keys = ["primary", "accent", "background", "surface", "text", "muted", "border"];
  const presets = {
    violet: {primary:"#7651F5",accent:"#16C9D5",background:"#F7F5FC",surface:"#FFFFFF",text:"#211A3B",muted:"#817A98",border:"#EAE5F4"},
    mint: {primary:"#0B8967",accent:"#F1B85B",background:"#F3F8F5",surface:"#FFFFFF",text:"#182D26",muted:"#71847B",border:"#E1ECE6"},
    ocean: {primary:"#256E9B",accent:"#36BCD0",background:"#F2F7FA",surface:"#FFFFFF",text:"#1B2D3A",muted:"#71828D",border:"#DFEAF0"},
    sunset: {primary:"#A75C43",accent:"#E6A64D",background:"#FBF5F1",surface:"#FFFFFF",text:"#34251F",muted:"#8A766D",border:"#EFE3DB"},
    midnight: {primary:"#9A83FF",accent:"#27D0D3",background:"#11111B",surface:"#1C1B2A",text:"#F2F0FF",muted:"#AAA5C3",border:"#363348"}
  };
  const hex = value => /^#[0-9a-f]{6}$/i.test(value || "") ? value.toUpperCase() : "#7651F5";
  const rgb = value => [1,3,5].map(i => parseInt(value.slice(i, i+2), 16));
  const toHex = channels => "#" + channels.map(v => Math.max(0,Math.min(255,Math.round(v))).toString(16).padStart(2,"0")).join("").toUpperCase();
  const rgbToHsl = (r,g,b) => {
    r/=255;g/=255;b/=255;
    const max=Math.max(r,g,b),min=Math.min(r,g,b),d=max-min;
    let h=0,s=0,l=(max+min)/2;
    if(d){s=d/(1-Math.abs(2*l-1));switch(max){case r:h=((g-b)/d+(g<b?6:0))/6;break;case g:h=((b-r)/d+2)/6;break;default:h=((r-g)/d+4)/6;}}
    return [h,s,l];
  };
  const hslToRgb = (h,s,l) => {
    const k=n=>(n+h*12)%12;
    const a=s*Math.min(l,1-l);
    const f=n=>l-a*Math.max(-1,Math.min(k(n)-3,Math.min(9-k(n),1)));
    return [f(0),f(8),f(4)].map(v=>v*255);
  };
  const blend = (a,b,t) => toHex(rgb(a).map((v,i)=>v*(1-t)+rgb(b)[i]*t));
  const lighten = (c,t) => blend(c,"#FFFFFF",t);
  const darken = (c,t) => blend(c,"#111111",t);
  const readPalette = () => Object.fromEntries(keys.map(key=>[key,hex(fields[key]?.value)]));
  const setRootTokens = palette => {
    const dark = darken(palette.primary,.27);
    const soft = blend(palette.background,palette.primary,.11);
    const surfaceSoft = blend(palette.background,palette.surface,.55);
    const backgroundLightness=rgbToHsl(...rgb(palette.background))[2];
    const props = {
      "--brand-primary":palette.primary,"--brand-dark":dark,"--brand-soft":soft,"--brand-accent":palette.accent,
      "--bg":palette.background,"--surface":palette.surface,"--surface-soft":surfaceSoft,
      "--text":palette.text,"--muted":palette.muted,"--line":palette.border,"--focus-ring":lighten(palette.primary,.30),
      "--ui-color-scheme":backgroundLightness<.42?"dark":"light"
    };
    Object.entries(props).forEach(([key,value])=>root.style.setProperty(key,value));
    Array.from(root.style).filter(name=>name.startsWith("--paint-")).forEach(name=>{
      let raw=name.slice(8), alpha=1;
      if(raw.length===8){alpha=parseInt(raw.slice(6,8),16)/255;raw=raw.slice(0,6);}
      if(raw.length===4)raw=raw.slice(0,3).split("").map(x=>x+x).join("");
      if(raw.length===3)raw=raw.split("").map(x=>x+x).join("");
      if(raw.length!==6)return;
      const original="#"+raw;
      const [h,s,l]=rgbToHsl(...rgb(original));
      let mapped;
      if(alpha<.42&&s<.2)mapped=original;
      else if(s<.18){
        if(l>=.93)mapped=palette.surface;
        else if(l>=.80)mapped=blend(palette.surface,palette.background,(.93-l)/.13*.72);
        else if(l>=.64)mapped=blend(palette.muted,palette.surface,(l-.64)/.16*.24);
        else if(l>=.32)mapped=blend(palette.text,palette.muted,(l-.32)/.32);
        else mapped=blend(palette.text,dark,.22);
      }else if(h<=.035||h>=.965)mapped="#D94F68";
      else if(h>=.07&&h<=.18)mapped=original;
      else{
        const accent=h>=.43&&h<=.73;
        const [targetHue,,targetSat]=rgbToHsl(...rgb(accent?palette.accent:palette.primary));
        mapped=toHex(hslToRgb(targetHue,Math.max(.28,Math.min(.94,s*(.68+targetSat*.38))),Math.max(.12,Math.min(.91,l))));
      }
      const value=alpha<.999?"rgba("+rgb(mapped).join(", ")+", "+alpha.toFixed(3)+")":mapped;
      root.style.setProperty(name,value);
    });
  };
  const syncPreview = () => {
    const palette=readPalette();
    setRootTokens(palette);
    Object.entries(palette).forEach(([key,value])=>{
      const target=form.querySelector('[data-palette-value="'+key+'"]');
      if(target)target.textContent=value;
    });
    swatches.forEach(button=>button.classList.toggle("is-selected",button.dataset.preset===(select?.value||"violet")));
  };
  const choosePreset = key => {
    const palette=presets[key];
    if(!palette)return;
    keys.forEach(name=>{if(fields[name])fields[name].value=palette[name];});
    if(select)select.value=key;
    syncPreview();
  };
  swatches.forEach(button=>button.addEventListener("click",()=>{
    if(button.dataset.preset==="custom"){if(select)select.value="custom";syncPreview();return;}
    choosePreset(button.dataset.preset);
  }));
  select?.addEventListener("change",()=>{
    if(presets[select.value])choosePreset(select.value);
    else syncPreview();
  });
  Object.values(fields).forEach(input=>input?.addEventListener("input",()=>{
    if(select)select.value="custom";
    syncPreview();
  }));
  form.querySelector("[data-palette-reset]")?.addEventListener("click",()=>choosePreset("violet"));
  if(select&&presets[select.value])choosePreset(select.value);else syncPreview();
});
