import requests

def get_osrm_matrices(coordinates):
    """
    Mengambil matriks jarak dan waktu dari OSRM API.
    coordinates: list of [lng, lat] -> Indeks 0 HARUS Depot/SPPG
    Mengembalikan: distance_matrix (dalam KM), time_matrix (dalam MENIT)
    """
    # Gabungkan koordinat menjadi format string OSRM: lng1,lat1;lng2,lat2;...
    coord_string = ";".join([f"{coord[0]},{coord[1]}" for coord in coordinates])
    
    # URL OSRM Table API menggunakan profil driving (mobil boks)
    url = f"http://router.project-osrm.org/table/v1/driving/{coord_string}"
    
    # Meminta OSRM mengembalikan data jarak (distance) dan durasi (duration) sekaligus
    params = {
        "annotations": "duration,distance"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response_data = response.json()
        
        if response_data.get("code") != "Ok":
            raise Exception(f"OSRM Error Status: {response_data.get('code')}")
            
        # OSRM mengembalikan jarak dalam METER. Konversi ke KILOMETER.
        raw_distances = response_data["distances"]
        distance_matrix = [[meter / 1000.0 for meter in row] for row in raw_distances]
        
        # OSRM mengembalikan durasi dalam DETIK. Konversi ke MENIT.
        raw_durations = response_data["durations"]
        time_matrix = [[second / 60.0 for second in row] for row in raw_durations]
        
        return distance_matrix, time_matrix
        
    except Exception as e:
        print(f"[Peringatan] Gagal mengambil data OSRM: {e}. Menggunakan matriks fallback (0.0).")
        n = len(coordinates)
        return [[0.0] * n for _ in range(n)], [[0.0] * n for _ in range(n)]