# 🚀 VPN Management API - One Click Install

Instalasi VPN Management API hanya dengan satu perintah!

## ⚡ Quick Install

### Method 1: Using curl
```bash
bash <(curl -sL https://raw.githubusercontent.com/alrel1408/API/main/quick_install.sh)
```

### Method 2: Using wget  
```bash
bash <(wget -qO- https://raw.githubusercontent.com/alrel1408/API/main/quick_install.sh)
```

## 📋 System Requirements

- **OS**: Ubuntu 18.04+, Debian 9+, CentOS 7+
- **RAM**: Minimal 512MB
- **Storage**: Minimal 1GB free space
- **Network**: Internet connection required
- **Privileges**: Root access required

## 🎯 What Will Be Installed

### Core Components
- ✅ Python 3 + pip
- ✅ Flask framework
- ✅ Gunicorn WSGI server
- ✅ Nginx reverse proxy
- ✅ Systemd service

### API Features
- ✅ SSH account management
- ✅ Trojan account management  
- ✅ VLess account management
- ✅ VMess account management
- ✅ Trial account creation
- ✅ Account listing & deletion
- ✅ Server statistics
- ✅ API key authentication

### Management Tools
- ✅ `vpn-api` command for service control
- ✅ Management panel script
- ✅ API testing script
- ✅ Uninstaller script

## 🔧 After Installation

### 1. Check Service Status
```bash
vpn-api status
```

### 2. View API Key
```bash
vpn-api key
```

### 3. Test API
```bash
# Replace YOUR_API_KEY with actual key from step 2
curl -H "X-API-Key: YOUR_API_KEY" http://YOUR_SERVER_IP:5000/api/v1/info
```

### 4. Create Trial Account
```bash
# SSH Trial
curl -X POST -H "X-API-Key: YOUR_API_KEY" http://YOUR_SERVER_IP:5000/api/v1/trial/ssh

# Trojan Trial  
curl -X POST -H "X-API-Key: YOUR_API_KEY" http://YOUR_SERVER_IP:5000/api/v1/trial/trojan
```

## 🛠️ Management Commands

```bash
vpn-api start      # Start API service
vpn-api stop       # Stop API service  
vpn-api restart    # Restart API service
vpn-api status     # Check service status
vpn-api logs       # View service logs
vpn-api key        # Show API keys
```

## 📚 Management Tools

### Interactive Management Panel
```bash
/etc/API/manage_api.sh
```

### Test All Endpoints
```bash
/etc/API/test_api.sh
```

### View Documentation
```bash
cat /etc/API/README.md
cat /etc/API/API_DOCUMENTATION.md
```

## 🔗 API Endpoints

### Server Info
```bash
GET /api/v1/info
```

### SSH Management
```bash
POST /api/v1/ssh/create          # Create SSH account
POST /api/v1/trial/ssh           # Create SSH trial
GET  /api/v1/ssh/list            # List SSH accounts
DELETE /api/v1/ssh/delete/{user} # Delete SSH account
```

### Trojan Management  
```bash
POST /api/v1/trojan/create          # Create Trojan account
POST /api/v1/trial/trojan           # Create Trojan trial
GET  /api/v1/trojan/list            # List Trojan accounts
DELETE /api/v1/trojan/delete/{uuid} # Delete Trojan account
```

### VLess Management
```bash
POST /api/v1/vless/create          # Create VLess account
POST /api/v1/trial/vless           # Create VLess trial  
GET  /api/v1/vless/list            # List VLess accounts
DELETE /api/v1/vless/delete/{uuid} # Delete VLess account
```

### VMess Management
```bash
POST /api/v1/vmess/create          # Create VMess account
POST /api/v1/trial/vmess           # Create VMess trial
GET  /api/v1/vmess/list            # List VMess accounts  
DELETE /api/v1/vmess/delete/{uuid} # Delete VMess account
```

## 🔐 Authentication

Semua API endpoint memerlukan header `X-API-Key`:

```bash
curl -H "X-API-Key: your-api-key-here" http://server:5000/api/v1/info
```

## 🌐 Access URLs

Setelah instalasi, API dapat diakses di:
- **Local**: http://localhost:5000
- **External**: http://YOUR_SERVER_IP:5000

## 📱 Example Usage

### Create SSH Account
```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass123","days":30}' \
  http://YOUR_SERVER_IP:5000/api/v1/ssh/create
```

### Create Trojan Trial
```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  http://YOUR_SERVER_IP:5000/api/v1/trial/trojan
```

### List All SSH Accounts
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://YOUR_SERVER_IP:5000/api/v1/ssh/list
```

## 🗑️ Uninstall

Untuk menghapus API sepenuhnya:
```bash
/etc/API/uninstall_api.sh
```

## ❓ Troubleshooting

### Service Not Starting
```bash
# Check logs
journalctl -u vpn-api -f

# Check port
netstat -tlnp | grep 5000

# Restart service
vpn-api restart
```

### API Not Responding
```bash
# Check if service is running
vpn-api status

# Check nginx
systemctl status nginx

# Test local connection
curl http://localhost:5000/api/v1/info
```

### Permission Issues
```bash
# Fix permissions
chmod +x /etc/API/*.sh
chown -R root:root /etc/API/
```

## 🆘 Support

Jika mengalami masalah:

1. **Check logs**: `vpn-api logs`
2. **Check status**: `vpn-api status` 
3. **Test locally**: `curl http://localhost:5000/api/v1/info`
4. **Check firewall**: Pastikan port 5000 terbuka
5. **Reinstall**: Jalankan uninstaller lalu install ulang

## 📈 Features

- ✅ **Multi-Protocol**: SSH, Trojan, VLess, VMess
- ✅ **Trial Accounts**: Auto-expire trial accounts
- ✅ **Secure**: API key authentication
- ✅ **RESTful**: Standard REST API
- ✅ **Logging**: Comprehensive logging
- ✅ **Management**: Web-based management tools
- ✅ **Auto-Install**: One command installation
- ✅ **Auto-Uninstall**: Clean removal option

---

**Repository**: https://github.com/alrel1408/API  
**License**: MIT  
**Version**: 1.0
