document.addEventListener('DOMContentLoaded',()=>{
const form=document.getElementById('system-form') || document.getElementById('settings-form');
const result=document.getElementById('result');
const saveButton=document.getElementById('save-settings');

function snapshot(){
  if(!form)return '';
  const data={};
  new FormData(form).forEach((v,k)=>data[k]=v);
  form.querySelectorAll('input[type=checkbox]').forEach(x=>data[x.name]=x.checked);
  return JSON.stringify(data);
}

let initialState=snapshot();
function markChanged(){
  const changed=snapshot()!==initialState;
  if(saveButton){
    saveButton.hidden=!changed;
    saveButton.disabled=!changed;
  }
  if(result && changed) result.textContent='';
}

async function save(payload){
  const r=await fetch(`/api/guild/${window.FLAME_GUILD}/settings`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  return await r.json();
}

if(form){
  form.addEventListener('input',markChanged);
  form.addEventListener('change',markChanged);
  form.addEventListener('submit',async e=>{
    e.preventDefault();
    if(snapshot()===initialState)return;
    if(saveButton)saveButton.disabled=true;
    const p={};
    new FormData(form).forEach((v,k)=>p[k]=v);
    form.querySelectorAll('input[type=checkbox]').forEach(x=>p[x.name]=x.checked);
    ['xp_min','xp_max','level_cooldown'].forEach(k=>{if(p[k]!==undefined&&p[k]!=='')p[k]=Number(p[k]);});
    try{
      const d=await save(p);
      if(d.ok){
        initialState=snapshot();
        if(saveButton){saveButton.hidden=true;saveButton.disabled=true;}
        if(result)result.textContent='✓ تم الحفظ بنجاح.';
      }else{
        if(saveButton)saveButton.disabled=false;
        if(result)result.textContent='✕ '+(d.error||'تعذر الحفظ');
      }
    }catch(err){
      if(saveButton)saveButton.disabled=false;
      if(result)result.textContent='✕ تعذر الاتصال بالسيرفر.';
    }
  });
}

markChanged();

const add=document.getElementById('add-reply');
if(add)add.onclick=async()=>{
  const t=document.getElementById('reply-trigger'),r=document.getElementById('reply-response');
  if(!t.value.trim()||!r.value.trim())return alert('اكتب الكلمة والرد أولاً.');
  const d=await save({autoreply_action:'add',trigger:t.value.trim(),response:r.value.trim()});
  if(d.ok)location.reload();else alert(d.error||'تعذر الإضافة');
};
document.querySelectorAll('.delete-reply').forEach(b=>b.onclick=async()=>{
  if(!confirm('حذف هذا الرد؟'))return;
  const d=await save({autoreply_action:'delete',trigger:b.dataset.trigger});
  if(d.ok)location.reload();else alert(d.error||'تعذر الحذف');
});
});
