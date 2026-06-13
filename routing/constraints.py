from datetime import datetime, timedelta


# ==========================================
# HELPER
# ==========================================
def minutes_to_time_str(base_time_str, minutes_added):
    base_time = datetime.strptime(base_time_str, "%H:%M")
    result_time = base_time + timedelta(minutes=minutes_added)
    return result_time.strftime("%H:%M")


def distance_to_minutes(distance_km):
    """
    Asumsi mobil boks:
    40 km/jam
    """
    return (distance_km / 40) * 60


# ==========================================
# EVALUATOR CVRPTW + RELOAD
# ==========================================
def evaluate_solution(
    sequence,
    schools,
    distance_matrix,
    time_matrix,   # tidak dipakai lagi, tetap dibiarkan agar kompatibel
    config,
    sppg_name="SPPG"
):

    max_cap = config["max_capacity"]
    max_time = config["max_time_minutes"]
    service_time = config["service_time_per_school"]
    loading_in_time = config.get("loading_in_time", 20)
    loading_out_time = config.get("loading_out_time", 20)

    remaining_demand = {
        i: schools[i]["demand"]
        for i in range(len(schools))
    }

    total_distance_global = 0.0
    time_spent = loading_in_time  # muat barang di SPPG sebelum berangkat

    prev_matrix_idx = 0
    current_load = 0

    reload_count = 0

    current_route_nodes = []

    # ==========================================
    # LOOP SEKOLAH
    # ==========================================
    for seq_idx in sequence:

        if remaining_demand[seq_idx] <= 0:
            continue

        matrix_idx = seq_idx + 1

        while remaining_demand[seq_idx] > 0:

            demand_sekolah = remaining_demand[seq_idx]

            tersisa_di_boks = max_cap - current_load

            # ======================================
            # REFILL
            # ======================================
            if tersisa_di_boks < demand_sekolah and current_load > 0:

                travel_dist_to_sppg = distance_matrix[prev_matrix_idx][0]
                travel_time_to_sppg = distance_to_minutes(
                    travel_dist_to_sppg
                )

                total_distance_global += travel_dist_to_sppg
                time_spent += travel_time_to_sppg

                arrival_refill = time_spent
                time_spent += loading_in_time  # muat ulang di SPPG

                current_route_nodes.append({
                    "event": "REFILL",
                    "location": sppg_name,
                    "arrival_time": minutes_to_time_str(
                        "08:00",
                        arrival_refill
                    ),
                    "departure_time": minutes_to_time_str(
                        "08:00",
                        time_spent
                    )
                })

                reload_count += 1

                current_load = 0
                prev_matrix_idx = 0

                tersisa_di_boks = max_cap

            # ======================================
            # KIRIM KE SEKOLAH
            # ======================================
            jumlah_drop = min(
                demand_sekolah,
                tersisa_di_boks
            )

            travel_dist = distance_matrix[
                prev_matrix_idx
            ][matrix_idx]

            travel_time = distance_to_minutes(
                travel_dist
            )

            total_distance_global += travel_dist
            time_spent += travel_time

            arrival_str = minutes_to_time_str(
                "08:00",
                time_spent
            )

            time_spent += service_time

            departure_str = minutes_to_time_str(
                "08:00",
                time_spent
            )

            current_route_nodes.append({
                "school": schools[seq_idx]["nama_sekolah"],
                "drop_tray": jumlah_drop,
                "arrival_time": arrival_str,
                "departure_time": departure_str
            })

            current_load += jumlah_drop
            remaining_demand[seq_idx] -= jumlah_drop

            prev_matrix_idx = matrix_idx

    # ==========================================
    # KEMBALI KE DEPOT
    # ==========================================
    if prev_matrix_idx != 0:

        travel_dist_to_depot = distance_matrix[
            prev_matrix_idx
        ][0]

        travel_time_to_depot = distance_to_minutes(
            travel_dist_to_depot
        )

        total_distance_global += travel_dist_to_depot
        time_spent += travel_time_to_depot

    arrival_depot = time_spent
    time_spent += loading_out_time  # bongkar muatan di SPPG setelah kembali

    current_route_nodes.append({
        "event": "RETURN_DEPOT",
        "location": sppg_name,
        "arrival_time": minutes_to_time_str(
            "08:00",
            arrival_depot
        ),
        "finish_time": minutes_to_time_str(
            "08:00",
            time_spent
        )
    })

    # ==========================================
    # FEASIBILITY
    # ==========================================
    feasible_time = time_spent <= max_time

    total_demand = sum(
        school["demand"]
        for school in schools
    )

    capacity_utilization = (
        total_demand /
        ((reload_count + 1) * max_cap)
    ) * 100

    # ==========================================
    # FITNESS
    # ==========================================
    penalty = 0

    if not feasible_time:
        penalty += (
            time_spent - max_time
        ) * 10000

    fitness_score = (
        total_distance_global +
        penalty
    )

    # ==========================================
    # DETAIL SPPG
    # ==========================================
    single_sppg_route = {

        "distance_km":
            round(total_distance_global, 2),

        "time_spent_minutes":
            round(time_spent, 2),

        "departure_time":
            minutes_to_time_str("08:00", loading_in_time),

        "return_time":
            minutes_to_time_str(
                "08:00",
                time_spent
            ),

        "feasible_time":
            feasible_time,

        "reload_count":
            reload_count,

        "capacity_utilization":
            round(
                capacity_utilization,
                2
            ),

        "schools_served":
            len(schools),

        "route":
            current_route_nodes
    }

    return {

        "single_route_data":
            single_sppg_route,

        "total_distance_km":
            round(
                total_distance_global,
                2
            ),

        "total_time_minutes":
            round(
                time_spent,
                2
            ),

        "is_feasible":
            feasible_time,

        "fitness":
            fitness_score
    }