# V2Fun.ai Interactive Discovery - Quick Start

## 🚀 Cara Menjalankan

### Option 1: Double-click (Recommended)
```
Double-click file: run_v2fun_discovery.bat
```

### Option 2: Command Prompt
```cmd
cd E:\APEP\WEB\Codebudy9router
run_v2fun_discovery.bat
```

### Option 3: Python Direct
```cmd
cd E:\APEP\WEB\Codebudy9router
python v2fun_interactive_discovery.py
```

---

## 📋 Apa Yang Akan Terjadi

### 1. Browser Akan Terbuka
- Browser Chrome akan terbuka otomatis
- Jangan tutup terminal/command prompt!
- Terminal akan memberikan instruksi

### 2. Instruksi Step-by-Step

**STEP 1: Landing Page**
- Script navigate ke v2fun.ai
- Anda tunggu sampai loaded
- Press Enter untuk lanjut

**STEP 2: Registrasi**
- Anda daftar akun baru (atau login)
- Email: johnston7504@gezon.net (atau baru)
- Script capture semua API calls
- Press Enter setelah selesai

**STEP 3: Dashboard**
- Explore dashboard/profile
- Lihat quota/usage
- Script capture APIs
- Press Enter untuk lanjut

**STEP 4: Chat**
- Buat conversation baru
- Ketik: "Hello, how are you?"
- Tunggu response
- Script capture chat APIs
- Press Enter untuk lanjut

**STEP 5: Generate Image**
- Cari fitur Image Generation
- Prompt: "A beautiful sunset over mountains"
- Klik Generate
- Tunggu sampai selesai
- Press Enter (JANGAN download dulu)

**STEP 6: Download Image**
- Klik tombol Download
- Save gambar
- Script capture download URL
- Press Enter

**STEP 7: Optional**
- Explore fitur lain
- Klik berbagai menu
- More APIs captured!
- Press Enter jika selesai

### 3. Hasil Otomatis Tersimpan

File yang dibuat:
- `v2fun_capture_TIMESTAMP.json` - Full data
- `v2fun_endpoints.txt` - Endpoint summary

---

## 🎯 Yang Akan Di-Capture

✅ **Registration/Login APIs**
- Endpoint registrasi
- Format request/response
- Token yang didapat

✅ **User Info APIs**
- Profile endpoint
- Quota/usage endpoint
- Settings

✅ **Chat APIs**
- Create conversation
- Send message
- Get response
- Model selection

✅ **Image Generation APIs**
- Generate image endpoint
- Request format
- Response dengan image URL

✅ **Download APIs**
- Image download URL
- Download method

✅ **All Other APIs**
- Models list
- History
- Any other features

---

## ⚠️ PENTING

1. **JANGAN tutup terminal** selama proses
2. **BACA instruksi di terminal** dengan teliti
3. **Press Enter** setelah selesai setiap step
4. **Jangan terburu-buru** - tunggu API calls selesai

---

## 📊 Output Preview

Terminal akan menampilkan:
```
[REQ] POST https://api.prod.v2fun.ai/auth/register
      Body: {"email":"..."}

[RES] OK 200 https://api.prod.v2fun.ai/auth/register
      [!] TOKEN FOUND!
      Data: {"token":"eyJhbG...","userid":"..."}

[REQ] GET https://api.prod.v2fun.ai/models/list?token=xxx

[RES] OK 200 https://api.prod.v2fun.ai/models/list
      [!] MODEL LIST FOUND!
      Data: [{"id":"gpt-4","name":"GPT-4"}...]
```

---

## ✅ Setelah Selesai

1. Check file `v2fun_endpoints.txt` untuk summary
2. Check file `v2fun_capture_*.json` untuk detail
3. Saya akan analyze dan buat automation!

---

## 🚀 READY?

**Jalankan sekarang:**
```cmd
run_v2fun_discovery.bat
```

Atau double-click file `run_v2fun_discovery.bat`

---

**Let's capture those APIs! 🎯**
