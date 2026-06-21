# VRP-MBG-Surabaya-Timur
Vehicle Routing Problem (VRP) Optimization for the Indonesian Free Nutritious Meal Program (Makan Bergizi Gratis / MBG) in East Surabaya using Soft Computing algorithms.

## Overview
This project aims to optimize food distribution routes from SPPG (Satuan Pelayanan Pemenuhan Gizi) facilities to public schools in East Surabaya.

The system consists of:
* School data scraping from OpenStreetMap (OSM)
* SPPG data scraping from the official BGN website
* School-to-SPPG clustering
* Vehicle Routing Problem (VRP) instance generation
* Route optimization using Soft Computing algorithms
* Interactive web-based route visualization

## Study Area
East Surabaya Districts:
* Gubeng
* Gunung Anyar
* Mulyorejo
* Rungkut
* Sukolilo
* Tambaksari
* Tenggilis Mejoyo

## Dataset

### Schools
Source: OpenStreetMap (Overpass API)
Attributes:
* School Name
* Education Level
* Number of Students
* Latitude
* Longitude
* District

### SPPG
Source: Badan Gizi Nasional (BGN)
Attributes:
* SPPG Name
* Address
* Latitude
* Longitude
* District

### Clustered Data
Each school is assigned to its nearest feasible SPPG while considering service capacity balancing.

## Constraints

### Vehicle Capacity Constraint
Maximum vehicle capacity: 1050 trays
If the next school causes the vehicle load to exceed 1050 trays, the vehicle must:
1. Return to SPPG
2. Refill the load
3. Continue delivery

### Time Constraint
- Distribution starts at: 08:00 AM
- Deadline: 11:00 AM
- Maximum operational duration: 180 minutes

### Service Time
Loading/unloading time per school: 10 minutes

### Vehicle Speed
- Constant vehicle speed: 40 km/hour
- Travel time is calculated using:
- Travel Time (minutes) = Distance (km) / 40 × 60

## Project Structure
```text
VRP-MBG-Surabaya-Timur
│
├── scraping/
├── clustering/
├── data/
├── routing/
│   ├── algorithms/
│   ├── dist_matrix/
│   ├── results/
│   ├── build_instance.py
│   ├── constraints.py
│   ├── osrm_matrix.py
│   └── run_experiments.py
│
├── web/
│
├── README.md
└── requirements.txt
```

## Optimization Algorithms
Implemented:
* Simulated Annealing (SA)
* Genetic Algorithm (GA)
* Particle Swarm Optimization (PSO)
* Ant Colony Optimization (ACO)

## Workflow
```text
Data Scraping
      ↓
School-SPPG Clustering
      ↓
VRP Instance Generation
      ↓
Distance Matrix Construction
      ↓
Route Optimization
      ↓
Performance Evaluation
      ↓
Web Visualization
```

## How to Run

### 1. Prerequisites
* Python 3.9 or higher
* pip

### 2. Clone & Install Dependencies
```bash
git clone https://github.com/<your-org>/VRP-MBG-Surabaya-Timur.git
cd VRP-MBG-Surabaya-Timur
pip install -r requirements.txt
```

### 3. Data Scraping
Scrape school data from OpenStreetMap and SPPG data from BGN. This step can take a while due to API rate limiting and reverse geocoding validation.
```bash
python scraping/scrap_sekolah_surabaya_timur.py
python scraping/scrap_sppg_surabaya_timur.py
```
Output: `data/sekolah_surabaya_timur.csv` and `data/sppg_surabaya_timur.csv`

### 4. School-to-SPPG Clustering
Assigns each school to its nearest feasible SPPG while balancing service load.
```bash
python clustering/cluster.py
```
Output: `data/clustered_data.csv`

### 5. Build Distance & Time Matrix (OSRM)
Computes real road-network distance and travel time between depot and schools using the Open Source Routing Machine (OSRM) API.
```bash
python routing/osrm_matrix.py
```
Output: distance/time matrices used as input for VRP instance generation.

### 6. Build VRP Instances
Generates one JSON instance per SPPG cluster containing schools, depot, distance matrix, time matrix, and constraints (defined in `routing/constraints.py`).
```bash
python routing/build_instance.py
```
Output: `routing/dist_matrix/instance_*.json` (one file per SPPG cluster)

### 7. Run Route Optimization
Run each algorithm individually — each produces its own result file in `routing/results/`.
```bash
python routing/algorithms/sa.py     # Simulated Annealing  → results/sa.json
python routing/algorithms/ga.py     # Genetic Algorithm     → results/ga.json
python routing/algorithms/pso.py    # Particle Swarm Opt.   → results/pso.json
python routing/algorithms/aco.py    # Ant Colony Opt.       → results/aco.json
```

Alternatively, run all four algorithms across multiple trials (for performance comparison and convergence analysis) using:
```bash
python routing/run_experiments.py
```
This runs each algorithm N times (default 10), records best/average distance, runtime, and convergence curves, and saves the aggregated results to `routing/results/history.json`.

### 8. Launch the Web Dashboard
Serve the `web/` directory using a local HTTP server (required for the dashboard to fetch JSON results):
```bash
python3 -m http.server 8000
```
Then open in your browser:
```
http://localhost:8000/web/index.html
```

The dashboard provides:
* Interactive route map per SPPG cluster
* Algorithm comparison charts (distance, time, runtime)
* Per-SPPG result table
* Experiment history & convergence chart

## Output
Each optimization algorithm generates a JSON result containing:
* Total distance
* Total travel time
* Route sequence
* Delivery schedule
* Feasibility status

Example:
```json
{
  "algorithm": "Simulated Annealing",
  "global_summary": {
    "total_distance_km": 413.95,
    "total_time_minutes": 174.21,
    "total_mobil": 47,
    "feasible": true
  }
}
```

## Future Development
* Multi-Vehicle VRP
* Dynamic Traffic Integration
* Real-Time Route Reoptimization
* Interactive Dashboard
* Comparative Analysis of Soft Computing Algorithms

## Authors
* Izzuddin Hammadi Faiz   (5026231018)
* Bagas Rafi Dewantara    (5026231091)
* Raffi Deva Anargya      (5026231104)
* Abdul Ghoni             (5026231109)

Information Systems Department
Institut Teknologi Sepuluh Nopember (ITS)
2026
