(function () {
"use strict";
const button=document.querySelector("[data-tiana-push-enable]");
const status=document.querySelector("[data-tiana-push-status]");
if(!button||!("Notification" in window)||!("serviceWorker" in navigator))return;
const csrf=()=>{const m=document.cookie.match(/(?:^|; )csrftoken=([^;]*)/);return m?decodeURIComponent(m[1]):"";};
button.addEventListener("click",async()=>{
button.disabled=true;
try{
if(!window.firebase||!window.TIANA_FIREBASE_CONFIG||!window.TIANA_FIREBASE_CONFIG.apiKey)throw new Error("Firebase web configuration is not ready.");
const permission=await Notification.requestPermission();
if(permission!=="granted")throw new Error("Notification permission was not granted.");
const registration=await navigator.serviceWorker.ready;
const app=window.firebase.apps.length?window.firebase.app():window.firebase.initializeApp(window.TIANA_FIREBASE_CONFIG);
const messaging=window.firebase.messaging(app);
const vapidKey=document.querySelector('meta[name="tiana-fcm-vapid"]')?.content||"";
if(!vapidKey)throw new Error("Firebase Web Push VAPID key is missing.");
const token=await messaging.getToken({vapidKey,serviceWorkerRegistration:registration});
if(!token)throw new Error("Firebase did not return a device token.");
const response=await fetch("/api/push/register/",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json","X-CSRFToken":csrf()},body:JSON.stringify({token,platform:"web"})});
if(!response.ok)throw new Error("TIANA could not register this device.");
if(status)status.textContent="Notifications enabled on this device.";
button.textContent="Enabled";
}catch(error){if(status)status.textContent=error.message||"Could not enable notifications.";button.disabled=false;}
});
})();