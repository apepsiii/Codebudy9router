# Admin Account Management Guide

## Current Admin Account

Akun admin sudah dibuat di database:

- **Email:** admin@v2fun.local
- **User ID:** 1
- **Created:** 2026-08-27 05:04:08

## Cara Login

1. Jalankan web server:
   ```bash
   python v2fun_scripts/v2fun_web_v2.py
   ```

2. Buka browser: http://localhost:5000/login

3. Login dengan:
   - Email: admin@v2fun.local
   - Password: (password yang sudah dibuat sebelumnya)

## Cara Membuat Akun Admin Baru

### Metode 1: Menggunakan Script `create_admin.py`

```bash
python create_admin.py <email> <password>
```

Contoh:
```bash
python create_admin.py admin@example.com MySecurePassword123
```

### Metode 2: Menggunakan `manage_users.py`

```bash
# Melihat semua user
python manage_users.py list

# Membuat user baru
python manage_users.py create admin2@example.com Password456

# Reset password user yang ada
python manage_users.py reset admin@v2fun.local NewPassword789
```

## Cara Reset Password Admin

Jika lupa password admin yang sudah ada:

```bash
python manage_users.py reset admin@v2fun.local NewPasswordHere
```

## Cara Mengaktifkan Registrasi Publik (Opsional)

Jika ingin mengizinkan user untuk registrasi sendiri melalui web UI:

Edit file `v2fun_scripts/v2fun_web_v2.py`:

1. Ubah route `/register` (line 373-376):
   ```python
   @app.route('/register')
   def register_page():
       """Registration page"""
       return render_template('register.html')  # Enable registration
   ```

2. Ubah endpoint `/api/register` (line 379-382):
   ```python
   @app.route('/api/register', methods=['POST'])
   def api_register():
       """Register new user"""
       data = request.json
       email = data.get('email')
       password = data.get('password')
       
       if not email or not password:
           return jsonify({"success": False, "message": "Email and password required"})
       
       user_id = create_user(email, password)
       
       if user_id:
           return jsonify({"success": True, "message": "Registration successful! Please login."})
       else:
           return jsonify({"success": False, "message": "Email already exists"})
   ```

Tapi untuk keamanan, **disarankan tetap disable registrasi publik** dan hanya admin yang bisa membuat akun via script.

## Verifikasi Akun di Database

Cek langsung ke database SQLite:

```bash
# Menggunakan sqlite3 command line
sqlite3 v2fun_data/v2fun.db "SELECT id, email, created_at FROM users;"

# Atau menggunakan Python
python -c "from v2fun_scripts.database import get_db; conn = get_db(); cursor = conn.cursor(); cursor.execute('SELECT id, email, created_at FROM users'); [print(row) for row in cursor.fetchall()]; conn.close()"
```

## Tools yang Tersedia

1. **create_admin.py** - Membuat admin account baru
2. **manage_users.py** - Manage users (list, create, reset password)
3. **v2fun_scripts/database.py** - Fungsi database low-level

## Troubleshooting

### Problem: Tidak bisa login
**Solution:** Reset password menggunakan `manage_users.py reset`

### Problem: Lupa email admin
**Solution:** Lihat semua user dengan `manage_users.py list`

### Problem: Database corrupt
**Solution:** Backup dan recreate database dengan `python v2fun_scripts/database.py`

## Security Notes

- Password di-hash menggunakan SHA-256
- Session token: 32-byte random (7 hari expiry)
- Jangan expose port 5000 ke internet tanpa HTTPS
- Untuk production, gunakan reverse proxy (nginx/apache) dengan SSL

## Next Steps

Setelah login sebagai admin, Anda bisa:

1. Import V2Fun accounts (Google accounts)
2. Process accounts untuk mendapatkan JWT token
3. Generate images menggunakan V2Fun API
4. Monitor quota dan usage dashboard
5. Export/import data backup

---

**Last Updated:** 2026-08-27
