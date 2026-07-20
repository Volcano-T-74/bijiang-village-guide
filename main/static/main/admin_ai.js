(() => {
  "use strict";

  const root = document.getElementById("ai-workspace");
  if (!root) return;

  const conversationSelect = document.getElementById("ai-conversation-select");
  const newButton = document.getElementById("ai-new-conversation");
  const title = document.getElementById("ai-chat-title");
  const days = document.getElementById("ai-days");
  const messages = document.getElementById("ai-messages");
  const form = document.getElementById("ai-question-form");
  const question = document.getElementById("ai-question");
  const sendButton = document.getElementById("ai-send");
  const requestStatus = document.getElementById("ai-request-status");
  const csrfToken = form.querySelector("input[name=csrfmiddlewaretoken]").value;
  let currentConversationId = null;
  let busy = false;

  const errorMessages = {
    configuration: "DeepSeek 尚未配置，请检查 Render 环境变量。",
    authentication: "DeepSeek 密钥无效或没有访问权限，请在 Render 中更换密钥。",
    balance: "DeepSeek 账户余额不足，请充值后重试。",
    rate_limit: "DeepSeek 请求过于频繁，请稍后重试。",
    timeout: "DeepSeek 响应超时，可以稍后重试。",
    network: "Render 无法连接 DeepSeek，请检查网络后重试。",
    upstream: "DeepSeek 服务端暂时异常，可以稍后重试。",
    response: "DeepSeek 返回内容无法解析，可以重新提问。",
  };

  function createElement(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function setStatus(text, isError = false) {
    requestStatus.textContent = text;
    requestStatus.classList.toggle("is-error", isError);
  }

  function setBusy(value) {
    busy = value;
    sendButton.disabled = value;
    newButton.disabled = value;
    conversationSelect.disabled = value;
    messages.setAttribute("aria-busy", value ? "true" : "false");
  }

  async function request(url, options = {}) {
    const response = await fetch(url, {
      credentials: "same-origin",
      headers: { "X-CSRFToken": csrfToken },
      ...options,
    });
    const payload = await response.json();
    return { ok: response.ok, payload };
  }

  function encoded(data) {
    return new URLSearchParams(data);
  }

  function readableItem(item) {
    if (typeof item === "string") return item;
    if (item === null || item === undefined) return "";
    if (typeof item !== "object") return String(item);
    return Object.entries(item)
      .map(([key, value]) => `${key}：${Array.isArray(value) ? value.join("、") : String(value)}`)
      .join("；");
  }

  function appendAnswerSection(container, heading, items) {
    if (!Array.isArray(items) || items.length === 0) return;
    const section = createElement("section", "ai-answer-section");
    section.appendChild(createElement("h3", "", heading));
    const list = document.createElement("ul");
    items.forEach((item) => list.appendChild(createElement("li", "", readableItem(item))));
    section.appendChild(list);
    container.appendChild(section);
  }

  function renderTurn(turn) {
    const wrapper = createElement("article", "ai-turn");
    wrapper.dataset.turnId = String(turn.id);
    wrapper.appendChild(createElement("div", "ai-question", turn.question));
    const answer = createElement("div", "ai-answer");
    if (turn.status === "completed") {
      answer.appendChild(createElement("p", "ai-answer-summary", turn.answer.summary || ""));
      appendAnswerSection(answer, "热门景点", turn.answer.popular_attractions);
      appendAnswerSection(answer, "经营建议", turn.answer.business_recommendations);
      appendAnswerSection(answer, "数据依据", turn.answer.evidence);
      appendAnswerSection(answer, "分析局限", turn.answer.limitations);
    } else if (turn.status === "failed") {
      answer.classList.add("ai-failure");
      answer.appendChild(createElement("p", "", errorMessages[turn.error_code] || "分析失败，可以稍后重试。"));
      const retry = createElement("button", "ai-retry-button", "重试");
      retry.type = "button";
      retry.dataset.retryTurn = String(turn.id);
      answer.appendChild(retry);
    } else {
      answer.appendChild(createElement("p", "ai-answer-summary", "正在分析匿名运营数据…"));
    }
    wrapper.appendChild(answer);
    wrapper.appendChild(createElement("div", "ai-turn-meta", `统计周期：最近 ${turn.days} 天`));
    return wrapper;
  }

  function renderEmptyState() {
    const empty = createElement("div", "ai-empty-state");
    empty.appendChild(createElement("h3", "", "开始一次运营分析"));
    const examples = createElement("div", "ai-examples");
    examples.setAttribute("aria-label", "示例问题");
    ["最近30天哪个景点最受欢迎？", "哪些景点适合投放文创或小吃摊？", "目前的数据有哪些局限性？"].forEach((text) => {
      const button = createElement("button", "", text);
      button.type = "button";
      button.dataset.exampleQuestion = text;
      examples.appendChild(button);
    });
    empty.appendChild(examples);
    messages.replaceChildren(empty);
  }

  function renderLoading() {
    const loading = createElement("div", "ai-loading-row");
    for (let index = 0; index < 3; index += 1) loading.appendChild(createElement("div", "ai-loading-line"));
    messages.replaceChildren(loading);
  }

  function upsertConversationOption(conversation) {
    let option = conversationSelect.querySelector(`option[value="${conversation.id}"]`);
    if (!option) {
      option = document.createElement("option");
      option.value = String(conversation.id);
      conversationSelect.appendChild(option);
    }
    option.textContent = conversation.title;
    conversationSelect.value = String(conversation.id);
  }

  async function loadConversation(id) {
    if (!id) {
      currentConversationId = null;
      title.textContent = "新对话";
      renderEmptyState();
      return;
    }
    currentConversationId = Number(id);
    renderLoading();
    setStatus("正在载入会话…");
    try {
      const result = await request(`${root.dataset.conversationBase}${id}/`);
      if (!result.ok) throw new Error("load");
      const conversation = result.payload.data;
      title.textContent = conversation.title;
      days.value = String(conversation.default_days);
      upsertConversationOption(conversation);
      messages.replaceChildren(...conversation.turns.map(renderTurn));
      if (conversation.turns.length === 0) renderEmptyState();
      const url = new URL(window.location.href);
      url.searchParams.set("conversation", String(conversation.id));
      window.history.replaceState({}, "", url);
      setStatus("");
      messages.scrollTop = messages.scrollHeight;
    } catch (error) {
      renderEmptyState();
      setStatus("会话载入失败，请刷新页面。", true);
    }
  }

  async function createConversation() {
    const result = await request(root.dataset.createUrl, {
      method: "POST",
      body: encoded({ default_days: days.value }),
    });
    if (!result.ok) throw new Error("create");
    upsertConversationOption(result.payload.data);
    await loadConversation(result.payload.data.id);
  }

  async function submitQuestion(event) {
    event.preventDefault();
    if (busy || !question.value.trim()) return;
    setBusy(true);
    setStatus("正在分析匿名运营数据…");
    const submittedQuestion = question.value.trim();
    try {
      if (!currentConversationId) await createConversation();
      renderLoading();
      const result = await request(`${root.dataset.conversationBase}${currentConversationId}/ask/`, {
        method: "POST",
        body: encoded({ question: submittedQuestion, days: days.value }),
      });
      question.value = "";
      await loadConversation(currentConversationId);
      if (!result.ok) setStatus(errorMessages[result.payload.error] || "分析失败，可以重试。", true);
    } catch (error) {
      setStatus("网络连接中断，请确认 Render 服务正常后重试。", true);
      if (currentConversationId) await loadConversation(currentConversationId);
    } finally {
      setBusy(false);
      question.focus();
    }
  }

  async function retryTurn(turnId) {
    if (busy) return;
    setBusy(true);
    setStatus("正在重新分析…");
    try {
      const result = await request(`${root.dataset.turnBase}${turnId}/retry/`, { method: "POST" });
      await loadConversation(currentConversationId);
      if (!result.ok) setStatus(errorMessages[result.payload.error] || "重试失败。", true);
    } catch (error) {
      setStatus("网络连接中断，请稍后重试。", true);
    } finally {
      setBusy(false);
    }
  }

  conversationSelect.addEventListener("change", () => {
    if (!busy) loadConversation(conversationSelect.value);
  });

  messages.addEventListener("click", (event) => {
    const example = event.target.closest("[data-example-question]");
    if (example) {
      question.value = example.dataset.exampleQuestion;
      question.focus();
    }
    const retry = event.target.closest("[data-retry-turn]");
    if (retry) retryTurn(retry.dataset.retryTurn);
  });

  newButton.addEventListener("click", () => {
    if (busy) return;
    conversationSelect.value = "";
    currentConversationId = null;
    title.textContent = "新对话";
    setStatus("");
    renderEmptyState();
    question.focus();
  });

  form.addEventListener("submit", submitQuestion);

  const requestedId = new URL(window.location.href).searchParams.get("conversation");
  if (requestedId && conversationSelect.querySelector(`option[value="${requestedId}"]`)) {
    loadConversation(requestedId);
  } else if (conversationSelect.options.length > 1) {
    loadConversation(conversationSelect.options[1].value);
  } else {
    renderEmptyState();
  }
})();
