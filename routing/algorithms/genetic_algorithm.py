import os
import json
import random
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, "..")))
from constraints import evaluate_solution

POPULATION_SIZE = 50
MAX_GENERATIONS = 200
CROSSOVER_RATE = 0.85
MUTATION_RATE = 0.15
TOURNAMENT_K = 3
ELITE_SIZE = 2
PATIENCE = 30


def _fitness(sequence, instance):
    return evaluate_solution(
        sequence,
        instance["schools"],
        instance["distance_matrix"],
        instance["time_matrix"],
        instance["constraints"],
        sppg_name=instance["sppg_name"],
    )


def _tournament_select(population, fitnesses):
    candidates = random.sample(range(len(population)), TOURNAMENT_K)
    best = min(candidates, key=lambda i: fitnesses[i])
    return population[best]


def _order_crossover(parent1, parent2):
    n = len(parent1)
    a, b = sorted(random.sample(range(n), 2))
    child = [None] * n
    child[a:b+1] = parent1[a:b+1]
    segment = set(child[a:b+1])
    fill = [x for x in parent2 if x not in segment]
    ptr = 0
    for i in range(n):
        if child[i] is None:
            child[i] = fill[ptr]
            ptr += 1
    return child


def _swap_mutate(sequence):
    mutant = sequence.copy()
    i, j = random.sample(range(len(mutant)), 2)
    mutant[i], mutant[j] = mutant[j], mutant[i]
    return mutant


class GeneticAlgorithmVRP:
    def __init__(self, instance_data):
        self.instance = instance_data
        self.n = len(instance_data["schools"])

    def run(self):
        # Edge case: 0 or 1 school — no optimization needed
        if self.n == 0:
            return evaluate_solution([], self.instance["schools"], self.instance["distance_matrix"],
                                     self.instance["time_matrix"], self.instance["constraints"],
                                     sppg_name=self.instance["sppg_name"])
        if self.n == 1:
            seq = [0]
            return _fitness(seq, self.instance)

        # Initialize population
        population = [list(range(self.n)) for _ in range(POPULATION_SIZE)]
        for chrom in population:
            random.shuffle(chrom)

        fitnesses = [_fitness(c, self.instance)["fitness"] for c in population]

        best_idx = min(range(POPULATION_SIZE), key=lambda i: fitnesses[i])
        best_seq = population[best_idx].copy()
        best_fitness = fitnesses[best_idx]
        best_eval = _fitness(best_seq, self.instance)

        no_improve = 0

        for _ in range(MAX_GENERATIONS):
            # Elitism: carry top ELITE_SIZE individuals unchanged
            elite_indices = sorted(range(POPULATION_SIZE), key=lambda i: fitnesses[i])[:ELITE_SIZE]
            new_population = [population[i].copy() for i in elite_indices]

            while len(new_population) < POPULATION_SIZE:
                p1 = _tournament_select(population, fitnesses)
                p2 = _tournament_select(population, fitnesses)

                if self.n >= 2 and random.random() < CROSSOVER_RATE:
                    child = _order_crossover(p1, p2)
                else:
                    child = p1.copy()

                if self.n >= 2 and random.random() < MUTATION_RATE:
                    child = _swap_mutate(child)

                new_population.append(child)

            population = new_population
            fitnesses = [_fitness(c, self.instance)["fitness"] for c in population]

            gen_best_idx = min(range(POPULATION_SIZE), key=lambda i: fitnesses[i])
            if fitnesses[gen_best_idx] < best_fitness:
                best_fitness = fitnesses[gen_best_idx]
                best_seq = population[gen_best_idx].copy()
                best_eval = _fitness(best_seq, self.instance)
                no_improve = 0
            else:
                no_improve += 1
                if no_improve >= PATIENCE:
                    break

        return best_eval


if __name__ == "__main__":
    routing_dir = os.path.abspath(os.path.join(current_dir, ".."))
    instances_dir = os.path.join(routing_dir, "dist_matrix")
    results_dir = os.path.join(routing_dir, "results")

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    if not os.path.exists(instances_dir):
        print(f"Error: Folder {instances_dir} tidak ditemukan.")
        sys.exit()

    json_files = [f for f in os.listdir(instances_dir) if f.startswith("instance_") and f.endswith(".json")]

    if not json_files:
        print("Error: Tidak ditemukan file instance_*.json di folder 'dist_matrix'.")
    else:
        print(f"Ditemukan {len(json_files)} cluster SPPG. Menghitung Genetic Algorithm...")

        final_output = {
            "algorithm": "Genetic Algorithm",
            "global_summary": {
                "total_distance_km": 0.0,
                "total_time_minutes": 0.0,
                "total_mobil": 0,
                "feasible": True
            },
            "results_per_sppg": []
        }

        for file_name in sorted(json_files):
            file_path = os.path.join(instances_dir, file_name)

            with open(file_path, "r") as f:
                instance_data = json.load(f)

            sppg_name = instance_data["sppg_name"]
            n_schools = len(instance_data["schools"])
            print(f"-> Memproses rute untuk: {sppg_name} ({n_schools} sekolah)")

            ga = GeneticAlgorithmVRP(instance_data)
            details = ga.run()
            rute_sppg = details["single_route_data"]

            final_output["global_summary"]["total_distance_km"] += details["total_distance_km"]
            final_output["global_summary"]["total_time_minutes"] += rute_sppg["time_spent_minutes"]
            final_output["global_summary"]["total_mobil"] += 1

            if not details["is_feasible"]:
                final_output["global_summary"]["feasible"] = False

            final_output["results_per_sppg"].append({
                "sppg": sppg_name,
                "distance_km": rute_sppg["distance_km"],
                "time_spent_minutes": rute_sppg["time_spent_minutes"],
                "departure_time": rute_sppg["departure_time"],
                "return_time": rute_sppg["return_time"],
                "feasible_time": rute_sppg["feasible_time"],
                "route": rute_sppg["route"]
            })

        final_output["global_summary"]["total_distance_km"] = round(final_output["global_summary"]["total_distance_km"], 2)
        final_output["global_summary"]["total_time_minutes"] = round(final_output["global_summary"]["total_time_minutes"], 2)

        output_json_path = os.path.join(results_dir, "ga.json")
        with open(output_json_path, "w") as f:
            json.dump(final_output, f, indent=4)

        print(f"\n==============================================")
        print(f"PROSES GENETIC ALGORITHM SELESAI!")
        print(f"File output sukses ditulis ke: {output_json_path}")
        print(f"Total Jarak Surabaya Timur: {final_output['global_summary']['total_distance_km']} km")
        print(f"==============================================")
