import pandas as pd
import json
import os
from osrm_matrix import get_osrm_matrices 

def build_all_instances(csv_path, output_dir):
    # Validasi apakah file CSV hasil cluster benar-benar ada
    if not os.path.exists(csv_path):
        print(f"Error: File data tidak ditemukan di {csv_path}")
        return
        
    # Buat folder results jika belum otomatis terbuat
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    df = pd.read_csv(csv_path)
    
    # Grouping sekolah berdasarkan SPPG Pelayan masing-masing
    grouped = df.groupby('sppg_pelayan')
    
    for sppg_name, group in grouped:
        print(f"\n--- Memproses Cluster SPPG: {sppg_name} ---")
        
        # Ambil baris pertama dari grup untuk data koordinat SPPG (Depot)
        first_row = group.iloc[0]
        sppg_lat = float(first_row['lat_sppg'])
        sppg_lng = float(first_row['lng_sppg'])
        
        # Inisialisasi list koordinat. Indeks 0 WAJIB berupa Depot [lng, lat]
        coordinates = [[sppg_lng, sppg_lat]]
        
        schools_data = []
        for idx, row in group.iterrows():
            coordinates.append([float(row['lng_sekolah']), float(row['lat_sekolah'])])
            schools_data.append({
                "no_sekolah": int(row['no_sekolah']),
                "nama_sekolah": row['nama_sekolah'],
                "demand": int(row['jumlah_siswa']),  # Demand = Jumlah siswa (bawaan boks)
                "lat": float(row['lat_sekolah']),
                "lng": float(row['lng_sekolah'])
            })
            
        print(f"Menghubungi OSRM API untuk menghitung rute (1 Depot + {len(schools_data)} Sekolah)...")
        
        # Panggil fungsi OSRM Matrix yang sudah dibuat di file sebelah
        distance_matrix, time_matrix = get_osrm_matrices(coordinates)
        
        # Struktur objek Instance Data VRP yang akan di-consume oleh GA, ACO, PSO, SA
        instance_data = {
            "sppg_name": sppg_name,
            "depot": {
                "lat": sppg_lat,
                "lng": sppg_lng
            },
            "constraints": {
                "max_capacity": 1050,           # Batas muatan mobil boks
                "max_time_minutes": 180,        # Batas waktu 3 jam (08.00 - 11.00)
                "service_time_per_school": 10,  # Waktu bongkar muat per sekolah (menit)
                "loading_in_time": 20,          # Waktu muat di SPPG sebelum berangkat / refill (menit)
                "loading_out_time": 20          # Waktu bongkar di SPPG setelah kembali (menit)
            },
            "schools": schools_data,
            "distance_matrix": distance_matrix,
            "time_matrix": time_matrix
        }
        
        # Amankan nama file dari spasi dan karakter aneh
        safe_filename = "".join([c if c.isalnum() else "_" for c in sppg_name])
        output_file = os.path.join(output_dir, f"instance_{safe_filename}.json")
        
        with open(output_file, 'w') as f:
            json.dump(instance_data, f, indent=4)
            
        print(f"Berhasil membuat data instance -> {output_file}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    CSV_INPUT = os.path.abspath(os.path.join(current_dir, "../data/clustered_data.csv"))
    
    # KITA PINDAHKAN KESINI: khusus buat nyimpen data mentah matriks jarak
    OUTPUT_FOLDER = os.path.join(current_dir, "dist_matrix") 
    
    print(f"Membaca file dari: {CSV_INPUT}")
    print(f"Menyimpan file matriks/instance ke: {OUTPUT_FOLDER}")
    
    build_all_instances(CSV_INPUT, OUTPUT_FOLDER)

