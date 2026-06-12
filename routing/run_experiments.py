"""
run_experiments.py — Jalankan setiap algoritma N_RUNS kali, catat semua hasil,
hitung best & average, simpan ke routing/results/history.json, dan update
masing-masing {alg}.json dengan solusi terbaik yang ditemukan.
"""

import os
import sys
import json
import time
import glob
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "algorithms"))

from simulated_annealing import run_optimization as sa_run
from genetic_algorithm import run_optimization as ga_run
from particle_swarm_optimization import run_optimization as pso_run
from ant_colony_algorithm import run_optimization as aco_run

N_RUNS = 10
INSTANCES_DIR = os.path.join(current_dir, "dist_matrix")
RESULTS_DIR = os.path.join(current_dir, "results")

ALGORITHMS = [
    ("sa",  "Simulated Annealing",    sa_run),
    ("ga",  "Genetic Algorithm",      ga_run),
    ("pso", "Particle Swarm Opt.",    pso_run),
    ("aco", "Ant Colony Opt.",        aco_run),
]


def build_route_order(sppg_name, route, depot, schools):
    ro = [{"type": "depot", "name": sppg_name,
           "lat": depot["lat"], "lng": depot["lng"]}]
    for stop in route:
        if "school" in stop:
            nama = stop["school"].split(" (")[0]
            for s in schools:
                if s["nama_sekolah"] == nama:
                    ro.append({"type": "school", "name": s["nama_sekolah"],
                               "lat": s["lat"], "lng": s["lng"]})
                    break
    ro.append({"type": "depot", "name": sppg_name,
               "lat": depot["lat"], "lng": depot["lng"]})
    return ro


def run_once(alg_name, run_fn, instances, run_number):
    """Jalankan satu algoritma pada semua instance, kembalikan metrik & data rute lengkap."""
    all_times = []
    total_distance = 0.0
    total_runtime = 0.0
    feasible = True
    results_per_sppg = []

    for instance_data in instances:
        sppg_name = instance_data["sppg_name"]
        t0 = time.time()
        details = run_fn(instance_data)
        runtime = round(time.time() - t0, 3)

        rute = details["single_route_data"]
        total_distance += details["total_distance_km"]
        all_times.append(rute["time_spent_minutes"])
        total_runtime += runtime
        if not details["is_feasible"]:
            feasible = False

        route_order = build_route_order(
            sppg_name, rute["route"],
            instance_data["depot"], instance_data["schools"]
        )

        results_per_sppg.append({
            "sppg": sppg_name,
            "distance_km": rute["distance_km"],
            "time_spent_minutes": rute["time_spent_minutes"],
            "departure_time": rute["departure_time"],
            "return_time": rute["return_time"],
            "feasible_time": rute["feasible_time"],
            "route_order": route_order,
            "route": rute["route"],
        })

    summary = {
        "run": run_number,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "total_distance_km": round(total_distance, 2),
        "total_time_minutes": round(max(all_times), 2) if all_times else 0.0,
        "runtime_seconds": round(total_runtime, 2),
        "feasible": feasible,
    }
    return summary, results_per_sppg


def save_best_alg_json(alg_key, alg_name, best_summary, best_sppg):
    """Tulis ulang {alg}.json dengan solusi terbaik dari eksperimen."""
    output = {
        "algorithm": alg_name,
        "global_summary": {
            "total_distance_km": best_summary["total_distance_km"],
            "total_time_minutes": best_summary["total_time_minutes"],
            "total_algorithm_runtime_seconds": best_summary["runtime_seconds"],
            "total_mobil": len(best_sppg),
            "feasible": best_summary["feasible"],
        },
        "results_per_sppg": best_sppg,
    }
    path = os.path.join(RESULTS_DIR, f"{alg_key}.json")
    with open(path, "w") as f:
        json.dump(output, f, indent=4)
    print(f"   -> {alg_key}.json diupdate dengan run terbaik (run #{best_summary['run']})")


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    instance_files = sorted(glob.glob(os.path.join(INSTANCES_DIR, "instance_*.json")))
    if not instance_files:
        print("Error: Tidak ada instance_*.json di dist_matrix/")
        sys.exit(1)

    instances = []
    for path in instance_files:
        with open(path) as f:
            instances.append(json.load(f))

    print(f"Ditemukan {len(instances)} cluster SPPG.")
    print(f"Menjalankan {N_RUNS} run × {len(ALGORITHMS)} algoritma\n")

    history = {
        "last_updated": datetime.now().isoformat(timespec="seconds"),
        "n_runs": N_RUNS,
        "algorithms": {}
    }

    for alg_key, alg_name, run_fn in ALGORITHMS:
        print(f"{'='*50}")
        print(f"ALGORITMA: {alg_name}")
        print(f"{'='*50}")

        runs_summary = []
        best_summary = None
        best_sppg = None

        for r in range(1, N_RUNS + 1):
            print(f"  Run {r}/{N_RUNS}...", end=" ", flush=True)
            summary, sppg_data = run_once(alg_key, run_fn, instances, r)
            runs_summary.append(summary)

            print(f"{summary['total_distance_km']:.2f} km | "
                  f"{summary['total_time_minutes']:.1f} mnt | "
                  f"{summary['runtime_seconds']:.2f} dtk | "
                  f"{'OK' if summary['feasible'] else 'INFEASIBLE'}")

            if best_summary is None or summary["total_distance_km"] < best_summary["total_distance_km"]:
                best_summary = summary
                best_sppg = sppg_data

        distances = [r["total_distance_km"] for r in runs_summary]
        times     = [r["total_time_minutes"] for r in runs_summary]
        runtimes  = [r["runtime_seconds"] for r in runs_summary]

        average = {
            "total_distance_km": round(sum(distances) / N_RUNS, 2),
            "total_time_minutes": round(sum(times) / N_RUNS, 2),
            "runtime_seconds":   round(sum(runtimes) / N_RUNS, 2),
        }

        history["algorithms"][alg_key] = {
            "name": alg_name,
            "runs": runs_summary,
            "best": best_summary,
            "average": average,
        }

        print(f"  Best : {best_summary['total_distance_km']:.2f} km (run #{best_summary['run']})")
        print(f"  Avg  : {average['total_distance_km']:.2f} km\n")

        save_best_alg_json(alg_key, alg_name, best_summary, best_sppg)

    history_path = os.path.join(RESULTS_DIR, "history.json")
    with open(history_path, "w") as f:
        json.dump(history, f, indent=4)

    print(f"\nHistory tersimpan di: {history_path}")
    print("Selesai.")


if __name__ == "__main__":
    main()
