
// Toggle chat
function toggleChat(){
    const chat = document.getElementById("chatbox");
    chat.style.display = chat.style.display === "flex" ? "none" : "flex";
}

// ENTER key support
function handleKey(e){
    if(e.key === "Enter"){
        sendChat();
    }
}

// ✅ Your function (improved slightly)
function sendChat(){

  const input = document.getElementById("chat-input");
  const message = input.value.trim();

  if(message === "") return;

  const chatBox = document.getElementById("chat-messages");

  // Show user message
  chatBox.innerHTML += `<div><b>You:</b> ${message}</div>`;

  // Clear input
  input.value = "";

  fetch("/chat",{
    method:"POST",
    headers:{
      "Content-Type":"application/json"
    },
    body: JSON.stringify({message})
  })
  .then(r=>r.json())
  .then(data=>{
     chatBox.innerHTML += `<div><b>AI:</b> ${data.reply}</div>`;
     chatBox.scrollTop = chatBox.scrollHeight;
  })
  .catch(err=>{
     chatBox.innerHTML += `<div><b>AI:</b> Error connecting to server</div>`;
  });

}
