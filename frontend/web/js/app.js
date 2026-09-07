/**
 * VeriDoc AI - Frontend Application Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const statusBadge = document.getElementById("system-status-badge");
  const statusText = document.getElementById("status-text");
  const navChunkCount = document.getElementById("nav-chunk-count");
  const navLlmModel = document.getElementById("nav-llm-model");
  const navEmbedModel = document.getElementById("nav-embed-model");
  const docCountBadge = document.getElementById("doc-count-badge");
  const documentList = document.getElementById("document-list");
  const btnClearAll = document.getElementById("btn-clear-all");
  const btnRefreshDocs = document.getElementById("btn-refresh-docs");

  // Upload elements
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const btnBrowseFile = document.getElementById("btn-browse-file");
  const uploadProgress = document.getElementById("upload-progress-container");
  const uploadProgressBar = document.getElementById("upload-progress-bar");
  const uploadStatusLabel = document.getElementById("upload-status-label");

  // Settings elements
  const cfgChunkSize = document.getElementById("cfg-chunk-size");
  const cfgChunkOverlap = document.getElementById("cfg-chunk-overlap");
  const cfgTopK = document.getElementById("cfg-top-k");
  const cfgThreshold = document.getElementById("cfg-threshold");
  const valChunkSize = document.getElementById("val-chunk-size");
  const valChunkOverlap = document.getElementById("val-chunk-overlap");
  const valTopK = document.getElementById("val-top-k");
  const valThreshold = document.getElementById("val-threshold");

  // Chat elements
  const chatMessages = document.getElementById("chat-messages");
  const welcomeHero = document.getElementById("welcome-hero");
  const ragQueryForm = document.getElementById("rag-query-form");
  const queryInput = document.getElementById("query-input");
  const btnSubmitQuery = document.getElementById("btn-submit-query");

  // Modal elements
  const chunkModal = document.getElementById("chunk-modal");
  const modalDocTitle = document.getElementById("modal-doc-title");
  const modalChunkBody = document.getElementById("modal-chunk-body");
  const btnCloseModal = document.getElementById("btn-close-modal");

  // Update slider label values
  cfgChunkSize.addEventListener("input", (e) => valChunkSize.textContent = e.target.value);
  cfgChunkOverlap.addEventListener("input", (e) => valChunkOverlap.textContent = e.target.value);
  cfgTopK.addEventListener("input", (e) => valTopK.textContent = e.target.value);
  cfgThreshold.addEventListener("input", (e) => valThreshold.textContent = e.target.value);

  // Auto-resize textarea
  queryInput.addEventListener("input", () => {
    queryInput.style.height = "auto";
    queryInput.style.height = Math.min(queryInput.scrollHeight, 120) + "px";
  });

  queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      ragQueryForm.dispatchEvent(new Event("submit"));
    }
  });

  // Suggestion chips click
  document.querySelectorAll(".chip-item").forEach(chip => {
    chip.addEventListener("click", () => {
      queryInput.value = chip.getAttribute("data-query");
      queryInput.focus();
      ragQueryForm.dispatchEvent(new Event("submit"));
    });
  });

  // Initialize App
  fetchSystemHealth();
  fetchDocumentList();

  // Polling / Periodic health check
  setInterval(fetchSystemHealth, 20000);

  // --- API Functions ---

  async function fetchSystemHealth() {
    try {
      const res = await fetch("/api/system/health");
      if (!res.ok) throw new Error("Health check failed");
      const data = await res.json();

      statusText.textContent = "Online";
      statusBadge.style.background = "rgba(16, 185, 129, 0.12)";
      statusBadge.style.color = "#34d399";
      statusBadge.querySelector(".status-dot").style.background = "#10b981";

      navChunkCount.textContent = data.vector_store.total_chunks;
      navLlmModel.textContent = data.providers.llm.active_model || data.providers.llm.configured;
      navEmbedModel.textContent = data.providers.embeddings.model || data.providers.embeddings.configured;
    } catch (err) {
      statusText.textContent = "Offline";
      statusBadge.style.background = "rgba(244, 63, 94, 0.15)";
      statusBadge.style.color = "#fb7185";
      statusBadge.querySelector(".status-dot").style.background = "#f43f5e";
    }
  }

  async function fetchDocumentList() {
    try {
      const res = await fetch("/api/documents");
      if (!res.ok) throw new Error("Failed to load documents");
      const data = await res.json();

      docCountBadge.textContent = data.total_documents;
      renderDocumentList(data.documents);
    } catch (err) {
      console.error("Error loading documents:", err);
    }
  }

  function renderDocumentList(docs) {
    documentList.innerHTML = "";
    if (!docs || docs.length === 0) {
      documentList.innerHTML = `
        <div class="empty-docs-state">
          <p>No documents uploaded yet.</p>
          <span>Upload a PDF, Word document, or text file to index knowledge.</span>
        </div>
      `;
      return;
    }

    docs.forEach(doc => {
      const card = document.createElement("div");
      card.className = "doc-card";

      const ext = doc.file_type.toUpperCase();
      const kbSize = (doc.file_size_bytes / 1024).toFixed(1);

      card.innerHTML = `
        <div class="doc-card-info" title="${doc.filename}">
          <div class="doc-type-icon">${ext}</div>
          <div class="doc-details">
            <div class="doc-name">${escapeHtml(doc.filename)}</div>
            <div class="doc-meta-sub">
              <span>${doc.total_chunks} chunks</span>
              <span>${kbSize} KB</span>
            </div>
          </div>
        </div>
        <div class="doc-actions">
          <button class="btn-icon btn-inspect-chunks" title="Inspect chunks" data-filename="${escapeHtml(doc.filename)}">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path><circle cx="12" cy="12" r="3"></circle></svg>
          </button>
          <button class="btn-icon btn-delete-doc" title="Delete document" data-filename="${escapeHtml(doc.filename)}" style="color: #f43f5e;">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          </button>
        </div>
      `;

      card.querySelector(".btn-inspect-chunks").addEventListener("click", () => {
        inspectDocumentChunks(doc.filename);
      });

      card.querySelector(".btn-delete-doc").addEventListener("click", async () => {
        if (confirm(`Delete '${doc.filename}' and all its vector chunks?`)) {
          await deleteDocument(doc.filename);
        }
      });

      documentList.appendChild(card);
    });
  }

  async function deleteDocument(filename) {
    try {
      const res = await fetch(`/api/documents/${encodeURIComponent(filename)}`, {
        method: "DELETE"
      });
      if (!res.ok) throw new Error("Delete failed");
      await fetchDocumentList();
      await fetchSystemHealth();
    } catch (err) {
      alert(`Error deleting document: ${err.message}`);
    }
  }

  // Clear All
  btnClearAll.addEventListener("click", async () => {
    if (confirm("Are you sure you want to clear ALL documents and reset the vector store?")) {
      try {
        const res = await fetch("/api/documents/clear", { method: "POST" });
        if (!res.ok) throw new Error("Failed to clear index");
        await fetchDocumentList();
        await fetchSystemHealth();
      } catch (err) {
        alert(err.message);
      }
    }
  });

  btnRefreshDocs.addEventListener("click", () => {
    fetchDocumentList();
    fetchSystemHealth();
  });

  // --- Upload Handling ---

  btnBrowseFile.addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-active");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("drag-active");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-active");
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  });

  async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("chunk_size", cfgChunkSize.value);
    formData.append("chunk_overlap", cfgChunkOverlap.value);

    uploadProgress.style.display = "block";
    uploadProgressBar.style.width = "20%";
    uploadStatusLabel.textContent = `Extracting & indexing '${file.name}'...`;

    try {
      uploadProgressBar.style.width = "60%";
      const res = await fetch("/api/documents/upload", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      uploadProgressBar.style.width = "100%";
      uploadStatusLabel.textContent = `Success! Indexed ${data.total_chunks} chunks.`;

      setTimeout(() => {
        uploadProgress.style.display = "none";
        uploadProgressBar.style.width = "0%";
      }, 2500);

      await fetchDocumentList();
      await fetchSystemHealth();
    } catch (err) {
      uploadProgressBar.style.width = "100%";
      uploadProgressBar.style.background = "#f43f5e";
      uploadStatusLabel.textContent = `Error: ${err.message}`;

      setTimeout(() => {
        uploadProgress.style.display = "none";
        uploadProgressBar.style.width = "0%";
        uploadProgressBar.style.background = "";
      }, 4000);
    } finally {
      fileInput.value = "";
    }
  }

  // --- Chunks Inspection Modal ---

  async function inspectDocumentChunks(filename) {
    modalDocTitle.textContent = `Chunks for: ${filename}`;
    modalChunkBody.innerHTML = `<div class="loader-spinner"></div>`;
    chunkModal.style.display = "flex";

    try {
      const res = await fetch(`/api/documents/${encodeURIComponent(filename)}/chunks`);
      if (!res.ok) throw new Error("Could not fetch chunks");
      const chunks = await res.json();

      if (!chunks || chunks.length === 0) {
        modalChunkBody.innerHTML = `<p style="color: var(--text-muted);">No chunks found.</p>`;
        return;
      }

      modalChunkBody.innerHTML = chunks.map(chunk => `
        <div class="chunk-card-modal">
          <div class="chunk-meta-header">
            <span>Chunk #${chunk.chunk_index} (Page ${chunk.page_number})</span>
            <span>${chunk.char_count} chars</span>
          </div>
          <div class="chunk-content-text">${escapeHtml(chunk.content)}</div>
        </div>
      `).join("");
    } catch (err) {
      modalChunkBody.innerHTML = `<p style="color: #f43f5e;">Failed to load chunks: ${err.message}</p>`;
    }
  }

  btnCloseModal.addEventListener("click", () => chunkModal.style.display = "none");
  chunkModal.addEventListener("click", (e) => {
    if (e.target === chunkModal) chunkModal.style.display = "none";
  });

  // --- RAG Query Chat Handling ---

  ragQueryForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;

    // Hide welcome hero if first message
    if (welcomeHero) welcomeHero.style.display = "none";

    // Append User Message
    appendUserMessage(query);
    queryInput.value = "";
    queryInput.style.height = "auto";
    btnSubmitQuery.disabled = true;

    // Append Loading Assistant Message
    const botMsgRow = appendBotLoading();

    try {
      const res = await fetch("/api/rag/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          top_k: parseInt(cfgTopK.value),
          score_threshold: parseFloat(cfgThreshold.value),
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Query failed");

      updateBotMessage(botMsgRow, data);
    } catch (err) {
      botMsgRow.querySelector(".msg-bubble").innerHTML = `
        <span style="color: #f43f5e;">⚠️ Error executing RAG query: ${escapeHtml(err.message)}</span>
      `;
    } finally {
      btnSubmitQuery.disabled = false;
      queryInput.focus();
    }
  });

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
    requestAnimationFrame(() => {
      chatMessages.scrollTop = chatMessages.scrollHeight;
    });
    setTimeout(() => {
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }, 80);
  }

  function appendUserMessage(text) {
    const row = document.createElement("div");
    row.className = "msg-row user";
    row.innerHTML = `
      <div class="msg-bubble">${escapeHtml(text)}</div>
      <div class="avatar user-avatar">U</div>
    `;
    chatMessages.appendChild(row);
    scrollToBottom();
  }

  function appendBotLoading() {
    const row = document.createElement("div");
    row.className = "msg-row bot";
    row.innerHTML = `
      <div class="avatar bot">AI</div>
      <div class="msg-bubble">
        <div class="loader-spinner" style="margin: 6px 0; width: 18px; height: 18px;"></div>
      </div>
    `;
    chatMessages.appendChild(row);
    scrollToBottom();
    return row;
  }

  function updateBotMessage(row, data) {
    const bubble = row.querySelector(".msg-bubble");
    const isGrounded = data.is_grounded;
    const formattedAnswer = formatMarkdown(data.answer);

    let citationsHtml = "";
    if (data.sources && data.sources.length > 0) {
      citationsHtml = `
        <div class="citations-box">
          <div class="citations-title">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
            Cited Sources (${data.sources.length}):
          </div>
          <div class="citations-grid">
            ${data.sources.map(s => `
              <div class="citation-card" title="Click to view chunk" onclick="alert('${escapeHtml(s.excerpt).replace(/'/g, "\\'")}')">
                <div class="cite-header">
                  <span class="cite-doc">${escapeHtml(s.document_name)}</span>
                  <span class="cite-page">P.${s.page_number}</span>
                </div>
                <div class="cite-excerpt">${escapeHtml(s.excerpt)}</div>
                <div class="cite-score">Score: ${(s.similarity_score * 100).toFixed(1)}%</div>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    }

    bubble.innerHTML = `
      <div class="bot-text">${formattedAnswer}</div>
      ${citationsHtml}
      <div class="msg-meta-row">
        <span class="grounded-badge ${isGrounded ? 'verified' : 'unsupported'}">
          ${isGrounded ? '✓ Grounded in Documents' : 'ℹ Out of Scope / Unverified'}
        </span>
        <span class="latency-tag">${data.processing_time_ms} ms</span>
        <span class="latency-tag">Model: ${data.model_name}</span>
      </div>
    `;

    scrollToBottom();
  }

  function formatMarkdown(text) {
    if (!text) return "";
    let clean = escapeHtml(text);
    // Bold
    clean = clean.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Inline code
    clean = clean.replace(/`([^`]+)`/g, "<code>$1</code>");
    // New lines to paragraphs/breaks
    clean = clean.replace(/\n\n/g, "</p><p>").replace(/\n/g, "<br/>");
    return `<p>${clean}</p>`;
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
