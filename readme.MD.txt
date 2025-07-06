Aplikasi Dashboard Bisnis Streamlit
Aplikasi ini adalah dashboard interaktif yang dibangun dengan Streamlit untuk membantu Anda menganalisis data penjualan, inbound barang, dan stok. Dashboard ini menyediakan wawasan penting tentang kinerja bisnis Anda melalui berbagai visualisasi dan metrik.

Fitur Utama
Autentikasi Pengguna: Sistem login sederhana untuk membedakan pengguna biasa dan admin.

Unggah Data (Admin Only): Admin dapat mengunggah file Excel untuk data Master SKU, Penjualan, Inbound Barang, dan Stok.

Penyimpanan Data Lokal: Data yang diunggah oleh admin disimpan secara lokal untuk sesi mendatang.

Filter Interaktif: Filter berdasarkan rentang tanggal, kategori produk, lokasi penjualan, dan nama produk untuk analisis yang disesuaikan.

Ringkasan KPI: Menampilkan metrik kinerja utama seperti Total Penjualan, Laba Kotor, Kuantitas Terjual, Barang Masuk, Stok Tersedia, dan Perputaran Stok.

Analisis Penjualan Mendalam:

Penjualan berdasarkan Kategori, Sub Kategori, Tahun Produksi, Musim, Warna, dan Ukuran.

Analisis Profitabilitas berdasarkan Kategori dan Sub Kategori.

Analisis Produk Deffect.

Prediksi Penjualan menggunakan Moving Average, ETS, ARIMA, dan Prophet.

Perbandingan Penjualan Periode (YoY dan MoM).

Penjualan Berdasarkan Saluran.

10 Produk Terlaris.

Tren Penjualan Bulanan.

Analisis Pelanggan (RFM): Segmentasi pelanggan berdasarkan Recency, Frequency, dan Monetary value.

Analisis Pemasok: Kinerja pemasok berdasarkan kuantitas diterima dan jumlah belanja.

Analisis Stok & Barang Masuk:

Ringkasan stok saat ini.

Perbandingan Stok Tersedia vs. Barang Diterima.

Distribusi Stok Berdasarkan Lokasi.

Notifikasi Stok Minimum untuk produk terlaris.

Rekomendasi Otomatis: Mengidentifikasi produk dengan stok rendah/penjualan tinggi dan stok berlebih.

Peringatan & Notifikasi: Atur ambang batas untuk metrik utama dan dapatkan peringatan jika kinerja di bawah target.

Analisis Skenario 'Bagaimana Jika': Simulasikan dampak perubahan harga atau kuantitas pada penjualan dan laba.

Analisis Korelasi: Pahami hubungan antara penjualan bersih dan laba kotor pada berbagai tingkat agregasi.

Analisis Tren Harga Produk: Visualisasikan perubahan harga produk tertentu seiring waktu.

Ekspor Laporan: Unduh data yang difilter dalam format CSV atau Excel.

Persyaratan
Untuk menjalankan aplikasi ini, Anda memerlukan Python dan pustaka berikut:

streamlit

pandas

plotly

openpyxl (untuk membaca/menulis file Excel)

statsmodels (untuk ETS dan ARIMA)

prophet (untuk model Prophet)

Anda dapat menginstal semua dependensi ini menggunakan pip:

pip install streamlit pandas plotly openpyxl statsmodels prophet

Cara Menjalankan Aplikasi
Simpan Kode: Simpan kode Python yang disediakan ke dalam sebuah file (misalnya, dashboard_app.py).

Buka Terminal: Navigasikan ke direktori tempat Anda menyimpan file dashboard_app.py di terminal atau command prompt Anda.

Jalankan Aplikasi: Eksekusi perintah berikut:

streamlit run dashboard_app.py

Akses Dashboard: Aplikasi akan terbuka di browser web default Anda (biasanya di http://localhost:8501).

Cara Menggunakan
Login:

Di sidebar, masukkan ID Pengguna Anda.

Jika Anda adalah admin (misalnya, masukkan admin atau ID admin yang telah Anda tentukan di kode), Anda akan memiliki akses ke fitur unggah data.

Klik "Login / Muat Data". Aplikasi akan mencoba memuat data yang disimpan sebelumnya oleh admin.

Unggah Data (Admin Only):

Jika Anda login sebagai admin, Anda akan melihat bagian "Unggah file Excel Anda di bawah ini" di sidebar.

Unggah file Excel Anda untuk Master SKU, Penjualan, Inbound Barang, dan Stok Barang.

Penting: Unggah file Master SKU terlebih dahulu karena diperlukan untuk parsing SKU di data lain.

Setelah mengunggah semua file, klik "Simpan Data & Perbarui Dashboard" untuk memproses dan menyimpan data secara lokal.

Filter Data:

Gunakan filter di sidebar (Rentang Tanggal Penjualan, Kategori, Lokasi Penjualan, Nama Produk) untuk menyesuaikan data yang ditampilkan di dashboard.

Jelajahi Tab Dashboard:

Dashboard dibagi menjadi beberapa tab untuk berbagai jenis analisis (Penjualan, Pelanggan, Pemasok, Stok, Prediksi, dll.).

Klik pada setiap tab untuk melihat visualisasi dan metrik yang relevan.

Analisis Prediksi:

Di tab "Prediksi Penjualan", pilih tipe prediksi (Penjualan Bersih atau Jumlah Terjual), model prediksi (Rata-rata Bergerak, ETS, ARIMA, Prophet), dan horizon prediksi.

Analisis 'Bagaimana Jika':

Di tab "Analisis Skenario 'Bagaimana Jika'", pilih cakupan skenario (Semua Penjualan, Kategori Tertentu, Produk Tertentu) dan sesuaikan persentase perubahan harga dan kuantitas untuk melihat dampaknya.

Ekspor Laporan:

Di bagian bawah dashboard, Anda dapat mengunduh data yang difilter sebagai file CSV atau Excel.

Struktur Data yang Diharapkan (Untuk File Excel)
Aplikasi ini mengharapkan format kolom tertentu dalam file Excel Anda. Pastikan nama kolom Anda sesuai dengan yang diharapkan (atau sesuaikan kode load_data jika nama kolom Anda berbeda).

Master SKU:

CODE: Kode SKU

ARTI: Arti atau deskripsi kode

JENIS: Tipe kode (misalnya, CATEGORY, SUB CATEGORY, SEASON, WARNA, UKURAN, TAHUN PRODUKSI, SINGKATAN DARI NAMA PRODUK, DEFFECT)

Data Penjualan:

Tanggal: Tanggal dan waktu transaksi (format %d/%m/%Y %H:%M)

SKU: Kode SKU produk

QTY: Kuantitas terjual

Harga: Harga per unit

Sub Total: Sub total penjualan

Nett Sales: Penjualan bersih

HPP: Harga Pokok Penjualan

Gross Profit: Laba kotor

Channel: Saluran penjualan

Customer ID: ID pelanggan

No Transaksi (atau No. Transaksi, ID Transaksi, Nomor Transaksi, Order ID, Transaction ID): Nomor transaksi unik

Nama Barang: Nama produk

Lokasi: Lokasi penjualan

Data Inbound Barang:

Tanggal: Tanggal barang diterima

SKU: Kode SKU produk

Qty Diterima: Kuantitas barang yang diterima

Harga: Harga beli per unit

Amount: Total jumlah pembelian

Nama Supplier (atau supplier_name): Nama pemasok

No PO (atau purchaseorder_no): Nomor Purchase Order

No Bill (atau bill_no): Nomor Bill/Faktur

Catatan: Catatan tambahan

Pajak Total (atau Pajak.1): Total pajak

Grand Total: Total keseluruhan

Data Stok Barang:

SKU: Kode SKU produk

Nama Item (atau Nama): Nama item

Lokasi: Lokasi penyimpanan stok

QTY: Total kuantitas stok

Dipesan: Kuantitas yang dipesan

Tersedia: Kuantitas yang tersedia

Harga Jual: Harga jual per unit

HPP: Harga Pokok Penjualan per unit

Nilai Persediaan: Nilai total persediaan

is_bundle: Indikator apakah item adalah bundle

Catatan Tambahan
Aplikasi ini menyimpan data yang diunggah secara lokal di folder user_data/admin/. Ini berarti data akan tetap ada meskipun Anda menutup dan membuka kembali aplikasi, tetapi tidak dirancang untuk multi-pengguna atau produksi skala besar tanpa integrasi database yang sebenarnya.

Jika Anda mengalami masalah, pastikan format file Excel Anda sesuai dengan struktur yang diharapkan.