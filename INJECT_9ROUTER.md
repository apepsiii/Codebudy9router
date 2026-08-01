# Cara Inject Kiro Refresh Token ke 9Router

## Masalah yang Ditemui
- Error "Invalid provider" saat menggunakan provider name "kiro"
- 9router tidak mengenali provider "kiro"

## Solusi
Gunakan provider name **"anthropic"** karena:
- Kiro menggunakan infrastruktur Anthropic (Claude)
- Refresh token Kiro compatible dengan Anthropic API
- 9router menerima provider "anthropic" sebagai provider valid

## Cara Inject

### 1. Dari File kiro_tokens.txt
```bash
python main.py --inject-from-file kiro_tokens.txt --router-password YOUR_PASSWORD --provider anthropic
```

### 2. Langsung Saat Login/Register
```bash
python main.py 10 4 --inject-9router --router-password YOUR_PASSWORD --provider anthropic
```

### 3. Default Provider
Secara default, script sudah menggunakan provider "anthropic". Jika tidak spesifik `--provider`, akan otomatis menggunakan "anthropic".

```bash
# Tanpa --provider (otomatis anthropic)
python main.py --inject-from-file kiro_tokens.txt --router-password YOUR_PASSWORD
```

## Format File kiro_tokens.txt
```
email@example.com:refresh_token_part1:refresh_token_part2
```

**CATATAN:** Jangan tambahkan prefix "(done)" di depan email. Format harus bersih seperti contoh di atas.

## Verifikasi Hasil
Buka dashboard 9router di:
```
http://localhost:20128/dashboard/providers/anthropic
```

Atau cek via API:
```bash
curl -H "Cookie: auth_token=YOUR_TOKEN" http://localhost:20128/api/providers
```

## Provider Valid di 9router
- ✅ **anthropic** (untuk Kiro tokens)
- ✅ openai
- ✅ cloudflare-ai
- ✅ dan provider lainnya
- ❌ kiro (tidak valid)
- ❌ kr (tidak valid)

## Contoh Output Sukses
```
════════════════════════════════════════════════════════════
INJECT KIRO REFRESH TOKEN KE 9ROUTER DARI FILE
════════════════════════════════════════════════════════════

>  File: C:\laragon\www\KiroApiKey\kiro_tokens.txt
>  9router: http://localhost:20128
>  Provider: anthropic
>  Workers: 2

+  Total entry: 11
+  Berhasil inject: 11

════════════════════════════════════════════════════════════
SELESAI
════════════════════════════════════════════════════════════
```

## Troubleshooting

### Error: "Invalid provider"
- Pastikan menggunakan `--provider anthropic`
- Jangan gunakan "kiro" atau "kr"

### Error: "HTTP 401: Unauthorized"
- Pastikan 9router sudah running di `http://localhost:20128`
- Pastikan password 9router benar

### Error: "duplicate"
- Akun sudah ada di 9router
- Script otomatis skip akun yang sudah ada (tidak error)

### Tokens tidak muncul di dashboard
- Cek URL yang benar: `http://localhost:20128/dashboard/providers/anthropic`
- BUKAN: `http://localhost:20128/dashboard/providers/kiro`
