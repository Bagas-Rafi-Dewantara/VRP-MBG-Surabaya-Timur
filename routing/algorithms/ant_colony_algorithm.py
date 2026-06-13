import os
import json
import random
import math
import sys
import optuna

# Menyembunyikan log default Optuna agar terminal tetap bersih dan mudah dibaca
optuna.logging.set_verbosity(optuna.logging.WARNING)

# Memastikan Python bisa mengimpor constraints.py di folder induk
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, "..")))
from constraints import evaluate_solution

class AntColonyVRP:
    def __init__(self, instance_data, num_ants=20, iterations=50, alpha=1.0, beta=2.0, evap_rate=0.5, q=1000):
        self.instance = instance_data
        self.schools = instance_data["schools"]
        self.distance_matrix = instance_data["distance_matrix"]
        self.time_matrix = instance_data["time_matrix"]
        self.config = instance_data["constraints"]
        
        self.num_schools = len(self.schools)
        self.num_ants = num_ants
        self.iterations = iterations
        self.alpha = alpha
        self.beta = beta
        self.evap_rate = evap_rate
        self.q = q

    def run(self):
        # 1. Penanganan Kasus Khusus (Sekolah < 2)
        if self.num_schools < 2:
            best_sol = [0] if self.num_schools == 1 else []
            best_eval = evaluate_solution(best_sol, self.schools, self.distance_matrix, self.time_matrix, self.config, sppg_name=self.instance["sppg_name"])
            return best_sol, best_eval, []

        # 2. Inisialisasi Pheromone (Tau) dan Visibilitas (Eta) secara linier
        pheromone = [[1.0 for _ in range(self.num_schools)] for _ in range(self.num_schools)]
        eta = [[0.0 for _ in range(self.num_schools)] for _ in range(self.num_schools)]
        
        for i in range(self.num_schools):
            for j in range(self.num_schools):
                if i != j:
                    lat1 = math.radians(self.schools[i]['lat'])
                    lon1 = math.radians(self.schools[i]['lng'])
                    lat2 = math.radians(self.schools[j]['lat'])
                    lon2 = math.radians(self.schools[j]['lng'])
                    
                    dlon = lon2 - lon1
                    dlat = lat2 - lat1
                    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                    jarak_km = (2 * math.asin(math.sqrt(a))) * 6371.0
                    
                    # Semakin dekat jaraknya, visibilitas (eta) semakin besar
                    eta[i][j] = 1.0 / max(jarak_km, 0.001)

        best_sol = []
        best_eval = None
        best_fitness = float('inf')
        convergence = []

        # 3. Looping Utama ACO
        for _ in range(self.iterations):
            ant_solutions = []
            
            for ant in range(self.num_ants):
                # Semut mulai menyusun urutan kunjungan sekolah
                unvisited = list(range(self.num_schools))
                current = random.choice(unvisited)
                seq = [current]
                unvisited.remove(current)
                
                while unvisited:
                    probs = []
                    total_prob = 0.0
                    
                    # Hitung probabilitas pindah ke sekolah selanjutnya
                    for candidate in unvisited:
                        tau = pheromone[current][candidate] ** self.alpha
                        visibilitas = eta[current][candidate] ** self.beta
                        skor = tau * visibilitas
                        probs.append((candidate, skor))
                        total_prob += skor
                        
                    # Pilih sekolah berdasarkan Roulette Wheel Selection
                    rand_val = random.uniform(0, total_prob)
                    cumulative = 0.0
                    next_node = unvisited[-1] 
                    
                    for candidate, skor in probs:
                        cumulative += skor
                        if cumulative >= rand_val:
                            next_node = candidate
                            break
                            
                    seq.append(next_node)
                    unvisited.remove(next_node)
                    current = next_node
                    
                # Evaluasi urutan menggunakan file constraints
                current_eval = evaluate_solution(seq, self.schools, self.distance_matrix, self.time_matrix, self.config, sppg_name=self.instance["sppg_name"])
                current_fitness = current_eval["fitness"]
                
                ant_solutions.append((seq, current_fitness))
                
                # Update pencapaian terbaik global
                if current_fitness < best_fitness:
                    best_fitness = current_fitness
                    best_sol = seq.copy()
                    best_eval = current_eval

            # 4. Penguapan Pheromone (Evaporation)
            for i in range(self.num_schools):
                for j in range(self.num_schools):
                    pheromone[i][j] *= (1.0 - self.evap_rate)
                    
            # 5. Penaburan Pheromone Baru berdasarkan hasil semut iterasi ini
            for seq, fitness in ant_solutions:
                deposit = self.q / max(fitness, 1.0)
                for step in range(len(seq) - 1):
                    dari = seq[step]
                    ke = seq[step + 1]
                    pheromone[dari][ke] += deposit

            convergence.append(best_eval["total_distance_km"])

        return best_sol, best_eval, convergence

def run_optimization(instance_data):
    aco = AntColonyVRP(
        instance_data=instance_data,
        num_ants=25,
        iterations=50,
        alpha=1.0,
        beta=2.0,
        evap_rate=0.5,
        q=1000,
    )
    _, details, convergence = aco.run()
    details["convergence"] = convergence
    return details

if __name__ == "__main__":
    import time # Pastikan modul time di-import
    
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
        print(f"Ditemukan {len(json_files)} cluster SPPG. Menghitung Ant Colony Optimization...")
        
        all_times = []
        final_output = {
            "algorithm": "Ant Colony Optimization (Optuna Tuned)",
            "global_summary": {
                "total_distance_km": 0.0,
                "total_time_minutes": 0.0,
                "total_mobil": 0,
                "total_algorithm_runtime_seconds": 0.0, # 1. TEMPAT PENYIMPANAN RUNTIME GLOBAL
                "feasible": True
            },
            "results_per_sppg": []
        }
        
        for file_name in json_files:
            file_path = os.path.join(instances_dir, file_name)
            
            with open(file_path, 'r') as f:
                instance_data = json.load(f)
            
            sppg_name = instance_data["sppg_name"]
            print(f"-> Memproses rute ACO untuk: {sppg_name}")
            
            # 2. MULAI MENGHITUNG WAKTU KOMPUTASI
            waktu_mulai_algo = time.time()
            
            details = run_optimization(instance_data)
            
            # 3. HENTIKAN PENGHITUNGAN & KALKULASI DURASINYA
            waktu_selesai_algo = time.time()
            runtime_detik = round(waktu_selesai_algo - waktu_mulai_algo, 2)
            
            print(f"      [Runtime] Algoritma selesai dalam {runtime_detik} detik")
            
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

            all_times.append(rute_sppg["time_spent_minutes"])

            final_output["global_summary"]["total_distance_km"] += details["total_distance_km"]
            final_output["global_summary"]["total_mobil"] += 1
            final_output["global_summary"]["total_algorithm_runtime_seconds"] += runtime_detik

            if not details["is_feasible"]:
                final_output["global_summary"]["feasible"] = False

            final_output["results_per_sppg"].append({
                "sppg": sppg_name,
                "algorithm_runtime_seconds": runtime_detik,
                "distance_km": rute_sppg["distance_km"],
                "time_spent_minutes": rute_sppg["time_spent_minutes"],
                "departure_time": rute_sppg["departure_time"],
                "return_time": rute_sppg["return_time"],
                "feasible_time": rute_sppg["feasible_time"],
                "route_order": route_order,
                "route": rute_sppg["route"]
            })

        if all_times:
            final_output["global_summary"]["total_time_minutes"] = round(max(all_times), 2)
                
        final_output["global_summary"]["total_distance_km"] = round(final_output["global_summary"]["total_distance_km"], 2)
        final_output["global_summary"]["total_algorithm_runtime_seconds"] = round(final_output["global_summary"]["total_algorithm_runtime_seconds"], 2)
        
        output_json_path = os.path.join(results_dir, "aco.json")
        with open(output_json_path, 'w') as f:
            json.dump(final_output, f, indent=4)
            
        print(f"\n==============================================")
        print(f"PROSES ANT COLONY OPTIMIZATION SELESAI!")
        print(f"Total Runtime Komputasi: {final_output['global_summary']['total_algorithm_runtime_seconds']} detik")
        print(f"Total Jarak Surabaya Timur: {final_output['global_summary']['total_distance_km']} km")
        print(f"Total Waktu Tempuh: {final_output['global_summary']['total_time_minutes']} menit")
        print(f"File output sukses ditulis ke: {output_json_path}")
        print(f"==============================================")