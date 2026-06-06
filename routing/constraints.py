def evaluate_solution(sequence, schools, distance_matrix, time_matrix, config):
    """
    sequence: List urutan indeks sekolah (Contoh: [3, 1, 4, 2])
            Catatan: Indeks di dalam sequence ini merujuk pada urutan di list 'schools' (dimulai dari 0).
            Sedangkan pada matriks OSRM, indeks sekolah adalah (indeks_sequence + 1) karena indeks 0 adalah DEPOT.
    schools: List data sekolah dari JSON instance
    distance_matrix: Matriks jarak 2D dari OSRM
    time_matrix: Matriks waktu 2D dari OSRM
    config: Dict berisi nilai constraint (max_capacity, max_time_minutes, service_time_per_school)
    """
    max_cap = config["max_capacity"]
    max_time = config["max_time_minutes"]
    service_time = config["service_time_per_school"]
    
    routes = []
    current_route = [0]  # Mulai dari Depot (SPPG)
    current_load = 0
    total_distance = 0
    total_time = 0
    
    prev_matrix_idx = 0  # Mulai dari indeks 0 (Depot) pada matriks jarak/waktu
    
    for seq_idx in sequence:
        school = schools[seq_idx]
        demand = school["demand"]
        
        # Indeks sekolah di dalam matriks jarak/waktu OSRM adalah posisi sekolah + 1
        matrix_idx = seq_idx + 1
        
        # --- Evaluasi Constraint Kapasitas ---
        if current_load + demand > max_cap:
            # Jika melebihi kapasitas, paksa armada kembali ke Depot (0) dulu
            current_route.append(0)
            routes.append(current_route)
            
            # Hitung akumulasi jarak dan waktu perjalanan kembali ke Depot
            total_distance += distance_matrix[prev_matrix_idx][0]
            total_time += time_matrix[prev_matrix_idx][0]
            
            # Reset muatan dan mulai rute baru dari Depot (0) langsung menuju ke sekolah saat ini
            current_route = [0, matrix_idx]
            current_load = demand
            total_distance += distance_matrix[0][matrix_idx]
            total_time += time_matrix[0][matrix_idx] + service_time
        else:
            # Jika muatan masih aman, langsung lanjut ke sekolah tersebut
            current_route.append(matrix_idx)
            current_load += demand
            total_distance += distance_matrix[prev_matrix_idx][matrix_idx]
            total_time += time_matrix[prev_matrix_idx][matrix_idx] + service_time
            
        prev_matrix_idx = matrix_idx
        
    # Setelah semua sekolah selesai dikunjungi, armada wajib pulang ke Depot (0)
    current_route.append(0)
    routes.append(current_route)
    total_distance += distance_matrix[prev_matrix_idx][0]
    total_time += time_matrix[prev_matrix_idx][0]
    
    # --- Evaluasi Constraint Waktu (Hard Time Window) ---
    penalty = 0
    is_feasible = True
    
    if total_time > max_time:
        is_feasible = False
        # Berikan nilai penalti yang sangat besar jika melanggar waktu 180 menit
        penalty += (total_time - max_time) * 10000 
        
    # Fitness score dirancang untuk diminimasi (semakin kecil jarak + penalti, solusi semakin optimal)
    fitness_score = total_distance + penalty
    
    return {
        "routes": routes,                 # Struktur rute pecah berdasar bolak-balik depot
        "total_distance_km": total_distance,
        "total_time_minutes": total_time,
        "is_feasible": is_feasible,
        "fitness": fitness_score
    }