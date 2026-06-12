function renderHistoryTab() {
    const container = document.getElementById('history-content');
    if (!container) return;

    const data = getHistoryData();
    container.innerHTML = '';

    if (!data) {
        const empty = document.createElement('div');
        empty.className = 'history-empty';

        const icon  = document.createElement('div');
        icon.className = 'history-empty-icon';
        icon.textContent = '📊';

        const title = document.createElement('div');
        title.className = 'history-empty-title';
        title.textContent = 'Belum ada data eksperimen';

        const desc = document.createElement('div');
        desc.className = 'history-empty-desc';
        desc.textContent = 'Jalankan eksperimen 10× terlebih dahulu: python3 routing/run_experiments.py';

        empty.append(icon, title, desc);
        container.appendChild(empty);
        return;
    }

    const meta = document.getElementById('history-meta');
    if (meta) {
        const updated = new Date(data.last_updated).toLocaleString('id-ID');
        meta.textContent = `${data.n_runs} run × 4 algoritma · Diperbarui: ${updated}`;
    }

    const algOrder = ['sa', 'ga', 'pso', 'aco'];

    algOrder.forEach(key => {
        const algData = data.algorithms[key];
        if (!algData) return;

        const meta_ = algorithmMeta[key];
        const bestRun = algData.best.run;

        // ── Card container ───────────────────────────────────────────
        const card = document.createElement('div');
        card.className = `history-alg-card history-${key}`;

        // ── Header ───────────────────────────────────────────────────
        const header = document.createElement('div');
        header.className = 'history-alg-header';

        const algName = document.createElement('span');
        algName.className = 'history-alg-name';
        algName.textContent = meta_.name;

        const algBadge = document.createElement('span');
        algBadge.className = `algo-tab ${meta_.tabClass}`;
        algBadge.style.pointerEvents = 'none';
        algBadge.textContent = meta_.abbr;

        header.append(algName, algBadge);

        // ── Best badge ───────────────────────────────────────────────
        const bestBadge = document.createElement('div');
        bestBadge.className = 'history-best-badge';
        bestBadge.textContent =
            `Terbaik: ${algData.best.total_distance_km.toFixed(2)} km` +
            ` · ${algData.best.total_time_minutes.toFixed(2)} mnt` +
            ` · Run #${algData.best.run}`;

        // ── Table ────────────────────────────────────────────────────
        const tableWrapper = document.createElement('div');
        tableWrapper.className = 'table-wrapper';

        const table = document.createElement('table');
        table.className = 'data-table history-table';

        const thead = document.createElement('thead');
        const headRow = document.createElement('tr');
        ['Run', 'Jarak (km) ↑', 'Waktu (mnt) ↑', 'Runtime (dtk)', 'Feasible'].forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            headRow.appendChild(th);
        });
        thead.appendChild(headRow);

        const tbody = document.createElement('tbody');

        // Run rows
        algData.runs.forEach(r => {
            const tr = document.createElement('tr');
            if (r.run === bestRun) tr.classList.add('history-row-best');

            const tdRun = document.createElement('td');
            tdRun.textContent = r.run === bestRun ? `🏆 ${r.run}` : String(r.run);

            const tdDist = document.createElement('td');
            tdDist.className = 'td-num';
            tdDist.textContent = r.total_distance_km.toFixed(2);

            const tdTime = document.createElement('td');
            tdTime.className = 'td-num';
            tdTime.textContent = r.total_time_minutes.toFixed(2);

            const tdRuntime = document.createElement('td');
            tdRuntime.className = 'td-num';
            tdRuntime.textContent = r.runtime_seconds.toFixed(2);

            const tdFeas = document.createElement('td');
            const badge = document.createElement('span');
            badge.className = `badge-yes ${r.feasible ? 'green' : 'red'}`;
            badge.textContent = r.feasible ? 'Ya' : 'Tidak';
            tdFeas.appendChild(badge);

            tr.append(tdRun, tdDist, tdTime, tdRuntime, tdFeas);
            tbody.appendChild(tr);
        });

        // Average row
        const avg = algData.average;
        const avgRow = document.createElement('tr');
        avgRow.className = 'history-row-avg';

        const avgLabel = document.createElement('td');
        avgLabel.textContent = 'Rata-rata';

        const avgDist = document.createElement('td');
        avgDist.className = 'td-num';
        avgDist.textContent = avg.total_distance_km.toFixed(2);

        const avgTime = document.createElement('td');
        avgTime.className = 'td-num';
        avgTime.textContent = avg.total_time_minutes.toFixed(2);

        const avgRuntime = document.createElement('td');
        avgRuntime.className = 'td-num';
        avgRuntime.textContent = avg.runtime_seconds.toFixed(2);

        const avgFeas = document.createElement('td');
        avgFeas.textContent = '—';

        avgRow.append(avgLabel, avgDist, avgTime, avgRuntime, avgFeas);
        tbody.appendChild(avgRow);

        table.append(thead, tbody);
        tableWrapper.appendChild(table);
        card.append(header, bestBadge, tableWrapper);
        container.appendChild(card);
    });
}
