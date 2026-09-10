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
  const guildId=String(window.FLAME_GUILD || '').trim();
  const r=await fetch(`/api/guild/${guildId}/settings`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  return await r.json();
}

function buildSpecialPayload(p){
  if(document.querySelector('[name="ticket_button_label_1"]')){
    const buttons=[];
    for(let i=1;i<=5;i++){
      const label=document.querySelector(`[name="ticket_button_label_${i}"]`)?.value.trim() || '';
      if(!label) continue;
      buttons.push({
        label,
        emoji:document.querySelector(`[name="ticket_button_emoji_${i}"]`)?.value.trim() || '🎫',
        style:document.querySelector(`[name="ticket_button_style_${i}"]`)?.value || 'success',
        category_id:document.querySelector(`[name="ticket_button_category_${i}"]`)?.value || '',
        support_role_id:document.querySelector(`[name="ticket_button_role_${i}"]`)?.value || '',
        title:document.querySelector(`[name="ticket_button_title_${i}"]`)?.value.trim() || '',
        description:document.querySelector(`[name="ticket_button_description_${i}"]`)?.value.trim() || ''
      });
    }
    for(let i=1;i<=5;i++){
      delete p[`ticket_button_label_${i}`];
      delete p[`ticket_button_emoji_${i}`];
      delete p[`ticket_button_style_${i}`];
      delete p[`ticket_button_category_${i}`];
      delete p[`ticket_button_role_${i}`];
      delete p[`ticket_button_title_${i}`];
      delete p[`ticket_button_description_${i}`];
    }
    p.ticket_buttons=buttons;
  }
  if(document.querySelector('[name="level_reward_1"]')){
    const rewards={};
    for(let i=1;i<=20;i++){
      const value=document.querySelector(`[name="level_reward_${i}"]`)?.value || '';
      if(value) rewards[String(i)]=value;
      delete p[`level_reward_${i}`];
    }
    p.level_rewards=rewards;
  }
  return p;
}

function addVariablePanel(){
  if(!form || !location.pathname.includes('/system/')) return;
  const system=location.pathname.split('/').pop();
  const configs={
    welcome:{
      title:'المتغيرات المتاحة للترحيب',
      help:'انسخ المتغير وضعه داخل رسالة الترحيب، وسيتم استبداله تلقائياً عند دخول العضو.',
      items:[
        ['{member}','منشن العضو'],
        ['{username}','اسم العضو'],
        ['{server}','اسم السيرفر'],
        ['{members}','عدد أعضاء السيرفر'],
        ['{inviter}','الشخص الذي دعا العضو'],
        ['{count}','عدد الأعضاء (قديم ومتوافق)']
      ]
    },
    tickets:{
      title:'المتغيرات المتاحة للتذاكر',
      help:'تقدر تستخدمها داخل عنوان أو رسالة التذكرة.',
      items:[
        ['{member}','منشن صاحب التذكرة'],
        ['{username}','اسم صاحب التذكرة'],
        ['{server}','اسم السيرفر'],
        ['{ticket}','رقم التذكرة']
      ]
    }
  };
  const config=configs[system];
  if(!config)return;
  const target=form.querySelector('textarea[name="welcome_message"]') || form.querySelector('textarea[name="ticket_button_description_1"]') || form.querySelector('textarea[name="ticket_panel_description"]');
  if(!target)return;
  if(form.querySelector('.flame-variables'))return;
  const panel=document.createElement('div');
  panel.className='panel flame-variables';
  panel.style.marginTop='12px';
  panel.innerHTML=`<h3>${config.title}</h3><p>${config.help}</p><div class="flame-variable-list"></div>`;
  const list=panel.querySelector('.flame-variable-list');
  config.items.forEach(([value,label])=>{
    const row=document.createElement('div');
    row.className='flame-variable-row';
    row.innerHTML=`<code>${value}</code><span>${label}</span><button type="button" class="purple-btn flame-copy">نسخ</button>`;
    row.querySelector('.flame-copy').addEventListener('click',async()=>{
      try{await navigator.clipboard.writeText(value);row.querySelector('.flame-copy').textContent='تم النسخ';setTimeout(()=>row.querySelector('.flame-copy').textContent='نسخ',1200);}catch(e){target.focus();document.execCommand('insertText',false,value);}
    });
    list.appendChild(row);
  });
  target.closest('label')?.insertAdjacentElement('afterend',panel);
}

addVariablePanel();

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
    buildSpecialPayload(p);
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
