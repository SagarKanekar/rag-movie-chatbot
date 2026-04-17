const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const clearChatBtn = document.getElementById("clearChatBtn");
const messages = document.getElementById("messages");
const statusText = document.getElementById("statusText");
const chips = document.querySelectorAll(".chip");
const emptyState = document.getElementById("emptyState");

let isLoading = false;
let typingBubble = null;

function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

function updateEmptyState() {
  const hasMessages = messages.querySelector(".message") !== null;
  if (emptyState) {
    emptyState.hidden = hasMessages;
  }
}

function addMessage(role, content, isTyping = false) {
  const bubble = document.createElement("article");
  bubble.className = `message ${role} message-enter`;

  if (isTyping) {
    bubble.innerHTML = "<span class='typing' aria-label='Assistant is typing'><span></span><span></span><span></span></span>";
  } else {
    bubble.textContent = content;
  }

  messages.appendChild(bubble);
  updateEmptyState();
  scrollToBottom();
  return bubble;
}

function resetChat() {
  messages.querySelectorAll(".message").forEach((node) => node.remove());
  if (typingBubble) {
    typingBubble.remove();
    typingBubble = null;
  }
  statusText.textContent = "";
  updateEmptyState();
}

function setLoading(loading) {
  isLoading = loading;
  sendBtn.disabled = loading;
  clearChatBtn.disabled = loading;
  chips.forEach((chip) => {
    chip.disabled = loading;
  });
  if (loading) {
    statusText.textContent = "Assistant is thinking…";
  } else if (statusText.textContent === "Assistant is thinking…") {
    statusText.textContent = "";
  }
}

async function sendMessage(rawMessage) {
  const message = (rawMessage || "").trim();
  if (!message || isLoading) {
    return;
  }

  statusText.textContent = "";
  addMessage("user", message);
  setLoading(true);
  typingBubble = addMessage("assistant", "", true);

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    });

    let data = {};
    try {
      data = await response.json();
    } catch (_) {
      throw new Error("Unexpected server response.");
    }

    if (!response.ok || !data.reply) {
      throw new Error(data.detail || "Unable to get a response right now.");
    }

    if (typingBubble) {
      typingBubble.remove();
      typingBubble = null;
    }
    addMessage("assistant", data.reply);
  } catch (_) {
    if (typingBubble) {
      typingBubble.remove();
      typingBubble = null;
    }
    statusText.textContent = "Sorry, we couldn't reach the chat service. Please try again.";
    addMessage("assistant", "I hit an issue connecting to the server. Please try again in a moment.");
  } finally {
    setLoading(false);
    messageInput.focus();
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const draft = messageInput.value;
  const trimmed = draft.trim();
  if (!trimmed) {
    return;
  }
  messageInput.value = "";
  sendMessage(trimmed);
});

messageInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

chips.forEach((chip) => {
  chip.addEventListener("click", () => {
    if (isLoading) {
      return;
    }
    const prompt = (chip.dataset.prompt || "").trim();
    if (!prompt) {
      return;
    }
    messageInput.value = prompt;
    messageInput.focus();
    messageInput.setSelectionRange(prompt.length, prompt.length);
  });
});

clearChatBtn.addEventListener("click", () => {
  if (isLoading) {
    return;
  }
  resetChat();
  messageInput.focus();
});

updateEmptyState();
