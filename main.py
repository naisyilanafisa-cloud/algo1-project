import csv, os, sys
from datetime import datetime, date

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FILE_USERS, FILE_KATALOG, FILE_TRANSAKSI, FILE_PEMBAYARAN, FILE_PENGEMBALIAN = (
    "users.csv", "katalog.csv", "transaksi.csv", "pembayaran.csv", "pengembalian.csv"
)
DENDA_PER_HARI, PERSEN_DISKON_PELANGGAN_BARU = 20000, 10

HEADERS = {
    FILE_USERS: ["username", "password", "nik", "nama_lengkap", "no_hp", "alamat", "role"],
    FILE_KATALOG: ["kode", "nama_baju", "ukuran", "harga_sewa", "stok"],
    FILE_TRANSAKSI: [
        "id_transaksi", "username", "nik", "nama_penyewa", "no_hp",
        "kode_baju", "nama_baju", "jumlah", "tanggal_mulai", "tanggal_selesai",
        "lama_sewa", "harga_per_hari", "subtotal", "diskon", "total_bayar",
        "status", "tanggal_transaksi", "denda", "tanggal_pengembalian"
    ],
    FILE_PEMBAYARAN: ["id_pembayaran", "id_transaksi", "tanggal", "metode", "jumlah_bayar", "keterangan"],
    FILE_PENGEMBALIAN: ["id_pengembalian", "id_transaksi", "tanggal_rencana", "tanggal_realisasi", "terlambat_hari", "denda", "kondisi", "catatan"],
}

# --- CSV & File Handlers ---
def baca_csv(f):
    if not os.path.exists(f): return []
    with open(f, "r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))

def simpan_csv(f, data):
    fields = HEADERS[f]
    tmp = f + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as file:
        w = csv.DictWriter(file, fieldnames=fields)
        w.writeheader()
        for r in data:
            baris = {}
            for k in fields:
                baris[k] = r.get(k, "")
            w.writerow(baris)
    os.replace(tmp, f)

def inisialisasi_file():
    for f, h in HEADERS.items():
        if not os.path.exists(f):
            with open(f, "w", newline="", encoding="utf-8") as file:
                csv.writer(file).writerow(h)
        else:
            with open(f, "r", newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                rows, old_h = list(reader), reader.fieldnames or []
            if old_h != h:
                simpan_csv(f, [{k: r.get(k, "") for k in h} for r in rows])
    users = baca_csv(FILE_USERS)
    ada_admin = False
    for u in users:
        if u.get("username") == "admin":
            ada_admin = True
            break
    if not ada_admin:
        users.append({
            "username": "admin", "password": "admin123", "nik": "-",
            "nama_lengkap": "Administrator", "no_hp": "-", "alamat": "-", "role": "admin"
        })
        simpan_csv(FILE_USERS, users)

# --- Input & Helper ---
def konfirmasi(pesan):
    while True:
        j = input(f"{pesan} (Y/N): ").strip().upper()
        if j in ("Y", "N"): return j == "Y"
        print("Masukkan Y atau N.")

def input_wajib(pesan):
    while True:
        v = input(pesan).strip()
        if v: return v
        print("Input tidak boleh kosong.")

def input_angka(pesan, minimum=0):
    while True:
        try:
            v = int(input(pesan).strip())
            if v >= minimum: return v
            print(f"Nilai minimal adalah {minimum}.")
        except ValueError:
            print("Masukkan angka yang valid.")

def format_rupiah(v):
    return "Rp " + f"{int(v):,}".replace(",", ".")

def format_tanggal(d):
    return d.strftime("%Y-%m-%d")

def parse_tanggal(s):
    return datetime.strptime(s, "%Y-%m-%d").date()

def hitung_hari(m, s):
    return (s - m).days + 1

def input_tanggal(pesan, default=None):
    while True:
        t = input(pesan).strip()
        if not t and default: return default
        try: return parse_tanggal(t)
        except ValueError: print("Format tanggal harus YYYY-MM-DD. Contoh: 2026-11-20.")

def buat_id(prefix, data, kolom):
    maks = 0
    for r in data:
        nilai = r.get(kolom, "")
        if nilai.startswith(prefix) and nilai[len(prefix):].isdigit():
            nomor = int(nilai[len(prefix):])
            if nomor > maks:
                maks = nomor
    return f"{prefix}{maks + 1:04d}"

def cari_data(data, k, v):
    for r in data:
        if r.get(k) == v:
            return r
    return None

def garis(lebar=72):
    print("┌" + "─" * (lebar - 2) + "┐")

def judul_panel(judul, lebar=72):
    print("┌" + "─" * (lebar - 2) + "┐")
    print("│" + judul.center(lebar - 2) + "│")
    print("└" + "─" * (lebar - 2) + "┘")

def batas_tabel(lebar, ki="├", te="┼", ka="┤"):
    print(ki + te.join("─" * w for w in lebar) + ka)

def jeda():
    input("\nTekan Enter untuk kembali...")

# --- Auth ---
def register_pelanggan():
    print("\n=== REGISTRASI PELANGGAN ===")
    users = baca_csv(FILE_USERS)
    nik, nama = input_wajib("NIK (16 digit)       : "), input_wajib("Nama lengkap         : ").title()
    no_hp, alamat = input_wajib("No. HP (08xxxxxxxxxx): "), input_wajib("Alamat lengkap       : ")
    username, password = input_wajib("Username             : ").lower(), input_wajib("Password             : ")
    if not (nik.isdigit() and len(nik) == 16): return print("Gagal: NIK harus 16 digit angka.")
    if not (no_hp.isdigit() and no_hp.startswith("08") and 10 <= len(no_hp) <= 13): return print("Gagal: nomor HP harus 10-13 digit dan diawali 08.")
    for u in users:
        if u["nik"] == nik:
            return print("Gagal: NIK sudah terdaftar.")
    for u in users:
        if u["username"] == username:
            return print("Gagal: username sudah digunakan.")
    if konfirmasi(f"Simpan akun pelanggan {nama}?"):
        users.append({"username": username, "password": password, "nik": nik, "nama_lengkap": nama, "no_hp": no_hp, "alamat": alamat, "role": "pelanggan"})
        simpan_csv(FILE_USERS, users)
        print("Registrasi berhasil. Silakan login.")
    else: print("Registrasi dibatalkan.")

def login():
    print("\n=== LOGIN ===")
    users = baca_csv(FILE_USERS)
    for sisa in range(2, -1, -1):
        u, p = input("Username: ").strip().lower(), input("Password: ").strip()
        user = None
        for x in users:
            if x["username"] == u and x["password"] == p:
                user = x
                break
        if user:
            print(f"Selamat datang, {user['nama_lengkap']}!")
            return user
        print(f"Login gagal. Sisa percobaan: {sisa}")
    return None

# --- Katalog Baju Adat ---
def tampilkan_katalog(data=None):
    katalog = data if data is not None else baca_csv(FILE_KATALOG)
    lebar = [10, 30, 10, 17, 8]
    print()
    judul_panel("KATALOG BAJU ADAT", sum(lebar) + len(lebar) + 1)
    if not katalog: return print("  Belum ada data katalog.")
    print("│" + "Kode".ljust(10) + "│" + "Nama Baju".ljust(30) + "│" + "Ukuran".ljust(10) + "│" + "Harga/Hari".rjust(17) + "│" + "Stok".rjust(8) + "│")
    batas_tabel(lebar)
    for b in katalog:
        print(f"│{b['kode'][:10].ljust(10)}│{b['nama_baju'][:30].ljust(30)}│{b['ukuran'][:10].ljust(10)}│{format_rupiah(b['harga_sewa']).rjust(17)}│{b['stok'].rjust(8)}│")
    print("└" + "┴".join("─" * w for w in lebar) + "┘")

def tambah_baju():
    katalog = baca_csv(FILE_KATALOG)
    print("\n=== TAMBAH BAJU ADAT ===")
    kode = input_wajib("Kode baju   : ").upper()
    if cari_data(katalog, "kode", kode): return print("Kode sudah digunakan.")
    nama, ukuran = input_wajib("Nama baju   : ").title(), input_wajib("Ukuran      : ").upper()
    harga, stok = input_angka("Harga sewa/hari: ", 1), input_angka("Stok awal      : ", 0)
    if konfirmasi("Simpan data baju?"):
        katalog.append({"kode": kode, "nama_baju": nama, "ukuran": ukuran, "harga_sewa": str(harga), "stok": str(stok)})
        simpan_csv(FILE_KATALOG, katalog)
        print("Baju adat berhasil ditambahkan.")

def ubah_baju():
    katalog = baca_csv(FILE_KATALOG)
    tampilkan_katalog(katalog)
    kode = input("\nKode baju yang diubah: ").strip().upper()
    t = cari_data(katalog, "kode", kode)
    if not t: return print("Data baju tidak ditemukan.")
    print("Tekan Enter untuk mempertahankan nilai lama.")
    nama, ukuran = input(f"Nama [{t['nama_baju']}]: ").strip(), input(f"Ukuran [{t['ukuran']}]: ").strip()
    harga, stok = input(f"Harga/hari [{t['harga_sewa']}]: ").strip(), input(f"Stok [{t['stok']}]: ").strip()
    try:
        if (harga and int(harga) <= 0) or (stok and int(stok) < 0): raise ValueError
    except ValueError: return print("Harga harus lebih dari 0 dan stok tidak boleh negatif.")
    if konfirmasi("Simpan perubahan katalog?"):
        if nama: t["nama_baju"] = nama.title()
        if ukuran: t["ukuran"] = ukuran.upper()
        if harga: t["harga_sewa"] = harga
        if stok: t["stok"] = stok
        simpan_csv(FILE_KATALOG, katalog)
        print("Data katalog berhasil diperbarui.")

def hapus_baju():
    katalog = baca_csv(FILE_KATALOG)
    tampilkan_katalog(katalog)
    kode = input("\nKode baju yang dihapus: ").strip().upper()
    t = cari_data(katalog, "kode", kode)
    if not t: return print("Data tidak ditemukan.")
    dipakai = False
    for x in baca_csv(FILE_TRANSAKSI):
        if x["kode_baju"] == kode and x["status"] in ("RESERVASI", "DISEWA"):
            dipakai = True
            break
    if dipakai:
        return print("Baju tidak dapat dihapus karena masih memiliki reservasi/penyewaan aktif.")
    if konfirmasi(f"Hapus {t['nama_baju']} secara permanen?"):
        simpan_csv(FILE_KATALOG, [b for b in katalog if b["kode"] != kode])
        print("Data baju berhasil dihapus.")

def cari_baju():
    k = baca_csv(FILE_KATALOG)
    kata = input("Masukkan kode/nama/ukuran baju: ").strip().lower()
    hasil = []
    for b in k:
        if kata in b["kode"].lower() or kata in b["nama_baju"].lower() or kata in b["ukuran"].lower():
            hasil.append(b)
    tampilkan_katalog(hasil)

# --- Pelanggan CRUD ---
def tampilkan_pelanggan(data=None):
    pelanggan = [u for u in (data if data is not None else baca_csv(FILE_USERS)) if u["role"] == "pelanggan"]
    w = [15, 18, 23, 15, 37]
    print()
    judul_panel("DATA PELANGGAN", sum(w) + len(w) + 1)
    if not pelanggan: return print("  Belum ada pelanggan.")
    print("│" + "Username".ljust(15) + "│" + "NIK".ljust(18) + "│" + "Nama".ljust(23) + "│" + "No. HP".ljust(15) + "│" + "Alamat".ljust(37) + "│")
    batas_tabel(w)
    for u in pelanggan:
        print(f"│{u['username'][:15].ljust(15)}│{u['nik'][:18].ljust(18)}│{u['nama_lengkap'][:23].ljust(23)}│{u['no_hp'][:15].ljust(15)}│{u.get('alamat', '-')[:37].ljust(37)}│")
    print("└" + "┴".join("─" * x for x in w) + "┘")

def tambah_pelanggan_admin():
    print("\n=== TAMBAH PELANGGAN ===")
    users = baca_csv(FILE_USERS)
    nik, nama = input_wajib("NIK (16 digit): "), input_wajib("Nama lengkap : ").title()
    hp, almt = input_wajib("No. HP       : "), input_wajib("Alamat       : ")
    u, p = input_wajib("Username     : ").lower(), input_wajib("Password     : ")
    if not (nik.isdigit() and len(nik) == 16): return print("NIK harus 16 digit angka.")
    if not (hp.isdigit() and hp.startswith("08") and 10 <= len(hp) <= 13): return print("Nomor HP tidak valid.")
    for x in users:
        if x["nik"] == nik or x["username"] == u:
            return print("NIK atau username sudah terdaftar.")
    users.append({"username": u, "password": p, "nik": nik, "nama_lengkap": nama, "no_hp": hp, "alamat": almt, "role": "pelanggan"})
    simpan_csv(FILE_USERS, users)
    print("Pelanggan berhasil ditambahkan.")

def ubah_pelanggan():
    users = baca_csv(FILE_USERS)
    tampilkan_pelanggan(users)
    u = input("\nUsername pelanggan yang diubah: ").strip().lower()
    t = None
    for x in users:
        if x["username"] == u and x["role"] == "pelanggan":
            t = x
            break
    if not t: return print("Pelanggan tidak ditemukan.")
    print("Tekan Enter untuk mempertahankan data lama.")
    nama, nik = input(f"Nama [{t['nama_lengkap']}]: ").strip(), input(f"NIK [{t['nik']}]: ").strip()
    hp, almt = input(f"No. HP [{t['no_hp']}]: ").strip(), input(f"Alamat [{t.get('alamat', '-')}]: ").strip()
    pwd = input("Password baru (kosongkan jika tetap): ").strip()
    if nik and not (nik.isdigit() and len(nik) == 16): return print("NIK harus 16 digit.")
    if hp and not (hp.isdigit() and hp.startswith("08") and 10 <= len(hp) <= 13): return print("Nomor HP tidak valid.")
    if nik:
        for x in users:
            if x["nik"] == nik and x["username"] != u:
                return print("NIK sudah digunakan pelanggan lain.")
    if konfirmasi("Simpan perubahan pelanggan?"):
        if nama: t["nama_lengkap"] = nama.title()
        if nik: t["nik"] = nik
        if hp: t["no_hp"] = hp
        if almt: t["alamat"] = almt
        if pwd: t["password"] = pwd
        simpan_csv(FILE_USERS, users)
        print("Data pelanggan berhasil diperbarui.")

def hapus_pelanggan():
    users = baca_csv(FILE_USERS)
    tampilkan_pelanggan(users)
    u = input("\nUsername pelanggan yang dihapus: ").strip().lower()
    t = None
    for x in users:
        if x["username"] == u and x["role"] == "pelanggan":
            t = x
            break
    if not t: return print("Pelanggan tidak ditemukan.")
    if konfirmasi(f"Hapus akun {t['nama_lengkap']}? Riwayat transaksi tetap disimpan."):
        simpan_csv(FILE_USERS, [x for x in users if x["username"] != u])
        print("Akun pelanggan berhasil dihapus.")

def cari_pelanggan():
    kata = input("Cari username/nama/NIK/no. HP/alamat: ").strip().lower()
    hasil = []
    for u in baca_csv(FILE_USERS):
        if u["role"] != "pelanggan":
            continue
        if (kata in u.get("username", "").lower()
                or kata in u.get("nama_lengkap", "").lower()
                or kata in u.get("nik", "").lower()
                or kata in u.get("no_hp", "").lower()
                or kata in u.get("alamat", "").lower()):
            hasil.append(u)
    tampilkan_pelanggan(hasil)

# --- Stok, Reservasi & Transaksi ---
def stok_tersedia(kode, mulai, selesai, kecuali=None):
    baju = cari_data(baca_csv(FILE_KATALOG), "kode", kode)
    if not baju: return 0
    terpakai = 0
    for t in baca_csv(FILE_TRANSAKSI):
        if t["kode_baju"] != kode:
            continue
        if t["status"] not in ("RESERVASI", "DISEWA"):
            continue
        if kecuali is not None and t.get("id_transaksi") == kecuali:
            continue
        try:
            if mulai <= parse_tanggal(t["tanggal_selesai"]) and selesai >= parse_tanggal(t["tanggal_mulai"]):
                terpakai += int(t["jumlah"])
        except (ValueError, TypeError):
            continue
    return max(0, int(baju["stok"]) - terpakai)

def pelanggan_baru_berdasarkan_nik(nik, kecuali=None):
    for t in baca_csv(FILE_TRANSAKSI):
        if t.get("nik") != nik:
            continue
        if t.get("status") == "BATAL":
            continue
        if kecuali is not None and t.get("id_transaksi") == kecuali:
            continue
        return False
    return True

def hitung_total_sewa(harga, jumlah, hari, nik, kecuali=None):
    sub = harga * jumlah * hari
    baru = pelanggan_baru_berdasarkan_nik(nik, kecuali)
    diskon = int(sub * PERSEN_DISKON_PELANGGAN_BARU / 100) if baru else 0
    return sub, diskon, sub - diskon, baru

def buat_reservasi(user):
    tampilkan_katalog()
    kode = input("\nKode baju yang dipesan: ").strip().upper()
    baju = cari_data(baca_csv(FILE_KATALOG), "kode", kode)
    if not baju: return print("Baju tidak ditemukan.")
    mulai, selesai = input_tanggal("Tanggal mulai sewa (YYYY-MM-DD): "), input_tanggal("Tanggal selesai sewa (YYYY-MM-DD): ")
    if selesai < mulai: return print("Tanggal selesai tidak boleh sebelum tanggal mulai.")
    if mulai < date.today(): return print("Tanggal mulai tidak boleh berada di masa lalu.")
    jumlah = input_angka("Jumlah baju yang dipesan: ", 1)
    tersedia = stok_tersedia(kode, mulai, selesai)
    if jumlah > tersedia: return print(f"Stok tidak mencukupi. Tersedia pada periode tersebut: {tersedia}.")
    hari = hitung_hari(mulai, selesai)
    subtotal, diskon, total, baru = hitung_total_sewa(int(baju["harga_sewa"]), jumlah, hari, user["nik"])
    print(f"\n=== RINGKASAN RESERVASI ===\nBaju             : {baju['nama_baju']}\nPeriode          : {format_tanggal(mulai)} s.d. {format_tanggal(selesai)}")
    print(f"Jumlah           : {jumlah}\nLama sewa        : {hari} hari\nSubtotal         : {format_rupiah(subtotal)}")
    print(f"Status pelanggan : {'Baru' if baru else 'Pelanggan lama'}\nDiskon pelanggan : {PERSEN_DISKON_PELANGGAN_BARU}% jika NIK baru")
    print(f"Potongan diskon  : {format_rupiah(diskon)}\nTotal sewa       : {format_rupiah(total)}")
    if not konfirmasi("Buat reservasi ini?"): return print("Reservasi dibatalkan.")
    trx = baca_csv(FILE_TRANSAKSI)
    id_trx = buat_id("TRX", trx, "id_transaksi")
    trx.append({
        "id_transaksi": id_trx, "username": user["username"], "nik": user["nik"], "nama_penyewa": user["nama_lengkap"],
        "no_hp": user["no_hp"], "kode_baju": kode, "nama_baju": baju["nama_baju"], "jumlah": str(jumlah),
        "tanggal_mulai": format_tanggal(mulai), "tanggal_selesai": format_tanggal(selesai), "lama_sewa": str(hari),
        "harga_per_hari": baju["harga_sewa"], "subtotal": str(subtotal), "diskon": str(diskon), "total_bayar": str(total),
        "status": "RESERVASI", "tanggal_transaksi": datetime.now().strftime("%Y-%m-%d %H:%M"), "denda": "0", "tanggal_pengembalian": ""
    })
    simpan_csv(FILE_TRANSAKSI, trx)
    print(f"Reservasi berhasil dibuat. ID transaksi: {id_trx}")

def total_pembayaran_transaksi(id_trx):
    total = 0
    for p in baca_csv(FILE_PEMBAYARAN):
        if p["id_transaksi"] == id_trx:
            total += int(p["jumlah_bayar"])
    return total

def tampilkan_transaksi(data=None):
    trx = data if data is not None else baca_csv(FILE_TRANSAKSI)
    w = [9, 19, 21, 6, 24, 15, 12]
    print()
    judul_panel("DATA TRANSAKSI", sum(w) + len(w) + 1)
    if not trx: return print("  Belum ada transaksi.")
    headers = ["ID", "Penyewa", "Baju", "Jumlah", "Periode", "Total", "Status"]
    baris = "│"
    for i in range(len(headers)):
        if i == 3 or i == 5:
            baris += headers[i].rjust(w[i])
        else:
            baris += headers[i].ljust(w[i])
        baris += "│"
    print(baris)
    batas_tabel(w)
    for t in trx:
        periode = f"{t['tanggal_mulai']} s.d. {t['tanggal_selesai']}"
        v = [t["id_transaksi"][:9], t["nama_penyewa"][:19], t["nama_baju"][:21], t["jumlah"], periode[:24], format_rupiah(t["total_bayar"]), t["status"]]
        baris = "│"
        for i in range(len(v)):
            if i == 3 or i == 5:
                baris += v[i].rjust(w[i])
            else:
                baris += v[i].ljust(w[i])
            baris += "│"
        print(baris)
    print("└" + "┴".join("─" * x for x in w) + "┘")

def cari_transaksi():
    k = input("Cari ID/nama penyewa/nama baju/status: ").strip().lower()
    hasil = []
    for t in baca_csv(FILE_TRANSAKSI):
        if (k in t["id_transaksi"].lower() or k in t["nama_penyewa"].lower()
                or k in t["nama_baju"].lower() or k in t["status"].lower()):
            hasil.append(t)
    tampilkan_transaksi(hasil)

def ubah_transaksi():
    trx = baca_csv(FILE_TRANSAKSI)
    tampilkan_transaksi(trx)
    id_trx = input("\nID transaksi yang diubah: ").strip().upper()
    t = cari_data(trx, "id_transaksi", id_trx)
    if not t: return print("Transaksi tidak ditemukan.")
    if t["status"] in ("SELESAI", "BATAL"): return print("Transaksi selesai/dibatalkan tidak dapat diubah.")
    if total_pembayaran_transaksi(id_trx) > 0:
        return print("Transaksi yang sudah memiliki pembayaran tidak dapat diubah.\nSelesaikan penyesuaian pembayaran secara terpisah.")
    print("Kosongkan input jika tidak ingin mengubah nilai.")
    m = input_tanggal(f"Tanggal mulai [{t['tanggal_mulai']}]: ", default=parse_tanggal(t["tanggal_mulai"]))
    s = input_tanggal(f"Tanggal selesai [{t['tanggal_selesai']}]: ", default=parse_tanggal(t["tanggal_selesai"]))
    if s < m: return print("Tanggal selesai tidak valid.")
    jml_txt = input(f"Jumlah [{t['jumlah']}]: ").strip()
    try:
        jml = int(jml_txt) if jml_txt else int(t["jumlah"])
        if jml <= 0: raise ValueError
    except ValueError: return print("Jumlah harus berupa angka positif.")
    tersedia = stok_tersedia(t["kode_baju"], m, s, id_trx)
    if jml > tersedia: return print(f"Stok tidak cukup pada tanggal tersebut. Maksimal: {tersedia}.")
    hari = hitung_hari(m, s)
    sub, diskon, total, _ = hitung_total_sewa(int(t["harga_per_hari"]), jml, hari, t["nik"], id_trx)
    if konfirmasi("Simpan perubahan transaksi?"):
        t.update({"tanggal_mulai": format_tanggal(m), "tanggal_selesai": format_tanggal(s), "jumlah": str(jml), "lama_sewa": str(hari), "subtotal": str(sub), "diskon": str(diskon), "total_bayar": str(total)})
        simpan_csv(FILE_TRANSAKSI, trx)
        print("Transaksi berhasil diperbarui.")

def hapus_transaksi():
    trx = baca_csv(FILE_TRANSAKSI)
    tampilkan_transaksi(trx)
    id_trx = input("\nID transaksi yang dihapus: ").strip().upper()
    t = cari_data(trx, "id_transaksi", id_trx)
    if not t: return print("Transaksi tidak ditemukan.")
    if t["status"] == "SELESAI": return print("Transaksi selesai tidak dapat dihapus agar riwayat pengembalian tetap utuh.")
    if total_pembayaran_transaksi(id_trx) > 0: return print("Transaksi tidak dapat dihapus karena sudah memiliki pembayaran.\nGunakan status BATAL jika transaksi perlu dibatalkan.")
    if konfirmasi(f"Hapus transaksi {id_trx}?"):
        simpan_csv(FILE_TRANSAKSI, [x for x in trx if x["id_transaksi"] != id_trx])
        print("Transaksi berhasil dihapus.")

def ubah_status_transaksi():
    trx = baca_csv(FILE_TRANSAKSI)
    tampilkan_transaksi(trx)
    id_trx = input("\nID transaksi: ").strip().upper()
    t = cari_data(trx, "id_transaksi", id_trx)
    if not t: return print("Transaksi tidak ditemukan.")
    print("1. Konfirmasi reservasi menjadi DISEWA\n2. Batalkan reservasi")
    p = input("Pilih: ").strip()
    if p == "1" and t["status"] == "RESERVASI": t["status"] = "DISEWA"
    elif p == "2" and t["status"] == "RESERVASI": t["status"] = "BATAL"
    else: return print("Pilihan tidak sesuai dengan status transaksi.")
    if konfirmasi("Simpan perubahan status?"):
        simpan_csv(FILE_TRANSAKSI, trx)
        print("Status transaksi diperbarui.")

# --- Pembayaran ---
def kelola_pembayaran():
    trx = baca_csv(FILE_TRANSAKSI)
    tampilkan_transaksi(trx)
    id_trx = input("\nID transaksi yang dibayar: ").strip().upper()
    t = cari_data(trx, "id_transaksi", id_trx)
    if not t: return print("Transaksi tidak ditemukan.")
    if t["status"] == "BATAL": return print("Transaksi yang dibatalkan tidak dapat dibayar.")
    sudah, tagihan = total_pembayaran_transaksi(id_trx), int(t["total_bayar"]) + int(t["denda"] or 0)
    sisa = max(0, tagihan - sudah)
    print(f"\n=== RINGKASAN PEMBAYARAN ===\nID transaksi  : {id_trx}\nNama penyewa  : {t['nama_penyewa']}\nTotal sewa    : {format_rupiah(t['total_bayar'])}\nDenda         : {format_rupiah(t['denda'] or 0)}\nSudah dibayar : {format_rupiah(sudah)}\nSisa tagihan  : {format_rupiah(sisa)}")
    if sisa <= 0: return print("Tagihan sudah lunas.")
    jml = input_angka("Jumlah pembayaran (DP/pelunasan): ", 1)
    if jml > sisa: return print(f"Pembayaran melebihi sisa tagihan. Maksimal {format_rupiah(sisa)}.")
    metode_pilih = input("Metode pembayaran: 1. Tunai  2. Transfer\nPilih metode: ").strip()
    if metode_pilih not in ("1", "2"): return print("Metode pembayaran tidak valid.")
    pmb = baca_csv(FILE_PEMBAYARAN)
    id_bayar = buat_id("PAY", pmb, "id_pembayaran")
    pmb.append({"id_pembayaran": id_bayar, "id_transaksi": id_trx, "tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"), "metode": "Tunai" if metode_pilih == "1" else "Transfer", "jumlah_bayar": str(jml), "keterangan": "Pelunasan" if jml == sisa else "DP/Angsuran"})
    simpan_csv(FILE_PEMBAYARAN, pmb)
    tot = sudah + jml
    print(f"Pembayaran berhasil. ID pembayaran: {id_bayar}\nStatus pembayaran: {'LUNAS' if tot >= tagihan else 'BELUM LUNAS'}\nSisa tagihan: {format_rupiah(tagihan - tot)}")

def riwayat_pembayaran():
    pmb, id_trx = baca_csv(FILE_PEMBAYARAN), input("ID transaksi: ").strip().upper()
    hasil = [p for p in pmb if p["id_transaksi"] == id_trx]
    print(f"\n=== RIWAYAT PEMBAYARAN {id_trx} ===")
    if not hasil: return print("Belum ada pembayaran.")
    for p in hasil: print(f"{p['id_pembayaran']} | {p['tanggal']} | {p['metode']} | {format_rupiah(p['jumlah_bayar'])} | {p['keterangan']}")
    print(f"Total dibayar: {format_rupiah(total_pembayaran_transaksi(id_trx))}")

# --- Pengembalian & Denda ---
def proses_pengembalian():
    trx = baca_csv(FILE_TRANSAKSI)
    aktif = [t for t in trx if t["status"] == "DISEWA"]
    tampilkan_transaksi(aktif)
    id_trx = input("\nID transaksi yang dikembalikan: ").strip().upper()
    t = cari_data(aktif, "id_transaksi", id_trx)
    if not t: return print("Transaksi DISEWA tidak ditemukan.")
    t_rencana, t_kembali = parse_tanggal(t["tanggal_selesai"]), input_tanggal("Tanggal pengembalian aktual (YYYY-MM-DD), Enter untuk hari ini: ", default=date.today())
    if t_kembali < parse_tanggal(t["tanggal_mulai"]): return print("Tanggal pengembalian tidak boleh sebelum tanggal mulai sewa.")
    if t_kembali > date.today(): return print("Tanggal pengembalian tidak boleh melewati hari ini.")
    terlambat = max(0, (t_kembali - t_rencana).days)
    denda = terlambat * DENDA_PER_HARI
    print(f"\n=== PEMERIKSAAN PENGEMBALIAN ===\nTanggal rencana : {format_tanggal(t_rencana)}\nTanggal aktual  : {format_tanggal(t_kembali)}\nTerlambat       : {terlambat} hari\nDenda           : {format_rupiah(denda)}")
    k_map = {"1": "Baik", "2": "Rusak ringan", "3": "Rusak berat"}
    k_pilih = input("Kondisi baju: 1. Baik  2. Rusak ringan  3. Rusak berat\nPilih kondisi: ").strip()
    if k_pilih not in k_map: return print("Pilihan kondisi tidak valid.")
    catatan = input("Catatan (opsional): ").strip()
    if not konfirmasi("Proses pengembalian baju?"): return print("Pengembalian dibatalkan.")
    ret = baca_csv(FILE_PENGEMBALIAN)
    id_k = buat_id("RET", ret, "id_pengembalian")
    ret.append({"id_pengembalian": id_k, "id_transaksi": id_trx, "tanggal_rencana": format_tanggal(t_rencana), "tanggal_realisasi": format_tanggal(t_kembali), "terlambat_hari": str(terlambat), "denda": str(denda), "kondisi": k_map[k_pilih], "catatan": catatan})
    simpan_csv(FILE_PENGEMBALIAN, ret)
    t.update({"status": "SELESAI", "denda": str(denda), "tanggal_pengembalian": format_tanggal(t_kembali)})
    simpan_csv(FILE_TRANSAKSI, trx)
    print(f"Pengembalian berhasil dicatat. ID pengembalian: {id_k}")
    print("Denda masuk ke tagihan transaksi. Silakan proses pembayaran." if denda else "Tidak ada denda keterlambatan.")

def tampilkan_riwayat_pengembalian():
    data = baca_csv(FILE_PENGEMBALIAN)
    print("\n=== RIWAYAT PENGEMBALIAN ===")
    if not data: return print("Belum ada data pengembalian.")
    for r in data: print(f"{r['id_pengembalian']} | {r['id_transaksi']} | {r['tanggal_realisasi']} | Terlambat {r['terlambat_hari']} hari | Denda {format_rupiah(r['denda'])} | {r['kondisi']}")

# --- Laporan & Riwayat ---
def laporan_pendapatan():
    pembayaran, transaksi = baca_csv(FILE_PEMBAYARAN), baca_csv(FILE_TRANSAKSI)
    print("\n=== LAPORAN PENDAPATAN ===\n1. Semua periode\n2. Berdasarkan bulan dan tahun\n3. Berdasarkan rentang tanggal")
    p = input("Pilih: ").strip()
    if p == "1": terpilih = pembayaran
    elif p == "2":
        bln, thn = input("Bulan (01-12): ").strip(), input("Tahun (YYYY): ").strip()
        if not (bln.isdigit() and 1 <= int(bln) <= 12 and thn.isdigit() and len(thn) == 4):
            return print("Bulan harus 01-12 dan tahun harus 4 digit.")
        terpilih = [x for x in pembayaran if x["tanggal"][:7] == f"{thn}-{int(bln):02d}"]
    elif p == "3":
        aw, ak = input_tanggal("Tanggal awal (YYYY-MM-DD): "), input_tanggal("Tanggal akhir (YYYY-MM-DD): ")
        if ak < aw: return print("Rentang tanggal tidak valid.")
        terpilih, rusak = [], 0
        for x in pembayaran:
            try: tgl = parse_tanggal(x["tanggal"][:10])
            except (ValueError, TypeError): rusak += 1
            else:
                if aw <= tgl <= ak: terpilih.append(x)
        if rusak: print(f"Peringatan: {rusak} pembayaran bertanggal tidak valid dilewati.")
    else: return print("Pilihan tidak valid.")
    print("\nRINCIAN PEMBAYARAN")
    if not terpilih: print("Tidak ada pembayaran pada periode tersebut.")
    else:
        for x in terpilih:
            trx = cari_data(transaksi, "id_transaksi", x["id_transaksi"])
            print(f"{x['tanggal']} | {x['id_transaksi']} | {trx['nama_penyewa'] if trx else '-'} | {x['metode']} | {format_rupiah(x['jumlah_bayar'])}")
    total = 0
    for x in terpilih:
        total += int(x["jumlah_bayar"])
    aktif = []
    for t in transaksi:
        if t["status"] != "BATAL":
            aktif.append(t)
    tot_tag = 0
    for t in aktif:
        tot_tag += int(t["total_bayar"]) + int(t["denda"] or 0)
    tot_byr = 0
    for x in pembayaran:
        tot_byr += int(x["jumlah_bayar"])
    dibayar = {}
    for x in pembayaran:
        if x["id_transaksi"] in dibayar:
            dibayar[x["id_transaksi"]] += int(x["jumlah_bayar"])
        else:
            dibayar[x["id_transaksi"]] = int(x["jumlah_bayar"])
    piutang = 0
    for t in aktif:
        sisa = int(t["total_bayar"]) + int(t["denda"] or 0) - dibayar.get(t["id_transaksi"], 0)
        if sisa > 0:
            piutang += sisa
    print("─" * 65)
    print(f"Pendapatan diterima periode ini : {format_rupiah(total)}\nTotal pembayaran sepanjang waktu: {format_rupiah(tot_byr)}\nTotal tagihan transaksi aktif/selesai: {format_rupiah(tot_tag)}\nPiutang tersisa                  : {format_rupiah(piutang)}")

def laporan_stok():
    katalog, transaksi = baca_csv(FILE_KATALOG), baca_csv(FILE_TRANSAKSI)
    print()
    judul_panel("LAPORAN STOK BAJU ADAT", 100)
    if not katalog: return print("Belum ada data katalog.")
    print(f"{'Kode':<9} {'Nama Baju':<25} {'Stok Total':>12} {'Dipesan/Disewa Hari Ini':>24} {'Tersedia Hari Ini':>18}\n" + "─" * 100)
    for b in katalog:
        sedang = 0
        for t in transaksi:
            if t["kode_baju"] != b["kode"]:
                continue
            if t["status"] not in ("RESERVASI", "DISEWA"):
                continue
            try:
                mulai = parse_tanggal(t["tanggal_mulai"])
                selesai = parse_tanggal(t["tanggal_selesai"])
            except (ValueError, TypeError):
                continue
            if mulai <= date.today() <= selesai:
                sedang += int(t["jumlah"])
        print(f"{b['kode']:<9} {b['nama_baju'][:24]:<25} {int(b['stok']):>12} {sedang:>24} {stok_tersedia(b['kode'], date.today(), date.today()):>18}")
    print("─" * 100 + "\nCatatan: Ketersediaan dapat berbeda untuk tanggal reservasi mendatang.")

def tampilkan_sisa_tagihan(data):
    dibayar = {}
    for p in baca_csv(FILE_PEMBAYARAN):
        if p["id_transaksi"] in dibayar:
            dibayar[p["id_transaksi"]] += int(p["jumlah_bayar"])
        else:
            dibayar[p["id_transaksi"]] = int(p["jumlah_bayar"])
    for t in data:
        if t["id_transaksi"] in dibayar:
            bayar = dibayar[t["id_transaksi"]]
        else:
            bayar = 0
        sisa = int(t["total_bayar"]) + int(t["denda"] or 0) - bayar
        if sisa < 0:
            sisa = 0
        print(f"{t['id_transaksi']} | Dibayar {format_rupiah(bayar)} | Sisa {format_rupiah(sisa)}")

def riwayat_pelanggan(user):
    data = [t for t in baca_csv(FILE_TRANSAKSI) if t["username"] == user["username"]]
    tampilkan_transaksi(data)
    tampilkan_sisa_tagihan(data)

# --- Menu Navigasi ---
def menu_katalog_admin():
    while True:
        print()
        judul_panel("KELOLA KATALOG", 40)
        print("1. Tampilkan katalog\n2. Tambah baju\n3. Ubah baju\n4. Hapus baju\n5. Cari baju\n0. Kembali")
        p = input("Pilih: ").strip()
        if p == "0":
            break
        elif p == "1":
            tampilkan_katalog()
        elif p == "2":
            tambah_baju()
        elif p == "3":
            ubah_baju()
        elif p == "4":
            hapus_baju()
        elif p == "5":
            cari_baju()
        else:
            print("Pilihan tidak valid.")

def menu_pelanggan_admin():
    while True:
        print()
        judul_panel("KELOLA PELANGGAN", 40)
        print("1. Tampilkan pelanggan\n2. Tambah pelanggan\n3. Ubah pelanggan\n4. Hapus pelanggan\n5. Cari pelanggan\n0. Kembali")
        p = input("Pilih: ").strip()
        if p == "0":
            break
        elif p == "1":
            tampilkan_pelanggan()
        elif p == "2":
            tambah_pelanggan_admin()
        elif p == "3":
            ubah_pelanggan()
        elif p == "4":
            hapus_pelanggan()
        elif p == "5":
            cari_pelanggan()
        else:
            print("Pilihan tidak valid.")

def menu_transaksi_admin():
    while True:
        print()
        judul_panel("KELOLA TRANSAKSI", 40)
        print("1. Tampilkan transaksi\n2. Cari transaksi\n3. Ubah data transaksi\n4. Hapus transaksi\n5. Konfirmasi / batalkan reservasi\n0. Kembali")
        p = input("Pilih: ").strip()
        if p == "0":
            break
        elif p == "1":
            tampilkan_transaksi()
        elif p == "2":
            cari_transaksi()
        elif p == "3":
            ubah_transaksi()
        elif p == "4":
            hapus_transaksi()
        elif p == "5":
            ubah_status_transaksi()
        else:
            print("Pilihan tidak valid.")

def menu_admin(user):
    while True:
        print()
        judul_panel("SISTEM PENYEWAAN BAJU ADAT - ADMIN", 60)
        print(f"  Login sebagai: {user['nama_lengkap']}")
        garis(60)
        print("1. CRUD Katalog Baju Adat\n2. CRUD Pelanggan\n3. CRUD Transaksi\n4. Lihat Reservasi\n5. Manajemen Pembayaran\n6. Proses Pengembalian dan Denda\n7. Riwayat Pengembalian\n8. Laporan Pendapatan\n9. Laporan Stok\n0. Logout")
        p = input("Pilih menu: ").strip()
        if p == "1": menu_katalog_admin()
        elif p == "2": menu_pelanggan_admin()
        elif p == "3": menu_transaksi_admin()
        elif p == "4": tampilkan_transaksi([t for t in baca_csv(FILE_TRANSAKSI) if t["status"] == "RESERVASI"])
        elif p == "5":
            kelola_pembayaran()
            if konfirmasi("Lihat riwayat pembayaran?"): riwayat_pembayaran()
        elif p == "6": proses_pengembalian()
        elif p == "7": tampilkan_riwayat_pengembalian()
        elif p == "8": laporan_pendapatan()
        elif p == "9": laporan_stok()
        elif p == "0":
            if konfirmasi("Yakin ingin logout?"): break
        else: print("Pilihan tidak valid.")
        jeda()

def menu_pelanggan(user):
    while True:
        print()
        judul_panel("SISTEM PENYEWAAN BAJU ADAT - PELANGGAN", 60)
        print(f"  Selamat datang, {user['nama_lengkap']}")
        garis(60)
        print("1. Lihat katalog\n2. Cari baju adat\n3. Reservasi berdasarkan tanggal\n4. Riwayat transaksi\n5. Lihat status pembayaran\n0. Logout")
        p = input("Pilih menu: ").strip()
        if p == "1": tampilkan_katalog()
        elif p == "2": cari_baju()
        elif p == "3": buat_reservasi(user)
        elif p == "4": riwayat_pelanggan(user)
        elif p == "5":
            data = [t for t in baca_csv(FILE_TRANSAKSI) if t["username"] == user["username"]]
            print("\n=== STATUS PEMBAYARAN ===")
            if not data: print("Belum ada transaksi.")
            else: tampilkan_sisa_tagihan(data)
        elif p == "0":
            if konfirmasi("Yakin ingin logout?"): break
        else: print("Pilihan tidak valid.")
        jeda()

def main():
    inisialisasi_file()
    while True:
        print()
        judul_panel("SISTEM PENYEWAAN BAJU ADAT", 60)
        print("1. Login\n2. Register pelanggan\n0. Keluar")
        p = input("Pilih menu: ").strip()
        if p == "1":
            u = login()
            if u: (menu_admin if u["role"] == "admin" else menu_pelanggan)(u)
        elif p == "2": register_pelanggan()
        elif p == "0":
            if konfirmasi("Keluar dari program?"):
                print("Terima kasih telah menggunakan sistem.")
                break
        else: print("Pilihan tidak valid.")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\nProgram dihentikan oleh pengguna.")