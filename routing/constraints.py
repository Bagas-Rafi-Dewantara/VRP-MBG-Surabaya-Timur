from datetime import datetime, timedelta

def minutes_to_time_str(base_time_str, minutes_added):
    """Mengubah menit akumulasi menjadi format jam dinding (HH:MM)"""
    base_time = datetime.strptime(base_time_str, "%H:%M")
    result_time = base_time + timedelta(minutes=minutes_added)
    return result_time.strftime("%H:%M")

# Tambahkan parameter sppg_name di baris def ini
def evaluate_solution(sequence, schools, distance_matrix, time_matrix, config, sppg_name="SPPG"):
    """
    Evaluator CVRPTW Fix Logika Kapasitas & Timestamp Jam Dinding.
    Jika kapasitas boks habis, armada dipaksa mencatat rute kembali ke SPPG (0) 
    untuk refill, lalu melanjutkan sisa pengiriman.
    """
    max_cap = config["max_capacity"]
    max_time = config["max_time_minutes"]
    service_time = config["service_time_per_school"]
    
    remaining_demand = {i: schools[i]["demand"] for i in range(len(schools))}
    

    total_distance_global = 0
    prev_matrix_idx = 0 
    current_load = 0
    time_spent = 0
    current_route_nodes = []
    
    for seq_idx in sequence:
        if remaining_demand[seq_idx] <= 0:
            continue
            
        matrix_idx = seq_idx + 1
        
        while remaining_demand[seq_idx] > 0:
            demand_sekolah = remaining_demand[seq_idx]
            tersisa_di_boks = max_cap - current_load
            
            if tersisa_di_boks == 0:
                travel_time_to_sppg = time_matrix[prev_matrix_idx][0]
                travel_dist_to_sppg = distance_matrix[prev_matrix_idx][0]
                
                time_spent += travel_time_to_sppg
                total_distance_global += travel_dist_to_sppg
                
                # FIX DISINI: Pakai variabel sppg_name langsung, bukan mengambil dari objek school
                current_route_nodes.append({
                    "SPPG": f"{sppg_name} (Refill)",
                    "arrival_time": minutes_to_time_str("08:00", time_spent),
                    "departure_time": minutes_to_time_str("08:00", time_spent + 10)
                })
                time_spent += 10
                
                current_load = 0
                prev_matrix_idx = 0
                tersisa_di_boks = max_cap
            
            jumlah_drop = min(demand_sekolah, tersisa_di_boks)
            
            travel_time = time_matrix[prev_matrix_idx][matrix_idx]
            travel_dist = distance_matrix[prev_matrix_idx][matrix_idx]
            
            time_spent += travel_time
            arrival_str = minutes_to_time_str("08:00", time_spent)
            
            time_spent += service_time
            departure_str = minutes_to_time_str("08:00", time_spent)
            
            current_route_nodes.append({
                "school": f"{schools[seq_idx]['nama_sekolah']} (Drop: {jumlah_drop} tray)",
                "arrival_time": arrival_str,
                "departure_time": departure_str
            })
            
            current_load += jumlah_drop
            remaining_demand[seq_idx] -= jumlah_drop
            total_distance_global += travel_dist
            prev_matrix_idx = matrix_idx

    if prev_matrix_idx != 0:
        travel_time_to_depot = time_matrix[prev_matrix_idx][0]
        travel_dist_to_depot = distance_matrix[prev_matrix_idx][0]
        
        time_spent += travel_time_to_depot
        total_distance_global += travel_dist_to_depot
        
    return_str = minutes_to_time_str("08:00", time_spent)
    feasible_time = time_spent <= max_time
    
    single_sppg_route = {
        "distance_km": round(total_distance_global, 2),
        "time_spent_minutes": round(time_spent, 2),
        "departure_time": "08:00",
        "return_time": return_str,
        "feasible_time": feasible_time,
        "route": current_route_nodes
    }
    
    penalty = 0
    if time_spent > max_time:
        penalty += (time_spent - max_time) * 10000
        
    fitness_score = total_distance_global + penalty
    
    return {
        "single_route_data": single_sppg_route,
        "total_distance_km": round(total_distance_global, 2),
        "is_feasible": feasible_time,
        "fitness": fitness_score
    }