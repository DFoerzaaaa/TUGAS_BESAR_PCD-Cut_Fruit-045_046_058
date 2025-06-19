# Instruksi Menjalankan Proyek
1. Persiapan Lingkungan:
    Pastikan Python 3.8 atau lebih tinggi terinstal.
    Instal dependensi dengan perintah:
   
       pip install -r requirements.txt

2. Struktur Direktori:
   - Pastikan folder Fruits berisi gambar buah dan bom.
   - File fru.jpg (gambar game over), slice.wav, dan explosion.wav ada di direktori utama.
   - File gambar semangka.png, apel.png, bom.png, dan keranjang.png ada untuk permainan Fruit Catcher.

3. Menjalankan Aplikasi:
   - Jalankan aplikasi Streamlit dengan perintah:

      streamlit run main.py
   
   - Buka browser di http://localhost:8501 untuk mengakses menu permainan.

# Catatan:
Pastikan webcam tersambung untuk mendeteksi pose/muka.
File permainan (nose_fruit.py, fruit_eater.py, fruit_catcher.py) harus ada di direktori yang sama dengan main.py.

# Troubleshooting:
Jika ada error file tidak ditemukan, periksa path file gambar dan suara.
Pastikan semua dependensi terinstal dengan benar.

Referensi : https://github.com/SUcy6/mediapipe-game.git 
