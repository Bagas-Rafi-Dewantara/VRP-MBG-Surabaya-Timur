let map = null;
let routeLayerGroup = null;
let currentAlgData = null;

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

    currentBaseLayer =
        createBaseLayer("dark");

    currentBaseLayer.addTo(map);

    routeLayerGroup =
        L.layerGroup().addTo(map);

}

function toggleMapTheme() {

    console.log("BEFORE:", currentTheme);

    if (currentBaseLayer) {
        map.removeLayer(currentBaseLayer);
    }

    currentTheme =
        currentTheme === "dark"
            ? "light"
            : "dark";

    currentBaseLayer =
        createBaseLayer(currentTheme);

    currentBaseLayer.addTo(map);

}

/**
 * Re-render map for the given algData, optionally filtered to one SPPG.
 * Also updates the sidebar route-detail panel if a single SPPG is selected.
 */
function updateMap(algData, sppgFilter) {
    if (!map || !routeLayerGroup || !algData) return;

    currentAlgData = algData;
    routeLayerGroup.clearLayers();

    const sppgList =
        sppgFilter === 'all'
            ? algData.results_per_sppg
            : algData.results_per_sppg.filter(
                s => s.sppg === sppgFilter
            );

    const bounds = L.latLngBounds();

    let colorIdx = 0;

    sppgList.forEach((sppgData) => {

        const color =
            CLUSTER_PALETTE[
                colorIdx % CLUSTER_PALETTE.length
            ];

        colorIdx++;

        if (
            !sppgData.route_order ||
            sppgData.route_order.length < 2
        ) {
            return;
        }

        const shortName =
            sppgData.sppg.replace(
                "SPPG Kota Surabaya ",
                ""
            );

        const schoolCount =
            countSchools(sppgData);

        const coords =
            sppgData.route_order
                .map(
                    p => `${p.lng},${p.lat}`
                )
                .join(";");

        // MARKER DEPOT

        const depotLatLng = [
            sppgData.route_order[0].lat,
            sppgData.route_order[0].lng
        ];

        L.marker(
            depotLatLng,
            {
                icon: makeCircleIcon(
                    "#f43f5e",
                    18,
                    true
                )
            }
        )
        .addTo(routeLayerGroup)
        .bindPopup(`
            <strong>🏭 SPPG (Depot)</strong><br>
            ${shortName}<br><br>

            📦 ${schoolCount} sekolah<br>
            🛣️ ${sppgData.distance_km.toFixed(2)} km<br>
            ⏱️ ${sppgData.time_spent_minutes.toFixed(1)} menit<br>
            🕗 ${sppgData.departure_time} - ${sppgData.return_time}
        `);

        // MARKER SEKOLAH

        sppgData.route_order
            .slice(1, -1)
            .forEach((point, i) => {

                L.marker(
                    [point.lat, point.lng],
                    {
                        icon: makeCircleIcon(
                            color,
                            12
                        )
                    }
                )
                .addTo(routeLayerGroup)
                .bindPopup(`
                    <strong>${point.name}</strong><br>
                    Urutan ${i + 1}
                `);

            });

        // ROUTE OSRM

        fetch(
            `https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`
        )
        .then(res => res.json())
        .then(data => {

            if (
                !data.routes ||
                !data.routes.length
            ) {
                return;
            }

            const geometry =
                data.routes[0]
                    .geometry
                    .coordinates;

            const latlngs =
                geometry.map(
                    coord => [
                        coord[1],
                        coord[0]
                    ]
                );

            L.polyline(
                latlngs,
                {
                    color: "#ffffff",
                    weight: 10,
                    opacity: 0.25
                }
            ).addTo(routeLayerGroup);

            const polyline = L.polyline(latlngs, {
                color,
                weight: 4,
                opacity: 0.9,
                className: "animated-route"
            }).addTo(routeLayerGroup);

            polyline.bindTooltip(
                `<strong>${shortName}</strong><br>${schoolCount} sekolah · ${sppgData.distance_km.toFixed(2)} km`
            );

            polyline.on(
                'click',
                () => showRouteDetail(sppgData)
            );

            bounds.extend(
                polyline.getBounds()
            );

            map.fitBounds(
                bounds,
                {
                    padding: [30, 30],
                    maxZoom: 15
                }
            );

        })
        .catch(err => {
            console.error(
                "OSRM error:",
                err
            );
        });

    });

    updateRouteDetail(
        sppgFilter,
        algData
    );
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