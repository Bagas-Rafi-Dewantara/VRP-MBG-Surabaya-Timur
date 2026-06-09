import pandas as pd
import math

print("=" * 60)
print("Tahap 2: Klasterisasi Sekolah ke SPPG (Pemerataan Keadilan Beban)")
print("=" * 60)

file_sekolah = "data/sekolah_surabaya_timur.csv"
file_sppg = "data/sppg_surabaya_timur.csv"
output_file = "data/clustered_data.csv"

df_sekolah = pd.read_csv(file_sekolah)
df_sppg = pd.read_csv(file_sppg)

df_sekolah = df_sekolah.dropna(subset=['lat', 'lng'])
df_sppg = df_sppg.dropna(subset=['Latitude', 'Longitude'])

df_sekolah = df_sekolah.sort_values(by=['kecamatan', 'jumlah_siswa'], ascending=[True, False])

BATAS_KAPASITAS = 1200 
beban_sppg = {sppg['Nama_SPPG']: 0 for _, sppg in df_sppg.iterrows()}
hasil_cluster = []

# ─── PROSES KLASTERISASI LINIER DENGAN PEMERATAAN ──────────
for idx_sek, sekolah in df_sekolah.iterrows():
    lat_sek = math.radians(sekolah['lat'])
    lon_sek = math.radians(sekolah['lng'])
    kecamatan_sek = str(sekolah['kecamatan']).strip().upper()
    jumlah_siswa = sekolah['jumlah_siswa']
    
    kandidat_sppg = []
    for idx_sppg, sppg in df_sppg.iterrows():
        kecamatan_sppg = str(sppg['Kecamatan']).strip().upper()
        if kecamatan_sppg == kecamatan_sek:
            lat_sppg = math.radians(sppg['Latitude'])
            lon_sppg = math.radians(sppg['Longitude'])
            
            dlon = lon_sppg - lon_sek
            dlat = lat_sppg - lat_sek
            a = math.sin(dlat/2)**2 + math.cos(lat_sek) * math.cos(lat_sppg) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            jarak_km = c * 6371.0 
            
            kandidat_sppg.append({
                'jarak': jarak_km,
                'nama': sppg['Nama_SPPG'],
                'lat': sppg['Latitude'],
                'lon': sppg['Longitude']
            })
            
    # PERBAIKAN UTAMA: Urutkan berdasarkan BEBAN TERENDAH dulu, baru JARAK TERDEKAT
    kandidat_sppg.sort(key=lambda x: (beban_sppg[x['nama']], x['jarak']))
    
    sppg_terpilih = ""
    lat_terpilih = 0.0
    lon_terpilih = 0.0
    jarak_terpilih = 0.0
    
    for kandidat in kandidat_sppg:
        nama_kandidat = kandidat['nama']
        if beban_sppg[nama_kandidat] + jumlah_siswa <= BATAS_KAPASITAS:
            sppg_terpilih = nama_kandidat
            lat_terpilih = kandidat['lat']
            lon_terpilih = kandidat['lon']
            jarak_terpilih = kandidat['jarak']
            beban_sppg[nama_kandidat] += jumlah_siswa
            break
            
    # JIKA SEMUA SPPG DI KECAMATAN TERSEBUT PENUH
    if sppg_terpilih == "" and len(kandidat_sppg) > 0:
        kandidat_sppg.sort(key=lambda x: beban_sppg[x['nama']])
        terbaik = kandidat_sppg[0]
        
        sppg_terpilih = terbaik['nama']
        lat_terpilih = terbaik['lat']
        lon_terpilih = terbaik['lon']
        jarak_terpilih = terbaik['jarak']
        beban_sppg[sppg_terpilih] += jumlah_siswa

    # JIKA TIDAK ADA SPPG SAMA SEKALI DI KECAMATAN ITU
    if sppg_terpilih == "":
        jarak_terdekat = 999999.0
        for idx_sppg, sppg in df_sppg.iterrows():
            lat_sppg = math.radians(sppg['Latitude'])
            lon_sppg = math.radians(sppg['Longitude'])
            dlon = lon_sppg - lon_sek
            dlat = lat_sppg - lat_sek
            a = math.sin(dlat/2)**2 + math.cos(lat_sek) * math.cos(lat_sppg) * math.sin(dlon/2)**2
            jarak_km = (2 * math.asin(math.sqrt(a))) * 6371.0 
            
            if jarak_km < jarak_terdekat:
                jarak_terdekat = jarak_km
                sppg_terpilih = sppg['Nama_SPPG']
                lat_terpilih = sppg['Latitude']
                lon_terpilih = sppg['Longitude']
                jarak_terpilih = jarak_terdekat
        
        beban_sppg[sppg_terpilih] += jumlah_siswa

    hasil_cluster.append({
        "no_sekolah": sekolah.get('no', idx_sek + 1),
        "nama_sekolah": sekolah['nama_sekolah'],
        "jenjang": sekolah['jenjang'],
        "jumlah_siswa": sekolah['jumlah_siswa'],
        "kecamatan_sekolah": sekolah['kecamatan'],
        "lat_sekolah": sekolah['lat'],
        "lng_sekolah": sekolah['lng'],
        "sppg_pelayan": sppg_terpilih,
        "lat_sppg": lat_terpilih,
        "lng_sppg": lon_terpilih,
        "jarak_lurus_km": round(jarak_terpilih, 3)
    })

# ─── PENYIMPANAN DATA FINAL ────────────────────────────────
df_hasil = pd.DataFrame(hasil_cluster)
df_hasil.to_csv(output_file, index=False, encoding="utf-8-sig")

print("\n✅ Klasterisasi & Pemerataan Selesai!")
print(f"📄 Data hasil pemetaan disimpan di: {output_file}")
print("-" * 60)

rekap_lengkap = df_hasil.groupby(['kecamatan_sekolah', 'sppg_pelayan']).agg(
    jumlah_sekolah=('nama_sekolah', 'count'),
    total_siswa=('jumlah_siswa', 'sum')
).reset_index()

rekap_lengkap = rekap_lengkap.sort_values(by=['kecamatan_sekolah', 'total_siswa'], ascending=[True, False])

pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', 1000)

print("\nRekapitulasi Keseimbangan Beban SPPG:")
print(rekap_lengkap)

# Cek SPPG yang sama sekali tidak kebagian sekolah
sppg_aktif = df_hasil['sppg_pelayan'].unique()
sppg_kosong = [s for s in df_sppg['Nama_SPPG'] if s not in sppg_aktif]

if sppg_kosong:
    print("\n⚠️ SPPG YANG MASIH KOSONG:")
    for s in sppg_kosong:
        print(f"  - {s}")
else:
    print("\n🎉 SEMPURNA! Seluruh SPPG berhasil diberdayakan.")

print("\n" + "=" * 60)
overload = rekap_lengkap[rekap_lengkap['total_siswa'] > BATAS_KAPASITAS]
if not overload.empty:
    print(f"⚠️ SPPG OVERLOAD (> {BATAS_KAPASITAS} Siswa) - Akibat tingginya populasi siswa di kecamatan:")
    print("-" * 60)
    print(overload[['sppg_pelayan', 'total_siswa', 'jumlah_sekolah']].to_string(index=False))
else:
    print(f"Semua SPPG aman di bawah batas {BATAS_KAPASITAS} siswa.")