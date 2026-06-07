import requests

def get_osrm_matrices(coordinates):
    """
    Mengambil matriks jarak dari OSRM.
    Waktu tempuh dihitung dari asumsi kecepatan konstan 40 km/jam.

    coordinates: [[lng, lat], ...]
    return:
        distance_matrix -> km
        time_matrix -> menit
    """

    coord_string = ";".join(
        [f"{coord[0]},{coord[1]}" for coord in coordinates]
    )

    url = f"http://router.project-osrm.org/table/v1/driving/{coord_string}"

    params = {
        "annotations": "distance"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response_data = response.json()

        if response_data.get("code") != "Ok":
            raise Exception(
                f"OSRM Error Status: {response_data.get('code')}"
            )

        # Meter -> Kilometer
        raw_distances = response_data["distances"]

        distance_matrix = [
            [meter / 1000.0 for meter in row]
            for row in raw_distances
        ]

        # Asumsi kecepatan konstan 40 km/jam
        time_matrix = []

        for row in distance_matrix:
            time_row = []

            for dist_km in row:
                minutes = (dist_km / 40.0) * 60.0
                time_row.append(minutes)

            time_matrix.append(time_row)

        return distance_matrix, time_matrix

    except Exception as e:
        print(
            f"[Peringatan] Gagal mengambil data OSRM: {e}. "
            f"Menggunakan matriks fallback (0.0)."
        )

        n = len(coordinates)

        return (
            [[0.0] * n for _ in range(n)],
            [[0.0] * n for _ in range(n)]
        )