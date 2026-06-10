let map = null;
let routeLayerGroup = null;
let currentAlgData = null;

const CLUSTER_PALETTE = [
    '#3b82f6','#10b981','#f59e0b','#8b5cf6','#ec4899',
    '#14b8a6','#f97316','#06b6d4','#84cc16','#a855f7',
];

function makeCircleIcon(color, size = 12, pulse = false) {
    const pulseStyle = pulse
        ? `box-shadow: 0 0 0 4px ${color}44, 0 0 10px ${color}88;` : '';
    return L.divIcon({
        className: '',
        html: `<div style="
            width:${size}px; height:${size}px; border-radius:50%;
            background:${color}; border:2px solid rgba(255,255,255,0.7);
            ${pulseStyle} box-sizing:border-box;"></div>`,
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2],
        popupAnchor: [0, -size / 2],
    });
}

function initMap() {
    map = L.map('map', {
        center: [-7.29, 112.77],
        zoom: 13,
        zoomControl: true,
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap © CARTO',
        subdomains: 'abcd',
        maxZoom: 20,
    }).addTo(map);

    routeLayerGroup = L.layerGroup().addTo(map);
}

/**
 * Re-render map for the given algData, optionally filtered to one SPPG.
 * Also updates the sidebar route-detail panel if a single SPPG is selected.
 */
function updateMap(algData, sppgFilter) {
    if (!map || !routeLayerGroup || !algData) return;
    currentAlgData = algData;

    routeLayerGroup.clearLayers();

    const sppgList = sppgFilter === 'all'
        ? algData.results_per_sppg
        : algData.results_per_sppg.filter(s => s.sppg === sppgFilter);

    const bounds = L.latLngBounds();
    let colorIdx = 0;

    sppgList.forEach(sppgData => {
        const color = CLUSTER_PALETTE[colorIdx % CLUSTER_PALETTE.length];
        colorIdx++;

        if (!sppgData.polyline || sppgData.polyline.length < 2) return;

        // Draw animated dashed polyline
        const polyline = L.polyline(sppgData.polyline, {
            color,
            weight: 3,
            opacity: 0.85,
            dashArray: '8, 6',
        }).addTo(routeLayerGroup);

        const shortName = sppgData.sppg.replace('SPPG Kota Surabaya ', '');
        const schoolCount = countSchools(sppgData);

        polyline.bindTooltip(`<strong>${shortName}</strong><br>${schoolCount} sekolah · ${sppgData.distance_km.toFixed(2)} km`, {
            sticky: true,
            className: '',
        });

        polyline.on('click', () => showRouteDetail(sppgData));

        // Depot marker (first & last polyline point)
        const depotLatLng = sppgData.polyline[0];
        L.marker(depotLatLng, { icon: makeCircleIcon('#f43f5e', 14, true) })
            .addTo(routeLayerGroup)
            .bindPopup(`
                <strong>🏭 SPPG (Depot)</strong><br>
                ${sppgData.sppg.replace('SPPG Kota Surabaya ', '')}<br>
                <br>
                📦 <strong>${schoolCount} sekolah</strong> dilayani<br>
                🛣️ Jarak: <strong>${sppgData.distance_km.toFixed(2)} km</strong><br>
                ⏱️ Waktu: <strong>${sppgData.time_spent_minutes.toFixed(1)} menit</strong><br>
                🕗 Berangkat: ${sppgData.departure_time} | Kembali: ${sppgData.return_time}
            `);

        // School markers (intermediate polyline points)
        sppgData.polyline.slice(1, -1).forEach((latLng, i) => {
            L.marker(latLng, { icon: makeCircleIcon(color, 9) })
                .addTo(routeLayerGroup)
                .bindPopup(`<strong>🏫 Sekolah ke-${i + 1}</strong><br>Cluster: ${shortName}`);
        });

        bounds.extend(polyline.getBounds());
    });

    if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [30, 30], maxZoom: 15 });
    }

    // Update sidebar detail
    updateRouteDetail(sppgFilter, algData);
}

function showRouteDetail(sppgData) {
    // Switch SPPG select to that SPPG, which will trigger updateRouteDetail
    const select = document.getElementById('sppg-select');
    if (select) {
        select.value = sppgData.sppg;
        select.dispatchEvent(new Event('change'));
    }
}

function updateRouteDetail(sppgFilter, algData) {
    const panel = document.getElementById('route-detail-panel');
    const content = document.getElementById('route-detail-content');
    if (!panel || !content) return;

    if (sppgFilter === 'all' || !algData) {
        panel.style.display = 'none';
        return;
    }

    const sppgData = algData.results_per_sppg.find(s => s.sppg === sppgFilter);
    if (!sppgData) { panel.style.display = 'none'; return; }

    panel.style.display = '';
    content.innerHTML = '';

    const steps = sppgData.route;
    steps.forEach(step => {
        const div = document.createElement('div');

        if (step.school) {
            div.className = 'route-step school-step';
            div.innerHTML = `
                <span class="route-step-icon">🏫</span>
                <div class="route-step-info">
                    <div class="route-step-name">${step.school}</div>
                    <div class="route-step-meta">${step.arrival_time} tiba · ${step.departure_time} berangkat · ${step.drop_tray} tray</div>
                </div>`;
        } else if (step.event === 'REFILL') {
            div.className = 'route-step refill-step';
            div.innerHTML = `
                <span class="route-step-icon">🔄</span>
                <div class="route-step-info">
                    <div class="route-step-name">Refill Muatan</div>
                    <div class="route-step-meta">${step.arrival_time} tiba · ${step.departure_time} berangkat</div>
                </div>`;
        } else if (step.event === 'RETURN_DEPOT') {
            div.className = 'route-step return-step';
            div.innerHTML = `
                <span class="route-step-icon">🏁</span>
                <div class="route-step-info">
                    <div class="route-step-name">Kembali ke SPPG</div>
                    <div class="route-step-meta">Tiba: ${step.arrival_time}</div>
                </div>`;
        }

        content.appendChild(div);
    });
}
