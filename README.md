# 🚀 VPN Management API

API lengkap untuk mengelola akun SSH, Trojan, VLess, dan VMess dengan sistem keamanan yang kuat.

## ✨ Fitur Utama

- 🔐 **Autentikasi API Key** dengan header X-API-Key
- ⚠️ **Rate Limiting** (DISABLED untuk testing - uncomment untuk production)
- 📊 **Logging & Monitoring** lengkap
- 🎯 **Trial Account** dengan username otomatis
- ⚡ **Account Management** CRUD untuk semua service
- 📈 **Statistics & Analytics**
- 💾 **Database SQLite** untuk penyimpanan
- 🔄 **Auto Restart** service dengan systemd

## 📦 Instalasi

### 🚀 One-Click Install (Recommended)
```bash
# Method 1: curl
bash <(curl -sL https://raw.githubusercontent.com/alrel1408/API/main/quick_install.sh)

# Method 2: wget
bash <(wget -qO- https://raw.githubusercontent.com/alrel1408/API/main/quick_install.sh)
```

### Quick Install
```bash
# Download installer
wget https://raw.githubusercontent.com/alrel1408/API/main/install_api.sh
chmod +x install_api.sh

# Jalankan installer
./install_api.sh
```

### Manual Install
```bash
# Clone repository
git clone https://github.com/alrel1408/API.git
cd API

# Jalankan installer
chmod +x install_api.sh
./install_api.sh
```

### Uninstall
```bash
# Jalankan uninstaller
/etc/API/uninstall_api.sh

# Atau jika masih di direktori API
./uninstall_api.sh
```

## 🎯 Quick Start

### 1. Cek Status
```bash
vpn-api status
```

### 2. Lihat API Key
```bash
vpn-api key
```

### 3. Test API
```bash
/etc/API/test_api.sh
```

### 4. Management Panel
```bash
/etc/API/manage_api.sh
```

## 🔧 Endpoint Summary

### Trial Accounts (Auto Username)
- `POST /api/v1/trial/ssh` - SSH trial (Trial-SSH-xxx)
- `POST /api/v1/trial/trojan` - Trojan trial (Trial-xxx)  
- `POST /api/v1/trial/vless` - VLess trial (WV-xxx)
- `POST /api/v1/trial/vmess` - VMess trial (WV-xxx)

### Account Management
- `POST /api/v1/ssh/create` - Buat SSH (manual username/password)
- `POST /api/v1/trojan/create` - Buat Trojan (manual username)
- `POST /api/v1/vless/create` - Buat VLess (manual username)
- `POST /api/v1/vmess/create` - Buat VMess (manual username)

### List & Statistics
- `GET /api/v1/accounts/list` - List semua akun
- `GET /api/v1/accounts/stats` - Statistik akun
- `GET /api/v1/logs` - Activity logs
- `GET /api/v1/info` - Server info

### Delete Accounts
- `DELETE /api/v1/ssh/delete/{username}`
- `DELETE /api/v1/trojan/delete/{username}`

## 📋 Contoh Penggunaan

### Buat SSH Trial
```bash
curl -X POST http://your-server:5000/api/v1/trial/ssh \
  -H "X-API-Key: YOUR_API_KEY"
```

### Buat Trojan Account
```bash
curl -X POST http://your-server:5000/api/v1/trojan/create \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "client001",
    "expired_days": 30,
    "quota_gb": 50,
    "ip_limit": 2
  }'
```

### List Semua Akun
```bash
curl -X GET http://your-server:5000/api/v1/accounts/list \
  -H "X-API-Key: YOUR_API_KEY"
```

## 🛠️ Management Commands

```bash
# Service management
vpn-api start      # Start service
vpn-api stop       # Stop service  
vpn-api restart    # Restart service
vpn-api status     # Check status
vpn-api logs       # View logs
vpn-api key        # Show API keys

# Advanced management
/etc/API/manage_api.sh    # Management panel
/etc/API/test_api.sh      # Test all endpoints
```

## 📁 File Structure

```
/etc/API/
├── vpn_api.py                # Main API application
├── install_api.sh            # Full installer script
├── quick_install.sh          # One-click installer from GitHub
├── manage_api.sh             # Management script
├── test_api.sh               # Testing script
├── uninstall_api.sh          # Uninstaller script
├── README.md                 # Main documentation
├── API_DOCUMENTATION.md      # Detailed API docs
├── ONE_CLICK_INSTALL.md      # One-click install guide
├── GITHUB_UPLOAD_GUIDE.md    # GitHub upload instructions
├── api_keys.json             # API keys storage
└── vpn_accounts.db           # SQLite database

/var/log/api/
└── vpn_api.log             # API logs

/etc/systemd/system/
└── vpn-api.service         # Systemd service

/etc/nginx/sites-available/
└── vpn-api                 # Nginx config
```

## 🔐 Keamanan

### API Key Authentication
- Setiap request memerlukan header `X-API-Key`
- API key disimpan dalam format JSON dengan permissions
- Default admin key dibuat saat instalasi

### Rate Limiting
- Default: 200 requests/day, 50/hour
- Trial endpoints: 5 requests/minute
- Create endpoints: 10 requests/minute

### Logging
- Semua aktivitas dicatat dengan timestamp
- IP address tracking
- Error logging dengan rotation

## 📊 Monitoring

### Service Status
```bash
systemctl status vpn-api
systemctl status nginx
```

### Logs
```bash
# API logs
tail -f /var/log/api/vpn_api.log

# Nginx logs
tail -f /var/log/nginx/access.log | grep :5000

# System logs
journalctl -u vpn-api -f
```

### Database
```bash
# Connect to database
sqlite3 /etc/API/vpn_accounts.db

# View accounts
sqlite3 /etc/API/vpn_accounts.db "SELECT * FROM accounts;"

# View logs
sqlite3 /etc/API/vpn_accounts.db "SELECT * FROM activity_logs ORDER BY timestamp DESC LIMIT 10;"
```

## 🚨 Troubleshooting

### Service tidak berjalan
```bash
# Cek status
systemctl status vpn-api

# Restart service
vpn-api restart

# Cek logs
vpn-api logs
```

### Port sudah digunakan
```bash
# Cek port 5000
netstat -tlnp | grep :5000

# Kill process jika perlu
kill -9 <PID>
```

### API tidak response
```bash
# Test lokal
curl -H "X-API-Key: YOUR_KEY" http://localhost:5000/api/v1/info

# Cek nginx
nginx -t
systemctl status nginx
```

### Database error
```bash
# Backup database
cp /etc/API/vpn_accounts.db /etc/API/vpn_accounts.db.backup

# Reset database (akan dibuat ulang)
rm /etc/API/vpn_accounts.db
vpn-api restart
```

### Uninstall Issues
```bash
# Force stop semua proses
pkill -f vpn_api

# Manual cleanup jika uninstaller gagal
systemctl stop vpn-api
systemctl disable vpn-api
rm -f /etc/systemd/system/vpn-api.service
rm -f /usr/local/bin/vpn-api
rm -rf /etc/API
rm -rf /var/log/api

# Reset nginx
rm -f /etc/nginx/sites-enabled/vpn-api
rm -f /etc/nginx/sites-available/vpn-api
systemctl reload nginx
```

## 🔄 Update & Maintenance

### Update API
```bash
# Backup current
cp /etc/API/vpn_api.py /etc/API/vpn_api.py.backup

# Download new version
wget -O /etc/API/vpn_api.py https://raw.githubusercontent.com/your-repo/vpn_api.py

# Restart service
vpn-api restart
```

### Database Backup
```bash
# Manual backup
cp /etc/API/vpn_accounts.db /backup/vpn_accounts_$(date +%Y%m%d).db

# Automated backup (via management script)
/etc/API/manage_api.sh
# Choose option 7 for backup
```

## 📝 Development

### Menambah Endpoint Baru
1. Edit `/etc/API/vpn_api.py`
2. Tambahkan route baru dengan decorator `@require_api_key`
3. Restart service: `vpn-api restart`
4. Test endpoint baru

### Custom API Key Permissions
```python
# Dalam vpn_api.py, tambahkan check permission
def require_permission(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if permission not in request.api_key_data.get('permissions', []) and 'all' not in request.api_key_data.get('permissions', []):
                abort(403, description="Insufficient permissions")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Usage
@app.route('/api/v1/admin/endpoint', methods=['POST'])
@require_api_key
@require_permission('admin')
def admin_endpoint():
    # Admin only endpoint
    pass
```

## 🤝 Kontribusi

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch  
5. Create Pull Request

## 📄 License

MIT License - lihat file LICENSE untuk detail

## 📞 Support

- 📧 Email: support@your-domain.com
- 💬 Telegram: @your_username
- 🐛 Issues: GitHub Issues
- 📚 Docs: API_DOCUMENTATION.md

---

**Made with ❤️ for VPN Management**
