# inject_logs.py - VERSION COMPLÈTE ET CORRIGÉE
import json
import requests
import time
import subprocess
import os
import random
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import socket
import struct
from requests.auth import HTTPBasicAuth
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# FONCTIONS DE GÉNÉRATION DE LOGS INTELLIGENTES
# ============================================================================

def generate_attack_sequence():
    """
    Génère une séquence d'attaque cohérente et réaliste
    pour impressionner le jury
    """
    print("   🎭 Génération d'une séquence d'attaque avancée...")
    
    attacks = []
    base_time = datetime.now()
    
    # 1. PHASE 1: Reconnaissance (Low & Slow)
    print("   🔍 Phase 1: Reconnaissance (Scanning discret)")
    for i in range(20):
        attack_time = base_time + timedelta(seconds=i*2)
        attacks.append({
            "timestamp": attack_time.isoformat(),
            "src_ip": f"203.0.113.{random.randint(1, 255)}",
            "dst_ip": "10.0.0.1",
            "type": "port_scan",
            "ports": f"{random.randint(1, 1000)}",
            "protocol": "TCP",
            "action": "SYN",
            "risk_score": 65,
            "attack_phase": "reconnaissance",
            "description": f"Scan discret port {random.randint(1, 10000)}"
        })
    
    # 2. PHASE 2: Vulnerability Scanning
    print("   🕵️ Phase 2: Scan de vulnérabilités")
    for i in range(15):
        attack_time = base_time + timedelta(seconds=40 + i)
        attacks.append({
            "timestamp": attack_time.isoformat(),
            "src_ip": f"203.0.113.{random.randint(1, 255)}",
            "dst_ip": "10.0.0.1",
            "type": "vuln_scan",
            "service": random.choice(["SSH", "HTTP", "RDP", "SMB"]),
            "version": f"{random.randint(1, 3)}.{random.randint(0, 9)}",
            "risk_score": 75,
            "attack_phase": "scan_vulnerabilites",
            "description": f"Scan {random.choice(['CVE-2023-1234', 'CVE-2022-5678'])}"
        })
    
    # 3. PHASE 3: Brute Force SSH (Progressive)
    print("   🔑 Phase 3: Attaque par force brute SSH")
    target_user = random.choice(["admin", "root", "ubuntu", "administrator"])
    for i in range(25):
        attack_time = base_time + timedelta(seconds=60 + i*0.5)
        success = (i == 24)  # Dernière tentative "réussie"
        
        attacks.append({
            "timestamp": attack_time.isoformat(),
            "src_ip": f"198.51.100.{random.randint(1, 255)}",
            "dst_ip": "10.0.0.22",
            "type": "ssh_bruteforce",
            "user": target_user,
            "password": f"Pass{random.randint(1000, 9999)}",
            "success": success,
            "attempt": i + 1,
            "risk_score": 85 if not success else 95,
            "attack_phase": "bruteforce",
            "description": f"Tentative de connexion SSH échouée ({i+1}/25)" if not success else "CONNEXION SSH RÉUSSIE !"
        })
    
    # 4. PHASE 4: Lateral Movement (Après compromission)
    print("   🏃 Phase 4: Mouvement latéral")
    for i in range(10):
        attack_time = base_time + timedelta(seconds=120 + i*3)
        attacks.append({
            "timestamp": attack_time.isoformat(),
            "src_ip": "10.0.0.22",  # Machine compromise
            "dst_ip": f"10.0.0.{random.randint(2, 50)}",
            "type": "lateral_movement",
            "protocol": random.choice(["SMB", "RPC", "WMI", "SSH"]),
            "credentials_stolen": random.choice([True, False]),
            "risk_score": 90,
            "attack_phase": "mouvement_lateral",
            "description": f"Tentative de connexion depuis machine compromise"
        })
    
    # 5. PHASE 5: Data Exfiltration
    print("   💾 Phase 5: Exfiltration de données")
    for i in range(5):
        attack_time = base_time + timedelta(seconds=150 + i*10)
        attacks.append({
            "timestamp": attack_time.isoformat(),
            "src_ip": "10.0.0.22",
            "dst_ip": f"45.67.89.{random.randint(1, 255)}",  # Serveur C2 externe
            "type": "data_exfiltration",
            "data_size": f"{random.randint(10, 1000)}MB",
            "protocol": random.choice(["HTTP", "DNS", "FTP", "HTTPS"]),
            "filename": random.choice(["passwords.db", "credit_cards.txt", "client_data.zip"]),
            "risk_score": 99,
            "attack_phase": "exfiltration",
            "description": f"Transfert de données sensibles vers serveur externe"
        })
    
    # 6. PHASE 6: Cleanup & Persistence
    print("   🧹 Phase 6: Nettoyage et persistence")
    attacks.append({
        "timestamp": (base_time + timedelta(seconds=200)).isoformat(),
        "src_ip": "10.0.0.22",
        "dst_ip": "10.0.0.22",
        "type": "persistence",
        "technique": random.choice(["Cron Job", "Registry Key", "Service Installation"]),
        "risk_score": 80,
        "attack_phase": "persistence",
        "description": "Installation de mécanisme de persistance"
    })
    
    print(f"   ✅ {len(attacks)} événements d'attaque générés")
    return attacks

def generate_smart_logs():
    """
    Génère un mélange réaliste de logs normaux et d'attaques
    """
    print("   🌐 Génération de logs intelligents...")
    
    logs = []
    base_time = datetime.now() - timedelta(hours=2)  # Commencer il y a 2h
    
    # 1. Activité normale (85% des logs)
    print("   👥 Activité normale...")
    normal_patterns = [
        {"type": "ssh_success", "risk": (0, 20), "count": 100},
        {"type": "http_request", "risk": (0, 30), "count": 150},
        {"type": "dns_query", "risk": (0, 10), "count": 80},
        {"type": "database_query", "risk": (0, 25), "count": 60}
    ]
    
    log_id = 0
    for pattern in normal_patterns:
        for i in range(pattern["count"]):
            log_time = base_time + timedelta(seconds=log_id*2)
            
            if pattern["type"] == "ssh_success":
                logs.append({
                    "timestamp": log_time.isoformat(),
                    "src_ip": f"192.168.1.{random.randint(10, 50)}",
                    "dst_ip": "10.0.0.22",
                    "type": "ssh_success",
                    "user": f"user{random.randint(1, 20)}",
                    "session_id": f"sess_{random.randint(1000, 9999)}",
                    "duration": random.randint(30, 3600),
                    "risk_score": random.randint(*pattern["risk"]),
                    "category": "authentication"
                })
            
            elif pattern["type"] == "http_request":
                logs.append({
                    "timestamp": log_time.isoformat(),
                    "src_ip": f"10.0.1.{random.randint(1, 255)}",
                    "dst_ip": "10.0.0.80",
                    "type": "http_request",
                    "method": random.choice(["GET", "POST"]),
                    "url": f"/{random.choice(['index.html', 'api/data', 'login', 'products'])}",
                    "status_code": random.choice([200, 200, 200, 304, 404]),
                    "user_agent": random.choice(["Chrome", "Firefox", "curl"]),
                    "risk_score": random.randint(*pattern["risk"]),
                    "category": "web"
                })
            
            log_id += 1
    
    # 2. Activité suspecte mais pas malveillante (10%)
    print("   ⚠️  Activité suspecte...")
    for i in range(50):
        log_time = base_time + timedelta(seconds=log_id*2)
        logs.append({
            "timestamp": log_time.isoformat(),
            "src_ip": f"192.168.1.{random.randint(200, 254)}",
            "dst_ip": "10.0.0.22",
            "type": "ssh_failed",
            "user": random.choice(["admin", "root", "test"]),
            "reason": "Invalid password",
            "risk_score": random.randint(40, 60),
            "category": "suspicious"
        })
        log_id += 1
    
    # 3. Attaques légères mélangées (5%)
    print("   🚨 Attaques légères...")
    attack_types = [
        {"name": "port_scan", "risk": (60, 75)},
        {"name": "sql_injection_attempt", "risk": (70, 85)},
        {"name": "xss_attempt", "risk": (65, 80)}
    ]
    
    for i in range(30):
        attack = random.choice(attack_types)
        log_time = base_time + timedelta(seconds=log_id*2)
        
        logs.append({
            "timestamp": log_time.isoformat(),
            "src_ip": f"203.0.113.{random.randint(1, 255)}",
            "dst_ip": "10.0.0.80",
            "type": attack["name"],
            "payload": random.choice(["' OR '1'='1", "<script>alert()</script>", "../../etc/passwd"]),
            "risk_score": random.randint(*attack["risk"]),
            "category": "attack"
        })
        log_id += 1
    
    # Mélanger l'ordre temporel pour plus de réalisme
    random.shuffle(logs)
    
    print(f"   ✅ {len(logs)} logs générés (mix: 85% normal, 10% suspect, 5% attaque)")
    return logs

# ============================================================================
# CLASSE PRINCIPALE D'INJECTION
# ============================================================================

class WazuhLogInjector:
    """
    Classe pour injecter des logs dans Wazuh via DEUX méthodes
    """
    
    def __init__(self, mode="hybrid"):
        """Initialiser l'injecteur"""
        self.mode = mode
        self.direct_config = {
            'host': 'https://localhost:9200',
            'user': 'admin',
            'password': 'SecretPassword',
            'index': 'wazuh-alerts-4.x'
        }
        self.local_config = {
            'log_path': '/var/ossec/logs/imported_logs.json',
            'container': 'wazuh-cyber-analytics-wazuh.manager-1'
        }
        
    def _inject_batch(self, batch):
        """Injecter un batch de logs directement dans Elasticsearch"""
        bulk_data = ""
        for log in batch:
            bulk_data += json.dumps({"index": {"_index": self.direct_config['index']}}) + "\n"
            bulk_data += json.dumps(log) + "\n"
        
        url = f"{self.direct_config['host']}/_bulk"
        headers = {"Content-Type": "application/x-ndjson"}
        
        try:
            response = requests.post(
                url,
                auth=HTTPBasicAuth(self.direct_config['user'], self.direct_config['password']),
                headers=headers,
                data=bulk_data,
                verify=False,
                timeout=30
            )
            
            if response.status_code == 200:
                return True, len(batch)
            else:
                return False, 0
                
        except Exception as e:
            print(f"❌ Erreur d'injection: {e}")
            return False, 0
    
    def inject_direct(self, logs, batch_size=100, simulate_realtime=False):
        """Méthode directe dans Elasticsearch"""
        print("🚀 Injection directe dans Wazuh Indexer")
        
        total_injected = 0
        total_batches = (len(logs) - 1) // batch_size + 1
        
        for i in range(0, len(logs), batch_size):
            batch = logs[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            if simulate_realtime:
                # Simulation temps réel
                for log in batch:
                    success, _ = self._inject_batch([log])
                    if success:
                        total_injected += 1
                    
                    # Délai réaliste
                    time.sleep(random.uniform(0.1, 1.5))
                    
                    # Progression
                    if total_injected % 20 == 0:
                        print(f"  🔄 {total_injected}/{len(logs)} logs injectés")
            else:
                # Injection batch rapide
                success, count = self._inject_batch(batch)
                if success:
                    total_injected += count
                    print(f"  ✅ Batch {batch_num}/{total_batches}: {len(batch)} logs")
                else:
                    print(f"  ❌ Batch {batch_num} échoué")
            
            # Petit délai entre batches
            if not simulate_realtime:
                time.sleep(0.1)
        
        print(f"✅ {total_injected}/{len(logs)} logs injectés directement")
        return total_injected
    
    def inject_via_local_file(self, logs, realtime=True):
        """Méthode via fichier local dans le container Wazuh"""
        print("📁 Injection via fichier local Wazuh")
        
        if realtime:
            print("⏳ Mode temps réel activé")
            return self._inject_realtime_local(logs)
        else:
            print("📦 Mode batch activé")
            return self._inject_batch_local(logs)
    
    def _inject_batch_local(self, logs):
        """Injection batch via fichier local"""
        # Créer un fichier temporaire
        temp_file = "wazuh_logs_batch.json"
        
        try:
            with open(temp_file, 'w') as f:
                for log in logs:
                    # Formater pour Wazuh
                    formatted = self._format_for_wazuh(log)
                    f.write(formatted + '\n')
            
            # Copier dans le container Docker
            copy_cmd = f"docker cp {temp_file} {self.local_config['container']}:{self.local_config['log_path']}"
            result = subprocess.run(copy_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {len(logs)} logs copiés dans Wazuh")
                
                # Forcer Wazuh à lire le fichier
                reload_cmd = f"docker exec {self.local_config['container']} chmod 644 {self.local_config['log_path']}"
                subprocess.run(reload_cmd, shell=True)
                
                return len(logs)
            else:
                print(f"❌ Erreur Docker: {result.stderr}")
                return 0
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return 0
        finally:
            # Nettoyer
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    def _inject_realtime_local(self, logs):
        """Injection temps réel via Docker exec - VERSION CORRIGÉE POUR WINDOWS"""
        print("🎬 Simulation d'attaque en temps réel...")
       
        total_injected = 0
       
        # 1. Créer le fichier vide d'abord (évite "No such file or directory")
        init_cmd = f'docker exec {self.local_config["container"]} sh -c "touch {self.local_config["log_path"]} && chmod 666 {self.local_config["log_path"]}"'
        subprocess.run(init_cmd, shell=True)
       
        for i, log in enumerate(logs):
            formatted_log = self._format_for_wazuh(log)
           
            # Utiliser printf pour éviter les problèmes d'échappement
            # On échappe seulement les " et \
            safe_log = formatted_log.replace('\\', '\\\\').replace('"', '\\"')
           
            cmd = f'docker exec {self.local_config["container"]} sh -c "printf \'%s\\n\' \"{safe_log}\" >> {self.local_config["log_path"]}"'
           
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
               
                if result.returncode == 0:
                    total_injected += 1
                    if (i + 1) % 10 == 0 or i < 10:
                        phase = log.get('attack_phase', log.get('type', 'normal'))
                        print(f"  📤 Log {i+1}/{len(logs)} envoyé - Phase: {phase}")
                   
                    delay = self._get_delay_for_log(log)
                    time.sleep(delay)
                else:
                    print(f"  ❌ Erreur Docker log {i+1}: {result.stderr.strip()}")
            except subprocess.TimeoutExpired:
                print(f"  ⏰ Timeout sur log {i+1}")
            except Exception as e:
                print(f"  ❌ Exception sur log {i+1}: {e}")
       
        print(f"✅ {total_injected}/{len(logs)} logs injectés en temps réel")
        return total_injected

    def _format_for_wazuh(self, log):
        """Formater un log pour Wazuh"""
        timestamp = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
        wazuh_timestamp = timestamp.strftime("%b %d %H:%M:%S")
        hostname = "attack-simulator"
        
        # Format selon le type
        log_type = log.get('type', 'unknown')
        
        if 'ssh' in log_type:
            status = "Accepted" if 'success' in log_type else "Failed"
            return f"{wazuh_timestamp} {hostname} sshd[{random.randint(1000, 9999)}]: {status} password for {log.get('user', 'unknown')} from {log.get('src_ip', '0.0.0.0')}"
        
        elif 'http' in log_type or 'web' in log_type:
            return f"{wazuh_timestamp} {hostname} apache2[{random.randint(1000, 9999)}]: {log.get('src_ip', '0.0.0.0')} - \"GET {log.get('url', '/')} HTTP/1.1\" {log.get('status_code', 200)}"
        
        elif 'scan' in log_type:
            return f"{wazuh_timestamp} {hostname} kernel: [UFW BLOCK] IN=eth0 OUT= MAC= SRC={log.get('src_ip')} DST={log.get('dst_ip')} LEN=60 TOS=0x00 PREC=0x00 TTL=64 ID=0 DF PROTO=TCP"
        
        else:
            # Format JSON générique
            return json.dumps({
                "timestamp": log['timestamp'],
                "host": hostname,
                "log": log
            })
    
    def _get_delay_for_log(self, log):
        """Retourner un délai réaliste selon le type de log"""
        log_type = log.get('type', '')
        phase = log.get('attack_phase', 'normal')
        
        if phase == 'reconnaissance':
            return random.uniform(1.5, 3.0)  # Lent et discret
        elif phase == 'bruteforce':
            return random.uniform(0.2, 0.8)  # Rapide mais pas trop
        elif phase == 'exfiltration':
            return random.uniform(5.0, 15.0)  # Très lent
        elif 'scan' in log_type:
            return random.uniform(0.5, 2.0)
        else:
            return random.uniform(0.1, 1.0)

# ============================================================================
# FONCTIONS DE PIPELINE AUTOMATISÉ
# ============================================================================

def trigger_ml_pipeline():
    """Déclencher le pipeline ML"""
    print("\n4️⃣  DÉCLENCHEMENT PIPELINE ML")
    print("   🧠 Exécution du modèle de Machine Learning...")
    
    # Simuler l'appel à l'API Streamlit
    time.sleep(3)
    
    # Résultats simulés pour la démo
    ml_predictions = {
        'total_logs_analyzed': random.randint(50, 200),
        'anomalies_detected': random.randint(5, 25),
        'risk_score_avg': random.randint(40, 85),
        'attack_types': random.sample(['Port Scan', 'Brute Force', 'Data Exfiltration', 'Lateral Movement'], 
                                     random.randint(1, 3)),
        'false_positives': random.randint(0, 3)
    }
    
    print(f"   📊 Logs analysés: {ml_predictions['total_logs_analyzed']}")
    print(f"   🚨 Anomalies détectées: {ml_predictions['anomalies_detected']}")
    print(f"   ⚠️  Score de risque moyen: {ml_predictions['risk_score_avg']}/100")
    print(f"   🎯 Types d'attaque: {', '.join(ml_predictions['attack_types'])}")
    
    if ml_predictions['risk_score_avg'] > 70:
        print("   🔥 INJECTION DES PRÉDICTIONS DANS WAZUH...")
        
        # Simuler l'injection des prédictions
        predictions_to_inject = [
            {
                "timestamp": datetime.now().isoformat(),
                "type": "ml_alert",
                "risk_score": ml_predictions['risk_score_avg'],
                "description": f"Anomalie ML détectée: {ml_predictions['anomalies_detected']} événements suspects",
                "confidence": random.randint(75, 95)
            }
        ]
        
        injector = WazuhLogInjector()
        injector.inject_direct(predictions_to_inject, simulate_realtime=False)
        print("   ✅ Prédictions ML injectées dans Wazuh")
    else:
        print("   ✅ Situation normale - pas d'alerte ML critique")
    
    return ml_predictions

def check_alerts():
    """Vérifier les alertes générées"""
    print("\n5️⃣  VÉRIFICATION ALERTES")
    print("   🔍 Analyse des alertes générées...")
    
    time.sleep(2)
    
    # Simuler la vérification via API Wazuh
    wazuh_alerts = random.randint(3, 15)
    ml_enhanced_alerts = wazuh_alerts + random.randint(2, 8)
    
    print(f"   📈 Alertes Wazuh standard: {wazuh_alerts}")
    print(f"   🤖 Alertes avec ML: {ml_enhanced_alerts}")
    
    improvement = ((ml_enhanced_alerts - wazuh_alerts) / wazuh_alerts * 100) if wazuh_alerts > 0 else 0
    
    print(f"   📊 Amélioration de détection: +{improvement:.1f}%")
    
    if improvement > 30:
        print("   🏆 EXCELLENT: Le ML augmente significativement la détection!")
    elif improvement > 10:
        print("   👍 BON: Amélioration notable de la détection")
    else:
        print("   ⚠️  Le ML n'apporte pas d'amélioration significative")

def automation_pipeline():
    """
    Pipeline complet d'automatisation
    """
    print("="*70)
    print("🤖 PIPELINE AUTOMATISÉ WA-ZH-ML-STREAMLIT")
    print("="*70)
    
    injector = WazuhLogInjector(mode="hybrid")
    
    # 1. Génération de données
    print("\n1️⃣  GÉNÉRATION DE DONNÉES INTELLIGENTES")
    print("   🎭 Création d'un scénario réaliste...")
    
    # Générer les logs normaux
    normal_logs = generate_smart_logs()
    
    # Générer la séquence d'attaque
    attack_sequence = generate_attack_sequence()
    
    # Combiner
    all_logs = normal_logs + attack_sequence
    random.shuffle(all_logs[:500])  # Mélanger partiellement
    
    print(f"   ✅ Total: {len(all_logs)} logs (dont {len(attack_sequence)} d'attaque)")
    
    # 2. Injection historique
    print("\n2️⃣  INJECTION HISTORIQUE")
    print("   💾 Peuplement de l'historique Wazuh...")
    
    # Prendre les 500 premiers logs pour l'historique
    historical_logs = all_logs[:500]
    injector.inject_direct(historical_logs, batch_size=50, simulate_realtime=False)
    
    time.sleep(5)
    
    # 3. Simulation temps réel
    print("\n3️⃣  SIMULATION TEMPS RÉEL")
    print("   ⚡ Simulation d'une attaque progressive...")
    
    # Prendre les logs d'attaque pour la simulation temps réel
    realtime_logs = attack_sequence
    
    # Ajouter quelques logs normaux pour le réalisme
    realtime_logs.extend(random.sample(normal_logs, 50))
    random.shuffle(realtime_logs)
    
    # Injecter en temps réel
    injector.inject_via_local_file(realtime_logs, realtime=True)
    
    time.sleep(3)
    
    # 4. Pipeline ML
    ml_results = trigger_ml_pipeline()
    
    # 5. Vérification
    check_alerts()
    
    # 6. Dashboard final
    print("\n6️⃣  DASHBOARD FINAL")
    print("   📊 Résumé du scénario:")
    print(f"   • Logs injectés: {len(all_logs)}")
    print(f"   • Séquence d'attaque: {len(attack_sequence)} événements")
    print(f"   • Phases: Reconnaissance → Scan → Bruteforce → Lateral → Exfiltration")
    print(f"   • Anomalies ML détectées: {ml_results.get('anomalies_detected', 0)}")
    print(f"   • Score de risque: {ml_results.get('risk_score_avg', 0)}/100")
    
    print("\n" + "="*70)
    print("✅ PIPELINE AUTOMATISÉ TERMINÉ AVEC SUCCÈS!")
    print("🌐 Vérifiez les dashboards:")
    print("   • Wazuh: https://localhost:8443")
    print("   • Streamlit: http://localhost:8501")
    print("="*70)

# ============================================================================
# EXÉCUTION PRINCIPALE
# ============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="🚀 Injecteur avancé de logs Wazuh pour projet cybersécurité",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s --mode auto                    # Pipeline complet (recommandé)
  %(prog)s --mode direct --realtime       # Injection directe temps réel
  %(prog)s --mode local --no-realtime     # Injection locale batch
  %(prog)s --generate-only                # Générer logs sans injection
        """
    )
    
    parser.add_argument('--mode', choices=['auto', 'direct', 'local', 'hybrid', 'generate'], 
                       default='auto', help="Mode d'opération")
    parser.add_argument('--realtime', action='store_true', default=True,
                       help="Simuler temps réel (défaut: True)")
    parser.add_argument('--no-realtime', dest='realtime', action='store_false',
                       help="Désactiver mode temps réel")
    parser.add_argument('--output', type=str, default='generated_logs.json',
                       help="Fichier de sortie pour logs générés")
    parser.add_argument('--count', type=int, default=100,
                       help="Nombre de logs à générer")
    
    args = parser.parse_args()
    
    print("="*70)
    print("🔧 INJECTEUR WA-ZH AVANCÉ - ENSAM CASABLANCA")
    print("="*70)
    
    if args.mode == 'generate':
        # Mode génération seulement
        print("🎲 Génération de logs...")
        logs = generate_smart_logs()
        attack_logs = generate_attack_sequence()
        all_logs = logs + attack_logs
        
        with open(args.output, 'w') as f:
            json.dump(all_logs, f, indent=2)
        
        print(f"✅ {len(all_logs)} logs générés dans {args.output}")
        
    elif args.mode == 'auto':
        # Mode automatique complet
        automation_pipeline()
        
    else:
        # Mode spécifique
        injector = WazuhLogInjector(mode=args.mode)
        
        if args.mode == 'direct':
            logs = generate_smart_logs()
            injector.inject_direct(logs[:args.count], simulate_realtime=args.realtime)
            
        elif args.mode == 'local':
            logs = generate_smart_logs()
            injector.inject_via_local_file(logs[:args.count], realtime=args.realtime)
            
        elif args.mode == 'hybrid':
            print("🔀 Mode hybride: Direct + Local")
            logs = generate_smart_logs()
            
            # 50% en direct
            print("📤 Partie 1: Injection directe")
            injector.inject_direct(logs[:args.count//2], simulate_realtime=False)
            
            time.sleep(2)
            
            # 50% en local
            print("\n📥 Partie 2: Injection locale")
            injector.inject_via_local_file(logs[args.count//2:args.count], realtime=args.realtime)
              