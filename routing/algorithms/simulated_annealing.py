import os
import json
import random
import math
import sys

# Supaya Python bisa mengimpor constraints.py di folder induk (routing/)
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, "..")))
from constraints import evaluate_solution

class SimulatedAnnealingVRP:
    def __init__(self, instance_data, initial_temp=500, cooling_rate=0.98, max_iter_per_temp=100, stopping_temp=0.01):
        self.instance = instance_data
        self.schools = instance_data["schools"]
        self.distance_matrix = instance_data["distance_matrix"]
        self.time_matrix = instance_data["time_matrix"]
        self.config = instance_data["constraints"]
        
        self.num_schools = len(self.schools)
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.max_iter_per_temp = max_iter_per_temp
        self.stopping_temp = stopping_temp
        self.convergence_history = []

    def create_initial_solution(self):
        # Membuat solusi awal berupa urutan acak indeks sekolah (0 sampai N-1)
        solution = list(range(self.num_schools))
        random.shuffle(solution)
        return solution

    def get_neighbor(self, solution):
        # Jika sekolah kurang dari 2, tidak ada yang bisa ditukar (Swap)
        if self.num_schools < 2:
            return solution.copy()
            
        # Membuat solusi tetangga (perturbation) dengan menukar posisi 2 sekolah secara acak
        neighbor = solution.copy()
        idx1, idx2 = random.sample(range(self.num_schools), 2)
        neighbor[idx1], neighbor[idx2] = neighbor[idx2], neighbor[idx1]
        return neighbor

    def run(self):
        # 1. Inisialisasi solusi awal
        current_sol = self.create_initial_solution()
        
        # TAMBAHKAN PARAMETER sppg_name DI UJUNG SINI
        current_eval = evaluate_solution(current_sol, self.schools, self.distance_matrix, self.time_matrix, self.config, sppg_name=self.instance["sppg_name"])
        current_fitness = current_eval["fitness"]
        
        best_sol = current_sol.copy()
        best_eval = current_eval
        best_fitness = current_fitness
        
        if self.num_schools < 2:
            return best_sol, best_eval
            
        temp = self.initial_temp
        
        # 2. Looping SA
        while temp > self.stopping_temp:
            for _ in range(self.max_iter_per_temp):
                neighbor_sol = self.get_neighbor(current_sol)
                
                # TAMBAHKAN PARAMETER sppg_name DI UJUNG SINI JUGA
                neighbor_eval = evaluate_solution(neighbor_sol, self.schools, self.distance_matrix, self.time_matrix, self.config, sppg_name=self.instance["sppg_name"])
                neighbor_fitness = neighbor_eval["fitness"]
                
                delta_energy = neighbor_fitness - current_fitness
                
                if delta_energy < 0:
                    current_sol = neighbor_sol
                    current_fitness = neighbor_fitness
                    current_eval = neighbor_eval
                    
                    if neighbor_fitness < best_fitness:
                        best_sol = neighbor_sol.copy()
                        best_fitness = neighbor_fitness
                        best_eval = neighbor_eval
                else:
                    acceptance_probability = math.exp(-delta_energy / temp)
                    if random.random() < acceptance_probability:
                        current_sol = neighbor_sol
                        current_fitness = neighbor_fitness
                        current_eval = neighbor_eval
            
            self.convergence_history.append(best_fitness)
            temp *= self.cooling_rate
            
        best_eval["convergence"] = self.convergence_history
        return best_sol, best_eval

def run_optimization(instance_data):
    """
    Menjalankan Simulated Annealing yang sudah di-tuning agar cepat (Fast-SA)
    """
    sa = SimulatedAnnealingVRP(
        instance_data=instance_data,
        initial_temp=50,        # Diturunkan dari 1500 ke 100 (sudah cukup untuk VRP skala kecil)
        cooling_rate=0.90,        # Dipercepat penurunannya dari 0.98 ke 0.90
        max_iter_per_temp=50,     # Dikurangi dari 100 ke 30 iterasi per langkah suhu
        stopping_temp=0.1         # Dinaikkan dari 0.01 ke 0.1
    )
    best_seq, details = sa.run()
    return details

if __name__ == "__main__":
    import time
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
        print(f"Ditemukan {len(json_files)} cluster SPPG. Menghitung Simulated Annealing...")
        
        all_times = []
        # Objek utama sesuai arsitektur ideal VRP
        final_output = {
            "algorithm": "Simulated Annealing",
            "global_summary": {
            "total_distance_km": 0.0,
            "total_time_minutes": 0.0,
            "total_algorithm_runtime_seconds": 0.0,
            "total_mobil": 0,
            "total_algorithm_runtime_seconds": 0.0,
            "feasible": True
        
        },
        "convergence": [],
        "results_per_sppg": []
        }
        
        for file_name in json_files:
            file_path = os.path.join(instances_dir, file_name)
            
            with open(file_path, 'r') as f:
                instance_data = json.load(f)
            
            sppg_name = instance_data["sppg_name"]
            print(f"-> Memproses rute untuk: {sppg_name}")
            
            waktu_mulai_algo = time.time()
            # Jalankan optimasi SA Fast-Tuning
            details = run_optimization(instance_data)
            if not final_output["convergence"]:
                final_output["convergence"] = details["convergence"]
            rute_sppg = details["single_route_data"]
            route_order = []

            # Depot awal
            route_order.append({
                "type": "depot",
                "name": sppg_name,
                "lat": instance_data["depot"]["lat"],
                "lng": instance_data["depot"]["lng"]
            })

            for stop in rute_sppg["route"]:

                if "school" not in stop:
                    continue

                nama_sekolah = stop["school"].split(" (")[0]

                for school in instance_data["schools"]:

                    if school["nama_sekolah"] == nama_sekolah:

                        route_order.append({
                            "type": "school",
                            "name": school["nama_sekolah"],
                            "lat": school["lat"],
                            "lng": school["lng"]
                        })

                        break

            # Depot akhir
            route_order.append({
                "type": "depot",
                "name": sppg_name,
                "lat": instance_data["depot"]["lat"],
                "lng": instance_data["depot"]["lng"]
            })
            all_times.append(
                rute_sppg["time_spent_minutes"]
            )
            waktu_selesai_algo = time.time()
            runtime_detik = round(waktu_selesai_algo - waktu_mulai_algo, 2)           
            
            # Akumulasikan ke Global Summary
            final_output["global_summary"]["total_distance_km"] += details["total_distance_km"]
            final_output["global_summary"]["total_algorithm_runtime_seconds"] += runtime_detik   
            # Asumsi total waktu operasional adalah akumulasi seluruh mobil yang jalan berseri/paralel
            final_output["global_summary"]["total_mobil"] += 1 # 1 SPPG dihandle 1 mobil (atau disesuaikan rute)
            
            if not details["is_feasible"]:
                final_output["global_summary"]["feasible"] = False
            
            # Masukkan detail ke list per SPPG
            final_output["results_per_sppg"].append({
                "sppg": sppg_name,
                "distance_km": rute_sppg["distance_km"],
                "time_spent_minutes": rute_sppg["time_spent_minutes"],
                "departure_time": rute_sppg["departure_time"],
                "return_time": rute_sppg["return_time"],
                "feasible_time": rute_sppg["feasible_time"],
                "route_order": route_order,
                "route": rute_sppg["route"]
            })

        if all_times:
            final_output["global_summary"]["total_time_minutes"] = round(
            max(all_times),
            2
        )
                
        # Pembulatan angka akhir global
        final_output["global_summary"]["total_distance_km"] = round(final_output["global_summary"]["total_distance_km"], 2)
        
        # Simpan hasil akhir kompilasi menjadi sa.json
        output_json_path = os.path.join(results_dir, "sa.json")
        with open(output_json_path, 'w') as f:
            json.dump(final_output, f, indent=4)
            
        print(f"\n==============================================")
        print(f"PROSES SIMULATED ANNEALING SELESAI!")
        print(f"File output sukses ditulis ke: {output_json_path}")
        print(f"Total Jarak Surabaya Timur: {final_output['global_summary']['total_distance_km']} km")
        print(f"==============================================")