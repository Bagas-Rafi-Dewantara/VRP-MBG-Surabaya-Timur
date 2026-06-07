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

Distribution starts at: 08:00 AM
Deadline:11:00 AM
Maximum operational duration:180 minutes

### Service Time
Loading/unloading time per school: 10 minutes

### Vehicle Speed
Constant vehicle speed: 40 km/hour
Travel time is calculated using:
Travel Time (minutes) = Distance (km) / 40 × 60

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
│   └── results/
│
├── web/
│
├── README.md
└── requirements.txt
```

## Optimization Algorithms

Implemented:

* Simulated Annealing (SA)

Planned:

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

Izzuddin Hammadi Faiz   (5026231018)
Bagas Rafi Dewantara    (5026231091)
Raffi Deva Anargya      (5026231104)
Abdul Ghoni             (5026231109)

Information Systems Department
Institut Teknologi Sepuluh Nopember (ITS)
2026
