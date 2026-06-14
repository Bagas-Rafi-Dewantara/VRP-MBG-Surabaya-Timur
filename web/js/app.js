document.addEventListener("DOMContentLoaded", async () => {
  // --- Theme toggle ---
  const themeToggleBtn = document.getElementById("theme-toggle");
  const savedTheme = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", savedTheme);
  themeToggleBtn.textContent = savedTheme === "light" ? "☀️" : "🌙";

  themeToggleBtn.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    themeToggleBtn.textContent = next === "light" ? "☀️" : "🌙";
    updateMapTile(next);
  });
  // --- Initialize map & charts (need DOM ready) ---
  initMap();
  initCharts();
  updateMapTile(savedTheme);

  // --- Load all data (algorithm JSONs + history) in parallel ---
  const [data] = await Promise.all([loadAllData(), loadHistoryData()]);
  const loadedAlgs = Object.keys(data);

  if (loadedAlgs.length === 0) {
    document.body.innerHTML = `
            <div style="display:flex;align-items:center;justify-content:center;height:100vh;flex-direction:column;gap:1rem;color:#7b9bc8;font-family:Inter,sans-serif;">
                <div style="font-size:3rem;">⚠️</div>
                <div style="font-size:1.25rem;font-weight:600;">Gagal memuat data</div>
                <div style="font-size:0.875rem;max-width:400px;text-align:center;">
                    Pastikan server lokal sudah berjalan:<br>
                    <code style="background:#162240;padding:4px 8px;border-radius:4px;">python3 -m http.server 8000</code><br><br>
                    Lalu buka: <code>http://localhost:8000/web/index.html</code>
                </div>
            </div>`;
    return;
  }

  let currentAlg = loadedAlgs[0];

  // --- Build algorithm tab buttons in header ---
  const algoTabsEl = document.getElementById("algo-tabs");
  loadedAlgs.forEach((alg) => {
    const meta = algorithmMeta[alg];
    const btn = document.createElement("button");
    btn.className = "algo-tab";
    btn.id = `tab-alg-${alg}`;
    btn.textContent = meta.abbr;
    btn.title = meta.name;
    btn.addEventListener("click", () => selectAlgorithm(alg));
    algoTabsEl.appendChild(btn);
  });

  // --- Tab panel navigation ---
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.tab;
      document
        .querySelectorAll(".tab-btn")
        .forEach((b) => b.classList.remove("active"));
      document
        .querySelectorAll(".tab-panel")
        .forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(targetId)?.classList.add("active");

      // When switching to compare tab, re-render charts
      if (targetId === "compare-tab") {
        renderCompareTab(currentAlg);
      }
      // When switching to history tab, render history
      if (targetId === "history-tab") {
        renderHistoryTab();
      }
    });
  });

  // --- SPPG select filter ---
  const sppgSelect = document.getElementById("sppg-select");
  sppgSelect.addEventListener("change", () => {
    const algData = getAlgorithmData(currentAlg);
    updateMap(algData, sppgSelect.value);
  });

  // --- Table search ---
  const searchInput = document.getElementById("table-search");
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      filterTable(searchInput.value.toLowerCase());
    });
  }

  // --- Initial render ---
  selectAlgorithm(currentAlg);

  // ================================================================
  //  CORE FUNCTIONS
  // ================================================================

  function selectAlgorithm(alg) {
    currentAlg = alg;
    const algData = getAlgorithmData(alg);
    if (!algData) return;

    // Highlight active tab button
    loadedAlgs.forEach((a) => {
      const btn = document.getElementById(`tab-alg-${a}`);
      if (!btn) return;
      btn.className = "algo-tab";
      if (a === alg) {
        btn.classList.add(algorithmMeta[alg].tabClass);
      }
    });

    // Update sidebar summary
    updateSidebar(algData);

    // Populate SPPG dropdown
    sppgSelect.innerHTML = '<option value="all">Semua Cluster SPPG</option>';
    algData.results_per_sppg.forEach((s) => {
      const opt = document.createElement("option");
      opt.value = s.sppg;
      opt.textContent = s.sppg.replace("SPPG Kota Surabaya ", "");
      sppgSelect.appendChild(opt);
    });
    sppgSelect.disabled = false;
    sppgSelect.value = "all";

    // Update map
    updateMap(algData, "all");

    // Update per-sppg chart
    updatePerSppgChart(algData);

    // If compare tab is visible, re-render
    if (document.getElementById("compare-tab")?.classList.contains("active")) {
      renderCompareTab(alg);
    }

    // Update table
    buildTable(algData);
  }

  // ----------------------------------------------------------------

  function updateSidebar(algData) {
    const gs = algData.global_summary;

    document.getElementById("val-distance").textContent =
      `${gs.total_distance_km.toFixed(2)}`;
    document.getElementById("val-time").textContent =
      `${gs.total_time_minutes.toFixed(1)}`;
    document.getElementById("val-vehicles").textContent = `${gs.total_mobil}`;

    const feasEl = document.getElementById("val-feasible");
    if (gs.feasible) {
      feasEl.textContent = "Feasible ✓";
      feasEl.style.color = "var(--accent-green)";
    } else {
      feasEl.textContent = "Tidak Feasible ✗";
      feasEl.style.color = "var(--accent-red)";
    }
  }

  // ----------------------------------------------------------------

  function renderCompareTab(selectedAlg) {
    const compData = getComparisonData();
    updateComparisonCharts(compData, selectedAlg);
    buildCompareCards(compData, selectedAlg);
  }

  // ----------------------------------------------------------------

  function buildCompareCards(compData, selectedAlg) {
    const container = document.getElementById("compare-cards");
    if (!container) return;
    container.innerHTML = "";

    // Find bests
    const algs = Object.keys(compData);
    const bestDist = Math.min(...algs.map((a) => compData[a].distance));
    const bestTime = Math.min(...algs.map((a) => compData[a].time));
    const runtimes = algs
      .map((a) => compData[a].runtime)
      .filter((r) => r !== null);
    const bestRuntime = runtimes.length ? Math.min(...runtimes) : null;

    algs.forEach((alg) => {
      const d = compData[alg];
      const meta = algorithmMeta[alg];
      const isSelected = alg === selectedAlg;
      const isBestDist = d.distance === bestDist;
      const isBestTime = d.time === bestTime;
      const isBestRuntime = bestRuntime !== null && d.runtime === bestRuntime;

      const card = document.createElement("div");
      card.className = `compare-alg-card ${meta.cssClass}${isSelected ? " is-selected" : ""}`;
      card.innerHTML = `
                <div class="compare-alg-name">${meta.name}</div>
                <span class="compare-alg-abbr">${meta.abbr}</span>
                <div class="compare-alg-metrics">
                    <div class="compare-metric-row">
                        <span class="compare-metric-label">Jarak total</span>
                        <span class="compare-metric-value">
                            ${d.distance.toFixed(2)} km
                            ${isBestDist ? '<span class="badge-best">Terbaik</span>' : ""}
                        </span>
                    </div>
                    <div class="compare-metric-row">
                        <span class="compare-metric-label">Waktu maks.</span>
                        <span class="compare-metric-value">
                            ${d.time.toFixed(1)} mnt
                            ${isBestTime ? '<span class="badge-best">Terbaik</span>' : ""}
                        </span>
                    </div>
                    <div class="compare-metric-row">
                        <span class="compare-metric-label">Runtime</span>
                        <span class="compare-metric-value">
                            ${d.runtime !== null ? d.runtime.toFixed(2) + " dtk" : "— "}
                            ${isBestRuntime ? '<span class="badge-best">Terbaik</span>' : ""}
                        </span>
                    </div>
                    <div class="compare-metric-row">
                        <span class="compare-metric-label">Feasible</span>
                        <span class="compare-metric-value" style="color:${d.feasible ? "var(--accent-green)" : "var(--accent-red)"}">
                            ${d.feasible ? "Ya ✓" : "Tidak ✗"}
                        </span>
                    </div>
                </div>`;
      card.addEventListener("click", () => selectAlgorithm(alg));
      container.appendChild(card);
    });
  }

  // ----------------------------------------------------------------

  function buildTable(algData) {
    const tbody = document.getElementById("sppg-table-body");
    if (!tbody) return;
    tbody.innerHTML = "";

    algData.results_per_sppg.forEach((s, i) => {
      const schools = countSchools(s);
      const refill = hasRefill(s);
      const shortName = s.sppg.replace("SPPG Kota Surabaya ", "");

      const tr = document.createElement("tr");
      tr.dataset.sppg = shortName.toLowerCase();
      tr.innerHTML = `
                <td class="row-idx">${i + 1}</td>
                <td>${shortName}</td>
                <td class="td-num">${s.distance_km.toFixed(2)}</td>
                <td class="td-num ${s.time_spent_minutes > 120 ? "warn" : "good"}">${s.time_spent_minutes.toFixed(1)}</td>
                <td>${s.departure_time}</td>
                <td>${s.return_time}</td>
                <td>${schools}</td>
                <td><span class="badge-yes ${refill ? "amber" : "green"}">${refill ? "Ya" : "Tidak"}</span></td>
                <td><span class="badge-yes ${s.feasible_time ? "green" : "red"}">${s.feasible_time ? "Feasible" : "Tidak"}</span></td>`;

      tr.style.cursor = "pointer";
      tr.addEventListener("click", () => {
        // Switch to map tab and filter to this SPPG
        document
          .querySelectorAll(".tab-btn")
          .forEach((b) => b.classList.remove("active"));
        document
          .querySelectorAll(".tab-panel")
          .forEach((p) => p.classList.remove("active"));
        document.getElementById("btn-map")?.classList.add("active");
        document.getElementById("map-tab")?.classList.add("active");

        sppgSelect.value = s.sppg;
        sppgSelect.dispatchEvent(new Event("change"));
      });

      tbody.appendChild(tr);
    });
  }

  // ----------------------------------------------------------------

  function filterTable(query) {
    const rows = document.querySelectorAll("#sppg-table-body tr");
    rows.forEach((row) => {
      row.style.display = row.dataset.sppg?.includes(query) ? "" : "none";
    });
  }
});
