(function(){
"use strict";
document.addEventListener("DOMContentLoaded",function(){
 const form=document.querySelector("[data-ai-form]");
 const input=document.querySelector("#aiPrompt");
 const send=document.querySelector("[data-ai-send]");
 const transcript=document.querySelector("[data-ai-transcript]");
 const loading=document.querySelector("[data-ai-loading]");
 if(!form||!input||!send)return;
 document.querySelectorAll("[data-fill-prompt]").forEach(function(button){
  button.addEventListener("click",function(){input.value=button.dataset.fillPrompt||"";input.focus();input.dispatchEvent(new Event("input",{bubbles:true}));});
 });
 const resize=function(){input.style.height="auto";input.style.height=Math.min(input.scrollHeight,130)+"px";};
 input.addEventListener("input",resize);
 input.addEventListener("keydown",function(event){if(event.key==="Enter"&&!event.shiftKey){event.preventDefault();form.requestSubmit();}});
 form.addEventListener("submit",async function(event){
  if(!input.value.trim())return;
  if(form.dataset.tianaAdPassed!=="true"&&window.TianaAdGate){
   event.preventDefault();
   if(form.dataset.tianaAdPending==="true")return;
   form.dataset.tianaAdPending="true";
   try{
    const allowed=await window.TianaAdGate.show();
    if(!allowed){delete form.dataset.tianaAdPending;return;}
    form.dataset.tianaAdPassed="true";
    delete form.dataset.tianaAdPending;
    form.requestSubmit(send);
    return;
   }catch(error){
    delete form.dataset.tianaAdPending;
    return;
   }
  }
  delete form.dataset.tianaAdPassed;
  send.disabled=true;send.setAttribute("aria-label","Sending message");
  if(loading)loading.classList.add("active");
  if(transcript)transcript.scrollTop=transcript.scrollHeight;
 });
 if(transcript)transcript.scrollTop=transcript.scrollHeight;
 resize();
});
})();