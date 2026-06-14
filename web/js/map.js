let map = null;
let routeLayerGroup = null;
let currentAlgData = null;
let tileLayer = null;

const TILE_DARK  = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const TILE_LIGHT = 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';

let currentTheme = "dark";
let currentBaseLayer = null;

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

function createBaseLayer(theme) {

    return L.tileLayer(
        theme === "dark"
            ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            : "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        {
            attribution: "© OpenStreetMap © CARTO",
            subdomains: "abcd",
            maxZoom: 20
        }
    );

}

function initMap() {

    map = L.map("map", {
        center: [-7.29, 112.77],
        zoom: 13,
        zoomControl: true
    });

    currentBaseLayer = createBaseLayer("dark");
    currentBaseLayer.addTo(map);

    routeLayerGroup = L.layerGroup().addTo(map);

}

function toggleMapTheme() {
    if (currentBaseLayer) {
        map.removeLayer(currentBaseLayer);
    }

    currentTheme = currentTheme === "dark" ? "light" : "dark";
    currentBaseLayer = createBaseLayer(currentTheme);
    currentBaseLayer.addTo(map);
}

function updateMapTile(theme) {
    if (!map || !currentBaseLayer) return;
    currentBaseLayer.setUrl(theme === 'light' ? TILE_LIGHT : TILE_DARK);
    currentTheme = theme;
}

function updateMap(algData, sppgFilter) {
    if (!map || !routeLayerGroup || !algData) return;

    currentAlgData = algData;
    routeLayerGroup.clearLayers();

    const sppgList =
        sppgFilter === 'all'
            ? algData.results_per_sppg
            : algData.results_per_sppg.filter(s => s.sppg === sppgFilter);

    const bounds = L.latLngBounds();
    let colorIdx = 0;

    sppgList.forEach((sppgData) => {
        const color = CLUSTER_PALETTE[colorIdx % CLUSTER_PALETTE.length];
        colorIdx++;

        if (!sppgData.route_order || sppgData.route_order.length < 2) return;

        const shortName   = sppgData.sppg.replace("SPPG Kota Surabaya ", "");
        const schoolCount = countSchools(sppgData);
        const coords      = sppgData.route_order.map(p => `${p.lng},${p.lat}`).join(";");

        // ── MARKER DEPOT ────────────────────────────────────────────
        const depotLatLng = [
            sppgData.route_order[0].lat,
            sppgData.route_order[0].lng,
        ];

        L.marker(depotLatLng, { icon: makeCircleIcon("#f43f5e", 14, true) })
            .addTo(routeLayerGroup)
            .bindPopup(`
                <strong>🏭 SPPG (Depot)</strong><br>
                ${shortName}<br>
                <hr style="border-color:rgba(99,147,255,0.2);margin:6px 0">
                📦 ${schoolCount} sekolah<br>
                🛣️ ${sppgData.distance_km.toFixed(2)} km<br>
                ⏱️ ${sppgData.time_spent_minutes.toFixed(1)} menit<br>
                🕗 ${sppgData.departure_time} — ${sppgData.return_time}
            `, { maxWidth: 240 });

        // ── MARKER SEKOLAH ──────────────────────────────────────────
        const totalSchools = sppgData.route_order.length - 2; // exclude depot awal & akhir

        sppgData.route_order.slice(1, -1).forEach((point, i) => {

            // Cocokkan dengan data detail di route[] untuk dapat waktu & tray
            const routeDetail = sppgData.route.find(r => r.school === point.name);
            const tray      = routeDetail?.drop_tray      ?? '—';

            const popupHtml = `
                <strong>🏫 ${point.name}</strong><br>
                <hr style="border-color:rgba(99,147,255,0.2);margin:6px 0">
                📍 Urutan ke-<b>${i + 1}</b> dari <b>${totalSchools}</b> sekolah<br>
                🏭 SPPG: <b>${sppgData.sppg.replace('SPPG Kota Surabaya ', '')}</b>
                📦 Drop: <b>${tray} tray</b>
            `;

            L.marker([point.lat, point.lng], { icon: makeCircleIcon(color, 9) })
                .addTo(routeLayerGroup)
                .bindPopup(popupHtml, { maxWidth: 240 });
        });

        // ── ROUTE OSRM ──────────────────────────────────────────────
        // ── ROUTE OSRM ──────────────────────────────────────────────
    fetch(`https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`)
        .then(res => res.json())
        .then(data => {

            if (!data.routes || !data.routes.length) return;

            const latlngs =
                data.routes[0].geometry.coordinates.map(
                    coord => [coord[1], coord[0]]
                );

            let polyline;

            // MODE SEMUA CLUSTER
            if (sppgFilter === "all") {

                // glow belakang
                L.polyline(latlngs, {
                    color: color,
                    weight: 10,
                    opacity: 0.12
                }).addTo(routeLayerGroup);

                // route utama
                polyline = L.polyline(latlngs, {
                    color: color,
                    weight: 4,
                    opacity: 0.9
                }).addTo(routeLayerGroup);

            }
            else {
                L.polyline(latlngs, {
                    color: color,
                    weight: 16,
                    opacity: 0.18
                }).addTo(routeLayerGroup);

                // Route utama
                polyline = L.polyline(latlngs, {
                    color: color,
                    weight: 6,
                    opacity: 1
                }).addTo(routeLayerGroup);

                const decorator = L.polylineDecorator(polyline, {
                    patterns: [{
                        offset: 0,
                        repeat: 80,
                        symbol: L.Symbol.arrowHead({
                            pixelSize: 14,
                            polygon: true,
                            pathOptions: {
                                fillOpacity: 1,
                                fillColor: color,
                                color: color,
                                weight: 0
                            }
                        })
                    }]
                }).addTo(routeLayerGroup);

                let offset = 0;
                const animation = setInterval(() => {
                    offset = (offset + 3) % 80;
                    decorator.setPatterns([{
                        offset: offset,
                        repeat: 80,
                        symbol: L.Symbol.arrowHead({
                            pixelSize: 14,
                            polygon: true,
                            pathOptions: {
                                fillOpacity: 1,
                                fillColor: color,
                                color: color,
                                weight: 0
                            }
                        })
                    }]);
                }, 60);
            }

            polyline.bindTooltip(
                `<strong>${shortName}</strong><br>
                ${schoolCount} sekolah ·
                ${sppgData.distance_km.toFixed(2)} km`
            );

            polyline.on("click", () => {
                showRouteDetail(sppgData);
            });

            bounds.extend(polyline.getBounds());

            map.fitBounds(bounds, {
                padding: [30, 30],
                maxZoom: 15
            });

        })
        .catch(err => {
            console.error("OSRM error:", err);
        });
    });

    updateRouteDetail(sppgFilter, algData);
}

function showRouteDetail(sppgData) {
    const select = document.getElementById('sppg-select');
    if (select) {
        select.value = sppgData.sppg;
        select.dispatchEvent(new Event('change'));
    }
}

function updateRouteDetail(sppgFilter, algData) {
    const panel   = document.getElementById('route-detail-panel');
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

    sppgData.route.forEach(step => {
        const div = document.createElement('div');

        if (step.school) {
            div.className = 'route-step school-step';
            div.innerHTML = `
                <span class="route-step-icon">
                    <i data-lucide="school"></i>
                </span>
                <div class="route-step-info">
                    <div class="route-step-name">${step.school}</div>
                    <div class="route-step-meta">
                        ${step.arrival_time} tiba · ${step.departure_time} berangkat · ${step.drop_tray} tray
                    </div>
                </div>`;

        } else if (step.event === 'REFILL') {
            div.className = 'route-step refill-step';
            div.innerHTML = `
                <span class="route-step-icon">
                    <i data-lucide="refresh-cw"></i>
                </span>
                <div class="route-step-info">
                    <div class="route-step-name">Refill Muatan</div>
                    <div class="route-step-meta">
                        ${step.arrival_time} tiba · ${step.departure_time} berangkat
                    </div>
                </div>`;

        } else if (step.event === 'RETURN_DEPOT') {
            div.className = 'route-step return-step';
            div.innerHTML = `
                <span class="route-step-icon">
                    <i data-lucide="flag"></i>
                </span>
                <div class="route-step-info">
                    <div class="route-step-name">Kembali ke SPPG</div>
                    <div class="route-step-meta">${
                        step.finish_time
                            ? `Tiba: ${step.arrival_time} · Selesai bongkar: ${step.finish_time}`
                            : `Tiba: ${step.arrival_time}`
                    }</div>
                </div>`;
        }

        content.appendChild(div);
        lucide.createIcons();
    });
}

document.addEventListener("DOMContentLoaded", () => {

    const toggle =
        document.getElementById("theme-toggle-btn");

    const label =
        document.getElementById("theme-label");

    if (!toggle) return;

    toggle.addEventListener("change", () => {

        toggleMapTheme();

        label.innerHTML =
            currentTheme === "dark"
                ? "🌙 Dark"
                : "☀️ Light";

    });

});