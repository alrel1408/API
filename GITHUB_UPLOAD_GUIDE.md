# Panduan Upload ke GitHub

## Langkah 1: Persiapan File
Pastikan semua file berikut ada di direktori `/etc/API/`:

```bash
ls -la /etc/API/
```

File yang harus di-upload:
- `vpn_api.py` - Main API application
- `install_api.sh` - Full installer 
- `quick_install.sh` - One-click installer
- `manage_api.sh` - Management script
- `test_api.sh` - Testing script
- `uninstall_api.sh` - Uninstaller script
- `README.md` - Main documentation
- `API_DOCUMENTATION.md` - Detailed API docs
- `GITHUB_UPLOAD_GUIDE.md` - This guide
- `ONE_CLICK_INSTALL.md` - One-click install instructions

## Langkah 2: Upload ke GitHub

### Method 1: Via Git Command Line
```bash
# Clone repository kosong
git clone https://github.com/alrel1408/API.git
cd API

# Copy semua file dari /etc/API/
cp /etc/API/*.py .
cp /etc/API/*.sh .
cp /etc/API/*.md .

# Add semua file
git add .

# Commit
git commit -m "Initial commit - VPN Management API"

# Push ke GitHub
git push origin main
```

### Method 2: Via GitHub Web Interface
1. Buka https://github.com/alrel1408/API
2. Klik "uploading an existing file"
3. Drag & drop semua file dari `/etc/API/`
4. Tulis commit message: "Initial commit - VPN Management API"
5. Klik "Commit changes"

## Langkah 3: Test One-Click Install

Setelah file di-upload, test installer dengan:

```bash
# Method 1: curl
bash <(curl -sL https://raw.githubusercontent.com/alrel1408/API/main/quick_install.sh)

# Method 2: wget
bash <(wget -qO- https://raw.githubusercontent.com/alrel1408/API/main/quick_install.sh)
```

## File Structure di GitHub
```
alrel1408/API/
├── vpn_api.py              # Main API application
├── install_api.sh          # Full installer with all features
├── quick_install.sh        # One-click installer from GitHub
├── manage_api.sh           # Management panel script
├── test_api.sh             # API testing script
├── uninstall_api.sh        # Uninstaller script
├── README.md               # Main documentation
├── API_DOCUMENTATION.md    # Detailed API documentation
├── GITHUB_UPLOAD_GUIDE.md  # This upload guide
└── ONE_CLICK_INSTALL.md    # One-click install instructions
```

## Troubleshooting Upload

### Jika ada error "repository not empty":
```bash
git pull origin main --allow-unrelated-histories
git add .
git commit -m "Merge with initial commit"
git push origin main
```

### Jika file terlalu besar:
```bash
# Check file sizes
ls -lh /etc/API/

# Remove large files jika ada
# git rm large_file.txt
# git commit -m "Remove large file"
```

### Test setelah upload:
```bash
# Test raw content accessible
curl -sL https://raw.githubusercontent.com/alrel1408/API/main/quick_install.sh | head -10

# Test installer download
curl -sL https://raw.githubusercontent.com/alrel1408/API/main/vpn_api.py | head -10
```
