# VPN Management API Documentation

API untuk mengelola akun SSH, Trojan, VLess, dan VMess dengan sistem autentikasi yang aman.

## 🚀 Quick Start

### Instalasi
```bash
# Download dan jalankan installer
wget https://raw.githubusercontent.com/your-repo/vpn-api/main/install_api.sh
chmod +x install_api.sh
./install_api.sh
```

### Authentication
Semua endpoint memerlukan header `X-API-Key`:
```bash
curl -H "X-API-Key: YOUR_API_KEY" http://your-server:8080/api/v1/info
```

## 📋 Endpoints

### Server Information
```http
GET /api/v1/info
```
Mendapatkan informasi server (domain, city, NS domain, pub key).

**Response:**
```json
{
  "status": "success",
  "data": {
    "domain": "example.com",
    "city": "Jakarta",
    "ns_domain": "ns.example.com",
    "pub_key": "..."
  }
}
```

---

## 🎯 Trial Endpoints

### SSH Trial
```http
POST /api/v1/trial/ssh
```
Membuat akun SSH trial dengan username dan password otomatis.

**Response:**
```json
{
  "status": "success",
  "message": "Akun SSH trial berhasil dibuat",
  "data": {
    "username": "Trial-SSH-123",
    "password": "ssh1234",
    "service_type": "ssh",
    "ip_limit": 2,
    "expire_date": "2024-01-02",
    "trial_duration": "1 hari",
    "config_url": "https://example.com:81/ssh-Trial-SSH-123.txt"
  }
}
```

### Trojan Trial
```http
POST /api/v1/trial/trojan
```
Membuat akun Trojan trial dengan username otomatis.

**Response:**
```json
{
  "status": "success",
  "message": "Akun Trojan trial berhasil dibuat",
  "data": {
    "username": "Trial-123",
    "uuid": "12345678-1234-1234-1234-123456789abc",
    "service_type": "trojan",
    "quota_gb": 1,
    "ip_limit": 3,
    "expire_date": "2024-01-02",
    "trial_duration": "1 hari",
    "links": {
      "ws_tls": "trojan://uuid@domain:443?...",
      "grpc": "trojan://uuid@domain:443?mode=gun...",
      "ws_ntls": "trojan://uuid@domain:80?..."
    },
    "config_url": "https://example.com:81/trojan-Trial-123.txt"
  }
}
```

### VLess Trial
```http
POST /api/v1/trial/vless
```
Membuat akun VLess trial dengan username otomatis (WV-xxx).

### VMess Trial
```http
POST /api/v1/trial/vmess
```
Membuat akun VMess trial dengan username otomatis (WV-xxx).

---

## 🔧 Account Management

### SSH Account Management

#### Create SSH Account
```http
POST /api/v1/ssh/create
```

**Request Body:**
```json
{
  "username": "user123",
  "password": "password123",
  "limit_ip": 2,
  "expired_days": 30,
  "bug_host": "bug.com"
}
```

#### List SSH Accounts
```http
GET /api/v1/ssh/list
```

#### Delete SSH Account
```http
DELETE /api/v1/ssh/delete/{username}
```

### Trojan Account Management

#### Create Trojan Account
```http
POST /api/v1/trojan/create
```

**Request Body:**
```json
{
  "username": "user123",
  "expired_days": 30,
  "quota_gb": 10,
  "ip_limit": 2
}
```

#### List Trojan Accounts
```http
GET /api/v1/trojan/list
```

#### Delete Trojan Account
```http
DELETE /api/v1/trojan/delete/{username}
```

### VLess Account Management

#### Create VLess Account
```http
POST /api/v1/vless/create
```

**Request Body:**
```json
{
  "username": "user123",
  "expired_days": 30,
  "quota_gb": 10,
  "ip_limit": 2
}
```

### VMess Account Management

#### Create VMess Account
```http
POST /api/v1/vmess/create
```

**Request Body:**
```json
{
  "username": "user123",
  "expired_days": 30,
  "quota_gb": 10,
  "ip_limit": 2,
  "bug_host": "bug.com"
}
```

---

## 📊 General Endpoints

### List All Accounts
```http
GET /api/v1/accounts/list
GET /api/v1/accounts/list?type=ssh
GET /api/v1/accounts/list?type=trojan
```

### Account Statistics
```http
GET /api/v1/accounts/stats
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "service_stats": {
      "ssh": 10,
      "trojan": 5,
      "vless": 3,
      "vmess": 7
    },
    "active_stats": {
      "true": 20,
      "false": 5
    },
    "expiring_soon": 3
  }
}
```

### Activity Logs
```http
GET /api/v1/logs
GET /api/v1/logs?username=user123
GET /api/v1/logs?action=CREATE
GET /api/v1/logs?service_type=ssh&limit=50
```

---

## 🔐 API Key Management

### List API Keys (Admin Only)
```http
GET /api/v1/admin/keys
```

### Create API Key (Admin Only)
```http
POST /api/v1/admin/keys
```

**Request Body:**
```json
{
  "name": "Client API Key",
  "permissions": ["read", "create"]
}
```

---

## 📝 Examples

### Bash Script Example
```bash
#!/bin/bash

API_KEY="your_api_key_here"
SERVER="http://your-server:8080"

# Buat SSH trial
echo "Creating SSH trial..."
curl -X POST "$SERVER/api/v1/trial/ssh" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json"

# Buat Trojan account
echo "Creating Trojan account..."
curl -X POST "$SERVER/api/v1/trojan/create" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "client001",
    "expired_days": 30,
    "quota_gb": 50,
    "ip_limit": 2
  }'

# List semua akun
echo "Listing all accounts..."
curl -X GET "$SERVER/api/v1/accounts/list" \
  -H "X-API-Key: $API_KEY"
```

### Python Example
```python
import requests
import json

class VPNAPIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
    
    def create_ssh_trial(self):
        response = requests.post(
            f"{self.base_url}/api/v1/trial/ssh",
            headers=self.headers
        )
        return response.json()
    
    def create_trojan_account(self, username, expired_days=30, quota_gb=10, ip_limit=2):
        data = {
            'username': username,
            'expired_days': expired_days,
            'quota_gb': quota_gb,
            'ip_limit': ip_limit
        }
        response = requests.post(
            f"{self.base_url}/api/v1/trojan/create",
            headers=self.headers,
            json=data
        )
        return response.json()
    
    def list_accounts(self, service_type=None):
        params = {'type': service_type} if service_type else {}
        response = requests.get(
            f"{self.base_url}/api/v1/accounts/list",
            headers=self.headers,
            params=params
        )
        return response.json()

# Usage
client = VPNAPIClient('http://your-server:8080', 'your_api_key')

# Buat SSH trial
ssh_trial = client.create_ssh_trial()
print(f"SSH Trial: {ssh_trial}")

# Buat Trojan account
trojan_account = client.create_trojan_account('client001', 30, 50, 2)
print(f"Trojan Account: {trojan_account}")

# List semua akun SSH
ssh_accounts = client.list_accounts('ssh')
print(f"SSH Accounts: {ssh_accounts}")
```

---

## ⚡ Rate Limits

⚠️ **CURRENTLY DISABLED FOR TESTING**

Rate limiting telah dinonaktifkan untuk memudahkan pengujian. Untuk production, uncomment baris berikut di `vpn_api.py`:

```python
# Rate limiting - DISABLED FOR TESTING
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

Dan uncomment decorator `@limiter.limit()` di setiap endpoint yang memerlukan rate limiting.

**Production limits (when enabled):**
- **Default**: 200 requests per day, 50 per hour
- **Trial endpoints**: 5 requests per minute
- **Create endpoints**: 10 requests per minute

---

## 🛠️ Management Commands

Setelah instalasi, gunakan command `vpn-api`:

```bash
# Start/Stop/Restart service
vpn-api start
vpn-api stop
vpn-api restart

# Check status
vpn-api status

# View logs
vpn-api logs

# Show API keys
vpn-api key
```

---

## 🔧 Configuration Files

- **API Code**: `/etc/API/vpn_api.py`
- **API Keys**: `/etc/API/api_keys.json`
- **Database**: `/etc/API/vpn_accounts.db`
- **Logs**: `/var/log/api/vpn_api.log`
- **Nginx Config**: `/etc/nginx/sites-available/vpn-api`
- **Installer**: `/etc/API/install_api.sh`
- **Uninstaller**: `/etc/API/uninstall_api.sh`

---

## 🚨 Error Codes

- **400**: Bad Request - Invalid parameters
- **401**: Unauthorized - Invalid or missing API key
- **404**: Not Found - Endpoint or resource not found
- **429**: Too Many Requests - Rate limit exceeded
- **500**: Internal Server Error - Server error

---

## 🔒 Security Notes

1. **API Key Protection**: Jangan share API key di public
2. **HTTPS**: Gunakan HTTPS di production
3. **Firewall**: Batasi akses ke port API
4. **Monitoring**: Monitor log untuk aktivitas mencurigakan
5. **Backup**: Backup database secara berkala

---

## 🆘 Troubleshooting

### Service tidak berjalan
```bash
# Cek status
systemctl status vpn-api

# Cek log
vpn-api logs

# Restart service
vpn-api restart
```

### Port sudah digunakan
```bash
# Cek port yang digunakan
netstat -tlnp | grep :8080

# Kill process jika perlu
kill -9 <PID>
```

### Database error
```bash
# Cek permission database
ls -la /etc/API/vpn_accounts.db

# Reset database jika perlu
rm /etc/API/vpn_accounts.db
vpn-api restart
```

---

## 📞 Support

Jika mengalami masalah, cek:
1. Log file: `/var/log/api/vpn_api.log`
2. Service status: `vpn-api status`
3. Nginx status: `systemctl status nginx`
4. Port accessibility: `curl http://localhost:8080/api/v1/info -H "X-API-Key: YOUR_KEY"`
