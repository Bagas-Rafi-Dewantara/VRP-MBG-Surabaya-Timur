#!/bin/bash

# ============================================================
#  run_web.sh — Jalankan Dashboard Visualisasi VRP-MBG
#  Usage: bash run_web.sh
# ============================================================

PORT=8000
URL="http://localhost:$PORT/web/index.html"

echo ""
echo "🍱  VRP-MBG Surabaya Timur — Web Dashboard"
echo "============================================"

# Cek apakah port sudah terpakai, jika iya matikan dulu
EXISTING_PID=$(lsof -ti tcp:$PORT)
if [ -n "$EXISTING_PID" ]; then
    echo "⚠️  Port $PORT sudah dipakai. Mematikan proses lama..."
    echo "$EXISTING_PID" | xargs kill -9 2>/dev/null
    sleep 2
fi

# Jalankan HTTP server di background dari root project
echo "🚀  Menjalankan server di http://localhost:$PORT ..."
python3 -m http.server $PORT &> /dev/null &
SERVER_PID=$!

# Tunggu server siap
sleep 1

# Cek apakah server berhasil jalan
if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "❌  Gagal menjalankan server. Pastikan Python 3 sudah terinstall."
    exit 1
fi

echo "✅  Server berjalan (PID: $SERVER_PID)"
echo "🌐  Membuka Safari: $URL"
echo ""
echo "  Tekan Ctrl+C untuk menghentikan server."
echo "============================================"
echo ""

# Buka di Safari
open -a Safari "$URL"

# Tunggu hingga user menekan Ctrl+C
trap "echo ''; echo '🛑  Server dihentikan.'; kill $SERVER_PID 2>/dev/null; exit 0" INT
wait $SERVER_PID
