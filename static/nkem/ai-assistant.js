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
 form.addEventListener("submit",function(){
  if(!input.value.trim())return;
  send.disabled=true;send.setAttribute("aria-label","Sending message");
  if(loading)loading.classList.add("active");
  if(transcript)transcript.scrollTop=transcript.scrollHeight;
 });
 if(transcript)transcript.scrollTop=transcript.scrollHeight;
 resize();
});
})();