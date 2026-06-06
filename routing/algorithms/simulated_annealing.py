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
    def __init__(self, instance_data, initial_temp=1000, cooling_rate=0.98, max_iter_per_temp=100, stopping_temp=0.01):
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

    def create_initial_solution(self):
        # Membuat solusi awal berupa urutan acak indeks sekolah (0 sampai N-1)
        solution = list(range(self.num_schools))
        random.shuffle(solution)
        return solution

    def get_neighbor(self, solution):
        # Membuat solusi tetangga (perturbation) dengan menukar posisi 2 sekolah secara acak (Swap Mechanism)
        neighbor = solution.copy()
        idx1, idx2 = random.sample(range(self.num_schools), 2)
        neighbor[idx1], neighbor[idx2] = neighbor[idx2], neighbor[idx1]
        return neighbor

    def run(self):
        # 1. Inisialisasi solusi awal
        current_sol = self.create_initial_solution()
        current_eval = evaluate_solution(current_sol, self.schools, self.distance_matrix, self.time_matrix, self.config)
        current_fitness = current_eval["fitness"]
        
        # Catat solusi terbaik mutlak sepanjang masa
        best_sol = current_sol.copy()
        best_eval = current_eval
        best_fitness = current_fitness
        
        # Set temperatur awal
        temp = self.initial_temp
        
        # 2. Looping SA (Selama belum dingin)
        while temp > self.stopping_temp:
            for _ in range(self.max_iter_per_temp):
                # Ambil tetangga baru (acak urutan sedikit)
                neighbor_sol = self.get_neighbor(current_sol)
                neighbor_eval = evaluate_solution(neighbor_sol, self.schools, self.distance_matrix, self.time_matrix, self.config)
                neighbor_fitness = neighbor_eval["fitness"]
                
                # Hitung selisih cost/fitness (Delta E)
                # Ingat: Kita ingin meminimasi Jarak, jadi makin kecil fitness makin bagus
                delta_energy = neighbor_fitness - current_fitness
                
                # 3. Kriteria Penerimaan Solusi
                if delta_energy < 0:
                    # Jika rute baru lebih pendek/bagus, langsung terima!
                    current_sol = neighbor_sol
                    current_fitness = neighbor_fitness
                    current_eval = neighbor_eval
                    
                    # Update jika ini adalah rute terbaik mutlak baru
                    if neighbor_fitness < best_fitness:
                        best_sol = neighbor_sol.copy()
                        best_fitness = neighbor_fitness
                        best_eval = neighbor_eval
                else:
                    # Jika rute baru ternyata lebih jelek, hitung peluang berdasarkan Kriteria Metropolis
                    # Makin dingin suhunya (temp mengecil), peluang menerima solusi buruk makin kecil
                    acceptance_probability = math.exp(-delta_energy / temp)
                    
                    if random.random() < acceptance_probability:
                        # Terima solusi buruk demi mengeksplorasi jalur lain (keluar dari jebakan lokal)
                        current_sol = neighbor_sol
                        current_fitness = neighbor_fitness
                        current_eval = neighbor_eval
            
            # 4. Cooling Schedule: Turunkan suhu secara geometris
            temp *= self.cooling_rate
            
        return best_sol, best_eval

def run_optimization(instance_data):
    """
    Fungsi standard penyeragaman antar teman kelompok.
    Fungsi ini yang akan dipanggil oleh main.py atau web backend nantinya.
    """
    sa = SimulatedAnnealingVRP(
        instance_data=instance_data,
        initial_temp=1500,
        cooling_rate=0.95,
        max_iter_per_temp=80,
        stopping_temp=0.01
    )
    best_seq, details = sa.run()
    return details

# --- Area Uji Coba Mandiri Bagianmu ---
if __name__ == "__main__":
    results_dir = os.path.abspath(os.path.join(current_dir, "../results"))
    
    # Cari file instance JSON hasil build_instance.py kemarin
    json_files = [f for f in os.listdir(results_dir) if f.startswith("instance_")]
    
    if not json_files:
        print("Error: Tidak ditemukan file instance_*.json di folder 'results'.")
        print("Pastikan kamu sudah menjalankan build_instance.py terlebih dahulu!")
    else:
        # Kita uji coba pakai file instance pertama yang ketemu
        test_file = os.path.join(results_dir, json_files[0])
        print(f"=== Mengetes Simulated Annealing pada file: {json_files[0]} ===")
        
        with open(test_file, 'r') as f:
            data_sppg = json.load(f)
            
        # Jalankan optimasi
        hasil_rute = run_optimization(data_sppg)
        
        print("\n=== HASIL SIMULATED ANNEALING KAMU ===")
        print(f"SPPG Pelayan : {data_sppg['sppg_name']}")
        print(f"Total Jarak  : {hasil_rute['total_distance_km']:.2f} km")
        print(f"Total Waktu  : {hasil_rute['total_time_minutes']:.2f} menit")
        print(f"Status Rute  : {'LAYAK (Feasible)' if hasil_rute['is_feasible'] else 'TIDAK LAYAK (Melanggar Waktu)'}")
        print("\nPembagian Rute Mobil Box (0 = Depot):")
        for i, armada in enumerate(hasil_rute['routes']):
            print(f"  Mobil {i+1}: {armada}")