import csv
import os
from datetime import datetime, date
from pathlib import Path

# ============================================================
# SISTEM PENYEWAAN BAJU ADAT
# ============================================================

FILE_USERS = "users.csv"
FILE_KATALOG = "katalog.csv"
FILE_TRANSAKSI = "transaksi.csv"
FILE_PEMBAYARAN = "pembayaran.csv"
FILE_PENGEMBALIAN = "pengembalian.csv"

DENDA_PER_HARI = 20000
PERSEN_DISKON_PELANGGAN_BARU = 10

HEADERS = {
    FILE_USERS: [
        "username", "password", "nik", "nama_lengkap", "no_hp", "alamat", "role"
    ],
    FILE_KATALOG: [
        "kode", "nama_baju", "ukuran", "harga_sewa", "stok"
    ],
    FILE_TRANSAKSI: [
        "id_transaksi", "username", "nik", "nama_penyewa", "no_hp",
        "kode_baju", "nama_baju", "jumlah", "tanggal_mulai",
        "tanggal_selesai", "lama_sewa", "harga_per_hari",
        "subtotal", "diskon", "total_bayar", "status",
        "tanggal_transaksi", "denda", "tanggal_pengembalian"
    ],
    FILE_PEMBAYARAN: [
        "id_pembayaran", "id_transaksi", "tanggal", "metode",
        "jumlah_bayar", "keterangan"
    ],
    FILE_PENGEMBALIAN: [
        "id_pengembalian", "id_transaksi", "tanggal_rencana",
        "tanggal_realisasi", "terlambat_hari", "denda",
        "kondisi", "catatan"
    ],
}


# ------------------------- Pembaca CSV -------------------------

def baca_csv(nama_file):
    if not os.path.exists(nama_file):
        return []
    with open(nama_file, "r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def simpan_csv(nama_file, data):
    fieldnames = HEADERS[nama_file]
    with open(nama_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def inisialisasi_file():
    for nama_file, header in HEADERS.items():
        if not os.path.exists(nama_file):
            with open(nama_file, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(header)
        else:
            # Migrasi sederhana agar CSV versi lama tetap dapat digunakan.
            with open(nama_file, "r", newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                old_rows = list(reader)
                old_headers = reader.fieldnames or []

            if old_headers != header:
                migrated = []
                for row in old_rows:
                    new_row = {key: row.get(key, "") for key in header}
                    migrated.append(new_row)
                simpan_csv(nama_file, migrated)

    users = baca_csv(FILE_USERS)
    if not any(u.get("username") == "admin" for u in users):
        users.append({
            "username": "admin",
            "password": "admin123",
            "nik": "-",
            "nama_lengkap": "Administrator",
            "no_hp": "-",
            "alamat": "-",
            "role": "admin",
        })
        simpan_csv(FILE_USERS, users)


def konfirmasi(pesan):
    while True:
        jawab = input(f"{pesan} (Y/N): ").strip().upper()
        if jawab in ("Y", "N"):
            return jawab == "Y"
        print("Masukkan Y atau N.")


def input_wajib(pesan):
    while True:
        nilai = input(pesan).strip()
        if nilai:
            return nilai
        print("Input tidak boleh kosong.")


def input_angka(pesan, minimum=0):
    while True:
        try:
            nilai = int(input(pesan).strip())
            if nilai < minimum:
                print(f"Nilai minimal adalah {minimum}.")
                continue
            return nilai
        except ValueError:
            print("Masukkan angka yang valid.")


def format_rupiah(nilai):
    return "Rp " + f"{int(nilai):,}".replace(",", ".")


def format_tanggal(tgl):
    return tgl.strftime("%Y-%m-%d")


def input_tanggal(pesan, default=None):
    while True:
        teks = input(pesan).strip()
        if not teks and default:
            return default
        try:
            return datetime.strptime(teks, "%Y-%m-%d").date()
        except ValueError:
            print("Format tanggal harus YYYY-MM-DD. Contoh: 2026-11-20.")


def parse_tanggal(teks):
    return datetime.strptime(teks, "%Y-%m-%d").date()


def hitung_hari(mulai, selesai):
    # Tanggal mulai dan tanggal selesai sama-sama dihitung sebagai hari sewa.
    return (selesai - mulai).days + 1


def buat_id(prefix, data, kolom):
    angka_terbesar = 0
    for row in data:
        teks = row.get(kolom, "")
        if teks.startswith(prefix):
            try:
                angka_terbesar = max(angka_terbesar, int(teks[len(prefix):]))
            except ValueError:
                pass
    return f"{prefix}{angka_terbesar + 1:04d}"


def cari_data(data, kolom, nilai):
    return next((row for row in data if row.get(kolom) == nilai), None)



def garis(lebar=72, karakter="─"):
    print("┌" + karakter * (lebar - 2) + "┐")

def judul_panel(judul, lebar=72):
    print("┌" + "─" * (lebar - 2) + "┐")
    print("│" + judul.center(lebar - 2) + "│")
    print("└" + "─" * (lebar - 2) + "┘")

def batas_tabel(lebar, kiri="├", tengah="┼", kanan="┤"):
    print(kiri + tengah.join("─" * w for w in lebar) + kanan)


def jeda():
    input("\nTekan Enter untuk kembali...")


# ------------------------- Fitur Auth (LOGIN DAN REGISTRASI) -------------------------

def register_pelanggan():
    print("\n=== REGISTRASI PELANGGAN ===")
    users = baca_csv(FILE_USERS)

    nik = input_wajib("NIK (16 digit)       : ")
    nama = input_wajib("Nama lengkap         : ").title()
    no_hp = input_wajib("No. HP (08xxxxxxxxxx): ")
    alamat = input_wajib("Alamat lengkap       : ")
    username = input_wajib("Username             : ").lower()
    password = input_wajib("Password             : ")

    if not (nik.isdigit() and len(nik) == 16):
        print("Gagal: NIK harus 16 digit angka.")
        return
    if not (no_hp.isdigit() and no_hp.startswith("08") and 10 <= len(no_hp) <= 13):
        print("Gagal: nomor HP harus 10-13 digit dan diawali 08.")
        return
    if any(u["nik"] == nik for u in users):
        print("Gagal: NIK sudah terdaftar.")
        return
    if any(u["username"] == username for u in users):
        print("Gagal: username sudah digunakan.")
        return

    if konfirmasi(f"Simpan akun pelanggan {nama}?"):
        users.append({
            "username": username, "password": password, "nik": nik,
            "nama_lengkap": nama, "no_hp": no_hp, "alamat": alamat, "role": "pelanggan"
        })
        simpan_csv(FILE_USERS, users)
        print("Registrasi berhasil. Silakan login.")
    else:
        print("Registrasi dibatalkan.")


def login():
    print("\n=== LOGIN ===")
    users = baca_csv(FILE_USERS)
    for kesempatan in range(3):
        username = input("Username: ").strip().lower()
        password = input("Password: ").strip()
        user = next(
            (u for u in users
             if u["username"] == username and u["password"] == password),
            None
        )
        if user:
            print(f"Selamat datang, {user['nama_lengkap']}!")
            return user
        print(f"Login gagal. Sisa percobaan: {2 - kesempatan}")
    return None


# ------------------------- Fitur Katalog Baju Adat -------------------------

def tampilkan_katalog(data=None):
    katalog = data if data is not None else baca_csv(FILE_KATALOG)
    lebar = [10, 30, 10, 17, 8]
    print()
    judul_panel("KATALOG BAJU ADAT", sum(lebar) + len(lebar) + 1)
    if not katalog:
        print("  Belum ada data katalog.")
        return
    print("│" + "Kode".ljust(10) + "│" + "Nama Baju".ljust(30) + "│" + "Ukuran".ljust(10) + "│" + "Harga/Hari".rjust(17) + "│" + "Stok".rjust(8) + "│")
    batas_tabel(lebar)
    for b in katalog:
        print("│" + b["kode"][:10].ljust(10) + "│" + b["nama_baju"][:30].ljust(30) + "│" + b["ukuran"][:10].ljust(10) + "│" + format_rupiah(b["harga_sewa"]).rjust(17) + "│" + b["stok"].rjust(8) + "│")
    print("└" + "┴".join("─" * w for w in lebar) + "┘")


def tambah_baju():
    katalog = baca_csv(FILE_KATALOG)
    print("\n=== TAMBAH BAJU ADAT ===")
    kode = input_wajib("Kode baju   : ").upper()
    if cari_data(katalog, "kode", kode):
        print("Kode sudah digunakan.")
        return

    nama = input_wajib("Nama baju   : ").title()
    ukuran = input_wajib("Ukuran      : ").upper()
    harga = input_angka("Harga sewa/hari: ", 1)
    stok = input_angka("Stok awal      : ", 0)

    if konfirmasi("Simpan data baju?"):
        katalog.append({
            "kode": kode, "nama_baju": nama,
            "ukuran": ukuran, "harga_sewa": str(harga), "stok": str(stok)
        })
        simpan_csv(FILE_KATALOG, katalog)
        print("Baju adat berhasil ditambahkan.")


def ubah_baju():
    katalog = baca_csv(FILE_KATALOG)
    tampilkan_katalog(katalog)
    kode = input("\nKode baju yang diubah: ").strip().upper()
    target = cari_data(katalog, "kode", kode)
    if not target:
        print("Data baju tidak ditemukan.")
        return

    print("Tekan Enter untuk mempertahankan nilai lama.")
    nama = input(f"Nama [{target['nama_baju']}]: ").strip()
    ukuran = input(f"Ukuran [{target['ukuran']}]: ").strip()
    harga = input(f"Harga/hari [{target['harga_sewa']}]: ").strip()
    stok = input(f"Stok [{target['stok']}]: ").strip()

    try:
        if harga and int(harga) <= 0:
            raise ValueError
        if stok and int(stok) < 0:
            raise ValueError
    except ValueError:
        print("Harga harus lebih dari 0 dan stok tidak boleh negatif.")
        return

    if konfirmasi("Simpan perubahan katalog?"):
        if nama: target["nama_baju"] = nama.title()
        if ukuran: target["ukuran"] = ukuran.upper()
        if harga: target["harga_sewa"] = harga
        if stok: target["stok"] = stok
        simpan_csv(FILE_KATALOG, katalog)
        print("Data katalog berhasil diperbarui.")


def hapus_baju():
    katalog = baca_csv(FILE_KATALOG)
    tampilkan_katalog(katalog)
    kode = input("\nKode baju yang dihapus: ").strip().upper()
    target = cari_data(katalog, "kode", kode)
    if not target:
        print("Data tidak ditemukan.")
        return

    transaksi = baca_csv(FILE_TRANSAKSI)
    masih_aktif = any(
        t["kode_baju"] == kode and t["status"] in ("RESERVASI", "DISEWA")
        for t in transaksi
    )
    if masih_aktif:
        print("Baju tidak dapat dihapus karena masih memiliki reservasi/penyewaan aktif.")
        return

    if konfirmasi(f"Hapus {target['nama_baju']} secara permanen?"):
        simpan_csv(FILE_KATALOG, [b for b in katalog if b["kode"] != kode])
        print("Data baju berhasil dihapus.")


def cari_baju():
    katalog = baca_csv(FILE_KATALOG)
    kata = input("Masukkan kode/nama/ukuran baju: ").strip().lower()
    hasil = [
        b for b in katalog
        if kata in b["kode"].lower()
        or kata in b["nama_baju"].lower()
        or kata in b["ukuran"].lower()
    ]
    tampilkan_katalog(hasil)


# ------------------------- Fitur CRUD Pelanggan -------------------------

def tampilkan_pelanggan(data=None):
    users = data if data is not None else baca_csv(FILE_USERS)
    pelanggan = [u for u in users if u["role"] == "pelanggan"]
    print()
    judul_panel("DATA PELANGGAN", 112)
    if not pelanggan:
        print("  Belum ada pelanggan.")
        return
    widths = [15, 18, 23, 15, 37]
    print("│" + "Username".ljust(15) + "│" + "NIK".ljust(18) + "│" + "Nama".ljust(23) + "│" + "No. HP".ljust(15) + "│" + "Alamat".ljust(37) + "│")
    batas_tabel(widths)
    for u in pelanggan:
        alamat = u.get("alamat", "-")
        print("│" + u["username"][:15].ljust(15) + "│" + u["nik"][:18].ljust(18) + "│" + u["nama_lengkap"][:23].ljust(23) + "│" + u["no_hp"][:15].ljust(15) + "│" + alamat[:37].ljust(37) + "│")
    print("└" + "┴".join("─" * w for w in widths) + "┘")


def tambah_pelanggan_admin():
    print("\n=== TAMBAH PELANGGAN ===")
    users = baca_csv(FILE_USERS)
    nik = input_wajib("NIK (16 digit): ")
    nama = input_wajib("Nama lengkap : ").title()
    no_hp = input_wajib("No. HP       : ")
    alamat = input_wajib("Alamat       : ")
    username = input_wajib("Username     : ").lower()
    password = input_wajib("Password     : ")

    if not (nik.isdigit() and len(nik) == 16):
        print("NIK harus 16 digit angka.")
        return
    if not (no_hp.isdigit() and no_hp.startswith("08") and 10 <= len(no_hp) <= 13):
        print("Nomor HP tidak valid.")
        return
    if any(u["nik"] == nik or u["username"] == username for u in users):
        print("NIK atau username sudah terdaftar.")
        return

    users.append({
        "username": username, "password": password, "nik": nik,
        "nama_lengkap": nama, "no_hp": no_hp, "alamat": alamat, "role": "pelanggan"
    })
    simpan_csv(FILE_USERS, users)
    print("Pelanggan berhasil ditambahkan.")


def ubah_pelanggan():
    users = baca_csv(FILE_USERS)
    tampilkan_pelanggan(users)
    username = input("\nUsername pelanggan yang diubah: ").strip().lower()
    target = next(
        (u for u in users if u["username"] == username and u["role"] == "pelanggan"),
        None
    )
    if not target:
        print("Pelanggan tidak ditemukan.")
        return

    print("Tekan Enter untuk mempertahankan data lama.")
    nama = input(f"Nama [{target['nama_lengkap']}]: ").strip()
    nik = input(f"NIK [{target['nik']}]: ").strip()
    hp = input(f"No. HP [{target['no_hp']}]: ").strip()
    alamat = input(f"Alamat [{target.get('alamat', '-')}]: ").strip()
    password = input("Password baru (kosongkan jika tetap): ").strip()

    if nik and not (nik.isdigit() and len(nik) == 16):
        print("NIK harus 16 digit.")
        return
    if hp and not (hp.isdigit() and hp.startswith("08") and 10 <= len(hp) <= 13):
        print("Nomor HP tidak valid.")
        return
    if nik and any(u["nik"] == nik and u["username"] != username for u in users):
        print("NIK sudah digunakan pelanggan lain.")
        return

    if konfirmasi("Simpan perubahan pelanggan?"):
        if nama: target["nama_lengkap"] = nama.title()
        if nik: target["nik"] = nik
        if hp: target["no_hp"] = hp
        if alamat: target["alamat"] = alamat
        if password: target["password"] = password
        simpan_csv(FILE_USERS, users)
        print("Data pelanggan berhasil diperbarui.")


def hapus_pelanggan():
    users = baca_csv(FILE_USERS)
    tampilkan_pelanggan(users)
    username = input("\nUsername pelanggan yang dihapus: ").strip().lower()
    target = next(
        (u for u in users if u["username"] == username and u["role"] == "pelanggan"),
        None
    )
    if not target:
        print("Pelanggan tidak ditemukan.")
        return

    if konfirmasi(f"Hapus akun {target['nama_lengkap']}? Riwayat transaksi tetap disimpan."):
        simpan_csv(FILE_USERS, [u for u in users if u["username"] != username])
        print("Akun pelanggan berhasil dihapus.")


def cari_pelanggan():
    users = baca_csv(FILE_USERS)
    kata = input("Cari username/nama/NIK/no. HP/alamat: ").strip().lower()
    hasil = [
        u for u in users if u["role"] == "pelanggan"
        and (kata in u["username"].lower()
             or kata in u["nama_lengkap"].lower()
             or kata in u["nik"].lower()
             or kata in u["no_hp"].lower()
             or kata in u.get("alamat", "").lower())
    ]
    tampilkan_pelanggan(hasil)


# ------------------------- Fitur Stok dan Reservasi -------------------------

def stok_tersedia(kode_baju, mulai, selesai):
    katalog = baca_csv(FILE_KATALOG)
    baju = cari_data(katalog, "kode", kode_baju)
    if not baju:
        return 0

    stok_total = int(baju["stok"])
    terpakai = 0
    for t in baca_csv(FILE_TRANSAKSI):
        if t["kode_baju"] != kode_baju or t["status"] not in ("RESERVASI", "DISEWA"):
            continue
        try:
            t_mulai = parse_tanggal(t["tanggal_mulai"])
            t_selesai = parse_tanggal(t["tanggal_selesai"])
        except (ValueError, TypeError):
            continue

        # Dua rentang tanggal bertumpang tindih jika kondisi ini terpenuhi.
        if mulai <= t_selesai and selesai >= t_mulai:
            terpakai += int(t["jumlah"])
    return max(0, stok_total - terpakai)


def pelanggan_baru_berdasarkan_nik(nik):
    """Pelanggan baru jika NIK belum pernah memiliki transaksi sebelumnya."""
    return not any(
        t.get("nik") == nik and t.get("status") != "BATAL"
        for t in baca_csv(FILE_TRANSAKSI)
    )


def hitung_total_sewa(harga, jumlah, hari, nik):
    subtotal = harga * jumlah * hari
    pelanggan_baru = pelanggan_baru_berdasarkan_nik(nik)
    diskon = (
        int(subtotal * PERSEN_DISKON_PELANGGAN_BARU / 100)
        if pelanggan_baru else 0
    )
    return subtotal, diskon, subtotal - diskon, pelanggan_baru


def buat_reservasi(user):
    tampilkan_katalog()
    kode = input("\nKode baju yang dipesan: ").strip().upper()
    katalog = baca_csv(FILE_KATALOG)
    baju = cari_data(katalog, "kode", kode)
    if not baju:
        print("Baju tidak ditemukan.")
        return

    mulai = input_tanggal("Tanggal mulai sewa (YYYY-MM-DD): ")
    selesai = input_tanggal("Tanggal selesai sewa (YYYY-MM-DD): ")
    if selesai < mulai:
        print("Tanggal selesai tidak boleh sebelum tanggal mulai.")
        return
    if mulai < date.today():
        print("Tanggal mulai tidak boleh berada di masa lalu.")
        return

    jumlah = input_angka("Jumlah baju yang dipesan: ", 1)
    tersedia = stok_tersedia(kode, mulai, selesai)
    if jumlah > tersedia:
        print(f"Stok tidak mencukupi. Tersedia pada periode tersebut: {tersedia}.")
        return

    hari = hitung_hari(mulai, selesai)
    subtotal, diskon, total, pelanggan_baru = hitung_total_sewa(
        int(baju["harga_sewa"]), jumlah, hari, user["nik"]
    )
    print("\n=== RINGKASAN RESERVASI ===")
    print(f"Baju             : {baju['nama_baju']}")
    print(f"Periode          : {format_tanggal(mulai)} s.d. {format_tanggal(selesai)}")
    print(f"Jumlah           : {jumlah}")
    print(f"Lama sewa        : {hari} hari")
    print(f"Subtotal         : {format_rupiah(subtotal)}")
    print(f"Status pelanggan : {'Baru' if pelanggan_baru else 'Pelanggan lama'}")
    print(f"Diskon pelanggan : {PERSEN_DISKON_PELANGGAN_BARU}% jika NIK baru")
    print(f"Potongan diskon  : {format_rupiah(diskon)}")
    print(f"Total sewa       : {format_rupiah(total)}")

    if not konfirmasi("Buat reservasi ini?"):
        print("Reservasi dibatalkan.")
        return

    transaksi = baca_csv(FILE_TRANSAKSI)
    id_trx = buat_id("TRX", transaksi, "id_transaksi")
    transaksi.append({
        "id_transaksi": id_trx,
        "username": user["username"],
        "nik": user["nik"],
        "nama_penyewa": user["nama_lengkap"],
        "no_hp": user["no_hp"],
        "kode_baju": kode,
        "nama_baju": baju["nama_baju"],
        "jumlah": str(jumlah),
        "tanggal_mulai": format_tanggal(mulai),
        "tanggal_selesai": format_tanggal(selesai),
        "lama_sewa": str(hari),
        "harga_per_hari": baju["harga_sewa"],
        "subtotal": str(subtotal),
        "diskon": str(diskon),
        "total_bayar": str(total),
        "status": "RESERVASI",
        "tanggal_transaksi": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "denda": "0",
        "tanggal_pengembalian": ""
    })
    simpan_csv(FILE_TRANSAKSI, transaksi)
    print(f"Reservasi berhasil dibuat. ID transaksi: {id_trx}")


# ------------------------- Fitur CRUD Transaksi -------------------------

def total_pembayaran_transaksi(id_trx):
    return sum(
        int(p["jumlah_bayar"])
        for p in baca_csv(FILE_PEMBAYARAN)
        if p["id_transaksi"] == id_trx
    )


def tampilkan_transaksi(data=None):
    transaksi = data if data is not None else baca_csv(FILE_TRANSAKSI)
    widths = [9, 19, 21, 6, 24, 15, 12]
    total_width = sum(widths) + len(widths) + 1
    print()
    judul_panel("DATA TRANSAKSI", total_width)
    if not transaksi:
        print("  Belum ada transaksi.")
        return
    headers = ["ID", "Penyewa", "Baju", "Jumlah", "Periode", "Total", "Status"]
    print("│" + "│".join(h.ljust(w) if i < 5 or i == 6 else h.rjust(w) for i, (h, w) in enumerate(zip(headers, widths))) + "│")
    batas_tabel(widths)
    for t in transaksi:
        periode = f"{t['tanggal_mulai']} s.d. {t['tanggal_selesai']}"
        vals = [t["id_transaksi"][:9], t["nama_penyewa"][:19], t["nama_baju"][:21], t["jumlah"], periode[:24], format_rupiah(t["total_bayar"]), t["status"]]
        print("│" + "│".join(v.rjust(w) if i in (3, 5) else v.ljust(w) for i, (v, w) in enumerate(zip(vals, widths))) + "│")
    print("└" + "┴".join("─" * w for w in widths) + "┘")


def cari_transaksi():
    transaksi = baca_csv(FILE_TRANSAKSI)
    kata = input("Cari ID/nama penyewa/nama baju/status: ").strip().lower()
    hasil = [
        t for t in transaksi
        if kata in t["id_transaksi"].lower()
        or kata in t["nama_penyewa"].lower()
        or kata in t["nama_baju"].lower()
        or kata in t["status"].lower()
    ]
    tampilkan_transaksi(hasil)


def ubah_transaksi():
    transaksi = baca_csv(FILE_TRANSAKSI)
    tampilkan_transaksi(transaksi)
    id_trx = input("\nID transaksi yang diubah: ").strip().upper()
    target = cari_data(transaksi, "id_transaksi", id_trx)
    if not target:
        print("Transaksi tidak ditemukan.")
        return

    if target["status"] in ("SELESAI", "BATAL"):
        print("Transaksi selesai/dibatalkan tidak dapat diubah.")
        return
    if total_pembayaran_transaksi(id_trx) > 0:
        print("Transaksi yang sudah memiliki pembayaran tidak dapat diubah.")
        print("Selesaikan penyesuaian pembayaran secara terpisah.")
        return

    print("Kosongkan input jika tidak ingin mengubah nilai.")
    mulai_baru = input_tanggal(
        f"Tanggal mulai [{target['tanggal_mulai']}]: ",
        default=parse_tanggal(target["tanggal_mulai"])
    )
    selesai_baru = input_tanggal(
        f"Tanggal selesai [{target['tanggal_selesai']}]: ",
        default=parse_tanggal(target["tanggal_selesai"])
    )
    if selesai_baru < mulai_baru:
        print("Tanggal selesai tidak valid.")
        return

    jumlah_teks = input(f"Jumlah [{target['jumlah']}]: ").strip()
    try:
        jumlah = int(jumlah_teks) if jumlah_teks else int(target["jumlah"])
        if jumlah <= 0:
            raise ValueError
    except ValueError:
        print("Jumlah harus berupa angka positif.")
        return

    # Hitung ketersediaan tanpa menghitung transaksi yang sedang diedit.
    transaksi_lain = [
        t for t in transaksi if t["id_transaksi"] != id_trx
    ]
    stok = int(cari_data(baca_csv(FILE_KATALOG), "kode", target["kode_baju"])["stok"])
    terpakai = 0
    for t in transaksi_lain:
        if t["kode_baju"] != target["kode_baju"] or t["status"] not in ("RESERVASI", "DISEWA"):
            continue
        if mulai_baru <= parse_tanggal(t["tanggal_selesai"]) and selesai_baru >= parse_tanggal(t["tanggal_mulai"]):
            terpakai += int(t["jumlah"])
    if jumlah > stok - terpakai:
        print(f"Stok tidak cukup pada tanggal tersebut. Maksimal: {max(0, stok - terpakai)}.")
        return

    hari = hitung_hari(mulai_baru, selesai_baru)
    harga = int(target["harga_per_hari"])
    subtotal, diskon, total, _ = hitung_total_sewa(harga, jumlah, hari, target["nik"])

    if konfirmasi("Simpan perubahan transaksi?"):
        target["tanggal_mulai"] = format_tanggal(mulai_baru)
        target["tanggal_selesai"] = format_tanggal(selesai_baru)
        target["jumlah"] = str(jumlah)
        target["lama_sewa"] = str(hari)
        target["subtotal"] = str(subtotal)
        target["diskon"] = str(diskon)
        target["total_bayar"] = str(total)
        simpan_csv(FILE_TRANSAKSI, transaksi)
        print("Transaksi berhasil diperbarui.")


def hapus_transaksi():
    transaksi = baca_csv(FILE_TRANSAKSI)
    tampilkan_transaksi(transaksi)
    id_trx = input("\nID transaksi yang dihapus: ").strip().upper()
    target = cari_data(transaksi, "id_transaksi", id_trx)
    if not target:
        print("Transaksi tidak ditemukan.")
        return

    if total_pembayaran_transaksi(id_trx) > 0:
        print("Transaksi tidak dapat dihapus karena sudah memiliki pembayaran.")
        print("Gunakan status BATAL jika transaksi perlu dibatalkan.")
        return

    if konfirmasi(f"Hapus transaksi {id_trx}?"):
        simpan_csv(FILE_TRANSAKSI, [
            t for t in transaksi if t["id_transaksi"] != id_trx
        ])
        print("Transaksi berhasil dihapus.")


def ubah_status_transaksi():
    transaksi = baca_csv(FILE_TRANSAKSI)
    tampilkan_transaksi(transaksi)
    id_trx = input("\nID transaksi: ").strip().upper()
    target = cari_data(transaksi, "id_transaksi", id_trx)
    if not target:
        print("Transaksi tidak ditemukan.")
        return

    print("1. Konfirmasi reservasi menjadi DISEWA")
    print("2. Batalkan reservasi")
    pilih = input("Pilih: ").strip()
    if pilih == "1" and target["status"] == "RESERVASI":
        target["status"] = "DISEWA"
    elif pilih == "2" and target["status"] == "RESERVASI":
        target["status"] = "BATAL"
    else:
        print("Pilihan tidak sesuai dengan status transaksi.")
        return

    if konfirmasi("Simpan perubahan status?"):
        simpan_csv(FILE_TRANSAKSI, transaksi)
        print("Status transaksi diperbarui.")


# ------------------------- Fitur Pembayaran -------------------------

def kelola_pembayaran():
    transaksi = baca_csv(FILE_TRANSAKSI)
    tampilkan_transaksi(transaksi)
    id_trx = input("\nID transaksi yang dibayar: ").strip().upper()
    target = cari_data(transaksi, "id_transaksi", id_trx)
    if not target:
        print("Transaksi tidak ditemukan.")
        return
    if target["status"] == "BATAL":
        print("Transaksi yang dibatalkan tidak dapat dibayar.")
        return

    sudah_bayar = total_pembayaran_transaksi(id_trx)
    total_tagihan = int(target["total_bayar"]) + int(target["denda"] or 0)
    sisa = max(0, total_tagihan - sudah_bayar)

    print("\n=== RINGKASAN PEMBAYARAN ===")
    print(f"ID transaksi  : {id_trx}")
    print(f"Nama penyewa  : {target['nama_penyewa']}")
    print(f"Total sewa    : {format_rupiah(target['total_bayar'])}")
    print(f"Denda         : {format_rupiah(target['denda'] or 0)}")
    print(f"Sudah dibayar : {format_rupiah(sudah_bayar)}")
    print(f"Sisa tagihan  : {format_rupiah(sisa)}")
    if sisa <= 0:
        print("Tagihan sudah lunas.")
        return

    jumlah = input_angka("Jumlah pembayaran (DP/pelunasan): ", 1)
    if jumlah > sisa:
        print(f"Pembayaran melebihi sisa tagihan. Maksimal {format_rupiah(sisa)}.")
        return

    print("Metode pembayaran: 1. Tunai  2. Transfer")
    metode_pilih = input("Pilih metode: ").strip()
    if metode_pilih not in ("1", "2"):
        print("Metode pembayaran tidak valid.")
        return
    metode = "Tunai" if metode_pilih == "1" else "Transfer"

    pembayaran = baca_csv(FILE_PEMBAYARAN)
    id_bayar = buat_id("PAY", pembayaran, "id_pembayaran")
    pembayaran.append({
        "id_pembayaran": id_bayar,
        "id_transaksi": id_trx,
        "tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "metode": metode,
        "jumlah_bayar": str(jumlah),
        "keterangan": "Pelunasan" if jumlah == sisa else "DP/Angsuran"
    })
    simpan_csv(FILE_PEMBAYARAN, pembayaran)

    total_setelah = sudah_bayar + jumlah
    status_bayar = "LUNAS" if total_setelah >= total_tagihan else "BELUM LUNAS"
    print(f"Pembayaran berhasil. ID pembayaran: {id_bayar}")
    print(f"Status pembayaran: {status_bayar}")
    print(f"Sisa tagihan: {format_rupiah(total_tagihan - total_setelah)}")


def riwayat_pembayaran():
    pembayaran = baca_csv(FILE_PEMBAYARAN)
    id_trx = input("ID transaksi: ").strip().upper()
    hasil = [p for p in pembayaran if p["id_transaksi"] == id_trx]
    print(f"\n=== RIWAYAT PEMBAYARAN {id_trx} ===")
    if not hasil:
        print("Belum ada pembayaran.")
        return
    for p in hasil:
        print(
            f"{p['id_pembayaran']} | {p['tanggal']} | {p['metode']} | "
            f"{format_rupiah(p['jumlah_bayar'])} | {p['keterangan']}"
        )
    print(f"Total dibayar: {format_rupiah(total_pembayaran_transaksi(id_trx))}")


# ------------------------- Fitur Pengembalian dan Denda -------------------------

def proses_pengembalian():
    transaksi = baca_csv(FILE_TRANSAKSI)
    aktif = [t for t in transaksi if t["status"] == "DISEWA"]
    tampilkan_transaksi(aktif)
    id_trx = input("\nID transaksi yang dikembalikan: ").strip().upper()
    target = cari_data(aktif, "id_transaksi", id_trx)
    if not target:
        print("Transaksi DISEWA tidak ditemukan.")
        return

    tanggal_rencana = parse_tanggal(target["tanggal_selesai"])
    tanggal_kembali = input_tanggal(
        "Tanggal pengembalian aktual (YYYY-MM-DD), Enter untuk hari ini: ",
        default=date.today()
    )
    if tanggal_kembali < parse_tanggal(target["tanggal_mulai"]):
        print("Tanggal pengembalian tidak boleh sebelum tanggal mulai sewa.")
        return
    terlambat = max(0, (tanggal_kembali - tanggal_rencana).days)
    denda = terlambat * DENDA_PER_HARI

    print("\n=== PEMERIKSAAN PENGEMBALIAN ===")
    print(f"Tanggal rencana : {format_tanggal(tanggal_rencana)}")
    print(f"Tanggal aktual  : {format_tanggal(tanggal_kembali)}")
    print(f"Terlambat       : {terlambat} hari")
    print(f"Denda           : {format_rupiah(denda)}")
    print("Kondisi baju: 1. Baik  2. Rusak ringan  3. Rusak berat")
    kondisi_pilih = input("Pilih kondisi: ").strip()
    kondisi_map = {"1": "Baik", "2": "Rusak ringan", "3": "Rusak berat"}
    if kondisi_pilih not in kondisi_map:
        print("Pilihan kondisi tidak valid.")
        return
    catatan = input("Catatan (opsional): ").strip()

    if not konfirmasi("Proses pengembalian baju?"):
        print("Pengembalian dibatalkan.")
        return

    pengembalian = baca_csv(FILE_PENGEMBALIAN)
    id_kembali = buat_id("RET", pengembalian, "id_pengembalian")
    pengembalian.append({
        "id_pengembalian": id_kembali,
        "id_transaksi": id_trx,
        "tanggal_rencana": format_tanggal(tanggal_rencana),
        "tanggal_realisasi": format_tanggal(tanggal_kembali),
        "terlambat_hari": str(terlambat),
        "denda": str(denda),
        "kondisi": kondisi_map[kondisi_pilih],
        "catatan": catatan
    })
    simpan_csv(FILE_PENGEMBALIAN, pengembalian)

    target["status"] = "SELESAI"
    target["denda"] = str(denda)
    target["tanggal_pengembalian"] = format_tanggal(tanggal_kembali)
    simpan_csv(FILE_TRANSAKSI, transaksi)

    print(f"Pengembalian berhasil dicatat. ID pengembalian: {id_kembali}")
    if denda:
        print("Denda masuk ke tagihan transaksi. Silakan proses pembayaran.")
    else:
        print("Tidak ada denda keterlambatan.")


def tampilkan_riwayat_pengembalian():
    data = baca_csv(FILE_PENGEMBALIAN)
    print("\n=== RIWAYAT PENGEMBALIAN ===")
    if not data:
        print("Belum ada data pengembalian.")
        return
    for r in data:
        print(
            f"{r['id_pengembalian']} | {r['id_transaksi']} | "
            f"{r['tanggal_realisasi']} | Terlambat {r['terlambat_hari']} hari | "
            f"Denda {format_rupiah(r['denda'])} | {r['kondisi']}"
        )


# ------------------------- Fitur Laporan Pendapatan & Stok -------------------------

def laporan_pendapatan():
    pembayaran = baca_csv(FILE_PEMBAYARAN)
    transaksi = baca_csv(FILE_TRANSAKSI)
    print("\n=== LAPORAN PENDAPATAN ===")
    print("1. Semua periode")
    print("2. Berdasarkan bulan dan tahun")
    print("3. Berdasarkan rentang tanggal")
    pilih = input("Pilih: ").strip()

    if pilih == "1":
        terpilih = pembayaran
    elif pilih == "2":
        bulan = input("Bulan (01-12): ").strip()
        tahun = input("Tahun (YYYY): ").strip()
        terpilih = [
            p for p in pembayaran
            if p["tanggal"][:7] == f"{tahun}-{bulan.zfill(2)}"
        ]
    elif pilih == "3":
        awal = input_tanggal("Tanggal awal (YYYY-MM-DD): ")
        akhir = input_tanggal("Tanggal akhir (YYYY-MM-DD): ")
        if akhir < awal:
            print("Rentang tanggal tidak valid.")
            return
        terpilih = [
            p for p in pembayaran
            if awal <= datetime.strptime(p["tanggal"], "%Y-%m-%d %H:%M").date() <= akhir
        ]
    else:
        print("Pilihan tidak valid.")
        return

    total = sum(int(p["jumlah_bayar"]) for p in terpilih)
    print("\nRINCIAN PEMBAYARAN")
    if not terpilih:
        print("Tidak ada pembayaran pada periode tersebut.")
    else:
        for p in terpilih:
            trx = cari_data(transaksi, "id_transaksi", p["id_transaksi"])
            nama = trx["nama_penyewa"] if trx else "-"
            print(
                f"{p['tanggal']} | {p['id_transaksi']} | {nama} | "
                f"{p['metode']} | {format_rupiah(p['jumlah_bayar'])}"
            )
    total_tagihan = sum(
        int(t["total_bayar"]) + int(t["denda"] or 0)
        for t in transaksi if t["status"] != "BATAL"
    )
    total_dibayar_semua = sum(int(p["jumlah_bayar"]) for p in pembayaran)
    print("─" * 65)
    print(f"Pendapatan diterima periode ini : {format_rupiah(total)}")
    print(f"Total pembayaran sepanjang waktu: {format_rupiah(total_dibayar_semua)}")
    print(f"Total tagihan transaksi aktif/selesai: {format_rupiah(total_tagihan)}")
    print(f"Piutang tersisa                  : {format_rupiah(max(0, total_tagihan - total_dibayar_semua))}")


def laporan_stok():
    katalog = baca_csv(FILE_KATALOG)
    transaksi = baca_csv(FILE_TRANSAKSI)
    print()
    judul_panel("LAPORAN STOK BAJU ADAT", 100)
    if not katalog:
        print("Belum ada data katalog.")
        return

    print(f"{'Kode':<9} {'Nama Baju':<25} {'Stok Total':>12} {'Dipesan/Disewa Hari Ini':>24} {'Tersedia Hari Ini':>18}")
    print("─" * 100)
    for b in katalog:
        sedang = sum(
            int(t["jumlah"]) for t in transaksi
            if t["kode_baju"] == b["kode"]
            and t["status"] in ("RESERVASI", "DISEWA")
            and parse_tanggal(t["tanggal_mulai"]) <= date.today()
            and parse_tanggal(t["tanggal_selesai"]) >= date.today()
        )
        tersedia = stok_tersedia(b["kode"], date.today(), date.today())
        print(
            f"{b['kode']:<9} {b['nama_baju'][:24]:<25} "
            f"{int(b['stok']):>12} {sedang:>24} {tersedia:>18}"
        )
    print("─" * 100)
    print("Catatan: Ketersediaan dapat berbeda untuk tanggal reservasi mendatang.")


# ------------------------- Fitur Riwayat Pelanggan -------------------------

def riwayat_pelanggan(user):
    data = [
        t for t in baca_csv(FILE_TRANSAKSI)
        if t["username"] == user["username"]
    ]
    tampilkan_transaksi(data)
    for t in data:
        dibayar = total_pembayaran_transaksi(t["id_transaksi"])
        tagihan = int(t["total_bayar"]) + int(t["denda"] or 0)
        print(
            f"{t['id_transaksi']} | Dibayar {format_rupiah(dibayar)} | "
            f"Sisa {format_rupiah(max(0, tagihan - dibayar))}"
        )


# ------------------------- MENU -------------------------

def menu_katalog_admin():
    while True:
        print()
        judul_panel("KELOLA KATALOG", 40)
        print("1. Tampilkan katalog")
        print("2. Tambah baju")
        print("3. Ubah baju")
        print("4. Hapus baju")
        print("5. Cari baju")
        print("0. Kembali")
        pilih = input("Pilih: ").strip()
        if pilih == "1": tampilkan_katalog()
        elif pilih == "2": tambah_baju()
        elif pilih == "3": ubah_baju()
        elif pilih == "4": hapus_baju()
        elif pilih == "5": cari_baju()
        elif pilih == "0": break
        else: print("Pilihan tidak valid.")


def menu_pelanggan_admin():
    while True:
        print()
        judul_panel("KELOLA PELANGGAN", 40)
        print("1. Tampilkan pelanggan")
        print("2. Tambah pelanggan")
        print("3. Ubah pelanggan")
        print("4. Hapus pelanggan")
        print("5. Cari pelanggan")
        print("0. Kembali")
        pilih = input("Pilih: ").strip()
        if pilih == "1": tampilkan_pelanggan()
        elif pilih == "2": tambah_pelanggan_admin()
        elif pilih == "3": ubah_pelanggan()
        elif pilih == "4": hapus_pelanggan()
        elif pilih == "5": cari_pelanggan()
        elif pilih == "0": break
        else: print("Pilihan tidak valid.")


def menu_transaksi_admin():
    while True:
        print()
        judul_panel("KELOLA TRANSAKSI", 40)
        print("1. Tampilkan transaksi")
        print("2. Cari transaksi")
        print("3. Ubah data transaksi")
        print("4. Hapus transaksi")
        print("5. Konfirmasi / batalkan reservasi")
        print("0. Kembali")
        pilih = input("Pilih: ").strip()
        if pilih == "1": tampilkan_transaksi()
        elif pilih == "2": cari_transaksi()
        elif pilih == "3": ubah_transaksi()
        elif pilih == "4": hapus_transaksi()
        elif pilih == "5": ubah_status_transaksi()
        elif pilih == "0": break
        else: print("Pilihan tidak valid.")


def menu_admin(user):
    while True:
        print()
        judul_panel("SISTEM PENYEWAAN BAJU ADAT - ADMIN", 60)
        print(f"  Login sebagai: {user['nama_lengkap']}")
        garis(60)
        print("1. CRUD Katalog Baju Adat")
        print("2. CRUD Pelanggan")
        print("3. CRUD Transaksi")
        print("4. Lihat Reservasi")
        print("5. Manajemen Pembayaran")
        print("6. Proses Pengembalian dan Denda")
        print("7. Riwayat Pengembalian")
        print("8. Laporan Pendapatan")
        print("9. Laporan Stok")
        print("0. Logout")
        pilih = input("Pilih menu: ").strip()

        if pilih == "1": menu_katalog_admin()
        elif pilih == "2": menu_pelanggan_admin()
        elif pilih == "3": menu_transaksi_admin()
        elif pilih == "4": tampilkan_transaksi([
            t for t in baca_csv(FILE_TRANSAKSI) if t["status"] == "RESERVASI"
        ])
        elif pilih == "5":
            kelola_pembayaran()
            riwayat_pembayaran() if konfirmasi("Lihat riwayat pembayaran?") else None
        elif pilih == "6": proses_pengembalian()
        elif pilih == "7": tampilkan_riwayat_pengembalian()
        elif pilih == "8": laporan_pendapatan()
        elif pilih == "9": laporan_stok()
        elif pilih == "0":
            if konfirmasi("Yakin ingin logout?"):
                break
        else:
            print("Pilihan tidak valid.")
        jeda()


def menu_pelanggan(user):
    while True:
        print()
        judul_panel("SISTEM PENYEWAAN BAJU ADAT - PELANGGAN", 60)
        print(f"  Selamat datang, {user['nama_lengkap']}")
        garis(60)
        print("1. Lihat katalog")
        print("2. Cari baju adat")
        print("3. Reservasi berdasarkan tanggal")
        print("4. Riwayat transaksi")
        print("5. Lihat status pembayaran")
        print("0. Logout")
        pilih = input("Pilih menu: ").strip()

        if pilih == "1": tampilkan_katalog()
        elif pilih == "2": cari_baju()
        elif pilih == "3": buat_reservasi(user)
        elif pilih == "4": riwayat_pelanggan(user)
        elif pilih == "5":
            data = [
                t for t in baca_csv(FILE_TRANSAKSI)
                if t["username"] == user["username"]
            ]
            tampilkan_transaksi(data)
            for t in data:
                dibayar = total_pembayaran_transaksi(t["id_transaksi"])
                tagihan = int(t["total_bayar"]) + int(t["denda"] or 0)
                print(
                    f"{t['id_transaksi']}: {format_rupiah(dibayar)} dibayar, "
                    f"sisa {format_rupiah(max(0, tagihan - dibayar))}"
                )
        elif pilih == "0":
            if konfirmasi("Yakin ingin logout?"):
                break
        else:
            print("Pilihan tidak valid.")
        jeda()


def main():
    inisialisasi_file()
    while True:
        print()
        judul_panel("SISTEM PENYEWAAN BAJU ADAT", 60)
        print("1. Login")
        print("2. Register pelanggan")
        print("0. Keluar")
        pilih = input("Pilih menu: ").strip()

        if pilih == "1":
            user = login()
            if user:
                if user["role"] == "admin":
                    menu_admin(user)
                else:
                    menu_pelanggan(user)
        elif pilih == "2":
            register_pelanggan()
        elif pilih == "0":
            if konfirmasi("Keluar dari program?"):
                print("Terima kasih telah menggunakan sistem.")
                break
        else:
            print("Pilihan tidak valid.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram dihentikan oleh pengguna.")
