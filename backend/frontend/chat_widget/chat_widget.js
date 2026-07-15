const toggle = document.getElementById('chat-toggle');
const widget = document.getElementById('chat-widget');
const form = document.getElementById('chat-form');
const input = document.getElementById('chat-input');
const body = document.getElementById('chat-body');

toggle.addEventListener('click', ()=>{
  widget.classList.toggle('chat-hidden');
});

function appendMessage(text, who='bot'){
  const div = document.createElement('div');
  div.className = `message ${who}`;
  div.textContent = text;
  body.appendChild(div);
  body.scrollTop = body.scrollHeight;
}

form.addEventListener('submit', async (e)=>{
  e.preventDefault();
  const q = input.value.trim();
  if(!q) return;
  appendMessage(q,'user');
  input.value = '';
  try{
    const res = await fetch('/api/chat',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body: JSON.stringify({message:q})
    });
    if(!res.ok) throw new Error('Network');
    const data = await res.json();
    appendMessage(data.answer || '응답이 없습니다.');
  }catch(err){
    appendMessage('서버와 통신할 수 없습니다.');
  }
});
