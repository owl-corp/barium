import initSqlJs from "sql.js";
import wasmUrl from "sql.js/dist/sql-wasm.wasm?url";

let db = null;
let totalCount = 0;

const statusIndicator = document.getElementById("db-status");
const statusText = document.getElementById("status-text");
const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("search-input");
const searchBtn = document.getElementById("search-btn");
const clearBtn = document.getElementById("clear-btn");
const statTotalThreads = document.getElementById("stat-total-threads");
const resultsHeader = document.getElementById("results-header");
const resultsCount = document.getElementById("results-count");
const resultsContainer = document.getElementById("results-container");
const sortOrder = document.getElementById("sort-order");

async function initDatabase() {
  try {
    statusText.textContent = "Loading SQLite WASM engine...";

    // Fetch WASM directly as ArrayBuffer to prevent MIME-type rejection on generic HTTP servers
    const wasmResponse = await fetch(wasmUrl);
    if (!wasmResponse.ok) {
      throw new Error(`Failed to load wasm binary (${wasmResponse.status})`);
    }
    const wasmBinary = await wasmResponse.arrayBuffer();

    const SQL = await initSqlJs({
      wasmBinary
    });

    statusText.textContent = "Downloading SQLite index...";
    const response = await fetch("./index.db");
    if (!response.ok) {
      throw new Error(`Failed to fetch index.db (${response.status} ${response.statusText})`);
    }

    const buf = await response.arrayBuffer();
    db = new SQL.Database(new Uint8Array(buf));

    // Get count of total threads
    const countRes = db.exec("SELECT COUNT(*) FROM threads");
    totalCount = countRes[0].values[0][0];
    statTotalThreads.textContent = totalCount.toLocaleString();

    statusIndicator.className = "db-status ready";
    statusText.textContent = "Database ready";
    searchBtn.disabled = false;

    // Check URL query param on initial load (e.g. ?user_id=123)
    const urlParams = new URLSearchParams(window.location.search);
    const initialQuery = urlParams.get("q") || urlParams.get("user_id") || "";
    if (initialQuery) {
      searchInput.value = initialQuery;
      clearBtn.classList.remove("hidden");
      performSearch(initialQuery);
    }
  } catch (err) {
    console.error("Database initialization failed:", err);
    statusIndicator.className = "db-status error";
    statusText.textContent = "Error loading database";
  }
}

function performSearch(query) {
  if (!db) return;
  const q = query.trim();
  if (!q) {
    resultsHeader.classList.add("hidden");
    resultsContainer.innerHTML = `
      <div class="empty-state">
        <p>Enter a User ID or Username above to query threads.</p>
      </div>
    `;
    return;
  }

  // Update query in browser URL without reloading
  const url = new URL(window.location);
  url.searchParams.set("q", q);
  window.history.replaceState({}, "", url);

  const sort = sortOrder.value === "ASC" ? "ASC" : "DESC";

  // Query: exact match on user_id, or thread_id, or partial match on username
  let stmt;
  let isNumeric = /^\d+$/.test(q);

  if (isNumeric) {
    stmt = db.prepare(
      `SELECT thread_id, user_id, username, discriminator, created_at, closed_at, message_count, path
       FROM threads
       WHERE user_id = :query
       ORDER BY created_at ${sort}`
    );
    stmt.bind({ ":query": q });
  } else {
    stmt = db.prepare(
      `SELECT thread_id, user_id, username, discriminator, created_at, closed_at, message_count, path
       FROM threads
       WHERE thread_id = :query OR username LIKE :query_like
       ORDER BY created_at ${sort}`
    );
    stmt.bind({ ":query": q, ":query_like": `%${q}%` });
  }

  const results = [];
  while (stmt.step()) {
    results.push(stmt.getAsObject());
  }
  stmt.free();

  renderResults(results, q);
}

function renderResults(results, query) {
  resultsHeader.classList.remove("hidden");
  resultsCount.textContent = `${results.length} thread${results.length === 1 ? '' : 's'} found for "${query}"`;

  if (results.length === 0) {
    resultsContainer.innerHTML = `
      <div class="empty-state">
        <p>No threads found matching "${escapeHtml(query)}".</p>
      </div>
    `;
    return;
  }

  resultsContainer.innerHTML = results.map(row => {
    const isClosed = Boolean(row.closed_at);
    const userTag = row.discriminator && row.discriminator !== "0"
      ? `${escapeHtml(row.username)}#${escapeHtml(row.discriminator)}`
      : escapeHtml(row.username);
    const dateStr = (row.created_at || "").slice(0, 19);

    return `
      <a href="/logs/${row.thread_id}" class="thread-card">
        <div class="card-main">
          <div class="card-title">
            <span class="card-thread-id">#${escapeHtml(row.thread_id)}</span>
            <span class="card-username">${userTag}</span>
          </div>
          <div class="card-meta">
            <span>User ID: <code>${escapeHtml(row.user_id)}</code></span>
            <span>Created: <time>${escapeHtml(dateStr)}</time></span>
            <span>Messages: ${row.message_count}</span>
          </div>
        </div>
        <div class="card-side">
          <span class="card-badge ${isClosed ? 'closed' : 'open'}">
            ${isClosed ? 'CLOSED' : 'OPEN'}
          </span>
          <svg class="arrow-icon" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6-1.41-1.41z"/>
          </svg>
        </div>
      </a>
    `;
  }).join("");
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

searchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  performSearch(searchInput.value);
});

searchInput.addEventListener("input", () => {
  if (searchInput.value) {
    clearBtn.classList.remove("hidden");
  } else {
    clearBtn.classList.add("hidden");
  }
});

clearBtn.addEventListener("click", () => {
  searchInput.value = "";
  clearBtn.classList.add("hidden");
  performSearch("");
  searchInput.focus();
});

sortOrder.addEventListener("change", () => {
  if (searchInput.value.trim()) {
    performSearch(searchInput.value);
  }
});

initDatabase();
