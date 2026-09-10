/**
 * VeriDoc AI - Frontend Application Logic
 * Monochrome Edition with Advanced Document Scoping, Summarization & Analytics
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

  // Theme elements
  const themeToggleBtn = document.getElementById("theme-toggle-btn");
  const themeToggleText = document.getElementById("theme-toggle-text");

  // Toolbar & Scoping elements
  const docSelectorDropdown = document.getElementById("doc-selector-dropdown");
  const activeScopePill = document.getElementById("active-scope-pill");
  const activeScopeText = document.getElementById("active-scope-text");
  const btnClearFilter = document.getElementById("btn-clear-filter");
  const btnClearChat = document.getElementById("btn-clear-chat");
  const btnExportChat = document.getElementById("btn-export-chat");
  const activeFiltersBottom = document.getElementById("active-filters");

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
  const modalStatsRow = document.getElementById("modal-stats-row");
  const modalChunkBody = document.getElementById("modal-chunk-body");
  const btnCloseModal = document.getElementById("btn-close-modal");

  // Proof Modal elements
  const proofModal = document.getElementById("proof-modal");
  const proofDocTitle = document.getElementById("proof-doc-title");
  const proofPageTag = document.getElementById("proof-page-tag");
  const proofChunkTag = document.getElementById("proof-chunk-tag");
  const proofScoreTag = document.getElementById("proof-score-tag");
  const proofExcerptText = document.getElementById("proof-excerpt-text");
  const proofIframe = document.getElementById("proof-iframe");
  const btnProofNewTab = document.getElementById("btn-proof-new-tab");
  const btnCloseProof = document.getElementById("btn-close-proof");

  // Deletion Confirmation Modal elements
  const confirmModal = document.getElementById("confirm-modal");
  const confirmDocName = document.getElementById("confirm-doc-name");
  const btnConfirmDelete = document.getElementById("btn-confirm-delete");
  const btnCancelDelete = document.getElementById("btn-cancel-delete");
  const btnCloseConfirm = document.getElementById("btn-close-confirm");
  let pendingDeleteFilename = null;

  // Application State
  let activeDocumentFilter = null;
  let conversationHistory = [];

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

  // Attach chip listeners
  function initSuggestionChips() {
    document.querySelectorAll(".chip-item").forEach(chip => {
      chip.addEventListener("click", () => {
        queryInput.value = chip.getAttribute("data-query");
        queryInput.focus();
        ragQueryForm.dispatchEvent(new Event("submit"));
      });
    });
  }
  initSuggestionChips();

  // Theme Switching Logic
  const savedTheme = localStorage.getItem("veridoc-theme") || "light";
  applyTheme(savedTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      const currentTheme = document.documentElement.getAttribute("data-theme") || "light";
      const nextTheme = currentTheme === "light" ? "dark" : "light";
      applyTheme(nextTheme);
    });
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("veridoc-theme", theme);
    if (themeToggleText) {
      themeToggleText.textContent = theme === "light" ? "White & Black" : "Black & White";
    }
  }

  // --- Document-Specific Suggested Questions ---

  const promptChipsBar = document.getElementById("prompt-chips-bar");

  const DOCUMENT_SUGGESTIONS = {
    "apartment_lease_agreement.txt": [
      { label: "📄 What is this document about?", query: "What is this document all about and who are the parties?" },
      { label: "💰 Rent & Deposit", query: "What is the monthly rent and security deposit amount?" },
      { label: "🐾 Pet & Smoking Rules", query: "What are the rules regarding pets, smoking, and quiet hours?" },
      { label: "🛠️ Maintenance & Repairs", query: "What are the tenant's maintenance obligations vs landlord duties?" },
      { label: "📅 Lease Term & Notice", query: "What is the duration of the lease and termination notice period?" }
    ],
    "Star_Health_Insurance_Manual_10_Pages.pdf": [
      { label: "🏥 Policy Overview", query: "What is this health insurance policy all about and what does it cover?" },
      { label: "⏳ Pre-Existing Diseases", query: "What is the waiting period for pre-existing diseases?" },
      { label: "🛏️ Room Rent & ICU Caps", query: "What are the room rent limits and ICU charges covered under this policy?" },
      { label: "🎁 No-Claim Bonus", query: "How does the cumulative bonus / no-claim bonus work?" },
      { label: "💊 Day Care Procedures", query: "What day care treatments and modern medical procedures are covered?" }
    ],
    "sample_knowledge.pdf": [
      { label: "☁️ Architecture Overview", query: "What is this document all about regarding Acme Global AI architecture?" },
      { label: "🔒 Security & Access", query: "What encryption standards and access control policies are required?" },
      { label: "⚡ API Rate Limits", query: "What are the API rate limits and vector indexing specifications?" }
    ]
  };

  const DEFAULT_SUGGESTIONS = [
    { label: "📄 What is this document about?", query: "What is this document all about and what are its core points?" },
    { label: "📋 Key Policies & Terms", query: "What are the main policies, terms, and obligations specified?" },
    { label: "📅 Dates & Deadlines", query: "What important dates, deadlines, or timelines are mentioned?" },
    { label: "💰 Financial Terms & Costs", query: "What costs, fees, payments, or financial amounts are specified?" }
  ];

  function renderPromptSuggestions(filename) {
    if (!promptChipsBar) return;
    const suggestions = (filename && DOCUMENT_SUGGESTIONS[filename]) || DEFAULT_SUGGESTIONS;
    promptChipsBar.innerHTML = suggestions.map(s => `
      <button type="button" class="prompt-chip" data-query="${escapeHtml(s.query)}">
        ${escapeHtml(s.label)}
      </button>
    `).join("");

    promptChipsBar.querySelectorAll(".prompt-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        queryInput.value = chip.getAttribute("data-query");
        queryInput.focus();
        ragQueryForm.dispatchEvent(new Event("submit"));
      });
    });
  }

  // --- Document Scoping / Filtering ---

  function setActiveDocumentFilter(filename) {
    activeDocumentFilter = filename;
    renderPromptSuggestions(filename);

    if (filename) {
      activeScopeText.textContent = filename;
      activeScopePill.classList.add("is-active");
      activeScopePill.style.display = "inline-flex";
      if (btnClearFilter) btnClearFilter.style.display = "inline";
      if (activeFiltersBottom) {
        activeFiltersBottom.querySelector(".filter-label").textContent = `Target: ${filename} (Isolated Mode)`;
      }
    } else {
      activeScopeText.textContent = "All Documents";
      activeScopePill.classList.remove("is-active");
      activeScopePill.style.display = "none";
      if (btnClearFilter) btnClearFilter.style.display = "none";
      if (activeFiltersBottom) {
        activeFiltersBottom.querySelector(".filter-label").textContent = "Target: All Documents (Global Search)";
      }
    }

    // Sync dropdown
    if (docSelectorDropdown && docSelectorDropdown.value !== (filename || "")) {
      docSelectorDropdown.value = filename || "";
    }

    // Update document card selection styling & active badges
    document.querySelectorAll(".doc-card").forEach(card => {
      const cardFn = card.getAttribute("data-filename");
      const details = card.querySelector(".doc-details");
      const existingBadge = details ? details.querySelector(".badge-active-doc") : null;

      if (filename && cardFn === filename) {
        card.classList.add("is-selected");
        if (!existingBadge && details) {
          const badge = document.createElement("span");
          badge.className = "badge-active-doc";
          badge.textContent = "● Active for Q&A";
          details.appendChild(badge);
        }
      } else {
        card.classList.remove("is-selected");
        if (existingBadge) existingBadge.remove();
      }
    });
  }

  if (docSelectorDropdown) {
    docSelectorDropdown.addEventListener("change", (e) => {
      const val = e.target.value;
      setActiveDocumentFilter(val ? val : null);
    });
  }

  if (btnClearFilter) {
    btnClearFilter.addEventListener("click", (e) => {
      e.stopPropagation();
      setActiveDocumentFilter(null);
    });
  }

  if (activeScopePill) {
    activeScopePill.addEventListener("click", () => {
      if (activeDocumentFilter) {
        setActiveDocumentFilter(null);
      }
    });
  }

  // --- Deletion Confirmation Modal Handlers ---

  function promptDeleteDocument(filename) {
    pendingDeleteFilename = filename;
    if (confirmDocName) confirmDocName.textContent = filename;
    if (confirmModal) confirmModal.style.display = "flex";
  }

  function closeConfirmModal() {
    pendingDeleteFilename = null;
    if (confirmModal) confirmModal.style.display = "none";
  }

  if (btnCancelDelete) btnCancelDelete.addEventListener("click", closeConfirmModal);
  if (btnCloseConfirm) btnCloseConfirm.addEventListener("click", closeConfirmModal);
  if (confirmModal) {
    confirmModal.addEventListener("click", (e) => {
      if (e.target === confirmModal) closeConfirmModal();
    });
  }

  if (btnConfirmDelete) {
    btnConfirmDelete.addEventListener("click", async () => {
      if (!pendingDeleteFilename) return;
      const targetFilename = pendingDeleteFilename;
      closeConfirmModal();
      if (activeDocumentFilter === targetFilename) {
        setActiveDocumentFilter(null);
      }
      await deleteDocument(targetFilename);
    });
  }

  // --- Chat Toolbar Actions: Clear Chat & Export ---

  if (btnClearChat) {
    btnClearChat.addEventListener("click", () => {
      if (conversationHistory.length === 0) return;
      if (confirm("Clear current conversation history?")) {
        conversationHistory = [];
        chatMessages.innerHTML = `
          <div class="welcome-hero" id="welcome-hero">
            <div class="hero-badge">Verified Document Intelligence • RAG Engine</div>
            <h2>Ask Anything About Your Documents</h2>
            <p>Upload your research papers, company policies, manuals, or contracts. VeriDoc AI extracts the relevant snippets and generates factually grounded answers with verified citations.</p>
            <div class="suggestion-chips">
              <button class="chip-item" data-query="Summarize the core points of the uploaded document.">
                📄 Summarize the core points
              </button>
              <button class="chip-item" data-query="What are the key policies and procedures mentioned?">
                📋 Key policies and procedures
              </button>
              <button class="chip-item" data-query="What dates, deadlines, or timelines are specified?">
                📅 Important dates & deadlines
              </button>
            </div>
          </div>
        `;
        initSuggestionChips();
      }
    });
  }

  if (btnExportChat) {
    btnExportChat.addEventListener("click", () => {
      if (conversationHistory.length === 0) {
        alert("No conversation history to export yet. Ask some questions first!");
        return;
      }

      let markdown = `# VeriDoc AI - Verified Q&A Session Report\n`;
      markdown += `*Generated: ${new Date().toLocaleString()}*\n`;
      markdown += `*Active Scope: ${activeDocumentFilter || "All Documents"}*\n\n`;
      markdown += `---\n\n`;

      conversationHistory.forEach((msg, idx) => {
        if (msg.type === "user") {
          markdown += `### ❓ Question: ${msg.text}\n`;
          markdown += `*Target Scope: ${msg.scope} • Time: ${msg.time}*\n\n`;
        } else if (msg.type === "bot") {
          markdown += `### 💡 Answer:\n${msg.text}\n\n`;
          markdown += `*Status: ${msg.is_grounded ? "Verified & Grounded" : "Unverified / General"} | Model: ${msg.model}*\n\n`;

          if (msg.sources && msg.sources.length > 0) {
            markdown += `#### 📚 Source Provenance (${msg.sources.length} citations):\n`;
            msg.sources.forEach((s, sIdx) => {
              markdown += `${sIdx + 1}. **${s.document_name}** (Page ${s.page_number}, Chunk #${s.chunk_index}) - *Similarity Match: ${(s.similarity_score * 100).toFixed(1)}%*\n`;
              markdown += `   > "${s.excerpt.trim()}"\n\n`;
            });
          }
          markdown += `---\n\n`;
        }
      });

      const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `veridoc_report_${Date.now()}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  }

  // Initialize App
  renderPromptSuggestions(null);
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
      statusBadge.className = "stat-badge online";
      statusBadge.style.background = "";
      statusBadge.style.color = "";
      const dot = statusBadge.querySelector(".status-dot");
      if (dot) dot.style.background = "";

      navChunkCount.textContent = data.vector_store.total_chunks;
      navLlmModel.textContent = data.providers.llm.active_model || data.providers.llm.configured;
      navEmbedModel.textContent = data.providers.embeddings.model || data.providers.embeddings.configured;
    } catch (err) {
      statusText.textContent = "Offline";
      statusBadge.className = "stat-badge offline";
      statusBadge.style.background = "";
      statusBadge.style.color = "";
      const dot = statusBadge.querySelector(".status-dot");
      if (dot) dot.style.background = "";
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

    // Sync Document Selector Dropdown options
    if (docSelectorDropdown) {
      const currentVal = activeDocumentFilter;
      docSelectorDropdown.innerHTML = `<option value="">🌐 All Documents (Global Search)</option>`;
      if (docs && docs.length > 0) {
        docs.forEach(d => {
          const opt = document.createElement("option");
          opt.value = d.filename;
          opt.textContent = `📄 ${d.filename}`;
          if (currentVal === d.filename) opt.selected = true;
          docSelectorDropdown.appendChild(opt);
        });
      }
      docSelectorDropdown.value = currentVal || "";
    }

    if (!docs || docs.length === 0) {
      documentList.innerHTML = `
        <div class="empty-docs-state">
          <p>No documents uploaded yet.</p>
          <span>Upload a PDF, Word document, or text file to index knowledge.</span>
        </div>
      `;
      if (activeDocumentFilter) setActiveDocumentFilter(null);
      return;
    }

    docs.forEach(doc => {
      const isSelected = activeDocumentFilter === doc.filename;
      const card = document.createElement("div");
      card.className = "doc-card" + (isSelected ? " is-selected" : "");
      card.setAttribute("data-filename", doc.filename);

      const ext = doc.file_type.toUpperCase();
      const kbSize = (doc.file_size_bytes / 1024).toFixed(1);

      card.innerHTML = `
        <div class="doc-card-info" title="Click to isolate questions strictly to this document">
          <div class="doc-type-icon">${ext}</div>
          <div class="doc-details">
            <div class="doc-name">${escapeHtml(doc.filename)}</div>
            <div class="doc-meta-sub">
              <span>${doc.total_chunks} chunks</span>
              <span>${kbSize} KB</span>
            </div>
            ${isSelected ? '<span class="badge-active-doc">● Active for Q&A</span>' : ''}
          </div>
        </div>
        <div class="doc-actions">
          <button class="btn-action-sm summarize btn-summarize-doc" title="Quick Summarize this document" data-filename="${escapeHtml(doc.filename)}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
            </svg>
          </button>
          <button class="btn-action-sm btn-inspect-chunks" title="Inspect chunks & analytics" data-filename="${escapeHtml(doc.filename)}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path><circle cx="12" cy="12" r="3"></circle></svg>
          </button>
          <button class="btn-action-sm btn-delete-doc" title="Delete document" data-filename="${escapeHtml(doc.filename)}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          </button>
        </div>
      `;

      // Click card info to toggle document scoping
      card.querySelector(".doc-card-info").addEventListener("click", () => {
        if (activeDocumentFilter === doc.filename) {
          setActiveDocumentFilter(null);
        } else {
          setActiveDocumentFilter(doc.filename);
        }
      });

      // Quick summarize button
      card.querySelector(".btn-summarize-doc").addEventListener("click", (e) => {
        e.stopPropagation();
        setActiveDocumentFilter(doc.filename);
        queryInput.value = `Provide a comprehensive summary of "${doc.filename}", highlighting its main themes, key policies, and essential findings.`;
        ragQueryForm.dispatchEvent(new Event("submit"));
      });

      card.querySelector(".btn-inspect-chunks").addEventListener("click", (e) => {
        e.stopPropagation();
        inspectDocumentChunks(doc.filename);
      });

      // Delete document button triggering in-app confirmation modal
      card.querySelector(".btn-delete-doc").addEventListener("click", (e) => {
        e.stopPropagation();
        promptDeleteDocument(doc.filename);
      });

      documentList.appendChild(card);
    });
  }

  async function deleteDocument(filename) {
    try {
      const res = await fetch(`/api/documents/${encodeURIComponent(filename)}`, {
        method: "DELETE"
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${res.status}`);
      }
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
        setActiveDocumentFilter(null);
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
      uploadProgressBar.style.background = "var(--text-muted)";
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

  // --- Chunks Inspection Modal & Document Analytics ---

  async function inspectDocumentChunks(filename) {
    modalDocTitle.textContent = `Chunks for: ${filename}`;
    if (modalStatsRow) modalStatsRow.style.display = "none";
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

      // Calculate Document Analytics
      const totalChars = chunks.reduce((acc, c) => acc + (c.char_count || c.content.length), 0);
      const totalWords = chunks.reduce((acc, c) => acc + c.content.split(/\s+/).filter(Boolean).length, 0);
      const readingTimeMin = Math.max(1, Math.round(totalWords / 200));
      const avgChunkSize = Math.round(totalChars / (chunks.length || 1));

      if (modalStatsRow) {
        modalStatsRow.innerHTML = `
          <div class="modal-stat-box">
            <div class="stat-box-label">Chunks</div>
            <div class="stat-box-value">${chunks.length}</div>
          </div>
          <div class="modal-stat-box">
            <div class="stat-box-label">Words</div>
            <div class="stat-box-value">${totalWords.toLocaleString()}</div>
          </div>
          <div class="modal-stat-box">
            <div class="stat-box-label">Avg Size</div>
            <div class="stat-box-value">${avgChunkSize} ch</div>
          </div>
          <div class="modal-stat-box">
            <div class="stat-box-label">Est. Read</div>
            <div class="stat-box-value">~${readingTimeMin} min</div>
          </div>
        `;
        modalStatsRow.style.display = "grid";
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
      modalChunkBody.innerHTML = `<p class="text-mono-danger">Failed to load chunks: ${escapeHtml(err.message)}</p>`;
    }
  }

  btnCloseModal.addEventListener("click", () => chunkModal.style.display = "none");
  chunkModal.addEventListener("click", (e) => {
    if (e.target === chunkModal) chunkModal.style.display = "none";
  });

  // --- Document Page Proof Modal Logic ---

  function openDocumentProofModal(citation) {
    const filename = citation.document_name;
    const page = citation.page_number || 1;
    const scorePct = (citation.similarity_score * 100).toFixed(1);

    if (proofDocTitle) proofDocTitle.textContent = filename;
    if (proofPageTag) proofPageTag.textContent = `Page ${page}`;
    if (proofChunkTag) proofChunkTag.textContent = `Chunk #${citation.chunk_index}`;
    if (proofScoreTag) proofScoreTag.textContent = `Match: ${scorePct}%`;
    if (proofExcerptText) proofExcerptText.textContent = citation.content || citation.excerpt;

    const fileUrl = `/api/documents/${encodeURIComponent(filename)}/file#page=${page}`;
    if (proofIframe) proofIframe.src = fileUrl;
    if (btnProofNewTab) btnProofNewTab.href = fileUrl;

    if (proofModal) proofModal.style.display = "flex";
  }

  if (btnCloseProof) {
    btnCloseProof.addEventListener("click", () => {
      if (proofModal) proofModal.style.display = "none";
      if (proofIframe) proofIframe.src = "about:blank";
    });
  }

  if (proofModal) {
    proofModal.addEventListener("click", (e) => {
      if (e.target === proofModal) {
        proofModal.style.display = "none";
        if (proofIframe) proofIframe.src = "about:blank";
      }
    });
  }

  // --- RAG Query Chat Handling ---

  ragQueryForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;

    // Hide welcome hero if first message
    const hero = document.getElementById("welcome-hero");
    if (hero) hero.style.display = "none";

    // Track user message in history
    conversationHistory.push({
      type: "user",
      text: query,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      scope: activeDocumentFilter || "All Documents"
    });

    // Append User Message
    appendUserMessage(query);
    queryInput.value = "";
    queryInput.style.height = "auto";
    btnSubmitQuery.disabled = true;

    // Append Loading Assistant Message
    const botMsgRow = appendBotLoading();

    try {
      const payload = {
        query: query,
        top_k: parseInt(cfgTopK.value),
        score_threshold: parseFloat(cfgThreshold.value),
        document_filter: activeDocumentFilter ? [activeDocumentFilter] : null
      };

      const res = await fetch("/api/rag/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Query failed");

      // Track bot response in history
      conversationHistory.push({
        type: "bot",
        text: data.answer,
        is_grounded: data.is_grounded,
        sources: data.sources || [],
        model: data.model_name,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      });

      updateBotMessage(botMsgRow, data);
    } catch (err) {
      botMsgRow.querySelector(".msg-bubble").innerHTML = `
        <span class="text-mono-danger">⚠️ Error executing RAG query: ${escapeHtml(err.message)}</span>
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

    // Strictly deduplicate sources by (document_name, page_number) to eliminate duplicate page cards
    const uniqueSources = [];
    const seenPageKeys = new Set();
    if (data.sources && Array.isArray(data.sources)) {
      data.sources.forEach(s => {
        const pageKey = `${s.document_name}::p${s.page_number}`;
        if (!seenPageKeys.has(pageKey)) {
          seenPageKeys.add(pageKey);
          uniqueSources.push(s);
        }
      });
    }

    let citationsHtml = "";
    if (uniqueSources.length > 0) {
      citationsHtml = `
        <div class="citations-box">
          <div class="citations-title">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
            Cited Sources (${uniqueSources.length}):
          </div>
          <div class="citations-grid">
            ${uniqueSources.map((s, idx) => `
              <div class="citation-card" data-idx="${idx}" title="Click to view Page ${s.page_number} as proof in document viewer">
                <div class="cite-header">
                  <span class="cite-doc">${escapeHtml(s.document_name)}</span>
                  <span class="cite-page">P.${s.page_number}</span>
                </div>
                <div class="cite-excerpt">${escapeHtml(s.excerpt)}</div>
                <div class="cite-footer">
                  <span class="cite-score">Score: ${(s.similarity_score * 100).toFixed(1)}%</span>
                  <span class="cite-proof-btn">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                    Open Page ${s.page_number} Proof
                  </span>
                </div>
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
        <button type="button" class="btn-copy-msg" title="Copy answer to clipboard">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"></rect><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"></path></svg>
          <span>Copy</span>
        </button>
      </div>
    `;

    // Wire citation cards to open page proof modal
    bubble.querySelectorAll(".citation-card").forEach(card => {
      card.addEventListener("click", () => {
        const idx = parseInt(card.getAttribute("data-idx"));
        if (!isNaN(idx) && uniqueSources && uniqueSources[idx]) {
          openDocumentProofModal(uniqueSources[idx]);
        }
      });
    });

    // Wire copy button
    const copyBtn = bubble.querySelector(".btn-copy-msg");
    if (copyBtn) {
      copyBtn.addEventListener("click", async () => {
        let copyText = data.answer;
        if (uniqueSources && uniqueSources.length > 0) {
          copyText += "\n\nSources:";
          uniqueSources.forEach((s, idx) => {
            copyText += `\n[${idx + 1}] ${s.document_name} (Page ${s.page_number}): "${s.excerpt}"`;
          });
        }
        try {
          await navigator.clipboard.writeText(copyText);
          const originalContent = copyBtn.innerHTML;
          copyBtn.innerHTML = `<span>✓ Copied!</span>`;
          setTimeout(() => {
            copyBtn.innerHTML = originalContent;
          }, 2000);
        } catch (err) {
          alert("Failed to copy to clipboard.");
        }
      });
    }

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
