import pandas as pd
import math
from math import ceil

print("=" * 60)
print("Tahap 2: Klasterisasi Sekolah ke SPPG (Optimal)")
print("=" * 60)

file_sekolah = "data/sekolah_surabaya_timur.csv"
file_sppg    = "data/sppg_surabaya_timur.csv"
output_file  = "data/clustered_data.csv"

df_sekolah = pd.read_csv(file_sekolah).dropna(subset=['lat', 'lng'])
df_sppg    = pd.read_csv(file_sppg).dropna(subset=['Latitude', 'Longitude'])

df_sekolah['kecamatan'] = df_sekolah['kecamatan'].str.strip().str.upper()
df_sppg['Kecamatan']    = df_sppg['Kecamatan'].str.strip().str.upper()

hasil_cluster    = []
kecamatan_list   = df_sekolah['kecamatan'].unique()
BATAS_JARAK_KM   = 5.0
KAPASITAS_MAKS   = 2500  # ← constraint utama baru

def hitung_jarak(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return (2 * math.asin(math.sqrt(a))) * 6371.0

def hitung_skor(jarak, beban_siswa, jml_sekolah, target_siswa, target_sekolah):
    skor_jarak   = jarak / 10.0
    skor_siswa   = beban_siswa / max(target_siswa, 1)
    skor_sekolah = jml_sekolah / max(target_sekolah, 1)
    return skor_jarak + skor_siswa + skor_sekolah

for kec in kecamatan_list:
    sek_kec  = df_sekolah[df_sekolah['kecamatan'] == kec].copy()
    sppg_kec = df_sppg[df_sppg['Kecamatan'] == kec].copy()

    jml_sek  = len(sek_kec)
    jml_sppg = len(sppg_kec)

    # ── Tidak ada SPPG di kecamatan ini ────────────────────
    if jml_sppg == 0:
        for _, sek in sek_kec.iterrows():
            terdekat_jarak = 999999.0
            terdekat_sppg  = None
            for _, sppg in df_sppg.iterrows():
                jrk = hitung_jarak(sek['lat'], sek['lng'],
                                   sppg['Latitude'], sppg['Longitude'])
                if jrk < terdekat_jarak:
                    terdekat_jarak = jrk
                    terdekat_sppg  = sppg
            hasil_cluster.append({
                "no_sekolah":        sek.get('no', len(hasil_cluster) + 1),
                "nama_sekolah":      sek['nama_sekolah'],
                "jenjang":           sek['jenjang'],
                "jumlah_siswa":      sek['jumlah_siswa'],
                "kecamatan_sekolah": sek['kecamatan'],
                "lat_sekolah":       sek['lat'],
                "lng_sekolah":       sek['lng'],
                "sppg_pelayan":      terdekat_sppg['Nama_SPPG'],
                "lat_sppg":          terdekat_sppg['Latitude'],
                "lng_sppg":          terdekat_sppg['Longitude'],
                "jarak_lurus_km":    round(terdekat_jarak, 3)
            })
        continue

    # ── Target ideal per SPPG ───────────────────────────────
    total_siswa_kec     = sek_kec['jumlah_siswa'].sum()
    target_siswa_sppg   = total_siswa_kec / jml_sppg
    target_sekolah_sppg = jml_sek / jml_sppg
    batas_siswa         = min(target_siswa_sppg * 1.3, KAPASITAS_MAKS)  # ← pakai yang lebih ketat
    batas_sekolah       = ceil(target_sekolah_sppg) + 1

    jatah_sekolah_sppg = {row['Nama_SPPG']: 0 for _, row in sppg_kec.iterrows()}
    beban_siswa_sppg   = {row['Nama_SPPG']: 0 for _, row in sppg_kec.iterrows()}

    # Prioritas: SMA/SMK → SMP → SD, siswa terbanyak dulu
    urutan_jenjang = {"SMA/SMK": 0, "SMP": 1, "SD": 2}
    sek_kec['_sort'] = sek_kec['jenjang'].map(urutan_jenjang).fillna(3)
    sek_kec = sek_kec.sort_values(
        by=['_sort', 'jumlah_siswa'], ascending=[True, False]
    ).drop(columns=['_sort'])

    for _, sek in sek_kec.iterrows():
        kandidat = []
        for _, sppg in sppg_kec.iterrows():
            nama = sppg['Nama_SPPG']
            jrk  = hitung_jarak(sek['lat'], sek['lng'],
                                sppg['Latitude'], sppg['Longitude'])
            kandidat.append({
                'nama':        nama,
                'jarak':       jrk,
                'sppg':        sppg,
                'jml_sekolah': jatah_sekolah_sppg[nama],
                'beban_siswa': beban_siswa_sppg[nama],
            })

        sppg_terpilih = None

        # FILTER 1: Pecah telur — wajib isi SPPG yang masih kosong
        sppg_kosong = [k for k in kandidat if k['jml_sekolah'] == 0]
        if sppg_kosong:
            sppg_kosong.sort(key=lambda x: x['jarak'])
            sppg_terpilih = sppg_kosong[0]

        # FILTER 2: Semua constraint terpenuhi
        if not sppg_terpilih:
            sppg_ideal = [
                k for k in kandidat
                if (k['beban_siswa'] + sek['jumlah_siswa']) <= batas_siswa
                and (k['beban_siswa'] + sek['jumlah_siswa']) <= KAPASITAS_MAKS
                and k['jml_sekolah'] < batas_sekolah
                and k['jarak'] <= BATAS_JARAK_KM
            ]
            if sppg_ideal:
                sppg_ideal.sort(key=lambda x: hitung_skor(
                    x['jarak'], x['beban_siswa'],
                    x['jml_sekolah'], target_siswa_sppg, target_sekolah_sppg
                ))
                sppg_terpilih = sppg_ideal[0]

        # FILTER 3: Relaksasi jarak, tapi kapasitas tetap dijaga
        if not sppg_terpilih:
            sppg_relax = [
                k for k in kandidat
                if (k['beban_siswa'] + sek['jumlah_siswa']) <= batas_siswa
                and (k['beban_siswa'] + sek['jumlah_siswa']) <= KAPASITAS_MAKS
                and k['jml_sekolah'] < batas_sekolah
            ]
            if sppg_relax:
                sppg_relax.sort(key=lambda x: hitung_skor(
                    x['jarak'], x['beban_siswa'],
                    x['jml_sekolah'], target_siswa_sppg, target_sekolah_sppg
                ))
                sppg_terpilih = sppg_relax[0]

        # FILTER 4: Kapasitas absolut masih aman, constraint lain relaks
        if not sppg_terpilih:
            sppg_belum_penuh = [
                k for k in kandidat
                if (k['beban_siswa'] + sek['jumlah_siswa']) <= KAPASITAS_MAKS
            ]
            if sppg_belum_penuh:
                sppg_belum_penuh.sort(key=lambda x: hitung_skor(
                    x['jarak'], x['beban_siswa'],
                    x['jml_sekolah'], target_siswa_sppg, target_sekolah_sppg
                ))
                sppg_terpilih = sppg_belum_penuh[0]

        # FILTER 5 (Fallback mutlak): Semua SPPG penuh → pilih beban teringan
        if not sppg_terpilih:
            kandidat.sort(key=lambda x: hitung_skor(
                x['jarak'], x['beban_siswa'],
                x['jml_sekolah'], target_siswa_sppg, target_sekolah_sppg
            ))
            sppg_terpilih = kandidat[0]

        nama_terpilih = sppg_terpilih['nama']
        data_sppg     = sppg_terpilih['sppg']

        hasil_cluster.append({
            "no_sekolah":        sek.get('no', len(hasil_cluster) + 1),
            "nama_sekolah":      sek['nama_sekolah'],
            "jenjang":           sek['jenjang'],
            "jumlah_siswa":      sek['jumlah_siswa'],
            "kecamatan_sekolah": sek['kecamatan'],
            "lat_sekolah":       sek['lat'],
            "lng_sekolah":       sek['lng'],
            "sppg_pelayan":      nama_terpilih,
            "lat_sppg":          data_sppg['Latitude'],
            "lng_sppg":          data_sppg['Longitude'],
            "jarak_lurus_km":    round(sppg_terpilih['jarak'], 3)
        })

        jatah_sekolah_sppg[nama_terpilih] += 1
        beban_siswa_sppg[nama_terpilih]   += sek['jumlah_siswa']

# ─── PENYIMPANAN ───────────────────────────────────────────
df_hasil = pd.DataFrame(hasil_cluster)
df_hasil.to_csv(output_file, index=False, encoding="utf-8-sig")

print("\n✅ Klasterisasi Selesai!")
print(f"📄 Data disimpan di: {output_file}")
print("-" * 60)

rekap = df_hasil.groupby(['kecamatan_sekolah', 'sppg_pelayan']).agg(
    jumlah_sekolah=('nama_sekolah', 'count'),
    total_siswa=('jumlah_siswa', 'sum'),
    jarak_rata=('jarak_lurus_km', 'mean'),
    jarak_max=('jarak_lurus_km', 'max')
).reset_index()

rekap = rekap.sort_values(
    by=['kecamatan_sekolah', 'total_siswa'], ascending=[True, False]
)

pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', 1000)

print("\nRekapitulasi Keseimbangan Beban SPPG:")
print(rekap.to_string(index=False))

# Cek SPPG kosong
sppg_aktif  = df_hasil['sppg_pelayan'].unique()
sppg_kosong = [s for s in df_sppg['Nama_SPPG'] if s not in sppg_aktif]

print("\n" + "=" * 60)
if sppg_kosong:
    print("⚠️ SPPG YANG MASIH KOSONG:")
    for s in sppg_kosong:
        print(f"  - {s}")
else:
    print("🎉 SEMPURNA! Seluruh SPPG berhasil diberdayakan.")

# Cek kapasitas 2500
print("\n" + "=" * 60)
overload = rekap[rekap['total_siswa'] > KAPASITAS_MAKS]
if not overload.empty:
    print(f"⚠️ SPPG MELEBIHI KAPASITAS {KAPASITAS_MAKS} SISWA:")
    print(overload[['sppg_pelayan', 'total_siswa', 'jumlah_sekolah']].to_string(index=False))
else:
    print(f"✅ Semua SPPG di bawah kapasitas {KAPASITAS_MAKS} siswa.")

# Cek jarak jauh
print("\n" + "=" * 60)
jarak_jauh = rekap[rekap['jarak_max'] > BATAS_JARAK_KM]
if not jarak_jauh.empty:
    print(f"⚠️ SPPG DENGAN JARAK MAKSIMAL > {BATAS_JARAK_KM} KM:")
    print(jarak_jauh[['sppg_pelayan', 'jarak_max', 'jumlah_sekolah']].to_string(index=False))
else:
    print(f"✅ Semua sekolah dalam radius {BATAS_JARAK_KM} km dari SPPG-nya.")

# Statistik CV
print("\n" + "=" * 60)
print("📊 Statistik Keseimbangan Beban per Kecamatan:")
for kec in kecamatan_list:
    data_kec = rekap[rekap['kecamatan_sekolah'] == kec]
    if len(data_kec) > 1:
        std = data_kec['total_siswa'].std()
        avg = data_kec['total_siswa'].mean()
        cv  = (std / avg * 100) if avg > 0 else 0
        print(f"  {kec}: CV={cv:.1f}% {'✅' if cv < 20 else '⚠️'} "
              f"(std={std:.0f}, avg={avg:.0f}, max={data_kec['total_siswa'].max()}, "
              f"min={data_kec['total_siswa'].min()})")