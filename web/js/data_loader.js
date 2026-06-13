const algorithmFiles = ['sa', 'ga', 'pso', 'aco'];
let historyData = null;

const algorithmMeta = {
    'sa':  { name: 'Simulated Annealing', abbr: 'SA',  cssClass: 'alg-sa',  tabClass: 'active-sa'  },
    'ga':  { name: 'Genetic Algorithm',   abbr: 'GA',  cssClass: 'alg-ga',  tabClass: 'active-ga'  },
    'pso': { name: 'Particle Swarm Opt.', abbr: 'PSO', cssClass: 'alg-pso', tabClass: 'active-pso' },
    'aco': { name: 'Ant Colony Opt.',     abbr: 'ACO', cssClass: 'alg-aco', tabClass: 'active-aco' },
};

// Alias for backward compat
const algorithmNames = Object.fromEntries(
    Object.entries(algorithmMeta).map(([k, v]) => [k, v.name])
);

const routingData = {};

async function loadAllData() {
    const promises = algorithmFiles.map(async alg => {
        try {
            const response = await fetch(`../routing/results/${alg}.json`);
            if (response.ok) {
                routingData[alg] = await response.json();
            } else {
                console.warn(`Could not load ${alg}.json — status ${response.status}`);
            }
        } catch (e) {
            console.error(`Fetch error for ${alg}.json:`, e);
        }
    });
    await Promise.all(promises);
    return routingData;
}

async function loadHistoryData() {
    try {
        const response = await fetch('../routing/results/history.json');
        if (response.ok) {
            historyData = await response.json();
        } else {
            console.warn('history.json not found — run routing/run_experiments.py first');
        }
    } catch (e) {
        console.warn('Could not load history.json:', e);
    }
    return historyData;
}

function getHistoryData() {
    return historyData;
}

function getAlgorithmData(alg) {
    return routingData[alg];
}

function getComparisonData() {
    const result = {};
    algorithmFiles.forEach(alg => {
        const d = routingData[alg];
        if (!d) return;
        const gs = d.global_summary;
        result[alg] = {
            name:      algorithmMeta[alg].name,
            abbr:      algorithmMeta[alg].abbr,
            distance:  gs.total_distance_km,
            time:      gs.total_time_minutes,
            vehicles:  gs.total_mobil,
            feasible:  gs.feasible,
            runtime:   gs.total_algorithm_runtime_seconds ?? null,
        };
    });
    return result;
}

/** Count schools in a single SPPG result route (exclude events) */
function countSchools(sppgResult) {
    return sppgResult.route.filter(r => r.school).length;
}

/** Check if a route contains a REFILL event */
function hasRefill(sppgResult) {
    return sppgResult.route.some(r => r.event === 'REFILL');
}
