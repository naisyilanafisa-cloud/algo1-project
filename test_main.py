import unittest
import io
import os
import shutil
import tempfile
from contextlib import redirect_stdout
from datetime import date, timedelta
from unittest.mock import patch

# Import modul yang diuji
import main

class TestSistemPenyewaan(unittest.TestCase):
    def setUp(self):
        # Buat temporary directory untuk isolasi file CSV
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)
        main.inisialisasi_file()

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)

    # --- 1. Helper Function Tests ---
    def test_format_rupiah(self):
        self.assertEqual(main.format_rupiah(50000), "Rp 50.000")
        self.assertEqual(main.format_rupiah(1250000), "Rp 1.250.000")
        self.assertEqual(main.format_rupiah(0), "Rp 0")

    def test_hitung_hari(self):
        d1 = date(2026, 11, 20)
        d2 = date(2026, 11, 22)
        self.assertEqual(main.hitung_hari(d1, d2), 3)
        self.assertEqual(main.hitung_hari(d1, d1), 1)

    def test_format_dan_parse_tanggal(self):
        d = date(2026, 11, 20)
        formatted = main.format_tanggal(d)
        self.assertEqual(formatted, "2026-11-20")
        parsed = main.parse_tanggal("2026-11-20")
        self.assertEqual(parsed, d)

    def test_buat_id(self):
        data = [{"id": "TRX0001"}, {"id": "TRX0005"}, {"id": "TRX0003"}]
        new_id = main.buat_id("TRX", data, "id")
        self.assertEqual(new_id, "TRX0006")
        empty_id = main.buat_id("TRX", [], "id")
        self.assertEqual(empty_id, "TRX0001")

    def test_cari_data(self):
        data = [{"kode": "BA01", "nama": "Bali"}, {"kode": "BA02", "nama": "Jawa"}]
        self.assertEqual(main.cari_data(data, "kode", "BA01")["nama"], "Bali")
        self.assertIsNone(main.cari_data(data, "kode", "BA99"))

    # --- 2. Inisialisasi & CSV Tests ---
    def test_inisialisasi_file(self):
        for fname in main.HEADERS.keys():
            self.assertTrue(os.path.exists(fname))
        users = main.baca_csv(main.FILE_USERS)
        self.assertTrue(any(u["username"] == "admin" for u in users))

    # --- 3. Auth Tests ---
    def test_register_pelanggan_valid(self):
        inputs = [
            "1234567890123456",  # NIK
            "Budi Santoso",       # Nama
            "081234567890",       # HP
            "Jl. Mawar No. 1",    # Alamat
            "budi01",             # Username
            "pass123",            # Password
            "Y"                   # Konfirmasi
        ]
        with patch("builtins.input", side_effect=inputs):
            main.register_pelanggan()

        users = main.baca_csv(main.FILE_USERS)
        user = main.cari_data(users, "username", "budi01")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "pelanggan")
        self.assertEqual(user["nik"], "1234567890123456")

    def test_register_pelanggan_invalid_nik_hp(self):
        # NIK bukan 16 digit
        with patch("builtins.input", side_effect=["123", "Budi", "08123456789", "Alamat", "budi", "p"]):
            main.register_pelanggan()
        self.assertIsNone(main.cari_data(main.baca_csv(main.FILE_USERS), "username", "budi"))

    def test_login_success(self):
        with patch("builtins.input", side_effect=["admin", "admin123"]):
            u = main.login()
            self.assertIsNotNone(u)
            self.assertEqual(u["username"], "admin")

    def test_login_fail(self):
        with patch("builtins.input", side_effect=["admin", "salah", "admin", "salah", "admin", "salah"]):
            u = main.login()
            self.assertIsNone(u)

    # --- 4. Katalog CRUD Tests ---
    def test_tambah_baju(self):
        inputs = ["BA01", "Baju Adat Jawa", "L", "50000", "10", "Y"]
        with patch("builtins.input", side_effect=inputs):
            main.tambah_baju()
        katalog = main.baca_csv(main.FILE_KATALOG)
        baju = main.cari_data(katalog, "kode", "BA01")
        self.assertIsNotNone(baju)
        self.assertEqual(baju["nama_baju"], "Baju Adat Jawa")
        self.assertEqual(baju["stok"], "10")

    def test_ubah_baju(self):
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju Lama", "ukuran": "M", "harga_sewa": "50000", "stok": "5"
        }])
        inputs = ["BA01", "Baju Baru", "L", "60000", "8", "Y"]
        with patch("builtins.input", side_effect=inputs):
            main.ubah_baju()
        katalog = main.baca_csv(main.FILE_KATALOG)
        baju = main.cari_data(katalog, "kode", "BA01")
        self.assertEqual(baju["nama_baju"], "Baju Baru")
        self.assertEqual(baju["ukuran"], "L")
        self.assertEqual(baju["harga_sewa"], "60000")
        self.assertEqual(baju["stok"], "8")

    def test_hapus_baju(self):
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju Hapus", "ukuran": "M", "harga_sewa": "50000", "stok": "5"
        }])
        with patch("builtins.input", side_effect=["BA01", "Y"]):
            main.hapus_baju()
        katalog = main.baca_csv(main.FILE_KATALOG)
        self.assertIsNone(main.cari_data(katalog, "kode", "BA01"))

    # --- 5. Pelanggan CRUD (Admin) Tests ---
    def test_tambah_pelanggan_admin(self):
        inputs = ["1122334455667788", "Siti Aminah", "081298765432", "Bandung", "siti01", "siti123"]
        with patch("builtins.input", side_effect=inputs):
            main.tambah_pelanggan_admin()
        users = main.baca_csv(main.FILE_USERS)
        self.assertIsNotNone(main.cari_data(users, "username", "siti01"))

    def test_ubah_pelanggan(self):
        users = main.baca_csv(main.FILE_USERS)
        users.append({
            "username": "siti01", "password": "123", "nik": "1122334455667788",
            "nama_lengkap": "Siti", "no_hp": "081298765432", "alamat": "Bandung", "role": "pelanggan"
        })
        main.simpan_csv(main.FILE_USERS, users)
        inputs = ["siti01", "Siti Baru", "", "", "Jakarta", "", "Y"]
        with patch("builtins.input", side_effect=inputs):
            main.ubah_pelanggan()
        u = main.cari_data(main.baca_csv(main.FILE_USERS), "username", "siti01")
        self.assertEqual(u["nama_lengkap"], "Siti Baru")
        self.assertEqual(u["alamat"], "Jakarta")

    def test_hapus_pelanggan(self):
        users = main.baca_csv(main.FILE_USERS)
        users.append({
            "username": "hapus01", "password": "123", "nik": "9988776655443322",
            "nama_lengkap": "Hapus Me", "no_hp": "081200001111", "alamat": "Kota", "role": "pelanggan"
        })
        main.simpan_csv(main.FILE_USERS, users)
        with patch("builtins.input", side_effect=["hapus01", "Y"]):
            main.hapus_pelanggan()
        u = main.cari_data(main.baca_csv(main.FILE_USERS), "username", "hapus01")
        self.assertIsNone(u)

    # --- 6. Perhitungan Sewa, Diskon & Stok Overlap Tests ---
    def test_hitung_total_sewa_pelanggan_baru(self):
        # NIK baru -> diskon 10%
        nik = "3501234567890001"
        subtotal, diskon, total, is_baru = main.hitung_total_sewa(50000, 2, 3, nik)
        self.assertTrue(is_baru)
        self.assertEqual(subtotal, 300000)
        self.assertEqual(diskon, 30000)
        self.assertEqual(total, 270000)

    def test_hitung_total_sewa_pelanggan_lama(self):
        nik = "3501234567890001"
        # Tambahkan transaksi sebelumnya
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "nik": nik, "status": "SELESAI"
        }])
        subtotal, diskon, total, is_baru = main.hitung_total_sewa(50000, 2, 3, nik)
        self.assertFalse(is_baru)
        self.assertEqual(diskon, 0)
        self.assertEqual(total, 300000)
        # NIK lain tidak punya transaksi -> dianggap pelanggan baru
        self.assertTrue(main.pelanggan_baru_berdasarkan_nik("3509999999999999"))

    def test_stok_tersedia_overlap(self):
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju", "ukuran": "M", "harga_sewa": "50000", "stok": "5"
        }])
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "kode_baju": "BA01", "jumlah": "2",
            "tanggal_mulai": "2026-11-20", "tanggal_selesai": "2026-11-25",
            "status": "RESERVASI"
        }])
        # Periode overlap (2026-11-22 s.d 2026-11-23) -> terpakai 2, sisa 3
        tersedia = main.stok_tersedia("BA01", date(2026, 11, 22), date(2026, 11, 23))
        self.assertEqual(tersedia, 3)

        # Periode di luar sewa (2026-11-26 s.d 2026-11-28) -> sisa 5
        tersedia_bebas = main.stok_tersedia("BA01", date(2026, 11, 26), date(2026, 11, 28))
        self.assertEqual(tersedia_bebas, 5)

    # --- 7. Buat Reservasi & Pembayaran Tests ---
    def test_buat_reservasi(self):
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju Bali", "ukuran": "M", "harga_sewa": "50000", "stok": "5"
        }])
        user = {
            "username": "user01", "nik": "1234567890123456", "nama_lengkap": "User Test", "no_hp": "081234567890"
        }
        # Input: kode, mulai, selesai, jumlah, konfirmasi
        future_start = (date.today().year + 1)
        start_str = f"{future_start}-05-01"
        end_str = f"{future_start}-05-03"
        inputs = ["BA01", start_str, end_str, "2", "Y"]
        with patch("builtins.input", side_effect=inputs):
            main.buat_reservasi(user)

        trx = main.baca_csv(main.FILE_TRANSAKSI)
        self.assertEqual(len(trx), 1)
        self.assertEqual(trx[0]["status"], "RESERVASI")
        self.assertEqual(trx[0]["kode_baju"], "BA01")
        self.assertEqual(trx[0]["lama_sewa"], "3")

    def test_kelola_pembayaran(self):
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "nama_penyewa": "Budi", "total_bayar": "270000",
            "denda": "0", "status": "RESERVASI"
        }])
        # Bayar DP 100.000 tunai
        inputs = ["TRX0001", "100000", "1"]
        with patch("builtins.input", side_effect=inputs):
            main.kelola_pembayaran()

        pmb = main.baca_csv(main.FILE_PEMBAYARAN)
        self.assertEqual(len(pmb), 1)
        self.assertEqual(pmb[0]["id_transaksi"], "TRX0001")
        self.assertEqual(pmb[0]["jumlah_bayar"], "100000")
        self.assertEqual(pmb[0]["keterangan"], "DP/Angsuran")
        self.assertEqual(main.total_pembayaran_transaksi("TRX0001"), 100000)

    # --- 8. Pengembalian & Denda Tests ---
    def test_proses_pengembalian_dengan_denda(self):
        selesai = date.today() - timedelta(days=2)
        mulai = selesai - timedelta(days=2)
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "status": "DISEWA", "kode_baju": "BA01",
            "nama_penyewa": "Budi", "tanggal_mulai": mulai.isoformat(), "tanggal_selesai": selesai.isoformat(),
            "total_bayar": "150000", "denda": "0", "tanggal_pengembalian": ""
        }])
        # Kembali hari ini -> terlambat 2 hari -> denda 40.000
        inputs = ["TRX0001", date.today().isoformat(), "1", "Lengkap", "Y"]
        with patch("builtins.input", side_effect=inputs):
            main.proses_pengembalian()

        trx = main.cari_data(main.baca_csv(main.FILE_TRANSAKSI), "id_transaksi", "TRX0001")
        self.assertEqual(trx["status"], "SELESAI")
        self.assertEqual(trx["denda"], "40000")
        self.assertEqual(trx["tanggal_pengembalian"], date.today().isoformat())

        ret = main.baca_csv(main.FILE_PENGEMBALIAN)
        self.assertEqual(len(ret), 1)
        self.assertEqual(ret[0]["terlambat_hari"], "2")
        self.assertEqual(ret[0]["denda"], "40000")

    # --- 9. Display & Report Functions Tests ---
    def test_display_functions_no_error(self):
        # Pastikan tidak crash saat dipanggil
        main.tampilkan_katalog()
        main.tampilkan_pelanggan()
        main.tampilkan_transaksi()
        main.tampilkan_riwayat_pengembalian()
        main.laporan_stok()

    def test_laporan_pendapatan_semua(self):
        main.simpan_csv(main.FILE_PEMBAYARAN, [{
            "id_pembayaran": "PAY0001", "id_transaksi": "TRX0001", "tanggal": "2026-11-20 10:00",
            "metode": "Tunai", "jumlah_bayar": "150000", "keterangan": "Pelunasan"
        }])
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "total_bayar": "150000", "denda": "0", "status": "SELESAI", "nama_penyewa": "Budi"
        }])
        with patch("builtins.input", side_effect=["1"]):
            main.laporan_pendapatan()

    # --- 10. Regression Tests ---
    def test_ubah_transaksi_mempertahankan_diskon_pelanggan_baru(self):
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju", "ukuran": "M", "harga_sewa": "50000", "stok": "5"
        }])
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "username": "user01", "nik": "3501234567890001",
            "nama_penyewa": "User", "no_hp": "081234567890", "kode_baju": "BA01",
            "nama_baju": "Baju", "jumlah": "2", "tanggal_mulai": "2027-05-01",
            "tanggal_selesai": "2027-05-03", "lama_sewa": "3", "harga_per_hari": "50000",
            "subtotal": "300000", "diskon": "30000", "total_bayar": "270000",
            "status": "RESERVASI", "tanggal_transaksi": "2026-11-24 10:00",
            "denda": "0", "tanggal_pengembalian": ""
        }])
        with patch("builtins.input", side_effect=["TRX0001", "", "", "", "Y"]):
            main.ubah_transaksi()
        trx = main.cari_data(main.baca_csv(main.FILE_TRANSAKSI), "id_transaksi", "TRX0001")
        self.assertEqual(trx["diskon"], "30000")
        self.assertEqual(trx["total_bayar"], "270000")

    def test_simpan_csv_atomik(self):
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju", "ukuran": "M", "harga_sewa": "50000", "stok": "5"
        }])
        self.assertFalse(os.path.exists(main.FILE_KATALOG + ".tmp"))
        self.assertEqual(len(main.baca_csv(main.FILE_KATALOG)), 1)

        # Gagal saat replace: file lama harus tetap utuh.
        with open(main.FILE_KATALOG, encoding="utf-8") as f:
            isi_lama = f.read()
        with patch("main.os.replace", side_effect=OSError("gagal tulis")):
            with self.assertRaises(OSError):
                main.simpan_csv(main.FILE_KATALOG, [])
        with open(main.FILE_KATALOG, encoding="utf-8") as f:
            self.assertEqual(f.read(), isi_lama)

    def test_pengembalian_masa_depan_ditolak(self):
        mulai = date.today() - timedelta(days=2)
        selesai = date.today() + timedelta(days=2)
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "status": "DISEWA", "kode_baju": "BA01",
            "nama_penyewa": "Budi", "tanggal_mulai": mulai.isoformat(),
            "tanggal_selesai": selesai.isoformat(), "total_bayar": "150000",
            "denda": "0", "tanggal_pengembalian": ""
        }])
        besok = (date.today() + timedelta(days=1)).isoformat()
        with patch("builtins.input", side_effect=["TRX0001", besok]):
            main.proses_pengembalian()
        trx = main.cari_data(main.baca_csv(main.FILE_TRANSAKSI), "id_transaksi", "TRX0001")
        self.assertEqual(trx["status"], "DISEWA")
        self.assertEqual(main.baca_csv(main.FILE_PENGEMBALIAN), [])

    def test_laporan_bulan_tidak_valid(self):
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["2", "13", "2026"]), redirect_stdout(buf):
            main.laporan_pendapatan()
        self.assertIn("Bulan harus 01-12", buf.getvalue())

    def test_laporan_rentang_tahan_tanggal_rusak(self):
        main.simpan_csv(main.FILE_PEMBAYARAN, [{
            "id_pembayaran": "PAY0001", "id_transaksi": "TRX0001", "tanggal": "",
            "metode": "Tunai", "jumlah_bayar": "150000", "keterangan": "Pelunasan"
        }])
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["3", "2027-01-01", "2027-12-31"]), redirect_stdout(buf):
            main.laporan_pendapatan()
        self.assertIn("1 pembayaran bertanggal tidak valid dilewati", buf.getvalue())

    def test_stok_batas_hari_dan_status_batal(self):
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju", "ukuran": "M", "harga_sewa": "50000", "stok": "5"
        }])
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "kode_baju": "BA01", "jumlah": "2",
            "tanggal_mulai": "2026-11-20", "tanggal_selesai": "2026-11-22",
            "status": "RESERVASI"
        }])
        # Tanggal mulai baru sama dengan tanggal selesai lama tetap beririsan.
        self.assertEqual(main.stok_tersedia("BA01", date(2026, 11, 22), date(2026, 11, 22)), 3)
        # Sehari setelah selesai sudah bebas.
        self.assertEqual(main.stok_tersedia("BA01", date(2026, 11, 23), date(2026, 11, 23)), 5)
        # BATAL tidak mengunci stok.
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "kode_baju": "BA01", "jumlah": "2",
            "tanggal_mulai": "2026-11-20", "tanggal_selesai": "2026-11-22",
            "status": "BATAL"
        }])
        self.assertEqual(main.stok_tersedia("BA01", date(2026, 11, 20), date(2026, 11, 22)), 5)

    def test_hitung_diskon_abaikan_transaksi_batal(self):
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "nik": "3501234567890001", "status": "BATAL"
        }])
        _, diskon, _, baru = main.hitung_total_sewa(50000, 2, 3, "3501234567890001")
        self.assertTrue(baru)
        self.assertEqual(diskon, 30000)

    def test_tolak_pembayaran_lebih_bayar_dan_batal(self):
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "nama_penyewa": "Budi", "total_bayar": "100000",
            "denda": "0", "status": "RESERVASI"
        }])
        with patch("builtins.input", side_effect=["TRX0001", "150000"]):
            main.kelola_pembayaran()
        self.assertEqual(len(main.baca_csv(main.FILE_PEMBAYARAN)), 0)

        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "nama_penyewa": "Budi", "total_bayar": "100000",
            "denda": "0", "status": "BATAL"
        }])
        with patch("builtins.input", side_effect=["TRX0001", "1000", "1"]):
            main.kelola_pembayaran()
        self.assertEqual(len(main.baca_csv(main.FILE_PEMBAYARAN)), 0)

    def test_denda_tepat_waktu_nol(self):
        selesai = date.today()
        mulai = selesai - timedelta(days=2)
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "status": "DISEWA", "kode_baju": "BA01",
            "nama_penyewa": "Budi", "tanggal_mulai": mulai.isoformat(),
            "tanggal_selesai": selesai.isoformat(), "total_bayar": "150000",
            "denda": "0", "tanggal_pengembalian": ""
        }])
        with patch("builtins.input", side_effect=["TRX0001", "", "1", "", "Y"]):
            main.proses_pengembalian()
        trx = main.cari_data(main.baca_csv(main.FILE_TRANSAKSI), "id_transaksi", "TRX0001")
        self.assertEqual(trx["status"], "SELESAI")
        self.assertEqual(trx["denda"], "0")
        self.assertEqual(len(main.baca_csv(main.FILE_PENGEMBALIAN)), 1)

    def test_hapus_transaksi_selesai_ditolak(self):
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "status": "SELESAI", "total_bayar": "100000",
            "denda": "0", "nama_penyewa": "Budi"
        }])
        with patch("builtins.input", side_effect=["TRX0001"]):
            main.hapus_transaksi()
        self.assertIsNotNone(main.cari_data(main.baca_csv(main.FILE_TRANSAKSI), "id_transaksi", "TRX0001"))

    def test_laporan_piutang_tidak_tertutup_transaksi_batal(self):
        main.simpan_csv(main.FILE_TRANSAKSI, [
            {"id_transaksi": "TRX1", "total_bayar": "100000", "denda": "0", "status": "BATAL", "nama_penyewa": "Batal"},
            {"id_transaksi": "TRX2", "total_bayar": "100000", "denda": "0", "status": "RESERVASI", "nama_penyewa": "Aktif"},
        ])
        main.simpan_csv(main.FILE_PEMBAYARAN, [{
            "id_pembayaran": "PAY1", "id_transaksi": "TRX1", "tanggal": "2026-11-20 10:00",
            "metode": "Tunai", "jumlah_bayar": "100000", "keterangan": "Pelunasan"
        }])
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["1"]), redirect_stdout(buf):
            main.laporan_pendapatan()
        piutang = next(l for l in buf.getvalue().splitlines() if l.startswith("Piutang tersisa"))
        self.assertTrue(piutang.endswith("Rp 100.000"))

    def test_alur_lengkap_dari_register_sampai_laporan(self):
        mulai = date.today()
        selesai = mulai + timedelta(days=2)
        inputs = [
            "9", "2",  # menu utama invalid, lalu register
            "3501234567890123", "Budi Santoso", "081234567890", "Jember", "budi01", "pass123", "Y",
            "1", "budi01", "pass123",  # login pelanggan
            "9", "",  # menu invalid + jeda
            "1", "",  # katalog kosong + jeda
            "9", "", "0", "Y",  # invalid + jeda, logout
            "9", "1", "admin", "admin123",  # menu utama invalid, login admin
            "9", "",  # menu admin invalid + jeda
            "1", "9", "2",  # submenu katalog invalid, tambah baju
            "BA01", "Baju Bali", "M", "50000", "5", "Y",
            "0", "",  # kembali + jeda admin
            "0", "Y",  # logout admin
            "1", "budi01", "pass123",  # login pelanggan
            "9", "",  # invalid + jeda
            "3", "BA01", mulai.isoformat(), selesai.isoformat(), "2", "Y", "",
            "4", "",  # riwayat + jeda
            "5", "",  # status bayar + jeda
            "0", "Y",  # logout
            "1", "admin", "admin123",  # login admin
            "3", "9", "5", "TRX0001", "1", "Y", "0", "",  # konfirmasi reservasi
            "5", "TRX0001", "100000", "1", "Y", "TRX0001", "",  # DP + riwayat
            "6", "TRX0001", "", "1", "Lengkap", "Y", "",  # pengembalian
            "8", "1", "",  # laporan pendapatan
            "9", "",  # laporan stok
            "7", "",  # riwayat pengembalian
            "4", "",  # lihat reservasi
            "0", "Y",  # logout admin
            "0", "Y",  # keluar
        ]
        with patch("builtins.input", side_effect=inputs) as mock_input, redirect_stdout(io.StringIO()):
            main.main()
        self.assertEqual(mock_input.call_count, len(inputs))

        trx = main.cari_data(main.baca_csv(main.FILE_TRANSAKSI), "id_transaksi", "TRX0001")
        self.assertEqual(trx["status"], "SELESAI")
        self.assertEqual(trx["diskon"], "30000")
        self.assertEqual(trx["total_bayar"], "270000")
        self.assertEqual(trx["denda"], "0")
        self.assertEqual(main.total_pembayaran_transaksi("TRX0001"), 100000)
        self.assertEqual(len(main.baca_csv(main.FILE_PENGEMBALIAN)), 1)
        self.assertEqual(main.baca_csv(main.FILE_PENGEMBALIAN)[0]["kondisi"], "Baik")
        baju = main.cari_data(main.baca_csv(main.FILE_KATALOG), "kode", "BA01")
        self.assertEqual(baju["stok"], "5")

    def test_menu_pelanggan_admin_semua_opsi(self):
        inputs = [
            "1",
            "2", "1122334455667788", "Siti Aminah", "081298765432", "Bandung", "siti01", "siti123",
            "3", "siti01", "", "", "", "Jakarta", "", "Y",
            "4", "siti01", "Y",
            "5", "siti",
            "0",
        ]
        with patch("builtins.input", side_effect=inputs), redirect_stdout(io.StringIO()):
            main.menu_pelanggan_admin()
        self.assertIsNone(main.cari_data(main.baca_csv(main.FILE_USERS), "username", "siti01"))

    def test_menu_katalog_admin_semua_opsi(self):
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju Lama", "ukuran": "M", "harga_sewa": "50000", "stok": "5"
        }])
        inputs = ["1", "5", "baju", "3", "BA01", "", "", "", "", "Y", "4", "BA01", "Y", "0"]
        with patch("builtins.input", side_effect=inputs), redirect_stdout(io.StringIO()):
            main.menu_katalog_admin()
        self.assertEqual(main.baca_csv(main.FILE_KATALOG), [])

    def test_menu_transaksi_admin_semua_opsi(self):
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju", "ukuran": "M", "harga_sewa": "50000", "stok": "5"
        }])
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "username": "u", "nik": "3501234567890001",
            "nama_penyewa": "Budi", "no_hp": "0812", "kode_baju": "BA01", "nama_baju": "Baju",
            "jumlah": "1", "tanggal_mulai": "2027-05-01", "tanggal_selesai": "2027-05-02",
            "lama_sewa": "2", "harga_per_hari": "50000", "subtotal": "100000", "diskon": "10000",
            "total_bayar": "90000", "status": "RESERVASI", "tanggal_transaksi": "2026-11-24 10:00",
            "denda": "0", "tanggal_pengembalian": ""
        }])
        inputs = ["1", "2", "TRX0001", "3", "TRX0001", "", "", "", "Y", "4", "TRX0001", "Y", "0"]
        with patch("builtins.input", side_effect=inputs), redirect_stdout(io.StringIO()):
            main.menu_transaksi_admin()
        self.assertEqual(main.baca_csv(main.FILE_TRANSAKSI), [])

    def test_menu_admin_opsi_pelanggan(self):
        with patch("builtins.input", side_effect=["2", "0", "", "0", "Y"]), redirect_stdout(io.StringIO()):
            main.menu_admin({"username": "admin", "nama_lengkap": "Administrator", "role": "admin"})

    def test_hapus_baju_aktif_ditolak(self):
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju", "ukuran": "M", "harga_sewa": "50000", "stok": "5"
        }])
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX0001", "kode_baju": "BA01", "status": "RESERVASI"
        }])
        with patch("builtins.input", side_effect=["BA01", "Y"]), redirect_stdout(io.StringIO()):
            main.hapus_baju()
        self.assertIsNotNone(main.cari_data(main.baca_csv(main.FILE_KATALOG), "kode", "BA01"))

    def test_ubah_baju_validasi_dan_tidak_ada(self):
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju", "ukuran": "M", "harga_sewa": "50000", "stok": "5"
        }])
        with patch("builtins.input", side_effect=["BA99"]), redirect_stdout(io.StringIO()):
            main.ubah_baju()
        with patch("builtins.input", side_effect=["BA01", "", "", "0", ""]), redirect_stdout(io.StringIO()):
            main.ubah_baju()
        baju = main.cari_data(main.baca_csv(main.FILE_KATALOG), "kode", "BA01")
        self.assertEqual(baju["harga_sewa"], "50000")

    def test_buat_reservasi_tolak_kasus(self):
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju", "ukuran": "M", "harga_sewa": "50000", "stok": "1"
        }])
        user = {"username": "u", "nik": "3501234567890001", "nama_lengkap": "U", "no_hp": "0812"}
        hari_ini, besok = date.today(), date.today() + timedelta(days=1)
        kemarin = hari_ini - timedelta(days=1)
        kasus = [
            ["BA99"],
            ["BA01", besok.isoformat(), hari_ini.isoformat()],
            ["BA01", kemarin.isoformat(), hari_ini.isoformat()],
            ["BA01", hari_ini.isoformat(), hari_ini.isoformat(), "2"],
            ["BA01", hari_ini.isoformat(), hari_ini.isoformat(), "1", "N"],
        ]
        for inp in kasus:
            with patch("builtins.input", side_effect=inp), redirect_stdout(io.StringIO()):
                main.buat_reservasi(user)
        self.assertEqual(main.baca_csv(main.FILE_TRANSAKSI), [])

    def test_pembayaran_lunas_metode_invalid_dan_tidak_ada(self):
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX1", "nama_penyewa": "Budi", "total_bayar": "100000",
            "denda": "0", "status": "RESERVASI"
        }])
        with patch("builtins.input", side_effect=["TRX9"]), redirect_stdout(io.StringIO()):
            main.kelola_pembayaran()
        with patch("builtins.input", side_effect=["TRX1", "1000", "9"]), redirect_stdout(io.StringIO()):
            main.kelola_pembayaran()
        self.assertEqual(main.baca_csv(main.FILE_PEMBAYARAN), [])
        with patch("builtins.input", side_effect=["TRX1", "100000", "2"]), redirect_stdout(io.StringIO()):
            main.kelola_pembayaran()
        pmb = main.baca_csv(main.FILE_PEMBAYARAN)
        self.assertEqual(pmb[0]["keterangan"], "Pelunasan")
        self.assertEqual(pmb[0]["metode"], "Transfer")
        with patch("builtins.input", side_effect=["TRX1"]), redirect_stdout(io.StringIO()):
            main.kelola_pembayaran()
        self.assertEqual(len(main.baca_csv(main.FILE_PEMBAYARAN)), 1)

    def test_riwayat_pembayaran_kosong_dan_isi(self):
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["TRX1"]), redirect_stdout(buf):
            main.riwayat_pembayaran()
        self.assertIn("Belum ada pembayaran", buf.getvalue())
        main.simpan_csv(main.FILE_PEMBAYARAN, [{
            "id_pembayaran": "PAY1", "id_transaksi": "TRX1", "tanggal": "2026-11-20 10:00",
            "metode": "Tunai", "jumlah_bayar": "50000", "keterangan": "DP/Angsuran"
        }])
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["TRX1"]), redirect_stdout(buf):
            main.riwayat_pembayaran()
        self.assertIn("Total dibayar: Rp 50.000", buf.getvalue())

    def test_pengembalian_kondisi_invalid_dan_batal(self):
        selesai = date.today()
        mulai = selesai - timedelta(days=2)
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "TRX1", "status": "DISEWA", "kode_baju": "BA01",
            "nama_penyewa": "Budi", "tanggal_mulai": mulai.isoformat(),
            "tanggal_selesai": selesai.isoformat(), "total_bayar": "150000",
            "denda": "0", "tanggal_pengembalian": ""
        }])
        with patch("builtins.input", side_effect=["TRX9"]), redirect_stdout(io.StringIO()):
            main.proses_pengembalian()
        with patch("builtins.input", side_effect=["TRX1", "", "9"]), redirect_stdout(io.StringIO()):
            main.proses_pengembalian()
        with patch("builtins.input", side_effect=["TRX1", "", "1", "", "N"]), redirect_stdout(io.StringIO()):
            main.proses_pengembalian()
        self.assertEqual(main.baca_csv(main.FILE_PENGEMBALIAN), [])
        trx = main.cari_data(main.baca_csv(main.FILE_TRANSAKSI), "id_transaksi", "TRX1")
        self.assertEqual(trx["status"], "DISEWA")

    def test_laporan_bulan_valid_rentang_invalid_dan_pilihan_invalid(self):
        main.simpan_csv(main.FILE_PEMBAYARAN, [
            {"id_pembayaran": "PAY1", "id_transaksi": "TRX1", "tanggal": "2026-11-20 10:00",
             "metode": "Tunai", "jumlah_bayar": "150000", "keterangan": "Pelunasan"},
            {"id_pembayaran": "PAY2", "id_transaksi": "TRX2", "tanggal": "2026-12-01 10:00",
             "metode": "Tunai", "jumlah_bayar": "200000", "keterangan": "Pelunasan"},
        ])
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["2", "11", "2026"]), redirect_stdout(buf):
            main.laporan_pendapatan()
        self.assertIn("Pendapatan diterima periode ini : Rp 150.000", buf.getvalue())
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["3", "2026-12-01", "2026-11-01"]), redirect_stdout(buf):
            main.laporan_pendapatan()
        self.assertIn("Rentang tanggal tidak valid", buf.getvalue())
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["9"]), redirect_stdout(buf):
            main.laporan_pendapatan()
        self.assertIn("Pilihan tidak valid", buf.getvalue())

    def test_cari_pelanggan_dan_cari_baju(self):
        main.simpan_csv(main.FILE_USERS, [
            {"username": "admin", "password": "admin123", "nik": "-", "nama_lengkap": "Admin",
             "no_hp": "-", "alamat": "-", "role": "admin"},
            {"username": "budi01", "password": "p", "nik": "3501234567890001",
             "nama_lengkap": "Budi", "no_hp": "081234567890", "alamat": "Jember", "role": "pelanggan"},
        ])
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju Bali", "ukuran": "M", "harga_sewa": "50000", "stok": "5"
        }])
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["budi"]), redirect_stdout(buf):
            main.cari_pelanggan()
        self.assertIn("budi01", buf.getvalue())
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["bali"]), redirect_stdout(buf):
            main.cari_baju()
        self.assertIn("BA01", buf.getvalue())

    def test_input_helper_loop(self):
        with patch("builtins.input", side_effect=["", "isi"]):
            self.assertEqual(main.input_wajib("x"), "isi")
        with patch("builtins.input", side_effect=["", "abc", "0", "5"]), redirect_stdout(io.StringIO()):
            self.assertEqual(main.input_angka("x", 1), 5)
        with patch("builtins.input", side_effect=["salah", "2026-01-02"]), redirect_stdout(io.StringIO()):
            self.assertEqual(main.input_tanggal("x"), date(2026, 1, 2))
        with patch("builtins.input", side_effect=["x", "y"]), redirect_stdout(io.StringIO()):
            self.assertTrue(main.konfirmasi("x"))
        with patch("builtins.input", side_effect=["n"]):
            self.assertFalse(main.konfirmasi("x"))

    def test_inisialisasi_migrasi_dan_baca_file_hilang(self):
        with open(main.FILE_USERS, "w", newline="", encoding="utf-8") as f:
            f.write("username,password,role\nlama,rahasia,pelanggan\n")
        main.inisialisasi_file()
        users = main.baca_csv(main.FILE_USERS)
        lama = main.cari_data(users, "username", "lama")
        self.assertEqual(lama["nik"], "")
        self.assertIsNotNone(main.cari_data(users, "username", "admin"))
        os.remove(main.FILE_KATALOG)
        self.assertEqual(main.baca_csv(main.FILE_KATALOG), [])

    def test_register_pelanggan_batal(self):
        inputs = ["3501234567890123", "Budi", "081234567890", "Jember", "budi01", "pass123", "N"]
        with patch("builtins.input", side_effect=inputs), redirect_stdout(io.StringIO()):
            main.register_pelanggan()
        self.assertIsNone(main.cari_data(main.baca_csv(main.FILE_USERS), "username", "budi01"))

    def test_stok_tersedia_lewati_baris_rusak(self):
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju", "ukuran": "M", "harga_sewa": "50000", "stok": "5"
        }])
        main.simpan_csv(main.FILE_TRANSAKSI, [
            {"id_transaksi": "TRX1", "kode_baju": "BA01", "jumlah": "2",
             "tanggal_mulai": "", "tanggal_selesai": "", "status": "RESERVASI"},
            {"id_transaksi": "TRX2", "kode_baju": "BA99", "jumlah": "2",
             "tanggal_mulai": "2026-01-01", "tanggal_selesai": "2026-01-02", "status": "RESERVASI"},
            {"id_transaksi": "TRX3", "kode_baju": "BA01", "jumlah": "2",
             "tanggal_mulai": date.today().isoformat(), "tanggal_selesai": date.today().isoformat(), "status": "RESERVASI"},
        ])
        self.assertEqual(main.stok_tersedia("BA01", date.today(), date.today()), 3)
        self.assertEqual(main.stok_tersedia("BA01", date.today(), date.today(), "TRX3"), 5)

    def test_ubah_transaksi_tolak_pembayaran_dan_jumlah_invalid(self):
        trx = {
            "id_transaksi": "TRX1", "username": "u", "nik": "3501234567890001",
            "nama_penyewa": "Budi", "no_hp": "0812", "kode_baju": "BA01", "nama_baju": "Baju",
            "jumlah": "1", "tanggal_mulai": "2027-05-01", "tanggal_selesai": "2027-05-02",
            "lama_sewa": "2", "harga_per_hari": "50000", "subtotal": "100000", "diskon": "0",
            "total_bayar": "100000", "status": "RESERVASI", "tanggal_transaksi": "2026-11-24 10:00",
            "denda": "0", "tanggal_pengembalian": ""
        }
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju", "ukuran": "M", "harga_sewa": "50000", "stok": "5"
        }])
        main.simpan_csv(main.FILE_TRANSAKSI, [trx])
        main.simpan_csv(main.FILE_PEMBAYARAN, [{
            "id_pembayaran": "PAY1", "id_transaksi": "TRX1", "tanggal": "2026-11-24 10:00",
            "metode": "Tunai", "jumlah_bayar": "10000", "keterangan": "DP/Angsuran"
        }])
        with patch("builtins.input", side_effect=["TRX1"]), redirect_stdout(io.StringIO()):
            main.ubah_transaksi()
        main.simpan_csv(main.FILE_PEMBAYARAN, [])
        with patch("builtins.input", side_effect=["TRX1", "", "", "0"]), redirect_stdout(io.StringIO()):
            main.ubah_transaksi()
        self.assertEqual(main.cari_data(main.baca_csv(main.FILE_TRANSAKSI), "id_transaksi", "TRX1")["jumlah"], "1")

    def test_ubah_status_transaksi_batal_dan_pilihan_invalid(self):
        trx = {
            "id_transaksi": "TRX1", "username": "u", "nik": "3501234567890001",
            "nama_penyewa": "Budi", "no_hp": "0812", "kode_baju": "BA01", "nama_baju": "Baju",
            "jumlah": "1", "tanggal_mulai": "2027-05-01", "tanggal_selesai": "2027-05-02",
            "lama_sewa": "2", "harga_per_hari": "50000", "subtotal": "100000", "diskon": "0",
            "total_bayar": "100000", "status": "RESERVASI", "tanggal_transaksi": "2026-11-24 10:00",
            "denda": "0", "tanggal_pengembalian": ""
        }
        main.simpan_csv(main.FILE_TRANSAKSI, [trx])
        with patch("builtins.input", side_effect=["TRX1", "2", "Y"]), redirect_stdout(io.StringIO()):
            main.ubah_status_transaksi()
        self.assertEqual(main.cari_data(main.baca_csv(main.FILE_TRANSAKSI), "id_transaksi", "TRX1")["status"], "BATAL")

        main.simpan_csv(main.FILE_TRANSAKSI, [trx])
        with patch("builtins.input", side_effect=["TRX1", "9"]), redirect_stdout(io.StringIO()):
            main.ubah_status_transaksi()
        self.assertEqual(main.cari_data(main.baca_csv(main.FILE_TRANSAKSI), "id_transaksi", "TRX1")["status"], "RESERVASI")

    def test_laporan_rentang_valid(self):
        main.simpan_csv(main.FILE_PEMBAYARAN, [{
            "id_pembayaran": "PAY1", "id_transaksi": "TRX1", "tanggal": "2026-11-20 10:00",
            "metode": "Tunai", "jumlah_bayar": "150000", "keterangan": "Pelunasan"
        }])
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["3", "2026-11-01", "2026-11-30"]), redirect_stdout(buf):
            main.laporan_pendapatan()
        self.assertIn("Pendapatan diterima periode ini : Rp 150.000", buf.getvalue())

    def test_tampilkan_sisa_tagihan_dengan_pembayaran(self):
        main.simpan_csv(main.FILE_PEMBAYARAN, [{
            "id_pembayaran": "PAY1", "id_transaksi": "TRX1", "tanggal": "2026-11-20 10:00",
            "metode": "Tunai", "jumlah_bayar": "50000", "keterangan": "DP/Angsuran"
        }])
        buf = io.StringIO()
        with redirect_stdout(buf):
            main.tampilkan_sisa_tagihan([{"id_transaksi": "TRX1", "total_bayar": "100000", "denda": "10000"}])
        self.assertIn("Dibayar Rp 50.000 | Sisa Rp 60.000", buf.getvalue())

    def test_menu_admin_pilihan_invalid(self):
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["X", "", "0", "Y"]), redirect_stdout(buf):
            main.menu_admin({"username": "admin", "nama_lengkap": "Administrator", "role": "admin"})
        self.assertIn("Pilihan tidak valid", buf.getvalue())

    def test_entry_point_dan_keyboard_interrupt(self):
        import runpy
        path = os.path.abspath(main.__file__)
        with patch("builtins.input", side_effect=["0", "Y"]), redirect_stdout(io.StringIO()):
            runpy.run_path(path, run_name="__main__")
        buf = io.StringIO()
        with patch("builtins.input", side_effect=KeyboardInterrupt), redirect_stdout(buf):
            runpy.run_path(path, run_name="__main__")
        self.assertIn("Program dihentikan oleh pengguna", buf.getvalue())

    def test_register_duplikat_nik_dan_username(self):
        main.simpan_csv(main.FILE_USERS, [
            {"username": "admin", "password": "admin123", "nik": "-", "nama_lengkap": "Admin", "no_hp": "-", "alamat": "-", "role": "admin"},
            {"username": "budi01", "password": "p", "nik": "3501234567890001", "nama_lengkap": "Budi", "no_hp": "081234567890", "alamat": "Jember", "role": "pelanggan"},
        ])
        with patch("builtins.input", side_effect=["3501234567890001", "Nama", "081234567890", "Alamat", "baru01", "pass"]), redirect_stdout(io.StringIO()):
            main.register_pelanggan()
        with patch("builtins.input", side_effect=["3509999999999999", "Nama", "081234567890", "Alamat", "budi01", "pass"]), redirect_stdout(io.StringIO()):
            main.register_pelanggan()
        self.assertEqual(len(main.baca_csv(main.FILE_USERS)), 2)

    def test_tambah_pelanggan_duplikat_ditolak(self):
        main.simpan_csv(main.FILE_USERS, [{
            "username": "budi01", "password": "p", "nik": "3501234567890001",
            "nama_lengkap": "Budi", "no_hp": "0812", "alamat": "J", "role": "pelanggan"
        }])
        with patch("builtins.input", side_effect=["3501234567890001", "X", "081234567890", "A", "baru", "p"]), redirect_stdout(io.StringIO()):
            main.tambah_pelanggan_admin()
        self.assertEqual(len(main.baca_csv(main.FILE_USERS)), 1)

    def test_ubah_pelanggan_nik_bentrok_ditolak(self):
        main.simpan_csv(main.FILE_USERS, [
            {"username": "a", "password": "p", "nik": "3501234567890001", "nama_lengkap": "A", "no_hp": "081234567890", "alamat": "X", "role": "pelanggan"},
            {"username": "b", "password": "p", "nik": "3501234567890002", "nama_lengkap": "B", "no_hp": "081234567891", "alamat": "Y", "role": "pelanggan"},
        ])
        with patch("builtins.input", side_effect=["b", "", "3501234567890001", "", "", ""]), redirect_stdout(io.StringIO()):
            main.ubah_pelanggan()
        self.assertEqual(main.cari_data(main.baca_csv(main.FILE_USERS), "username", "b")["nik"], "3501234567890002")

    def test_cari_pelanggan_by_alamat_dan_transaksi_by_status(self):
        main.simpan_csv(main.FILE_USERS, [{
            "username": "budi01", "password": "p", "nik": "3501234567890001",
            "nama_lengkap": "Budi", "no_hp": "081234567890", "alamat": "Jember", "role": "pelanggan"
        }])
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "T1", "nama_penyewa": "Budi", "nama_baju": "Baju Bali",
            "status": "DISEWA", "tanggal_mulai": "", "tanggal_selesai": "",
            "jumlah": "1", "total_bayar": "0"
        }])
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["jember"]), redirect_stdout(buf):
            main.cari_pelanggan()
        self.assertIn("budi01", buf.getvalue())
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["disewa"]), redirect_stdout(buf):
            main.cari_transaksi()
        self.assertIn("T1", buf.getvalue())

    def test_laporan_stok_transaksi_hari_ini(self):
        main.simpan_csv(main.FILE_KATALOG, [{
            "kode": "BA01", "nama_baju": "Baju", "ukuran": "M", "harga_sewa": "50000", "stok": "5"
        }])
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "T1", "kode_baju": "BA01", "nama_baju": "Baju",
            "nama_penyewa": "Budi", "jumlah": "2", "status": "DISEWA",
            "tanggal_mulai": date.today().isoformat(), "tanggal_selesai": date.today().isoformat(),
            "total_bayar": "100000"
        }, {
            "id_transaksi": "T2", "kode_baju": "BA99", "nama_baju": "Lain",
            "nama_penyewa": "Ani", "jumlah": "1", "status": "DISEWA",
            "tanggal_mulai": date.today().isoformat(), "tanggal_selesai": date.today().isoformat(),
            "total_bayar": "100000"
        }, {
            "id_transaksi": "T3", "kode_baju": "BA01", "nama_baju": "Baju",
            "nama_penyewa": "Cici", "jumlah": "1", "status": "DISEWA",
            "tanggal_mulai": "", "tanggal_selesai": "", "total_bayar": "100000"
        }])
        buf = io.StringIO()
        with redirect_stdout(buf):
            main.laporan_stok()
        self.assertIn("BA01", buf.getvalue())
        self.assertIn("3", buf.getvalue())

    def test_tampilkan_sisa_tagihan_banyak_pembayaran(self):
        main.simpan_csv(main.FILE_PEMBAYARAN, [
            {"id_pembayaran": "P1", "id_transaksi": "T1", "tanggal": "x", "metode": "Tunai", "jumlah_bayar": "60000", "keterangan": "DP"},
            {"id_pembayaran": "P2", "id_transaksi": "T1", "tanggal": "x", "metode": "Tunai", "jumlah_bayar": "60000", "keterangan": "Pelunasan"},
        ])
        buf = io.StringIO()
        with redirect_stdout(buf):
            main.tampilkan_sisa_tagihan([{"id_transaksi": "T1", "total_bayar": "100000", "denda": "0"}])
        self.assertIn("Dibayar Rp 120.000 | Sisa Rp 0", buf.getvalue())

    def test_menu_katalog_admin_pilihan_invalid(self):
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["X", "0"]), redirect_stdout(buf):
            main.menu_katalog_admin()
        self.assertIn("Pilihan tidak valid", buf.getvalue())

    def test_menu_pelanggan_dan_transaksi_admin_pilihan_invalid(self):
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["X", "0"]), redirect_stdout(buf):
            main.menu_pelanggan_admin()
        with patch("builtins.input", side_effect=["X", "0"]), redirect_stdout(buf):
            main.menu_transaksi_admin()
        self.assertIn("Pilihan tidak valid", buf.getvalue())

    def test_laporan_dua_pembayaran_transaksi_sama(self):
        main.simpan_csv(main.FILE_PEMBAYARAN, [
            {"id_pembayaran": "P1", "id_transaksi": "T1", "tanggal": "2026-11-20 10:00", "metode": "Tunai", "jumlah_bayar": "50000", "keterangan": "DP"},
            {"id_pembayaran": "P2", "id_transaksi": "T1", "tanggal": "2026-11-21 10:00", "metode": "Tunai", "jumlah_bayar": "50000", "keterangan": "Pelunasan"},
        ])
        main.simpan_csv(main.FILE_TRANSAKSI, [{
            "id_transaksi": "T1", "nama_penyewa": "Budi", "total_bayar": "100000",
            "denda": "0", "status": "DISEWA"
        }])
        buf = io.StringIO()
        with patch("builtins.input", side_effect=["1"]), redirect_stdout(buf):
            main.laporan_pendapatan()
        piutang = next(l for l in buf.getvalue().splitlines() if l.startswith("Piutang tersisa"))
        self.assertTrue(piutang.endswith("Rp 0"))

    def test_output_aman_di_encoding_cp1252(self):
        import subprocess, sys
        env = {**os.environ, "PYTHONIOENCODING": "cp1252"}
        hasil = subprocess.run(
            [sys.executable, "-c", "import main; main.judul_panel('UJI')"],
            cwd=os.path.dirname(os.path.abspath(main.__file__)),
            env=env, capture_output=True, timeout=60
        )
        self.assertEqual(hasil.returncode, 0, hasil.stderr.decode("utf-8", "replace"))

if __name__ == "__main__":
    unittest.main()
