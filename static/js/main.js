/**
 * MONOGRAPH — Interactive Engineering Journal
 * Theme, Reading Progress, Interactive Wave Grid, Search, Code Blocks, Toasts
 */

(function () {
  "use strict";

  /* ══════════════════════════════════════════════════════════════
     1. THEME MANAGEMENT
     ══════════════════════════════════════════════════════════════ */
  function initTheme() {
    const saved = localStorage.getItem("monograph-theme") || "dark";
    document.documentElement.setAttribute("data-theme", saved);

    const btn = document.getElementById("theme-toggle");
    if (!btn) return;

    btn.addEventListener("click", () => {
      const cur = document.documentElement.getAttribute("data-theme");
      const next = cur === "light" ? "dark" : "light";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("monograph-theme", next);
    });
  }

  /* ══════════════════════════════════════════════════════════════
     2. READING PROGRESS BAR
     ══════════════════════════════════════════════════════════════ */
  function initReadingProgress() {
    const bar = document.getElementById("reading-progress");
    if (!bar) return;

    let ticking = false;
    window.addEventListener("scroll", () => {
      if (!ticking) {
        requestAnimationFrame(() => {
          const scrollTop = window.scrollY;
          const docH = document.documentElement.scrollHeight - window.innerHeight;
          bar.style.width = docH > 0 ? Math.min(100, (scrollTop / docH) * 100) + "%" : "0%";
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });
  }

  /* ══════════════════════════════════════════════════════════════
     3. INTERACTIVE WAVE GRID (Mouse-reactive canvas)
     A dot grid that ripples / waves wherever the cursor moves,
     using damped spring physics for smooth organic motion.
     ══════════════════════════════════════════════════════════════ */
  function initInteractiveGrid() {
    const canvas = document.getElementById("interactive-grid");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    let W, H;
    const SPACING = 36;
    const INFLUENCE = 120;
    const SPRING = 0.03;
    const DAMP = 0.85;
    let cols, rows, dots;
    let mouseX = -9999, mouseY = -9999;

    function resize() {
      const dpr = window.devicePixelRatio || 1;
      W = window.innerWidth;
      H = window.innerHeight;
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      canvas.style.width = W + "px";
      canvas.style.height = H + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      buildGrid();
    }

    function buildGrid() {
      cols = Math.ceil(W / SPACING) + 2;
      rows = Math.ceil(H / SPACING) + 2;
      dots = [];
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          dots.push({
            ox: c * SPACING,
            oy: r * SPACING,
            x: c * SPACING,
            y: r * SPACING,
            vx: 0,
            vy: 0,
          });
        }
      }
    }

    function tick() {
      const isDark = document.documentElement.getAttribute("data-theme") !== "light";

      ctx.clearRect(0, 0, W, H);

      for (let i = 0; i < dots.length; i++) {
        const d = dots[i];
        const dx = mouseX - d.ox;
        const dy = mouseY - d.oy;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < INFLUENCE && dist > 0) {
          const force = (INFLUENCE - dist) / INFLUENCE;
          const angle = Math.atan2(dy, dx);
          d.vx -= Math.cos(angle) * force * 2.2;
          d.vy -= Math.sin(angle) * force * 2.2;
        }

        // Spring back to origin
        d.vx += (d.ox - d.x) * SPRING;
        d.vy += (d.oy - d.y) * SPRING;
        d.vx *= DAMP;
        d.vy *= DAMP;
        d.x += d.vx;
        d.y += d.vy;

        // Draw the dot
        const displacement = Math.sqrt((d.x - d.ox) ** 2 + (d.y - d.oy) ** 2);
        const alpha = isDark
          ? 0.06 + Math.min(displacement * 0.015, 0.35)
          : 0.04 + Math.min(displacement * 0.012, 0.25);

        ctx.beginPath();
        ctx.arc(d.x, d.y, 1.2, 0, Math.PI * 2);
        ctx.fillStyle = isDark
          ? `rgba(255, 255, 255, ${alpha})`
          : `rgba(0, 0, 0, ${alpha})`;
        ctx.fill();
      }

      // Draw connecting lines between nearby dots
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const idx = r * cols + c;
          const d = dots[idx];

          // Right neighbor
          if (c < cols - 1) {
            const right = dots[idx + 1];
            drawLine(ctx, d, right, isDark);
          }
          // Bottom neighbor
          if (r < rows - 1) {
            const below = dots[idx + cols];
            drawLine(ctx, d, below, isDark);
          }
        }
      }

      requestAnimationFrame(tick);
    }

    function drawLine(ctx, a, b, isDark) {
      const dispA = Math.sqrt((a.x - a.ox) ** 2 + (a.y - a.oy) ** 2);
      const dispB = Math.sqrt((b.x - b.ox) ** 2 + (b.y - b.oy) ** 2);
      const avg = (dispA + dispB) / 2;
      const alpha = isDark
        ? 0.02 + Math.min(avg * 0.008, 0.12)
        : 0.015 + Math.min(avg * 0.006, 0.08);

      if (alpha < 0.015) return;

      ctx.beginPath();
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
      ctx.strokeStyle = isDark
        ? `rgba(255, 255, 255, ${alpha})`
        : `rgba(0, 0, 0, ${alpha})`;
      ctx.lineWidth = 0.5;
      ctx.stroke();
    }

    window.addEventListener("mousemove", (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
    });

    window.addEventListener("mouseleave", () => {
      mouseX = -9999;
      mouseY = -9999;
    });

    let resizeTimer;
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(resize, 150);
    });

    resize();
    requestAnimationFrame(tick);
  }

  /* ══════════════════════════════════════════════════════════════
     4. LIVE SEARCH & FILTER
     ══════════════════════════════════════════════════════════════ */
  function initLiveSearch() {
    const input = document.getElementById("post-search-input");
    const clearBtn = document.getElementById("search-clear-btn");
    const cards = document.querySelectorAll(".post-card");
    const emptyMsg = document.getElementById("search-empty-msg");
    if (!input || cards.length === 0) return;

    // Keyboard shortcut: Ctrl+K or /
    window.addEventListener("keydown", (e) => {
      const tag = document.activeElement.tagName;
      if ((e.ctrlKey && e.key.toLowerCase() === "k") ||
          (e.key === "/" && tag !== "TEXTAREA" && tag !== "INPUT")) {
        e.preventDefault();
        input.focus();
      }
    });

    input.addEventListener("input", () => {
      const q = input.value.toLowerCase().trim();
      let count = 0;

      if (clearBtn) clearBtn.style.display = q ? "block" : "none";

      cards.forEach((card) => {
        const title = (card.querySelector(".card-title")?.textContent || "").toLowerCase();
        const excerpt = (card.querySelector(".card-excerpt")?.textContent || "").toLowerCase();
        const tags = Array.from(card.querySelectorAll(".badge-tag")).map(t => t.textContent.toLowerCase()).join(" ");
        const cat = (card.querySelector(".badge-category")?.textContent || "").toLowerCase();

        const match = !q || title.includes(q) || excerpt.includes(q) || tags.includes(q) || cat.includes(q);
        card.style.display = match ? "flex" : "none";
        if (match) count++;
      });

      if (emptyMsg) emptyMsg.style.display = count === 0 ? "block" : "none";
    });

    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        input.value = "";
        input.dispatchEvent(new Event("input"));
        input.focus();
      });
    }
  }

  /* ══════════════════════════════════════════════════════════════
     5. CODE BLOCKS — macOS Terminal Window + SVG Copy
     ══════════════════════════════════════════════════════════════ */
  const SVG_CLIPBOARD = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`;
  const SVG_CHECK = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`;

  function initCodeBlocks() {
    const preBlocks = document.querySelectorAll(".markdown-content pre");

    preBlocks.forEach((pre) => {
      if (pre.parentElement.classList.contains("code-container")) return;

      const code = pre.querySelector("code");
      const langClass = code ? Array.from(code.classList).find(c => c.startsWith("language-")) : null;
      const lang = langClass ? langClass.replace("language-", "") : "code";

      const container = document.createElement("div");
      container.className = "code-container";

      const header = document.createElement("div");
      header.className = "code-header";
      header.innerHTML =
        `<div class="code-dots">` +
          `<span class="code-dot"></span>` +
          `<span class="code-dot"></span>` +
          `<span class="code-dot"></span>` +
        `</div>` +
        `<span class="code-lang-label">${lang}</span>` +
        `<button class="copy-code-btn" type="button" title="Copy code">` +
          `${SVG_CLIPBOARD} <span>Copy</span>` +
        `</button>`;

      pre.parentNode.insertBefore(container, pre);
      container.appendChild(header);
      container.appendChild(pre);

      const copyBtn = header.querySelector(".copy-code-btn");
      copyBtn.addEventListener("click", () => {
        const text = code ? code.innerText : pre.innerText;
        navigator.clipboard.writeText(text).then(() => {
          copyBtn.innerHTML = `${SVG_CHECK} <span style="color:var(--accent-emerald)">Copied</span>`;
          setTimeout(() => {
            copyBtn.innerHTML = `${SVG_CLIPBOARD} <span>Copy</span>`;
          }, 2000);
        });
      });
    });
  }

  /* ══════════════════════════════════════════════════════════════
     6. TOAST NOTIFICATIONS
     ══════════════════════════════════════════════════════════════ */
  function initToasts() {
    document.querySelectorAll(".toast").forEach((toast) => {
      setTimeout(() => {
        toast.style.transition = "all 0.35s cubic-bezier(0.16, 1, 0.3, 1)";
        toast.style.opacity = "0";
        toast.style.transform = "translateX(40px) scale(0.95)";
        setTimeout(() => toast.remove(), 350);
      }, 4500);
    });
  }

  /* ══════════════════════════════════════════════════════════════
     7. BACK TO TOP
     ══════════════════════════════════════════════════════════════ */
  function initBackToTop() {
    const btn = document.getElementById("back-to-top");
    if (!btn) return;

    window.addEventListener("scroll", () => {
      btn.classList.toggle("visible", window.scrollY > 400);
    }, { passive: true });

    btn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  /* ══════════════════════════════════════════════════════════════
     8. MARKDOWN EDITOR (Admin) — Tabs + Toolbar
     ══════════════════════════════════════════════════════════════ */
  function initMarkdownEditor() {
    const textarea = document.getElementById("body");
    const preview = document.getElementById("markdown-preview-pane");
    const tabWrite = document.getElementById("tab-write");
    const tabPreview = document.getElementById("tab-preview");
    if (!textarea || !preview || !tabWrite || !tabPreview) return;

    tabWrite.addEventListener("click", () => {
      tabWrite.classList.add("active");
      tabPreview.classList.remove("active");
      textarea.style.display = "block";
      preview.style.display = "none";
    });

    tabPreview.addEventListener("click", () => {
      tabPreview.classList.add("active");
      tabWrite.classList.remove("active");
      textarea.style.display = "none";
      preview.style.display = "block";
      preview.innerHTML = `<p style="color:var(--text-faint)">Rendering...</p>`;

      const csrf = document.querySelector('input[name="csrf_token"]')?.value || "";
      fetch("/api/preview-markdown", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
        body: JSON.stringify({ content: textarea.value }),
      })
        .then(r => r.json())
        .then(data => {
          preview.innerHTML = data.html || `<p style="color:var(--text-faint)">Nothing to preview.</p>`;
          preview.className = "markdown-content";
          preview.id = "markdown-preview-pane";
          initCodeBlocks();
        })
        .catch(() => {
          preview.innerHTML = `<p style="color:var(--accent-rose)">Preview failed.</p>`;
        });
    });

    // Toolbar formatting
    document.querySelectorAll(".tool-btn[data-format]").forEach(btn => {
      btn.addEventListener("click", () => {
        insertFormat(textarea, btn.getAttribute("data-format"));
      });
    });
  }

  function insertFormat(ta, fmt) {
    const s = ta.selectionStart, e = ta.selectionEnd;
    const sel = ta.value.substring(s, e);
    let rep = "";

    switch (fmt) {
      case "bold":    rep = `**${sel || "bold text"}**`; break;
      case "italic":  rep = `*${sel || "italic text"}*`; break;
      case "heading": rep = `\n## ${sel || "Heading"}\n`; break;
      case "quote":   rep = `\n> ${sel || "Quote"}\n`; break;
      case "code":
        rep = sel.includes("\n")
          ? `\n\`\`\`\n${sel || "code"}\n\`\`\`\n`
          : `\`${sel || "code"}\``;
        break;
      case "link": rep = `[${sel || "link text"}](https://)`; break;
      case "list": rep = `\n- ${sel || "Item"}\n`; break;
      default: return;
    }

    ta.focus();
    ta.setRangeText(rep, s, e, "end");
  }

  /* ══════════════════════════════════════════════════════════════
     9. ADMIN TABLE FILTER
     ══════════════════════════════════════════════════════════════ */
  function initAdminTableFilter() {
    const input = document.getElementById("admin-table-search");
    const rows = document.querySelectorAll(".admin-table tbody tr");
    if (!input || rows.length === 0) return;

    input.addEventListener("input", () => {
      const q = input.value.toLowerCase().trim();
      rows.forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(q) ? "" : "none";
      });
    });
  }

  /* ══════════════════════════════════════════════════════════════
     BOOT
     ══════════════════════════════════════════════════════════════ */
  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initReadingProgress();
    initInteractiveGrid();
    initLiveSearch();
    initCodeBlocks();
    initToasts();
    initBackToTop();
    initMarkdownEditor();
    initAdminTableFilter();
  });
})();
