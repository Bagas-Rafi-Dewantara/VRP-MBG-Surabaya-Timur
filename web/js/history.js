let _convChart = null;
let _selectedHistoryRun = null;
let _lastRenderedAlg = null; // track algorithm changes to reset run selection

function renderHistoryTab() {
    const container = document.getElementById('history-content');
    if (!container) return;

    const data = getHistoryData();
    container.innerHTML = '';

    if (!data) {
        const empty = document.createElement('div');
        empty.className = 'history-empty';

        const icon = document.createElement('div');
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

    // FIX #4: resolve algKey once and pass it everywhere (no dual fallback paths)
    const algKey = window.currentAlg || Object.keys(data.algorithms)[0] || 'sa';

    // FIX #1: reset run selection when algorithm changes
    if (algKey !== _lastRenderedAlg) {
        _selectedHistoryRun = null;
        _lastRenderedAlg = algKey;
    }

    const algData = data.algorithms[algKey];
    if (algData) {
        if (_selectedHistoryRun === null) {
            _selectedHistoryRun = algData.best.run;
        }
        container.appendChild(_buildAlgCard(algData, algKey));
    }

    // FIX #4: pass algKey as parameter instead of re-reading window.currentAlg
    _renderConvergenceSection(data, algKey);
}


function _buildAlgCard(algData, algKey) {
    const meta_ = algorithmMeta[algKey];
    const bestRun = algData.best.run;

    const card = document.createElement('div');
    card.className = `history-alg-card history-alg-card-full history-${algKey}`;

    // Header
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

    // Best badge
    const bestBadge = document.createElement('div');
    bestBadge.className = 'history-best-badge';
    bestBadge.textContent =
        `Terbaik: ${algData.best.total_distance_km.toFixed(2)} km` +
        ` · ${algData.best.total_time_minutes.toFixed(2)} mnt` +
        ` · Run #${algData.best.run}`;

    // Table
    const tableWrapper = document.createElement('div');
    tableWrapper.className = 'table-wrapper history-table-wrapper';

    const table = document.createElement('table');
    table.className = 'data-table history-table';

    const thead = document.createElement('thead');
    const headRow = document.createElement('tr');
    ['Run', 'Jarak (km)', 'Waktu (mnt)', 'Runtime (dtk)', 'Feasible'].forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        headRow.appendChild(th);
    });
    thead.appendChild(headRow);

    const tbody = document.createElement('tbody');

    algData.runs.forEach(r => {
        const tr = document.createElement('tr');
        tr.style.cursor = 'pointer';
        // FIX #2: restore best-run row highlight
        if (r.run === bestRun) tr.classList.add('history-row-best');
        if (r.run === _selectedHistoryRun) tr.classList.add('history-row-selected');

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

        tr.addEventListener('click', () => {
            _selectedHistoryRun = r.run;
            tbody.querySelectorAll('tr').forEach(row => row.classList.remove('history-row-selected'));
            tr.classList.add('history-row-selected');
            const freshData = getHistoryData();
            if (freshData) _renderConvergenceSection(freshData, algKey);
        });

        tbody.appendChild(tr);
    });

    // Average row
    const avg = algData.average;
    const avgRow = document.createElement('tr');
    avgRow.className = 'history-row-avg';
    _appendSummaryRow(avgRow, 'Rata-rata', avg.total_distance_km, avg.total_time_minutes, avg.runtime_seconds, '—');
    tbody.appendChild(avgRow);

    // Std dev row
    if (algData.std_dev) {
        const sdRow = document.createElement('tr');
        sdRow.className = 'history-row-stddev';
        _appendSummaryRow(sdRow, 'Std. Dev (σ)', algData.std_dev.total_distance_km, algData.std_dev.total_time_minutes, algData.std_dev.runtime_seconds, '—');
        tbody.appendChild(sdRow);
    }

    table.append(thead, tbody);
    tableWrapper.appendChild(table);
    card.append(header, bestBadge, tableWrapper);
    return card;
}

function _appendSummaryRow(tr, label, dist, time_, runtime, feasText) {
    const tdLabel = document.createElement('td');
    tdLabel.textContent = label;

    const tdDist = document.createElement('td');
    tdDist.className = 'td-num';
    tdDist.textContent = dist.toFixed(2);

    const tdTime = document.createElement('td');
    tdTime.className = 'td-num';
    tdTime.textContent = time_.toFixed(2);

    const tdRuntime = document.createElement('td');
    tdRuntime.className = 'td-num';
    tdRuntime.textContent = runtime.toFixed(2);

    const tdFeas = document.createElement('td');
    tdFeas.textContent = feasText;

    tr.append(tdLabel, tdDist, tdTime, tdRuntime, tdFeas);
}

// FIX #4: algKey passed as parameter; FIX #3: padCurve guards empty arr; FIX #6: order tiers
function _renderConvergenceSection(data, algKey) {
    const section = document.getElementById('convergence-section');
    if (!section) return;

    const algData = data.algorithms[algKey];
    if (!algData) { section.style.display = 'none'; return; }

    const perRunBest = algData.convergence_best_per_run || [];
    if (!perRunBest.length) { section.style.display = 'none'; return; }
    section.style.display = '';

    const unitBadge = section.querySelector('.unit-badge');
    if (unitBadge) unitBadge.textContent = `Semua Run (10 Konvergensi)`;

    const desc = section.querySelector('.chart-card-header p');
    if (desc) {
        desc.textContent = `Perbandingan konvergensi (Best So Far) untuk semua 10 run. Garis tebal menunjukkan run terbaik.`;
    }

    const maxLen = Math.max(...perRunBest.map(c => c.length));
    if (maxLen === 0) return;
    const labels = Array.from({ length: maxLen }, (_, i) => i + 1);

    const algColor = {
        sa:  '#3b82f6',
        ga:  '#10b981',
        pso: '#f59e0b',
        aco: '#8b5cf6',
    }[algKey] || '#3b82f6';

    // FIX #3: guard against empty individual curves
    const padCurve = (arr) => {
        if (arr.length === 0) return Array(maxLen).fill(0);
        const out = [...arr];
        while (out.length < maxLen) out.push(out[out.length - 1]);
        return out;
    };

    const datasets = perRunBest.map((curve, idx) => {
        const runNum = idx + 1;
        const isBest = runNum === algData.best.run;
        const isSelected = runNum === _selectedHistoryRun;

        const label = isBest ? `Run #${runNum} (Best)` : `Run #${runNum}`;

        return {
            label,
            data: padCurve(curve),
            borderColor: isBest ? algColor : (isSelected ? algColor : 'rgba(148,163,184,0.3)'),
            backgroundColor: 'transparent',
            borderWidth: isBest ? 3 : (isSelected ? 2 : 1),
            pointRadius: 0,
            tension: 0.3,
            fill: false,
            // FIX #6: three tiers so selected run always draws above grey non-best runs
            order: isBest ? 0 : (isSelected ? 1 : 2),
        };
    });

    const canvas = document.getElementById('chart-convergence');
    if (!canvas) return;

    if (_convChart) { _convChart.destroy(); _convChart = null; }

    _convChart = new Chart(canvas, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                    labels: { color: '#7b9bc8', font: { size: 10 }, boxWidth: 12 },
                },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)} km`,
                    },
                },
            },
            scales: {
                x: {
                    title: { display: true, text: 'Iterasi', color: '#4a6080' },
                    ticks: { color: '#4a6080', maxTicksLimit: 12 },
                    grid: { color: 'rgba(99,147,255,0.07)' },
                },
                y: {
                    title: { display: true, text: 'Total Jarak (km)', color: '#4a6080' },
                    ticks: { color: '#4a6080' },
                    grid: { color: 'rgba(99,147,255,0.07)' },
                },
            },
        },
    });
}
