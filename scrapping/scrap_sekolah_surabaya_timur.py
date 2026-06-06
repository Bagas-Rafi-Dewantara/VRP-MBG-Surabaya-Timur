import requests
import pandas as pd
import time
import re
import random
from geopy.geocoders import ArcGIS

# ─── KONFIGURASI ──────────────────────────────────────────────
OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# BBOX Sengaja diperlebar agar tidak ada yang terlewat, 
# seleksi aslinya nanti menggunakan ArcGIS
KECAMATAN_BBOX = [
    ("Gubeng",           -7.295, 112.733, -7.245, 112.775),
    ("Gunung Anyar",     -7.360, 112.770, -7.310, 112.820),
    ("Sukolilo",         -7.320, 112.762, -7.260, 112.828),
    ("Tambaksari",       -7.265, 112.740, -7.220, 112.790),
    ("Mulyorejo",        -7.280, 112.768, -7.230, 112.820),
    ("Rungkut",          -7.340, 112.760, -7.285, 112.825),
    ("Tenggilis Mejoyo", -7.340, 112.735, -7.295, 112.785),
]

output_file = "data/sekolah_surabaya_timur.csv"
all_schools = []

# Inisialisasi ArcGIS untuk mengecek kecamatan asli dari koordinat
geolocator = ArcGIS(timeout=30)

print("=" * 60)
print("CVRPTW MBG - Scraping Sekolah Negeri Surabaya Timur")
print("=" * 60)

# ─── PROSES SCRAPING LINIER ───────────────────────────────────
for nama_kec, lat_min, lon_min, lat_max, lon_max in KECAMATAN_BBOX:
    print(f"\n📍 Menarik data mentah area BBOX {nama_kec}...")
    
    bbox = f"{lat_min},{lon_min},{lat_max},{lon_max}"
    query = f"""[out:json][timeout:60];
(
  node["amenity"="school"]({bbox});
  way["amenity"="school"]({bbox});
  node["amenity"="college"]({bbox});
  way["amenity"="college"]({bbox});
);
out center tags;"""

    elements = []
    
    for mirror in OVERPASS_MIRRORS:
        if elements:
            break
            
        response = requests.post(
            mirror,
            data={"data": query},
            headers={"User-Agent": "CVRPTW-MBG-SurabayaTimur/4.0"}
        )
        
        if response.status_code == 200:
            res_elements = response.json().get("elements", [])
            if res_elements:
                elements = res_elements
        else:
            time.sleep(2)

    if not elements:
        print(f"  ⚠️ Tidak ada data ditemukan.")
        continue

    parsed_count = 0
    print(f"  → Ditemukan {len(elements)} kandidat. Memulai validasi alamat ArcGIS...")
    
    for el in elements:
        tags = el.get("tags", {})

        if el["type"] == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:
            center = el.get("center", {})
            lat, lon = center.get("lat"), center.get("lon")

        if not lat or not lon:
            continue

        nama = tags.get("name") or tags.get("name:id") or tags.get("official_name") or ""
        if not nama:
            continue

        nama_up = nama.upper()

        is_negeri = False
        if re.search(r'\bNEGERI\b', nama_up) or re.search(r'\b(SDN|SMPN|SMAN|SMKN|MIN|MTSN|MAN)\b', nama_up) or re.search(r'\b(SDN|SMPN|SMAN|SMKN|MIN|MTSN|MAN)\d+', nama_up):
            is_negeri = True
        
        if not is_negeri:
            continue

        school_level = tags.get("school:level", "").upper()
        jenjang = "TIDAK_DIKENAL"

        if any(x in nama_up for x in ["TK ", "TKN", "TKI", "PAUD", "KINDER", "RA ", "RAUDHATUL", "PLAYGRUP", "PLAYGROUP", " KB ", "KELOMPOK BERMAIN", "PG "]):
            jenjang = "TK/PAUD"
        elif any(x in nama_up for x in ["SMA", "SMK", "MA ", "ALIYAH", "ATAS"]) or "secondary" in school_level:
            jenjang = "SMA/SMK"
        elif any(x in nama_up for x in ["SMP", "MTS", "TSANAWIYAH", "PERTAMA"]) or "junior" in school_level:
            jenjang = "SMP"
        elif any(x in nama_up for x in ["SDN", "SD ", " SD", "SDI", "MIT ", "MI ", "IBTIDAIYAH", "DASAR"]) or "primary" in school_level:
            jenjang = "SD"

        if jenjang not in ["SD", "SMP", "SMA/SMK"]:
            continue
            
        # ─── VALIDASI KECAMATAN ABSOLUT DENGAN ARCGIS ───
        time.sleep(0.3) # Jeda agar API tidak terblokir
        lokasi_asli = geolocator.reverse(f"{lat}, {lon}")
        
        alamat_lengkap = ""
        if lokasi_asli:
            alamat_lengkap = lokasi_asli.address.upper()
            
        # Jika nama kecamatan target TIDAK ADA di alamat asli ArcGIS, buang!
        if nama_kec.upper() not in alamat_lengkap:
            continue 
            
        # ────────────────────────────────────────────────
            
        if jenjang == "SD":
            jumlah_siswa = random.randint(400, 450)
        elif jenjang == "SMP":
            jumlah_siswa = random.randint(1000, 1100)
        elif jenjang == "SMA/SMK":
            jumlah_siswa = random.randint(1100, 1200)

        all_schools.append({
            "osm_id":       el.get("id"),
            "nama_sekolah": nama.strip().title(),
            "jenjang":      jenjang,
            "jumlah_siswa": jumlah_siswa,
            "kecamatan":    nama_kec.upper(),
            "alamat":       alamat_lengkap.title() if alamat_lengkap else tags.get("addr:full", ""),
            "kota":         "Surabaya",
            "lat":          round(lat, 7),
            "lng":          round(lon, 7),
        })
        parsed_count += 1
        print(f"    [Valid] {nama.strip().title()}")

    print(f"  → Selesai. {parsed_count} sekolah lolos validasi area {nama_kec}")

# ─── PEMBERSIHAN DAN PENYIMPANAN DATA ───────────────────────
if not all_schools:
    print("\n❌ Tidak ada data sekolah yang berhasil dikumpulkan.")
    exit(1)

df = pd.DataFrame(all_schools)
total_awal = len(df)

df = df.drop_duplicates(subset=["lat", "lng"])
df["_nama_lower"] = df["nama_sekolah"].str.lower().str.strip()
df = df.drop_duplicates(subset=["_nama_lower"])
df = df.drop(columns=["_nama_lower"])

urutan_jenjang = {"SD": 0, "SMP": 1, "SMA/SMK": 2}
df["_sort_jenjang"] = df["jenjang"].map(urutan_jenjang)
df = df.sort_values(["kecamatan", "_sort_jenjang", "nama_sekolah"])
df = df.drop(columns=["_sort_jenjang"])
df = df.reset_index(drop=True)
df.index += 1

df.to_csv(output_file, index_label="no", encoding="utf-8-sig")

print(f"\n{'='*60}")
print(f"✅ Total Sekolah Tersimpan (Sudah Divalidasi ArcGIS): {len(df)}")
print(f"📄 Data mentah sukses ditulis ke: {output_file}")
print("=" * 60)