#!/usr/bin/env python3
"""
Trial Service Module untuk AlrelShop API Panel
Mengintegrasikan fungsi-fungsi dari script m-trial
"""

import subprocess
import json
import os
import re
import uuid
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TrialService:
    def __init__(self):
        self.domain = self._get_domain()
        self.trial_db_path = "/etc/trial/.trial.db"
        self.web_path = "/var/www/html"
        
    def _get_domain(self):
        """Get domain dari config"""
        try:
            with open("/etc/xray/domain", "r") as f:
                return f.read().strip()
        except:
            return "localhost"
    
    def _get_server_info(self):
        """Get server information"""
        try:
            with open("/etc/xray/isp", "r") as f:
                isp = f.read().strip()
        except:
            isp = "Unknown"
            
        try:
            with open("/etc/xray/city", "r") as f:
                city = f.read().strip()
        except:
            city = "Unknown"
            
        try:
            with open("/root/nsdomain", "r") as f:
                ns = f.read().strip()
        except:
            ns = "Unknown"
            
        try:
            with open("/etc/slowdns/server.pub", "r") as f:
                pub = f.read().strip()
        except:
            pub = "Unknown"
            
        return {
            "isp": isp,
            "city": city,
            "ns": ns,
            "pub": pub
        }
    
    def create_trial(self, data):
        """Create trial account untuk semua service"""
        try:
            service = data.get('service', 'all')  # ssh, vmess, vless, shadowsocks, trojan, all
            minutes = data.get('minutes', 60)
            
            if service not in ['ssh', 'vmess', 'vless', 'shadowsocks', 'trojan', 'all']:
                return {"status": "error", "message": "Service tidak valid"}
            
            results = {}
            
            if service == 'all' or service == 'ssh':
                # Create trial SSH
                ssh_result = self._create_trial_ssh(minutes)
                results['ssh'] = ssh_result
            
            if service == 'all' or service == 'vmess':
                # Create trial VMess
                vmess_result = self._create_trial_vmess(minutes)
                results['vmess'] = vmess_result
            
            if service == 'all' or service == 'vless':
                # Create trial VLess
                vless_result = self._create_trial_vless(minutes)
                results['vless'] = vless_result
            
            if service == 'all' or service == 'shadowsocks':
                # Create trial Shadowsocks
                ss_result = self._create_trial_shadowsocks(minutes)
                results['shadowsocks'] = ss_result
            
            if service == 'all' or service == 'trojan':
                # Create trial Trojan
                trojan_result = self._create_trial_trojan(minutes)
                results['trojan'] = trojan_result
            
            # Add to trial database
            self._add_to_trial_db(service, minutes, results)
            
            return {
                "status": "success",
                "message": f"Trial account untuk {service} berhasil dibuat",
                "data": results
            }
            
        except Exception as e:
            logger.error(f"Error creating trial account: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_trial(self, data):
        """Delete trial account"""
        try:
            username = data.get('username')
            service = data.get('service')
            
            if not username:
                return {"status": "error", "message": "Username harus diisi"}
            
            if not service:
                return {"status": "error", "message": "Service harus diisi"}
            
            # Delete from trial database
            self._remove_from_trial_db(username, service)
            
            # Delete from respective service
            if service == 'ssh':
                subprocess.run(['userdel', '--force', username], check=True)
            elif service in ['vmess', 'vless', 'shadowsocks', 'trojan']:
                # Remove from Xray config
                self._remove_from_xray_config(username, service)
            
            # Remove config files
            config_file = f"{self.web_path}/{service}-{username}.txt"
            if os.path.exists(config_file):
                os.remove(config_file)
            
            return {
                "status": "success",
                "message": f"Trial account {username} untuk {service} berhasil dihapus"
            }
            
        except Exception as e:
            logger.error(f"Error deleting trial account: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_trials(self):
        """List semua trial accounts"""
        try:
            trials = []
            
            if os.path.exists(self.trial_db_path):
                with open(self.trial_db_path, "r") as f:
                    for line in f:
                        if line.startswith("### "):
                            parts = line.strip().split()
                            if len(parts) >= 4:
                                service = parts[1]
                                username = parts[2]
                                minutes = parts[3]
                                created_time = parts[4] if len(parts) > 4 else "Unknown"
                                
                                trials.append({
                                    "service": service,
                                    "username": username,
                                    "minutes": minutes,
                                    "created_time": created_time,
                                    "status": self._get_trial_status(created_time, minutes)
                                })
            
            return {
                "status": "success",
                "data": trials,
                "total": len(trials)
            }
            
        except Exception as e:
            logger.error(f"Error listing trial accounts: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_info(self):
        """Get trial service info"""
        try:
            total_trials = len(self.list_trials().get('data', []))
            active_trials = len([trial for trial in self.list_trials().get('data', []) if trial.get('status') == 'active'])
            
            return {
                "status": "running",
                "total_trials": total_trials,
                "active_trials": active_trials,
                "domain": self.domain
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _create_trial_ssh(self, minutes):
        """Create trial SSH account"""
        try:
            username = f"WV-{uuid.uuid4().hex[:4].upper()}"
            password = "1"
            ip_limit = 4
            quota_gb = 5
            
            # Create system user
            expiry_date = datetime.now() + timedelta(minutes=minutes)
            expiry_str = expiry_date.strftime("%Y-%m-%d")
            
            subprocess.run(['useradd', '-e', expiry_str, '-s', '/bin/false', '-M', username], check=True)
            subprocess.run(['echo', f'{password}\n{password}', '|', 'passwd', username], shell=True, check=True)
            
            # Setup IP limit
            limit_path = "/etc/kyt/limit/ssh/ip"
            os.makedirs(limit_path, exist_ok=True)
            with open(f"{limit_path}/{username}", "w") as f:
                f.write(str(ip_limit))
            
            # Setup quota
            quota_bytes = quota_gb * 1024 * 1024 * 1024
            os.makedirs("/etc/ssh", exist_ok=True)
            with open(f"/etc/ssh/{username}", "w") as f:
                f.write(str(quota_bytes))
            
            # Create config file
            self._create_ssh_config(username, password, ip_limit, minutes)
            
            # Schedule deletion
            subprocess.run(['echo', f'userdel -f "{username}"', '|', 'at', 'now', '+', str(minutes), 'minutes'], shell=True)
            
            return {
                "username": username,
                "password": password,
                "ip_limit": ip_limit,
                "quota_gb": quota_gb,
                "config_url": f"https://{self.domain}:81/ssh-{username}.txt"
            }
            
        except Exception as e:
            logger.error(f"Error creating trial SSH: {e}")
            return {"status": "error", "message": str(e)}
    
    def _create_trial_vmess(self, minutes):
        """Create trial VMess account"""
        try:
            username = f"WV-{uuid.uuid4().hex[:3].upper()}"
            user_uuid = str(uuid.uuid4())
            quota_gb = 1
            ip_limit = 3
            bug = "bug.com"
            
            # Add to Xray config
            self._add_to_xray_config(username, user_uuid, 'vmess')
            
            # Setup IP limit
            limit_path = "/etc/kyt/limit/vmess/ip"
            os.makedirs(limit_path, exist_ok=True)
            with open(f"{limit_path}/{username}", "w") as f:
                f.write(str(ip_limit))
            
            # Setup quota
            quota_bytes = quota_gb * 1024 * 1024 * 1024
            os.makedirs("/etc/vmess", exist_ok=True)
            with open(f"/etc/vmess/{username}", "w") as f:
                f.write(str(quota_bytes))
            
            # Create config file
            self._create_vmess_config(username, user_uuid, quota_gb, ip_limit, minutes, bug)
            
            return {
                "username": username,
                "uuid": user_uuid,
                "quota_gb": quota_gb,
                "ip_limit": ip_limit,
                "config_url": f"https://{self.domain}:81/vmess-{username}.txt"
            }
            
        except Exception as e:
            logger.error(f"Error creating trial VMess: {e}")
            return {"status": "error", "message": str(e)}
    
    def _create_trial_vless(self, minutes):
        """Create trial VLess account"""
        try:
            username = f"WV-{uuid.uuid4().hex[:3].upper()}"
            user_uuid = str(uuid.uuid4())
            quota_gb = 1
            ip_limit = 2
            
            # Add to Xray config
            self._add_to_xray_config(username, user_uuid, 'vless')
            
            # Setup IP limit
            limit_path = "/etc/kyt/limit/vless/ip"
            os.makedirs(limit_path, exist_ok=True)
            with open(f"{limit_path}/{username}", "w") as f:
                f.write(str(ip_limit))
            
            # Setup quota
            quota_bytes = quota_gb * 1024 * 1024 * 1024
            os.makedirs("/etc/vless", exist_ok=True)
            with open(f"/etc/vless/{username}", "w") as f:
                f.write(str(quota_bytes))
            
            # Create config file
            self._create_vless_config(username, user_uuid, quota_gb, ip_limit, minutes)
            
            return {
                "username": username,
                "uuid": user_uuid,
                "quota_gb": quota_gb,
                "ip_limit": ip_limit,
                "config_url": f"https://{self.domain}:81/vless-{username}.txt"
            }
            
        except Exception as e:
            logger.error(f"Error creating trial VLess: {e}")
            return {"status": "error", "message": str(e)}
    
    def _create_trial_shadowsocks(self, minutes):
        """Create trial Shadowsocks account"""
        try:
            username = f"WV-{uuid.uuid4().hex[:3].upper()}"
            password = str(uuid.uuid4())
            cipher = "aes-128-gcm"
            quota_gb = 5
            
            # Add to Xray config
            self._add_to_xray_config(username, password, 'shadowsocks')
            
            # Setup quota
            quota_bytes = quota_gb * 1024 * 1024 * 1024
            os.makedirs("/etc/shadowsocks", exist_ok=True)
            with open(f"/etc/shadowsocks/{username}", "w") as f:
                f.write(str(quota_bytes))
            
            # Create config file
            self._create_shadowsocks_config(username, password, cipher, quota_gb, minutes)
            
            return {
                "username": username,
                "password": password,
                "cipher": cipher,
                "quota_gb": quota_gb,
                "config_url": f"https://{self.domain}:81/sodosokws-{username}.txt"
            }
            
        except Exception as e:
            logger.error(f"Error creating trial Shadowsocks: {e}")
            return {"status": "error", "message": str(e)}
    
    def _create_trial_trojan(self, minutes):
        """Create trial Trojan account"""
        try:
            username = f"WV-{uuid.uuid4().hex[:3].upper()}"
            password = str(uuid.uuid4())
            quota_gb = 1
            ip_limit = 3
            
            # Add to Xray config
            self._add_to_xray_config(username, password, 'trojan')
            
            # Setup IP limit
            limit_path = "/etc/kyt/limit/trojan/ip"
            os.makedirs(limit_path, exist_ok=True)
            with open(f"{limit_path}/{username}", "w") as f:
                f.write(str(ip_limit))
            
            # Setup quota
            quota_bytes = quota_gb * 1024 * 1024 * 1024
            os.makedirs("/etc/trojan", exist_ok=True)
            with open(f"/etc/trojan/{username}", "w") as f:
                f.write(str(quota_bytes))
            
            # Create config file
            self._create_trojan_config(username, password, quota_gb, ip_limit, minutes)
            
            return {
                "username": username,
                "password": password,
                "quota_gb": quota_gb,
                "ip_limit": ip_limit,
                "config_url": f"https://{self.domain}:81/trojan-{username}.txt"
            }
            
        except Exception as e:
            logger.error(f"Error creating trial Trojan: {e}")
            return {"status": "error", "message": str(e)}
    
    def _add_to_xray_config(self, username, credential, protocol):
        """Add user to Xray config"""
        try:
            config_path = "/etc/xray/config.json"
            
            # Read current config
            with open(config_path, "r") as f:
                config = json.load(f)
            
            # Add user based on protocol
            if protocol == 'vmess':
                user = {
                    "id": credential,
                    "alterId": 0,
                    "email": username
                }
            elif protocol == 'vless':
                user = {
                    "id": credential,
                    "email": username
                }
            elif protocol == 'shadowsocks':
                user = {
                    "password": credential,
                    "method": "aes-128-gcm",
                    "email": username
                }
            elif protocol == 'trojan':
                user = {
                    "password": credential,
                    "email": username
                }
            
            # Find protocol section and add user
            for inbound in config.get("inbounds", []):
                if inbound.get("protocol") == protocol:
                    if "settings" not in inbound:
                        inbound["settings"] = {}
                    if "clients" not in inbound["settings"]:
                        inbound["settings"]["clients"] = []
                    inbound["settings"]["clients"].append(user)
                    break
            
            # Write updated config
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error adding to Xray config: {e}")
            raise
    
    def _remove_from_xray_config(self, username, protocol):
        """Remove user from Xray config"""
        try:
            config_path = "/etc/xray/config.json"
            
            # Read current config
            with open(config_path, "r") as f:
                config = json.load(f)
            
            # Remove from protocol section
            for inbound in config.get("inbounds", []):
                if inbound.get("protocol") == protocol:
                    if "settings" in inbound and "clients" in inbound["settings"]:
                        inbound["settings"]["clients"] = [
                            client for client in inbound["settings"]["clients"]
                            if client.get("email") != username
                        ]
                    break
            
            # Write updated config
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error removing from Xray config: {e}")
            raise
    
    def _add_to_trial_db(self, service, minutes, results):
        """Add trial to database"""
        os.makedirs("/etc/trial", exist_ok=True)
        
        created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.trial_db_path, "a") as f:
            f.write(f"### {service} {results.get('username', 'unknown')} {minutes} {created_time}\n")
    
    def _remove_from_trial_db(self, username, service):
        """Remove trial from database"""
        if os.path.exists(self.trial_db_path):
            lines = []
            with open(self.trial_db_path, "r") as f:
                for line in f:
                    if not line.startswith(f"### {service} {username} "):
                        lines.append(line)
            
            with open(self.trial_db_path, "w") as f:
                f.writelines(lines)
    
    def _get_trial_status(self, created_time, minutes):
        """Get trial status (active/expired)"""
        try:
            created = datetime.strptime(created_time, "%Y-%m-%d %H:%M:%S")
            expiry = created + timedelta(minutes=int(minutes))
            
            if datetime.now() < expiry:
                return 'active'
            else:
                return 'expired'
        except:
            return 'unknown'
    
    def _create_ssh_config(self, username, password, ip_limit, minutes):
        """Create SSH config file"""
        server_info = self._get_server_info()
        
        config_content = f"""◇━━━━━━━━━━━━━━━━━◇
Format SSH OVPN Account
◇━━━━━━━━━━━━━━━━━◇
Username         : {username}
Password         : {password}
◇━━━━━━━━━━━━━━━━━◇
IP Limit         : {ip_limit}
Host             : {self.domain}
Port OpenSSH     : 443, 80, 22
Port Dropbear    : 443, 109
Port SSH UDP     : 1-65535
Port SSH WS      : 80, 8080, 8081-9999
Port SSH SSL WS  : 443
Port SSL/TLS     : 400-900
Port OVPN WS SSL : 443
Port OVPN SSL    : 443
Port OVPN TCP    : 1194
Port OVPN UDP    : 2200
BadVPN UDP       : 7100, 7300, 7300
Location         : {server_info['city']}
ISP              : {server_info['isp']}
Host Slowdns     : {server_info['ns']}
Pub Key          : {server_info['pub']}
◇━━━━━━━━━━━━━━━━━◇
Aktif Selama     : {minutes} Menit
Dibuat Pada      : {datetime.now().strftime('%d %b %Y')}
Berakhir Pada    : {datetime.now().strftime('%d %b %Y')}
===============================
Payload WSS: GET wss://bug.com/ HTTP/1.1[crlf]Host: {self.domain}[crlf]Upgrade: websocket[crlf][crlf] 
===============================
OVPN Download : https://{self.domain}:81/
=============================="""
        
        os.makedirs(self.web_path, exist_ok=True)
        with open(f"{self.web_path}/ssh-{username}.txt", "w") as f:
            f.write(config_content)
    
    def _create_vmess_config(self, username, user_uuid, quota_gb, ip_limit, minutes, bug):
        """Create VMess config file"""
        # Simplified config for trial
        config_content = f"""◇━━━━━━━━━━━━━━━━━◇
   Vmess Account (TRIAL)
◇━━━━━━━━━━━━━━━━━◇
Remarks          : {username}
Domain           : {self.domain}
User Quota       : {quota_gb} GB
User Ip          : {ip_limit} IP
User ID          : {user_uuid}
Aktif Selama     : {minutes} Menit
Dibuat Pada      : {datetime.now().strftime('%d %b %Y')}
◇━━━━━━━━━━━━━━━━━◇"""
        
        os.makedirs(self.web_path, exist_ok=True)
        with open(f"{self.web_path}/vmess-{username}.txt", "w") as f:
            f.write(config_content)
    
    def _create_vless_config(self, username, user_uuid, quota_gb, ip_limit, minutes):
        """Create VLess config file"""
        # Simplified config for trial
        config_content = f"""◇━━━━━━━━━━━━━━━━━◇
   Vless Account (TRIAL)
◇━━━━━━━━━━━━━━━━━◇
Remarks          : {username}
Domain           : {self.domain}
User Quota       : {quota_gb} GB
User Ip          : {ip_limit} IP
User ID          : {user_uuid}
Aktif Selama     : {minutes} Menit
Dibuat Pada      : {datetime.now().strftime('%d %b %Y')}
◇━━━━━━━━━━━━━━━━━◇"""
        
        os.makedirs(self.web_path, exist_ok=True)
        with open(f"{self.web_path}/vless-{username}.txt", "w") as f:
            f.write(config_content)
    
    def _create_shadowsocks_config(self, username, password, cipher, quota_gb, minutes):
        """Create Shadowsocks config file"""
        # Simplified config for trial
        config_content = f"""◇━━━━━━━━━━━━━━━━━◇
Shadowsocks Account (TRIAL)
◇━━━━━━━━━━━━━━━━━◇
Remarks          : {username}
Domain           : {self.domain}
User Quota       : {quota_gb} GB
Password         : {password}
Cipers           : {cipher}
Aktif Selama     : {minutes} Menit
Dibuat Pada      : {datetime.now().strftime('%d %b %Y')}
◇━━━━━━━━━━━━━━━━━◇"""
        
        os.makedirs(self.web_path, exist_ok=True)
        with open(f"{self.web_path}/sodosokws-{username}.txt", "w") as f:
            f.write(config_content)
    
    def _create_trojan_config(self, username, password, quota_gb, ip_limit, minutes):
        """Create Trojan config file"""
        # Simplified config for trial
        config_content = f"""◇━━━━━━━━━━━━━━━━━◇
   Trojan Account (TRIAL)
◇━━━━━━━━━━━━━━━━━◇
Remarks          : {username}
Domain           : {self.domain}
User Quota       : {quota_gb} GB
User Ip          : {ip_limit} IP
Password         : {password}
Aktif Selama     : {minutes} Menit
Dibuat Pada      : {datetime.now().strftime('%d %b %Y')}
◇━━━━━━━━━━━━━━━━━◇"""
        
        os.makedirs(self.web_path, exist_ok=True)
        with open(f"{self.web_path}/trojan-{username}.txt", "w") as f:
            f.write(config_content)
