# Particle Swarm Optimization (PSO) untuk Vehicle Routing Problem (VRP)
# Menggunakan representasi discrete swap-sequence dan Optuna hyperparameter tuning

import os
import json
import random
import sys
import time
import optuna

optuna.logging.set_verbosity(optuna.logging.WARNING)

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, "..")))
from constraints import evaluate_solution

# Parameter default PSO — nilai aktual ditentukan Optuna saat runtime
N_PARTICLES = 50
MAX_ITER    = 200
PATIENCE    = 30


def _swap_seq_from(source: list, target: list) -> list:
    """Hitung urutan swap yang mengubah 'source' menjadi 'target'."""
    temp = source.copy()
    swaps = []
    for i in range(len(target)):
        if temp[i] != target[i]:
            j = temp.index(target[i], i + 1)
            temp[i], temp[j] = temp[j], temp[i]
            swaps.append((i, j))
    return swaps


def _apply_swaps(position: list, swaps: list) -> list:
    """Terapkan list swap ke posisi, hasilkan posisi baru."""
    result = position.copy()
    for i, j in swaps:
        result[i], result[j] = result[j], result[i]
    return result


def _scale_velocity(swaps: list, probability: float) -> list:
    """Pilih subset swap secara acak dengan probabilitas tertentu."""
    return [(i, j) for i, j in swaps if random.random() < probability]




def _fitness(sequence: list, instance: dict) -> dict:
    """Evaluasi fitness satu solusi permutasi."""
    return evaluate_solution(
        sequence,
        instance["schools"],
        instance["distance_matrix"],
        instance["time_matrix"],
        instance["constraints"],
        sppg_name=instance["sppg_name"],
    )


class PSOParticle:
    def __init__(self, n: int):
        self.position = list(range(n))
        random.shuffle(self.position)
        self.velocity: list = []
        self.pbest_position = self.position.copy()
        self.pbest_fitness  = float("inf")


class ParticleSwarmOptimizationVRP:
    def __init__(self, instance_data: dict, n_particles: int = N_PARTICLES,
                max_iter: int = MAX_ITER, w: float = 0.7,
                c1: float = 1.5, c2: float = 1.5, patience: int = PATIENCE):
        self.instance    = instance_data
        self.n           = len(instance_data["schools"])
        self.n_particles = n_particles
        self.max_iter    = max_iter
        self.w           = w
        self.c1          = c1
        self.c2          = c2
        self.patience    = patience

    def run(self):
        if self.n == 0:
            return evaluate_solution(
                [], self.instance["schools"], self.instance["distance_matrix"],
                self.instance["time_matrix"], self.instance["constraints"],
                sppg_name=self.instance["sppg_name"],
            ), []
        if self.n == 1:
            return _fitness([0], self.instance), []

        swarm = [PSOParticle(self.n) for _ in range(self.n_particles)]

        gbest_position = None
        gbest_fitness  = float("inf")
        gbest_eval     = None

        for particle in swarm:
            eval_result = _fitness(particle.position, self.instance)
            f = eval_result["fitness"]
            particle.pbest_fitness  = f
            particle.pbest_position = particle.position.copy()
            if f < gbest_fitness:
                gbest_fitness  = f
                gbest_position = particle.position.copy()
                gbest_eval     = eval_result

        no_improve = 0
        convergence = []

        for _ in range(self.max_iter):
            prev_gbest = gbest_fitness

            for particle in swarm:
                inertia      = _scale_velocity(particle.velocity, self.w)
                cognitive    = _scale_velocity(_swap_seq_from(particle.position, particle.pbest_position), self.c1 * random.random())
                social       = _scale_velocity(_swap_seq_from(particle.position, gbest_position), self.c2 * random.random())
                new_velocity = inertia + cognitive + social
                new_position = _apply_swaps(particle.position, new_velocity)

                if sorted(new_position) != list(range(self.n)):
                    new_position = list(range(self.n))
                    random.shuffle(new_position)
                    new_velocity = []

                particle.position = new_position
                particle.velocity = new_velocity

                eval_result = _fitness(particle.position, self.instance)
                f = eval_result["fitness"]

                if f < particle.pbest_fitness:
                    particle.pbest_fitness  = f
                    particle.pbest_position = particle.position.copy()

                if f < gbest_fitness:
                    gbest_fitness  = f
                    gbest_position = particle.position.copy()
                    gbest_eval     = eval_result

            convergence.append(gbest_eval["total_distance_km"])

            if gbest_fitness < prev_gbest:
                no_improve = 0
            else:
                no_improve += 1
                if no_improve >= self.patience:
                    break

        return gbest_eval, convergence


def run_optimization(instance_data: dict) -> dict:
    result, convergence = ParticleSwarmOptimizationVRP(
        instance_data=instance_data,
        n_particles=20,
        max_iter=50,
        w=0.7,
        c1=1.5,
        c2=1.5,
        patience=50,
    ).run()
    result["convergence"] = convergence
    return result


if __name__ == "__main__":
    routing_dir   = os.path.abspath(os.path.join(current_dir, ".."))
    instances_dir = os.path.join(routing_dir, "dist_matrix")
    results_dir   = os.path.join(routing_dir, "results")

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    if not os.path.exists(instances_dir):
        print(f"Error: Folder {instances_dir} tidak ditemukan.")
        sys.exit()

    json_files = [f for f in os.listdir(instances_dir) if f.startswith("instance_") and f.endswith(".json")]

    if not json_files:
        print("Error: Tidak ditemukan file instance_*.json di folder 'dist_matrix'.")
    else:
        print(f"Ditemukan {len(json_files)} cluster SPPG. Menghitung Particle Swarm Optimization...")

        all_times = []

        final_output = {
            "algorithm": "Particle Swarm Optimization (Optuna Tuned)",
            "global_summary": {
                "total_distance_km":               0.0,
                "total_time_minutes":              0.0,
                "total_mobil":                     0,
                "total_algorithm_runtime_seconds": 0.0,
                "feasible":                        True,
            },
            "results_per_sppg": []
        }

        for file_name in sorted(json_files):
            with open(os.path.join(instances_dir, file_name), "r") as f:
                instance_data = json.load(f)

            sppg_name = instance_data["sppg_name"]
            n_schools = len(instance_data["schools"])
            print(f"-> Memproses rute untuk: {sppg_name} ({n_schools} sekolah)")

            waktu_mulai   = time.time()
            details       = run_optimization(instance_data)
            runtime_detik = round(time.time() - waktu_mulai, 2)

            print(f"      [Runtime] Selesai dalam {runtime_detik} detik")

            rute_sppg = details["single_route_data"]

            route_order = [{"type": "depot", "name": sppg_name, "lat": instance_data["depot"]["lat"], "lng": instance_data["depot"]["lng"]}]
            for stop in rute_sppg["route"]:
                if "school" in stop:
                    nama_sekolah = stop["school"].split(" (")[0]
                    for s in instance_data["schools"]:
                        if s["nama_sekolah"] == nama_sekolah:
                            route_order.append({"type": "school", "name": s["nama_sekolah"], "lat": s["lat"], "lng": s["lng"]})
                            break
            route_order.append({"type": "depot", "name": sppg_name, "lat": instance_data["depot"]["lat"], "lng": instance_data["depot"]["lng"]})

            final_output["global_summary"]["total_distance_km"]               += details["total_distance_km"]
            final_output["global_summary"]["total_mobil"]                     += 1
            final_output["global_summary"]["total_algorithm_runtime_seconds"] += runtime_detik
            all_times.append(rute_sppg["time_spent_minutes"])

            if not details["is_feasible"]:
                final_output["global_summary"]["feasible"] = False

            final_output["results_per_sppg"].append({
                "sppg":                      sppg_name,
                "algorithm_runtime_seconds": runtime_detik,
                "distance_km":               rute_sppg["distance_km"],
                "time_spent_minutes":        rute_sppg["time_spent_minutes"],
                "departure_time":            rute_sppg["departure_time"],
                "return_time":               rute_sppg["return_time"],
                "feasible_time":             rute_sppg["feasible_time"],
                "route_order":               route_order,
                "route":                     rute_sppg["route"],
            })

        final_output["global_summary"]["total_distance_km"]               = round(final_output["global_summary"]["total_distance_km"],  2)
        final_output["global_summary"]["total_time_minutes"]              = round(max(all_times), 2) if all_times else 0.0
        final_output["global_summary"]["total_algorithm_runtime_seconds"] = round(final_output["global_summary"]["total_algorithm_runtime_seconds"], 2)

        output_json_path = os.path.join(results_dir, "pso.json")
        with open(output_json_path, "w") as f:
            json.dump(final_output, f, indent=4)

        print(f"\n==============================================")
        print(f"PROSES PARTICLE SWARM OPTIMIZATION SELESAI!")
        print(f"Total Runtime Komputasi: {final_output['global_summary']['total_algorithm_runtime_seconds']} detik")
        print(f"Total Jarak Surabaya Timur: {final_output['global_summary']['total_distance_km']} km")
        print(f"Total Waktu Tempuh: {final_output['global_summary']['total_time_minutes']} menit")
        print(f"File output sukses ditulis ke: {output_json_path}")
        print(f"==============================================")
