import requests
import pandas as pd
import time
from bs4 import BeautifulSoup
from geopy.geocoders import ArcGIS

# ─── KONFIGURASI ──────────────────────────────────────────────
BASE_URL = "https://www.bgn.go.id/operasional-sppg"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
TARGET_KECAMATAN = [
    "GUBENG", "GUNUNG ANYAR", "SUKOLILO", "TAMBAKSARI", 
    "MULYOREJO", "RUNGKUT", "TENGGILIS MEJOYO"
]

output_file = "data/sppg_surabaya_timur.csv"

geolocator = ArcGIS(timeout=30)
all_results = []

print("=" * 60)
print("Scraping Data SPPG - Surabaya Timur (Optimized Search)")
print("=" * 60)

page = 1

# ─── PROSES SCRAPING LINIER OTOMATIS ──────────────────────────
while True:
    print(f"\nMengakses halaman {page}...")
    
    req_params = {
        "page": page,
        "search": "Surabaya"
    }
    
    response = requests.get(BASE_URL, params=req_params, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"  ⚠️ Gagal mengakses halaman {page}. Proses dihentikan.")
        break
        
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    
    if not table:
        print("  Tabel tidak ditemukan. Berhenti.")
        break
        
    rows = table.find_all("tr")[1:] 
    
    # Inisialisasi deteksi baris data yang benar-benar berisi informasi SPPG
    baris_valid = 0
        
    for row in rows:
        cols = row.find_all("td")
        
        # Cek apakah baris ini adalah data SPPG asli (punya minimal 7 kolom)
        if len(cols) >= 7:
            baris_valid += 1
            provinsi = cols[1].get_text(strip=True).upper()
            kab_kota = cols[2].get_text(strip=True).upper()
            kecamatan = cols[3].get_text(strip=True).upper()
            
            if kecamatan in TARGET_KECAMATAN:
                kelurahan = cols[4].get_text(strip=True)
                alamat = cols[5].get_text(strip=True)
                nama_sppg = cols[6].get_text(strip=True)
                
                print(f"  → Ditemukan: {nama_sppg} (Kec. {kecamatan})")
                
                time.sleep(0.5)
                search_query = f"{alamat}, {kelurahan}, {kecamatan}, {kab_kota}, {provinsi}, Indonesia"
                
                location = geolocator.geocode(search_query)
                
                lat = None
                lon = None
                if location:
                    lat = location.latitude
                    lon = location.longitude
                    
                all_results.append({
                    "Provinsi": provinsi,
                    "Kab_Kota": kab_kota,
                    "Kecamatan": kecamatan,
                    "Kelurahan_Desa": kelurahan,
                    "Alamat": alamat,
                    "Nama_SPPG": nama_sppg,
                    "Latitude": lat,
                    "Longitude": lon
                })
    
    # Jika dalam 1 halaman tidak ada data kolom yang valid, berarti sudah di ujung
    if baris_valid == 0:
        print("  Halaman tidak memiliki data valid. Seluruh data telah ditarik.")
        break
                
    page += 1

# ─── PENYIMPANAN DATA ─────────────────────────────────────────
if all_results:
    df = pd.DataFrame(all_results)
    df = df.drop_duplicates(subset=["Nama_SPPG"])
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    
    print("\n" + "=" * 60)
    print(f"✅ Scraping Selesai! Total SPPG target ditemukan: {len(df)}")
    print(f"📄 Data berhasil disimpan di: {output_file}")
else:
    print("\n❌ Tidak ada data SPPG Surabaya Timur yang ditemukan.")