# 🚀 VPN Management API - Panel Web Implementation Guide

Dokumentasi lengkap endpoint API untuk implementasi panel web management VPN services.

## 🔧 Base Configuration

### API Base URL
```javascript
const API_BASE_URL = 'http://your-server:7777/api/v1';
const API_KEY = 'YOUR_API_KEY_HERE';

// Headers untuk semua request
const headers = {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY
};
```

---

## 📋 DAFTAR LENGKAP ENDPOINT

### 🌐 1. SERVER INFORMATION

#### Get Server Info
```http
GET /api/v1/info
```

**JavaScript Implementation:**
```javascript
async function getServerInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/info`, {
            method: 'GET',
            headers: headers
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            return data.data; // {domain, city, ns_domain, pub_key}
        }
        throw new Error(data.error);
    } catch (error) {
        console.error('Error:', error);
        return null;
    }
}
```

**Response Example:**
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

### 🎯 2. TRIAL ENDPOINTS (Username Otomatis)

#### 2.1 SSH Trial
```http
POST /api/v1/trial/ssh
```

**JavaScript Implementation:**
```javascript
async function createSSHTrial() {
    try {
        const response = await fetch(`${API_BASE_URL}/trial/ssh`, {
            method: 'POST',
            headers: headers
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            return data.data;
        }
        throw new Error(data.error);
    } catch (error) {
        console.error('Error creating SSH trial:', error);
        return null;
    }
}
```

**Response Example:**
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

#### 2.2 Trojan Trial
```http
POST /api/v1/trial/trojan
```

**JavaScript Implementation:**
```javascript
async function createTrojanTrial() {
    try {
        const response = await fetch(`${API_BASE_URL}/trial/trojan`, {
            method: 'POST',
            headers: headers
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            return data.data;
        }
        throw new Error(data.error);
    } catch (error) {
        console.error('Error creating Trojan trial:', error);
        return null;
    }
}
```

#### 2.3 VLess Trial
```http
POST /api/v1/trial/vless
```

**JavaScript Implementation:**
```javascript
async function createVLessTrial() {
    try {
        const response = await fetch(`${API_BASE_URL}/trial/vless`, {
            method: 'POST',
            headers: headers
        });
        return await response.json();
    } catch (error) {
        console.error('Error creating VLess trial:', error);
        return null;
    }
}
```

#### 2.4 VMess Trial
```http
POST /api/v1/trial/vmess
```

**JavaScript Implementation:**
```javascript
async function createVMessTrial() {
    try {
        const response = await fetch(`${API_BASE_URL}/trial/vmess`, {
            method: 'POST',
            headers: headers
        });
        return await response.json();
    } catch (error) {
        console.error('Error creating VMess trial:', error);
        return null;
    }
}
```

---

### 🔧 3. ACCOUNT MANAGEMENT (Manual Username)

#### 3.1 SSH Account Management

##### Create SSH Account
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

**JavaScript Implementation:**
```javascript
async function createSSHAccount(accountData) {
    try {
        const response = await fetch(`${API_BASE_URL}/ssh/create`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(accountData)
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            return data.data;
        }
        throw new Error(data.error);
    } catch (error) {
        console.error('Error creating SSH account:', error);
        return null;
    }
}

// Usage example
const newSSHAccount = {
    username: "client001",
    password: "securepass123",
    limit_ip: 2,
    expired_days: 30,
    bug_host: "bug.com"
};
createSSHAccount(newSSHAccount);
```

##### List SSH Accounts
```http
GET /api/v1/ssh/list
```

**JavaScript Implementation:**
```javascript
async function listSSHAccounts() {
    try {
        const response = await fetch(`${API_BASE_URL}/ssh/list`, {
            method: 'GET',
            headers: headers
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            return data.data; // Array of SSH accounts
        }
        throw new Error(data.error);
    } catch (error) {
        console.error('Error listing SSH accounts:', error);
        return [];
    }
}
```

##### Delete SSH Account
```http
DELETE /api/v1/ssh/delete/{username}
```

**JavaScript Implementation:**
```javascript
async function deleteSSHAccount(username) {
    try {
        const response = await fetch(`${API_BASE_URL}/ssh/delete/${username}`, {
            method: 'DELETE',
            headers: headers
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            return true;
        }
        throw new Error(data.error);
    } catch (error) {
        console.error('Error deleting SSH account:', error);
        return false;
    }
}
```

#### 3.2 Trojan Account Management

##### Create Trojan Account
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

**JavaScript Implementation:**
```javascript
async function createTrojanAccount(accountData) {
    try {
        const response = await fetch(`${API_BASE_URL}/trojan/create`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(accountData)
        });
        return await response.json();
    } catch (error) {
        console.error('Error creating Trojan account:', error);
        return null;
    }
}
```

##### List Trojan Accounts
```http
GET /api/v1/trojan/list
```

**JavaScript Implementation:**
```javascript
async function listTrojanAccounts() {
    try {
        const response = await fetch(`${API_BASE_URL}/trojan/list`, {
            method: 'GET',
            headers: headers
        });
        return await response.json();
    } catch (error) {
        console.error('Error listing Trojan accounts:', error);
        return null;
    }
}
```

##### Delete Trojan Account
```http
DELETE /api/v1/trojan/delete/{username}
```

**JavaScript Implementation:**
```javascript
async function deleteTrojanAccount(username) {
    try {
        const response = await fetch(`${API_BASE_URL}/trojan/delete/${username}`, {
            method: 'DELETE',
            headers: headers
        });
        return await response.json();
    } catch (error) {
        console.error('Error deleting Trojan account:', error);
        return null;
    }
}
```

#### 3.3 VLess Account Management

##### Create VLess Account
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

**JavaScript Implementation:**
```javascript
async function createVLessAccount(accountData) {
    try {
        const response = await fetch(`${API_BASE_URL}/vless/create`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(accountData)
        });
        return await response.json();
    } catch (error) {
        console.error('Error creating VLess account:', error);
        return null;
    }
}
```

#### 3.4 VMess Account Management

##### Create VMess Account
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

**JavaScript Implementation:**
```javascript
async function createVMessAccount(accountData) {
    try {
        const response = await fetch(`${API_BASE_URL}/vmess/create`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(accountData)
        });
        return await response.json();
    } catch (error) {
        console.error('Error creating VMess account:', error);
        return null;
    }
}
```

---

### 📊 4. GENERAL ENDPOINTS

#### 4.1 List All Accounts
```http
GET /api/v1/accounts/list
GET /api/v1/accounts/list?type=ssh
GET /api/v1/accounts/list?type=trojan
GET /api/v1/accounts/list?type=vless
GET /api/v1/accounts/list?type=vmess
```

**JavaScript Implementation:**
```javascript
async function listAllAccounts(serviceType = null) {
    try {
        let url = `${API_BASE_URL}/accounts/list`;
        if (serviceType) {
            url += `?type=${serviceType}`;
        }
        
        const response = await fetch(url, {
            method: 'GET',
            headers: headers
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            return data.data;
        }
        throw new Error(data.error);
    } catch (error) {
        console.error('Error listing accounts:', error);
        return [];
    }
}

// Usage examples
listAllAccounts();           // All accounts
listAllAccounts('ssh');      // Only SSH accounts
listAllAccounts('trojan');   // Only Trojan accounts
```

#### 4.2 Account Statistics
```http
GET /api/v1/accounts/stats
```

**JavaScript Implementation:**
```javascript
async function getAccountStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/accounts/stats`, {
            method: 'GET',
            headers: headers
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            return data.data;
        }
        throw new Error(data.error);
    } catch (error) {
        console.error('Error getting stats:', error);
        return null;
    }
}
```

**Response Example:**
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

#### 4.3 Activity Logs
```http
GET /api/v1/logs
GET /api/v1/logs?username=user123
GET /api/v1/logs?action=CREATE
GET /api/v1/logs?service_type=ssh
GET /api/v1/logs?limit=50
```

**JavaScript Implementation:**
```javascript
async function getActivityLogs(filters = {}) {
    try {
        let url = `${API_BASE_URL}/logs`;
        const params = new URLSearchParams();
        
        if (filters.username) params.append('username', filters.username);
        if (filters.action) params.append('action', filters.action);
        if (filters.service_type) params.append('service_type', filters.service_type);
        if (filters.limit) params.append('limit', filters.limit);
        
        if (params.toString()) {
            url += `?${params.toString()}`;
        }
        
        const response = await fetch(url, {
            method: 'GET',
            headers: headers
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            return data.data;
        }
        throw new Error(data.error);
    } catch (error) {
        console.error('Error getting logs:', error);
        return [];
    }
}

// Usage examples
getActivityLogs();                                    // All logs
getActivityLogs({username: 'user123'});              // User specific logs
getActivityLogs({action: 'CREATE', limit: 20});      // Create actions only
```

---

### 🔑 5. API KEY MANAGEMENT (Admin Only)

#### 5.1 List API Keys
```http
GET /api/v1/admin/keys
```

**JavaScript Implementation:**
```javascript
async function listAPIKeys() {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/keys`, {
            method: 'GET',
            headers: headers
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            return data.data;
        }
        throw new Error(data.error);
    } catch (error) {
        console.error('Error listing API keys:', error);
        return null;
    }
}
```

#### 5.2 Create New API Key
```http
POST /api/v1/admin/keys
```

**Request Body:**
```json
{
  "name": "Panel Admin Key",
  "permissions": ["read", "write", "admin"]
}
```

**JavaScript Implementation:**
```javascript
async function createAPIKey(keyData) {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/keys`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(keyData)
        });
        return await response.json();
    } catch (error) {
        console.error('Error creating API key:', error);
        return null;
    }
}
```

---

## 🎨 PANEL WEB IMPLEMENTATION EXAMPLES

### HTML Form Examples

#### SSH Account Creation Form
```html
<form id="sshForm">
    <div class="form-group">
        <label>Username:</label>
        <input type="text" id="sshUsername" required>
    </div>
    <div class="form-group">
        <label>Password:</label>
        <input type="password" id="sshPassword" required>
    </div>
    <div class="form-group">
        <label>IP Limit:</label>
        <input type="number" id="sshIPLimit" value="2" min="1">
    </div>
    <div class="form-group">
        <label>Expired Days:</label>
        <input type="number" id="sshExpiredDays" value="30" min="1">
    </div>
    <div class="form-group">
        <label>Bug Host:</label>
        <input type="text" id="sshBugHost" value="bug.com">
    </div>
    <button type="submit">Create SSH Account</button>
</form>

<script>
document.getElementById('sshForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const accountData = {
        username: document.getElementById('sshUsername').value,
        password: document.getElementById('sshPassword').value,
        limit_ip: parseInt(document.getElementById('sshIPLimit').value),
        expired_days: parseInt(document.getElementById('sshExpiredDays').value),
        bug_host: document.getElementById('sshBugHost').value
    };
    
    const result = await createSSHAccount(accountData);
    if (result) {
        alert('SSH Account created successfully!');
        // Refresh account list or show success message
    } else {
        alert('Failed to create SSH account');
    }
});
</script>
```

#### Dashboard Statistics Display
```html
<div id="dashboard">
    <div class="stats-container">
        <div class="stat-card">
            <h3>Total SSH</h3>
            <span id="sshCount">0</span>
        </div>
        <div class="stat-card">
            <h3>Total Trojan</h3>
            <span id="trojanCount">0</span>
        </div>
        <div class="stat-card">
            <h3>Total VLess</h3>
            <span id="vlessCount">0</span>
        </div>
        <div class="stat-card">
            <h3>Total VMess</h3>
            <span id="vmessCount">0</span>
        </div>
        <div class="stat-card">
            <h3>Expiring Soon</h3>
            <span id="expiringSoon">0</span>
        </div>
    </div>
</div>

<script>
async function loadDashboard() {
    const stats = await getAccountStats();
    if (stats) {
        document.getElementById('sshCount').textContent = stats.service_stats.ssh || 0;
        document.getElementById('trojanCount').textContent = stats.service_stats.trojan || 0;
        document.getElementById('vlessCount').textContent = stats.service_stats.vless || 0;
        document.getElementById('vmessCount').textContent = stats.service_stats.vmess || 0;
        document.getElementById('expiringSoon').textContent = stats.expiring_soon || 0;
    }
}

// Load dashboard on page load
loadDashboard();
</script>
```

#### Account List Table
```html
<div id="accountsList">
    <table id="accountsTable">
        <thead>
            <tr>
                <th>Username</th>
                <th>Service Type</th>
                <th>Created Date</th>
                <th>Expire Date</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody id="accountsTableBody">
        </tbody>
    </table>
</div>

<script>
async function loadAccountsList() {
    const accounts = await listAllAccounts();
    const tbody = document.getElementById('accountsTableBody');
    tbody.innerHTML = '';
    
    accounts.forEach(account => {
        const row = tbody.insertRow();
        row.innerHTML = `
            <td>${account.username}</td>
            <td><span class="service-badge ${account.service_type}">${account.service_type.toUpperCase()}</span></td>
            <td>${new Date(account.created_date).toLocaleDateString()}</td>
            <td>${new Date(account.expire_date).toLocaleDateString()}</td>
            <td><span class="status-badge ${account.is_active ? 'active' : 'inactive'}">${account.is_active ? 'Active' : 'Inactive'}</span></td>
            <td>
                <button onclick="deleteAccount('${account.username}', '${account.service_type}')" class="btn-delete">Delete</button>
                <button onclick="viewConfig('${account.username}', '${account.service_type}')" class="btn-view">View Config</button>
            </td>
        `;
    });
}

async function deleteAccount(username, serviceType) {
    if (confirm(`Are you sure you want to delete ${username}?`)) {
        let result = false;
        
        switch (serviceType) {
            case 'ssh':
                result = await deleteSSHAccount(username);
                break;
            case 'trojan':
                result = await deleteTrojanAccount(username);
                break;
            // Add other service types as needed
        }
        
        if (result) {
            alert('Account deleted successfully!');
            loadAccountsList(); // Refresh the list
        } else {
            alert('Failed to delete account');
        }
    }
}

// Load accounts list on page load
loadAccountsList();
</script>
```

---

## 🔒 ERROR HANDLING

### Global Error Handler
```javascript
// Global error handler untuk semua API calls
function handleAPIError(error, operation) {
    console.error(`Error in ${operation}:`, error);
    
    // Show user-friendly error messages
    let message = 'An error occurred. Please try again.';
    
    if (error.message.includes('401')) {
        message = 'Authentication failed. Please check your API key.';
    } else if (error.message.includes('403')) {
        message = 'You don\'t have permission to perform this action.';
    } else if (error.message.includes('404')) {
        message = 'Resource not found.';
    } else if (error.message.includes('400')) {
        message = 'Invalid request. Please check your input.';
    }
    
    // Show error to user (you can customize this)
    showNotification(message, 'error');
}

function showNotification(message, type = 'info') {
    // Implement your notification system here
    // This could be a toast, modal, or any UI component
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 5000);
}
```

---

## 📱 RESPONSIVE DESIGN CONSIDERATIONS

### CSS Classes for Panel
```css
.service-badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
}

.service-badge.ssh { background-color: #007bff; color: white; }
.service-badge.trojan { background-color: #28a745; color: white; }
.service-badge.vless { background-color: #ffc107; color: black; }
.service-badge.vmess { background-color: #dc3545; color: white; }

.status-badge {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
}

.status-badge.active { background-color: #28a745; color: white; }
.status-badge.inactive { background-color: #6c757d; color: white; }

.stats-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}

.stat-card {
    background: #fff;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
}
```

---

## 🚀 DEPLOYMENT CHECKLIST

1. **API Configuration**
   - [ ] Update `API_BASE_URL` dengan domain/IP server Anda
   - [ ] Ganti `YOUR_API_KEY_HERE` dengan API key yang valid
   - [ ] Test koneksi ke API endpoint

2. **Security**
   - [ ] Implementasi HTTPS untuk production
   - [ ] Validasi input di frontend
   - [ ] Implementasi rate limiting di UI

3. **Error Handling**
   - [ ] Implementasi global error handler
   - [ ] User-friendly error messages
   - [ ] Loading states untuk semua operations

4. **Performance**
   - [ ] Implementasi caching untuk data yang jarang berubah
   - [ ] Pagination untuk list yang panjang
   - [ ] Lazy loading untuk komponen besar

5. **User Experience**
   - [ ] Loading indicators
   - [ ] Success/error notifications
   - [ ] Confirm dialogs untuk operasi destructive
   - [ ] Auto-refresh untuk data real-time

---

## 📞 SUPPORT

Jika ada pertanyaan atau masalah dalam implementasi, silakan:

1. Cek log API di server: `journalctl -u vpn-api -f`
2. Test endpoint dengan curl sebelum implementasi di panel
3. Pastikan API key memiliki permission yang sesuai
4. Verify bahwa service VPN API berjalan di port 7777

**File ini dibuat untuk memudahkan implementasi panel web VPN Management API. Semua endpoint telah ditest dan siap untuk digunakan.**
