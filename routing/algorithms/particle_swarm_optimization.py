import os
import json
import random
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(current_dir, "..")))
from constraints import evaluate_solution

# ============================================================
# PARAMETER PSO
# ============================================================
N_PARTICLES    = 50    # Jumlah partikel dalam swarm
MAX_ITER       = 200   # Maksimum iterasi
W              = 0.7   # Inertia weight — seberapa besar pengaruh velocity lama
C1             = 1.5   # Koefisien kognitif (personal best)
C2             = 1.5   # Koefisien sosial (global best)
PATIENCE       = 30    # Early stopping: berhenti jika tidak ada perbaikan selama N iter


# ============================================================
# REPRESENTASI DISCRETE PSO (Swap-Sequence / Clerc's method)
#
# Karena solusi VRP adalah PERMUTASI (bukan vektor kontinu),
# kita menggunakan representasi "swap sequence" untuk velocity:
#   - Posisi partikel = urutan kunjungan sekolah (list permutasi)
#   - Velocity        = list of (i, j) swap operations
#
# Operasi:
#   position + velocity  => terapkan setiap swap ke posisi
#   c * velocity         => ambil c (probabilitas) swap secara acak
#   v1 + v2              => gabungkan dua list swap
#   p_best - position    => hitung swap sequence yang mengubah posisi → p_best
# ============================================================

def _swap_seq_from(source: list, target: list) -> list:
    """
    Hitung urutan swap yang mengubah 'source' menjadi 'target'.
    Mengembalikan list of (i, j) swap operations.
    """
    temp = source.copy()
    swaps = []
    for i in range(len(target)):
        if temp[i] != target[i]:
            j = temp.index(target[i], i + 1)
            temp[i], temp[j] = temp[j], temp[i]
            swaps.append((i, j))
    return swaps


def _apply_swaps(position: list, swaps: list) -> list:
    """Terapkan list of swap operations ke posisi, hasilkan posisi baru."""
    result = position.copy()
    for i, j in swaps:
        result[i], result[j] = result[j], result[i]
    return result


def _scale_velocity(swaps: list, probability: float) -> list:
    """
    c * velocity: setiap swap dipilih secara acak dengan probabilitas `probability`.
    Memungkinkan partikel hanya mengikuti sebagian dari arah velocity.
    """
    return [(i, j) for i, j in swaps if random.random() < probability]


def _add_velocities(v1: list, v2: list) -> list:
    """v1 + v2: gabungkan dua swap sequence."""
    return v1 + v2


# ============================================================
# FITNESS HELPER
# ============================================================
def _fitness(sequence: list, instance: dict) -> dict:
    return evaluate_solution(
        sequence,
        instance["schools"],
        instance["distance_matrix"],
        instance["time_matrix"],
        instance["constraints"],
        sppg_name=instance["sppg_name"],
    )


# ============================================================
# KELAS UTAMA PSO VRP
# ============================================================
class PSOParticle:
    """Representasi satu partikel dalam swarm."""

    def __init__(self, n: int):
        # Posisi awal: permutasi acak indeks sekolah
        self.position = list(range(n))
        random.shuffle(self.position)

        # Velocity awal: kosong (tidak ada swap)
        self.velocity: list = []

        # Personal best
        self.pbest_position = self.position.copy()
        self.pbest_fitness = float("inf")


class ParticleSwarmOptimizationVRP:
    def __init__(self, instance_data: dict):
        self.instance = instance_data
        self.n = len(instance_data["schools"])

    def run(self) -> dict:
        # ─── Edge cases ───────────────────────────────────────────
        if self.n == 0:
            return evaluate_solution(
                [],
                self.instance["schools"],
                self.instance["distance_matrix"],
                self.instance["time_matrix"],
                self.instance["constraints"],
                sppg_name=self.instance["sppg_name"],
            )
        if self.n == 1:
            return _fitness([0], self.instance)

        # ─── Inisialisasi Swarm ───────────────────────────────────
        swarm = [PSOParticle(self.n) for _ in range(N_PARTICLES)]

        # Evaluasi fitness awal & tentukan global best
        gbest_position = None
        gbest_fitness  = float("inf")
        gbest_eval     = None

        for particle in swarm:
            eval_result = _fitness(particle.position, self.instance)
            f = eval_result["fitness"]
            particle.pbest_fitness   = f
            particle.pbest_position  = particle.position.copy()

            if f < gbest_fitness:
                gbest_fitness   = f
                gbest_position  = particle.position.copy()
                gbest_eval      = eval_result

        no_improve = 0

        # ─── Loop Iterasi Utama ───────────────────────────────────
        for _ in range(MAX_ITER):

            for particle in swarm:

                # ── Hitung komponen velocity baru ──────────────────
                # 1. Komponen inertia: pertahankan sebagian velocity lama
                inertia = _scale_velocity(particle.velocity, W)

                # 2. Komponen kognitif: bergerak menuju personal best
                cognitive_swaps = _swap_seq_from(particle.position, particle.pbest_position)
                cognitive       = _scale_velocity(cognitive_swaps, C1 * random.random())

                # 3. Komponen sosial: bergerak menuju global best
                social_swaps = _swap_seq_from(particle.position, gbest_position)
                social       = _scale_velocity(social_swaps, C2 * random.random())

                # Gabungkan ketiga komponen → velocity baru
                new_velocity = _add_velocities(_add_velocities(inertia, cognitive), social)

                # ── Update posisi ──────────────────────────────────
                new_position = _apply_swaps(particle.position, new_velocity)

                # Pastikan posisi tetap valid permutasi (antisipasi edge case)
                if sorted(new_position) != list(range(self.n)):
                    new_position = list(range(self.n))
                    random.shuffle(new_position)
                    new_velocity = []

                particle.position = new_position
                particle.velocity = new_velocity

                # ── Evaluasi posisi baru ───────────────────────────
                eval_result = _fitness(particle.position, self.instance)
                f = eval_result["fitness"]

                # Update personal best
                if f < particle.pbest_fitness:
                    particle.pbest_fitness  = f
                    particle.pbest_position = particle.position.copy()

                # Update global best
                if f < gbest_fitness:
                    gbest_fitness  = f
                    gbest_position = particle.position.copy()
                    gbest_eval     = eval_result

            # ── Early stopping ─────────────────────────────────────
            # Cek apakah ada perbaikan global best dalam iterasi ini
            prev_gbest = gbest_fitness
            if gbest_fitness < prev_gbest:
                no_improve = 0
            else:
                no_improve += 1
                if no_improve >= PATIENCE:
                    break

        return gbest_eval


# ============================================================
# ENTRY POINT — jalankan langsung dengan: python particle_swarm_optimization.py
# ============================================================
if __name__ == "__main__":
    routing_dir   = os.path.abspath(os.path.join(current_dir, ".."))
    instances_dir = os.path.join(routing_dir, "dist_matrix")
    results_dir   = os.path.join(routing_dir, "results")

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    if not os.path.exists(instances_dir):
        print(f"Error: Folder {instances_dir} tidak ditemukan.")
        sys.exit()

    json_files = [
        f for f in os.listdir(instances_dir)
        if f.startswith("instance_") and f.endswith(".json")
    ]

    if not json_files:
        print("Error: Tidak ditemukan file instance_*.json di folder 'dist_matrix'.")
    else:
        print(f"Ditemukan {len(json_files)} cluster SPPG. Menghitung Particle Swarm Optimization...")

        final_output = {
            "algorithm": "Particle Swarm Optimization",
            "global_summary": {
                "total_distance_km":  0.0,
                "total_time_minutes": 0.0,
                "total_mobil":        0,
                "feasible":           True
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

            pso   = ParticleSwarmOptimizationVRP(instance_data)
            details   = pso.run()
            rute_sppg = details["single_route_data"]

            # ── Bangun polyline koordinat ──────────────────────────
            polyline = [[instance_data["depot"]["lat"], instance_data["depot"]["lng"]]]

            for stop in rute_sppg["route"]:
                if "school" in stop:
                    nama_sekolah = stop["school"].split(" (")[0]
                    for s in instance_data["schools"]:
                        if s["nama_sekolah"] == nama_sekolah:
                            polyline.append([s["lat"], s["lng"]])
                            break

            polyline.append([instance_data["depot"]["lat"], instance_data["depot"]["lng"]])

            # ── Akumulasi ke global summary ────────────────────────
            final_output["global_summary"]["total_distance_km"]  += details["total_distance_km"]
            final_output["global_summary"]["total_time_minutes"] += rute_sppg["time_spent_minutes"]
            final_output["global_summary"]["total_mobil"]        += 1

            if not details["is_feasible"]:
                final_output["global_summary"]["feasible"] = False

            final_output["results_per_sppg"].append({
                "sppg":               sppg_name,
                "distance_km":        rute_sppg["distance_km"],
                "time_spent_minutes": rute_sppg["time_spent_minutes"],
                "departure_time":     rute_sppg["departure_time"],
                "return_time":        rute_sppg["return_time"],
                "feasible_time":      rute_sppg["feasible_time"],
                "polyline":           polyline,
                "route":              rute_sppg["route"]
            })

        final_output["global_summary"]["total_distance_km"]  = round(final_output["global_summary"]["total_distance_km"],  2)
        final_output["global_summary"]["total_time_minutes"] = round(final_output["global_summary"]["total_time_minutes"], 2)

        output_json_path = os.path.join(results_dir, "pso.json")
        with open(output_json_path, "w") as f:
            json.dump(final_output, f, indent=4)

        print(f"\n==============================================")
        print(f"PROSES PARTICLE SWARM OPTIMIZATION SELESAI!")
        print(f"File output sukses ditulis ke: {output_json_path}")
        print(f"Total Jarak Surabaya Timur: {final_output['global_summary']['total_distance_km']} km")
        print(f"==============================================")
