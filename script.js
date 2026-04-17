const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const clearChatBtn = document.getElementById("clearChatBtn");
const messages = document.getElementById("messages");
const statusText = document.getElementById("statusText");
const chips = document.querySelectorAll("button.chip");
const quickPromptChips = document.querySelectorAll("button.chip[data-prompt]");
const filterChips = document.querySelectorAll("button.filter-chip");
const emptyState = document.getElementById("emptyState");

const STORAGE_KEY = "cineScopeChatHistoryV1";
const FILTER_SUFFIX_PATTERN = /\n\n\[Filters:[\s\S]*?\]\s*$/;
const REVEAL_FRAME_DELAY_MS = 16;

let isLoading = false;
let typingBubble = null;
let currentThread = [];
let lastUserPrompt = "";
let lastFailedPrompt = "";
const activeFilters = {
  genre: "",
  mood: "",
  decade: "",
  runtime: "",
  language: ""
};

function scrollToBottom() {
  messages.scrollTop = messages.scrollHeight;
}

function isNearBottom() {
  const distanceFromBottom = messages.scrollHeight - messages.scrollTop - messages.clientHeight;
  return distanceFromBottom < 120;
}

function maybeScrollToBottom(force = false) {
  if (force || isNearBottom()) {
    scrollToBottom();
  }
}

function updateEmptyState() {
  const hasMessages = messages.querySelector(".message") !== null;
  if (emptyState) {
    emptyState.hidden = hasMessages;
  }
}

function saveHistory() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(currentThread));
  } catch (_) {
    // Ignore storage write failures.
  }
}

function clearHistory() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (_) {
    // Ignore storage clear failures.
  }
}

function loadHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter(
      (entry) =>
        entry &&
        (entry.role === "user" || entry.role === "assistant") &&
        typeof entry.content === "string"
    );
  } catch (_) {
    return [];
  }
}

function stripMarkdown(value) {
  // Lightweight markdown stripping for common assistant formatting.
  return value.replace(/\*\*(.*?)\*\*/g, "$1").replace(/`(.*?)`/g, "$1").trim();
}

function parseRecommendationCards(text) {
  const lines = text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  const listItems = lines
    .map((line) => line.match(/^(?:\d+[\).\s-]+|[-*•]\s+)(.+)$/)?.[1]?.trim())
    .filter(Boolean);

  if (listItems.length < 2) {
    return null;
  }

  const cards = listItems
    .map((item) => {
      const normalized = stripMarkdown(item);
      // Match "Title - Description", "Title — Description", or "Title: Description".
      const split = normalized.split(/\s[-–—:]\s(.+)/, 2);
      const title = stripMarkdown(split[0] || "");
      const description = stripMarkdown(split[1] || "");
      if (!title) {
        return null;
      }
      return { title, description };
    })
    .filter(Boolean);

  return cards.length >= 2 ? cards : null;
}

function renderAssistantContent(container, content, renderPlainTextOnly = false) {
  container.innerHTML = "";
  const text = typeof content === "string" ? content : String(content || "");

  if (renderPlainTextOnly) {
    container.textContent = text;
    return;
  }

  const cards = parseRecommendationCards(text);
  if (!cards) {
    container.textContent = text;
    return;
  }

  const cardList = document.createElement("div");
  cardList.className = "card-list";
  cards.forEach((card) => {
    const cardNode = document.createElement("section");
    cardNode.className = "rec-card";
    const title = document.createElement("h3");
    title.textContent = card.title;
    cardNode.appendChild(title);
    if (card.description) {
      const description = document.createElement("p");
      description.textContent = card.description;
      cardNode.appendChild(description);
    }
    cardList.appendChild(cardNode);
  });

  const fallbackText = document.createElement("p");
  fallbackText.className = "message-fallback";
  fallbackText.textContent = text;

  container.appendChild(cardList);
  container.appendChild(fallbackText);
}

function updateStatus(message = "", retryPrompt = "") {
  statusText.innerHTML = "";
  if (!message) {
    return;
  }
  statusText.appendChild(document.createTextNode(message));
  if (!retryPrompt) {
    return;
  }
  const retryBtn = document.createElement("button");
  retryBtn.type = "button";
  retryBtn.className = "retry-action";
  retryBtn.textContent = "Retry";
  retryBtn.addEventListener("click", () => {
    if (isLoading) {
      return;
    }
    sendMessage(retryPrompt, { appendUser: false });
  });
  statusText.append(" ");
  statusText.appendChild(retryBtn);
}

function updateInputWithFilters() {
  const baseText = messageInput.value.replace(FILTER_SUFFIX_PATTERN, "").trimEnd();
  const selectedParts = Object.entries(activeFilters)
    .filter(([, value]) => value)
    .map(([key, value]) => `${key}: ${value}`);
  const suffix = selectedParts.length ? `\n\n[Filters: ${selectedParts.join("; ")}]` : "";
  messageInput.value = baseText ? `${baseText}${suffix}` : suffix.replace(/^\n\n/, "");
}

async function copyToClipboard(text) {
  const copyText = typeof text === "string" ? text : "";
  if (!copyText.trim()) {
    return;
  }
  try {
    await navigator.clipboard.writeText(copyText);
    updateStatus("Copied to clipboard.");
    window.setTimeout(() => {
      if (statusText.textContent === "Copied to clipboard.") {
        updateStatus("");
      }
    }, 1200);
  } catch (_) {
    updateStatus("Copy failed. Please copy manually.");
  }
}

function buildAssistantActions(content) {
  const actions = document.createElement("div");
  actions.className = "message-actions";

  const copyBtn = document.createElement("button");
  copyBtn.type = "button";
  copyBtn.className = "assistant-action";
  copyBtn.textContent = "Copy";
  copyBtn.addEventListener("click", () => {
    copyToClipboard(content);
  });

  const regenerateBtn = document.createElement("button");
  regenerateBtn.type = "button";
  regenerateBtn.className = "assistant-action";
  regenerateBtn.textContent = "Regenerate";
  regenerateBtn.addEventListener("click", () => {
    if (!isLoading && lastUserPrompt) {
      sendMessage(lastUserPrompt, { appendUser: false });
    }
  });

  actions.appendChild(copyBtn);
  actions.appendChild(regenerateBtn);
  return actions;
}

function addMessage(role, content, isTyping = false, persist = true) {
  const bubble = document.createElement("article");
  bubble.className = `message ${role} message-enter`;
  bubble.dataset.role = role;

  if (isTyping) {
    bubble.innerHTML = "<span class='typing' aria-label='Assistant is typing'><span></span><span></span><span></span></span>";
  } else {
    const body = document.createElement("div");
    body.className = "message-content";
    if (role === "assistant") {
      renderAssistantContent(body, content);
      bubble.appendChild(body);
      bubble.appendChild(buildAssistantActions(content));
    } else {
      body.textContent = content;
      bubble.appendChild(body);
    }
  }

  messages.appendChild(bubble);
  if (persist && !isTyping) {
    currentThread.push({ role, content });
    saveHistory();
  }
  updateEmptyState();
  maybeScrollToBottom(true);
  return bubble;
}

function resetChat() {
  messages.querySelectorAll(".message").forEach((node) => node.remove());
  if (typingBubble) {
    typingBubble.remove();
    typingBubble = null;
  }
  updateStatus("");
  currentThread = [];
  lastUserPrompt = "";
  lastFailedPrompt = "";
  clearHistory();
  updateEmptyState();
}

function setLoading(loading) {
  isLoading = loading;
  sendBtn.disabled = loading;
  clearChatBtn.disabled = loading;
  chips.forEach((chip) => {
    chip.disabled = loading;
  });
  document.querySelectorAll("button.assistant-action, button.retry-action").forEach((action) => {
    action.disabled = loading;
  });
  if (loading) {
    updateStatus("Assistant is thinking…");
  } else if (statusText.textContent === "Assistant is thinking…") {
    updateStatus("");
  }
}

async function revealAssistantMessage(targetBubble, fullText) {
  const safeText = fullText.trim() || "I received an empty response. Please try asking again.";
  const content = targetBubble.querySelector(".message-content") || document.createElement("div");
  content.className = "message-content";
  targetBubble.innerHTML = "";
  targetBubble.appendChild(content);

  const chunks = safeText.match(/\S+\s*/g) || [safeText];
  let revealed = "";

  for (const chunk of chunks) {
    revealed += chunk;
    renderAssistantContent(content, revealed, true);
    maybeScrollToBottom();
    await new Promise((resolve) => window.setTimeout(resolve, REVEAL_FRAME_DELAY_MS));
  }

  renderAssistantContent(content, safeText);
  targetBubble.appendChild(buildAssistantActions(safeText));
  currentThread.push({ role: "assistant", content: safeText });
  saveHistory();
  maybeScrollToBottom();
}

async function sendMessage(rawMessage, options = {}) {
  const message = (rawMessage || "").trim();
  if (!message || isLoading) {
    return;
  }

  updateStatus("");
  lastUserPrompt = message;
  if (options.appendUser !== false) {
    addMessage("user", message);
  }
  setLoading(true);
  typingBubble = addMessage("assistant", "", true, false);

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

    if (!response.ok) {
      throw new Error(data.detail || "Unable to get a response right now.");
    }

    const replyText = typeof data.reply === "string" ? data.reply : String(data.reply || "");
    if (typingBubble) {
      await revealAssistantMessage(typingBubble, replyText);
      typingBubble = null;
    }
    lastFailedPrompt = "";
  } catch (error) {
    if (typingBubble) {
      typingBubble.remove();
      typingBubble = null;
    }
    const errorMessage = error instanceof Error && error.message ? error.message : "Sorry, we couldn't reach the chat service. Please try again.";
    lastFailedPrompt = message;
    updateStatus(errorMessage, lastFailedPrompt);
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

quickPromptChips.forEach((chip) => {
  chip.addEventListener("click", () => {
    if (isLoading) {
      return;
    }
    const prompt = (chip.dataset.prompt || "").trim();
    if (!prompt) {
      return;
    }
    messageInput.value = prompt;
    updateInputWithFilters();
    messageInput.focus();
    messageInput.setSelectionRange(messageInput.value.length, messageInput.value.length);
  });
});

filterChips.forEach((chip) => {
  chip.addEventListener("click", () => {
    if (isLoading) {
      return;
    }
    const group = chip.dataset.filterGroup;
    const value = chip.dataset.filterValue;
    if (!group || !value) {
      return;
    }

    const isAlreadySelected = activeFilters[group] === value;
    activeFilters[group] = isAlreadySelected ? "" : value;
    filterChips.forEach((filterChip) => {
      const sameGroup = filterChip.dataset.filterGroup === group;
      if (sameGroup) {
        const shouldSelect = activeFilters[group] && filterChip.dataset.filterValue === activeFilters[group];
        filterChip.classList.toggle("active", Boolean(shouldSelect));
        filterChip.setAttribute("aria-pressed", shouldSelect ? "true" : "false");
      }
    });
    updateInputWithFilters();
    messageInput.focus();
    messageInput.setSelectionRange(messageInput.value.length, messageInput.value.length);
  });
});

clearChatBtn.addEventListener("click", () => {
  if (isLoading) {
    return;
  }
  resetChat();
  messageInput.focus();
});

const restoredHistory = loadHistory();
restoredHistory.forEach((entry) => {
  addMessage(entry.role, entry.content, false, false);
  if (entry.role === "user") {
    lastUserPrompt = entry.content;
  }
});
currentThread = restoredHistory;
updateEmptyState();
