// Chart.js global defaults — dark theme
Chart.defaults.color = '#7b9bc8';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 12;

const ALG_COLORS = {
    sa:  { bg: 'rgba(59,130,246,0.75)',  border: '#3b82f6' },
    ga:  { bg: 'rgba(16,185,129,0.75)',  border: '#10b981' },
    pso: { bg: 'rgba(245,158,11,0.75)',  border: '#f59e0b' },
    aco: { bg: 'rgba(139,92,246,0.75)',  border: '#8b5cf6' },
};

const chartInstances = {};

const commonBarOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: 'rgba(15,28,51,0.95)',
            titleColor: '#e8f0ff',
            bodyColor: '#7b9bc8',
            borderColor: 'rgba(99,147,255,0.2)',
            borderWidth: 1,
            padding: 10,
            displayColors: false,
        },
    },
    scales: {
        x: {
            grid: { color: 'rgba(255,255,255,0.04)' },
            ticks: { color: '#7b9bc8', maxRotation: 0 },
        },
        y: {
            grid: { color: 'rgba(255,255,255,0.04)' },
            ticks: { color: '#7b9bc8' },
            beginAtZero: false,
        },
    },
    animation: { duration: 400, easing: 'easeOutQuart' },
};

function initCharts() {
    const ids = ['chart-distance', 'chart-time', 'chart-runtime', 'chart-dist-per-sppg'];
    ids.forEach(id => {
        const ctx = document.getElementById(id);
        if (!ctx) return;
        chartInstances[id] = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: { labels: [], datasets: [] },
            options: JSON.parse(JSON.stringify(commonBarOptions)),
        });
    });
}

/**
 * Update the three comparison charts (distance, time, runtime)
 * @param {Object} compData — result of getComparisonData()
 * @param {string} selectedAlg — currently selected alg key
 */
function updateComparisonCharts(compData, selectedAlg) {
    const algs = Object.keys(compData);
    const abbrs = algs.map(a => compData[a].abbr);

    // --- Distance chart ---
    _updateBarChart(
        'chart-distance',
        abbrs,
        algs.map(a => compData[a].distance),
        algs,
        selectedAlg,
        v => `${v.toFixed(2)} km`
    );

    // --- Time chart ---
    _updateBarChart(
        'chart-time',
        abbrs,
        algs.map(a => compData[a].time),
        algs,
        selectedAlg,
        v => `${v.toFixed(2)} menit`,
        180 // draw max time reference line
    );


    // --- Runtime chart (only if any has runtime data) ---
    const hasRuntime = algs.some(a => compData[a].runtime !== null);
    if (hasRuntime) {
        _updateBarChart(
            'chart-runtime',
            abbrs,
            algs.map(a => compData[a].runtime ?? 0),
            algs,
            selectedAlg,
            v => `${v.toFixed(2)} detik`
        );
    }
}

/**
 * Update the per-SPPG distance distribution chart for the selected algorithm
 */
function updatePerSppgChart(algData) {
    if (!algData || !chartInstances['chart-dist-per-sppg']) return;

    const labels = algData.results_per_sppg.map((s, i) => `${i + 1}`);
    const values = algData.results_per_sppg.map(s => s.distance_km);
    const times  = algData.results_per_sppg.map(s => s.time_spent_minutes);

    const chart = chartInstances['chart-dist-per-sppg'];
    chart.data = {
        labels,
        datasets: [
            {
                label: 'Jarak (km)',
                data: values,
                backgroundColor: 'rgba(59,130,246,0.6)',
                borderColor: '#3b82f6',
                borderWidth: 1,
                borderRadius: 3,
            },
        ],
    };
    chart.options.plugins.tooltip = {
        ...commonBarOptions.plugins.tooltip,
        callbacks: {
            title: ctx => {
                const idx = ctx[0].dataIndex;
                const sppg = algData.results_per_sppg[idx];
                return sppg.sppg.replace('SPPG Kota Surabaya ', '');
            },
            label: ctx => {
                const idx = ctx.dataIndex;
                return [
                    `Jarak: ${values[idx].toFixed(2)} km`,
                    `Waktu: ${times[idx].toFixed(1)} menit`,
                ];
            },
        },
    };
    chart.options.scales.x.ticks = {
        color: '#4a6080',
        font: { size: 9 },
    };
    chart.update();
}

// ---- internal helpers ----

function _updateBarChart(id, labels, values, algKeys, selectedAlg, tooltipFmt, maxLine) {
    const chart = chartInstances[id];
    if (!chart) return;

    const bgColors     = algKeys.map(a => ALG_COLORS[a]?.bg ?? 'rgba(99,147,255,0.5)');
    const borderColors = algKeys.map(a => ALG_COLORS[a]?.border ?? '#6393ff');
    const borderWidths = algKeys.map(a => a === selectedAlg ? 2 : 1);

    chart.data = {
        labels,
        datasets: [{
            data: values,
            backgroundColor: bgColors,
            borderColor: borderColors,
            borderWidth: borderWidths,
            borderRadius: 6,
        }],
    };

    const minVal = Math.min(...values);
    const maxVal = Math.max(...values);

    chart.options.scales.y = {
        beginAtZero: false,
        min: Math.floor(minVal - 1),
        max: Math.ceil(maxVal + 1),

        grid: {
            color: 'rgba(255,255,255,0.04)'
        },

        ticks: {
            color: '#7b9bc8'
        }
    };

    chart.options.plugins.tooltip = {
        ...commonBarOptions.plugins.tooltip,
        callbacks: {
            label: ctx => tooltipFmt(ctx.parsed.y),
        },
    };

    // Annotate max-time line if needed (just add a custom dataset)
    if (maxLine) {
        chart.data.datasets.push({
            type: 'line',
            label: `Batas ${maxLine}`,
            data: Array(labels.length).fill(maxLine),
            borderColor: 'rgba(244,63,94,0.6)',
            borderWidth: 1.5,
            borderDash: [5, 4],
            pointRadius: 0,
            fill: false,
        });
    }

    chart.update();
}
