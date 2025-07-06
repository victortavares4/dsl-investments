from flask import Flask, request, jsonify
from flask_cors import CORS
import socket
import threading
import time
import json
import hashlib
import hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import os
import base64
from datetime import datetime, timedelta
import secrets
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Criação da aplicação Flask
app = Flask(__name__)
CORS(app)

# Configurações do servidor
HOST = '127.0.0.1'
IOT_PORT = 65432
FLASK_PORT = 5000

# Armazenamento de dados
device_data = []
connected_devices = {}
security_logs = []

# Chaves de criptografia
symmetric_key = None
rsa_private_key = None
rsa_public_key = None
iot_server_running = False

class SecurityManager:
    def __init__(self):
        self.generate_keys()
    
    def generate_keys(self):
        global symmetric_key, rsa_private_key, rsa_public_key
        
        try:
            symmetric_key = os.urandom(32)
            rsa_private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            rsa_public_key = rsa_private_key.public_key()
            logger.info("✅ Chaves criptográficas geradas")
        except Exception as e:
            logger.error(f"❌ Erro ao gerar chaves: {e}")
    
    def encrypt_aes(self, data, key):
        try:
            iv = os.urandom(16)
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
            return base64.b64encode(iv + encryptor.tag + ciphertext).decode()
        except Exception as e:
            logger.error(f"Erro na criptografia: {e}")
            return None
    
    def decrypt_aes(self, encrypted_data, key):
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            iv = encrypted_bytes[:16]
            tag = encrypted_bytes[16:32]
            ciphertext = encrypted_bytes[32:]
            
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext.decode()
        except Exception as e:
            logger.error(f"Erro na descriptografia: {e}")
            return None
    
    def calculate_hash(self, data):
        return hashlib.sha256(data.encode()).hexdigest()
    
    def sign_data(self, data):
        try:
            signature = rsa_private_key.sign(
                data.encode(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            return base64.b64encode(signature).decode()
        except Exception as e:
            logger.error(f"Erro na assinatura: {e}")
            return None
    
    def verify_signature(self, data, signature):
        try:
            signature_bytes = base64.b64decode(signature)
            rsa_public_key.verify(
                signature_bytes, data.encode(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            return True
        except:
            return False

security_manager = SecurityManager()

class IoTServer:
    def __init__(self):
        self.socket = None
        self.running = False
    
    def start_server(self):
        global iot_server_running
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((HOST, IOT_PORT))
            self.socket.listen(5)
            self.running = True
            iot_server_running = True
            
            logger.info(f"🚀 Servidor IoT iniciado em {HOST}:{IOT_PORT}")
            
            while self.running:
                try:
                    self.socket.settimeout(1)
                    conn, addr = self.socket.accept()
                    thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                    thread.daemon = True
                    thread.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        logger.error(f"Erro no servidor IoT: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar servidor IoT: {e}")
            iot_server_running = False
        finally:
            if self.socket:
                self.socket.close()
            iot_server_running = False
            logger.info("🛑 Servidor IoT parado")
    
    def stop_server(self):
        self.running = False
        if self.socket:
            self.socket.close()
    
    def handle_client(self, conn, addr):
        logger.info(f"📡 Conexão estabelecida com {addr}")
        connected_devices[f"{addr[0]}:{addr[1]}"] = {
            'connected_at': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat()
        }
        
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                
                self.process_data(data.decode(), addr)
                
                addr_key = f"{addr[0]}:{addr[1]}"
                if addr_key in connected_devices:
                    connected_devices[addr_key]['last_seen'] = datetime.now().isoformat()
                
        except Exception as e:
            logger.error(f"Erro ao processar cliente {addr}: {e}")
        finally:
            conn.close()
            addr_key = f"{addr[0]}:{addr[1]}"
            if addr_key in connected_devices:
                del connected_devices[addr_key]
            logger.info(f"🔌 Conexão com {addr} encerrada")
    
    def process_data(self, data, addr):
        try:
            json_data = json.loads(data)
            json_data['timestamp'] = datetime.now().isoformat()
            json_data['device_address'] = f"{addr[0]}:{addr[1]}"
            
            if 'encrypted' in json_data and json_data['encrypted']:
                decrypted_data = security_manager.decrypt_aes(json_data['data'], symmetric_key)
                if decrypted_data:
                    json_data['decrypted_data'] = json.loads(decrypted_data)
            
            if 'hash' in json_data:
                original_data = json_data.get('original_data', '')
                calculated_hash = security_manager.calculate_hash(original_data)
                json_data['hash_valid'] = (calculated_hash == json_data['hash'])
            
            if 'signature' in json_data:
                original_data = json_data.get('original_data', '')
                json_data['signature_valid'] = security_manager.verify_signature(original_data, json_data['signature'])
            
            device_data.append(json_data)
            
            security_logs.append({
                'timestamp': datetime.now().isoformat(),
                'device': f"{addr[0]}:{addr[1]}",
                'action': 'data_received',
                'encrypted': json_data.get('encrypted', False),
                'hash_valid': json_data.get('hash_valid', None),
                'signature_valid': json_data.get('signature_valid', None)
            })
            
            logger.info(f"📦 Dados processados de {addr}: {json_data.get('device_id', 'Unknown')}")
            
        except json.JSONDecodeError:
            logger.warning(f"📦 Dados não-JSON recebidos de {addr}")
            device_data.append({
                'timestamp': datetime.now().isoformat(),
                'device_address': f"{addr[0]}:{addr[1]}",
                'raw_data': data[:500]
            })

iot_server = IoTServer()

# ============= ROTAS DA API FLASK =============

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'status': 'running',
        'connected_devices': len(connected_devices),
        'total_data_received': len(device_data),
        'security_logs': len(security_logs),
        'iot_server_running': iot_server_running,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/devices', methods=['GET'])
def get_devices():
    return jsonify(connected_devices)

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(device_data[-100:])

@app.route('/api/security-logs', methods=['GET'])
def get_security_logs():
    return jsonify(security_logs[-100:])

@app.route('/api/encrypt', methods=['POST'])
def encrypt_data():
    try:
        data = request.json.get('data', '')
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
            
        encrypted = security_manager.encrypt_aes(data, symmetric_key)
        if encrypted:
            return jsonify({
                'original': data,
                'encrypted': encrypted,
                'hash': security_manager.calculate_hash(data)
            })
        else:
            return jsonify({'error': 'Erro na criptografia'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/decrypt', methods=['POST'])
def decrypt_data():
    try:
        encrypted_data = request.json.get('encrypted_data', '')
        if not encrypted_data:
            return jsonify({'error': 'Dados criptografados não fornecidos'}), 400
            
        decrypted = security_manager.decrypt_aes(encrypted_data, symmetric_key)
        return jsonify({
            'encrypted': encrypted_data,
            'decrypted': decrypted
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sign', methods=['POST'])
def sign_data():
    try:
        data = request.json.get('data', '')
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
            
        signature = security_manager.sign_data(data)
        if signature:
            return jsonify({'data': data, 'signature': signature})
        else:
            return jsonify({'error': 'Erro na assinatura'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify', methods=['POST'])
def verify_signature():
    try:
        data = request.json.get('data', '')
        signature = request.json.get('signature', '')
        
        if not data or not signature:
            return jsonify({'error': 'Dados ou assinatura não fornecidos'}), 400
            
        is_valid = security_manager.verify_signature(data, signature)
        return jsonify({'data': data, 'signature': signature, 'valid': is_valid})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({
        'message': 'API funcionando!',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'services': {'flask': True, 'iot_server': iot_server_running}
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erro interno do servidor'}), 500

def start_iot_server():
    def run_server():
        try:
            iot_server.start_server()
        except Exception as e:
            logger.error(f"Erro no servidor IoT: {e}")
    
    iot_server_thread = threading.Thread(target=run_server, daemon=True)
    iot_server_thread.start()
    logger.info("🔄 Thread do servidor IoT iniciada")

def main():
    logger.info("=" * 60)
    logger.info("🚀 INICIANDO SERVIDOR IoT SECURITY")
    logger.info("UNISC - Trabalho 3 - Prof. Charles Neu")
    logger.info("=" * 60)
    
    try:
        logger.info("🔄 Iniciando servidor IoT...")
        start_iot_server()
        
        time.sleep(2)
        
        logger.info(f"🌐 Servidor Flask: http://localhost:{FLASK_PORT}")
        logger.info(f"📡 Servidor IoT: {HOST}:{IOT_PORT}")
        logger.info(f"🔗 API Base URL: http://localhost:{FLASK_PORT}/api")
        logger.info("")
        logger.info("🔧 Endpoints disponíveis:")
        logger.info("  GET  /api/status")
        logger.info("  GET  /api/devices") 
        logger.info("  GET  /api/data")
        logger.info("  GET  /api/security-logs")
        logger.info("  POST /api/encrypt")
        logger.info("  POST /api/decrypt")
        logger.info("  POST /api/sign")
        logger.info("  POST /api/verify")
        logger.info("")
        logger.info("⚠️  Para parar: Ctrl+C")
        logger.info("=" * 60)
        
        app.run(host='0.0.0.0', port=FLASK_PORT, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Parando servidores...")
        iot_server.stop_server()
        logger.info("👋 Servidores parados")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
    finally:
        if iot_server:
            iot_server.stop_server()

if __name__ == '__main__':
    main()