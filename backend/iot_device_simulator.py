#!/usr/bin/env python3
"""
Simulador de Dispositivos IoT Corrigido - Trabalho 3 Segurança IoT
UNISC - Prof. Charles Neu

Este arquivo resolve o problema "[Errno 111] Connection refused"
Salve como: iot_device_simulator.py
"""

import socket
import time
import json
import random
import threading
import hashlib
import hmac
import os
import base64
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

class IoTDevice:
    def __init__(self, device_id, device_type, server_host='127.0.0.1', server_port=65432):
        self.device_id = device_id
        self.device_type = device_type
        self.server_host = server_host
        self.server_port = server_port
        self.running = False
        self.socket = None
        self.connection_attempts = 0
        self.max_attempts = 5
        
        # Chaves de criptografia
        self.symmetric_key = None
        self.setup_crypto()
    
    def setup_crypto(self):
        """Configura criptografia"""
        self.symmetric_key = os.urandom(32)  # 256 bits para AES
        print(f"[{self.device_id}] 🔐 Criptografia configurada")
    
    def encrypt_aes(self, data):
        """Criptografia AES-256-GCM"""
        try:
            iv = os.urandom(16)
            cipher = Cipher(
                algorithms.AES(self.symmetric_key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
            return base64.b64encode(iv + encryptor.tag + ciphertext).decode()
        except Exception as e:
            print(f"[{self.device_id}] ❌ Erro na criptografia: {e}")
            return None
    
    def calculate_hash(self, data):
        """Calcula hash SHA-256"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def generate_sensor_data(self):
        """Gera dados do sensor baseado no tipo de dispositivo"""
        timestamp = datetime.now().isoformat()
        
        if self.device_type == 'temperature':
            return {
                'device_id': self.device_id,
                'type': 'temperature',
                'value': round(random.uniform(20.0, 30.0), 2),
                'unit': 'celsius',
                'timestamp': timestamp,
                'battery': round(random.uniform(80.0, 100.0), 1),
                'signal_strength': random.randint(-70, -30)
            }
        elif self.device_type == 'humidity':
            return {
                'device_id': self.device_id,
                'type': 'humidity',
                'value': round(random.uniform(40.0, 60.0), 2),
                'unit': 'percent',
                'timestamp': timestamp,
                'battery': round(random.uniform(80.0, 100.0), 1),
                'signal_strength': random.randint(-70, -30)
            }
        elif self.device_type == 'pressure':
            return {
                'device_id': self.device_id,
                'type': 'pressure',
                'value': round(random.uniform(1000.0, 1020.0), 2),
                'unit': 'hPa',
                'timestamp': timestamp,
                'battery': round(random.uniform(80.0, 100.0), 1),
                'signal_strength': random.randint(-70, -30)
            }
        else:
            return {
                'device_id': self.device_id,
                'type': 'generic',
                'value': round(random.uniform(0.0, 100.0), 2),
                'timestamp': timestamp,
                'battery': round(random.uniform(80.0, 100.0), 1)
            }
    
    def test_connection(self):
        """Testa se consegue conectar ao servidor"""
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(3)
            test_socket.connect((self.server_host, self.server_port))
            test_socket.close()
            return True
        except:
            return False
    
    def send_data(self, data, use_encryption=False, use_hash=False):
        """Envia dados para o servidor com retry automático"""
        if self.connection_attempts >= self.max_attempts:
            print(f"[{self.device_id}] ❌ Máximo de tentativas excedido")
            return False
        
        try:
            # Testa conexão primeiro
            if not self.test_connection():
                self.connection_attempts += 1
                print(f"[{self.device_id}] ⚠️  Servidor não disponível (tentativa {self.connection_attempts}/{self.max_attempts})")
                if self.connection_attempts == 1:
                    print(f"[{self.device_id}] 💡 SOLUÇÃO: Execute 'python app.py' primeiro!")
                return False
            
            # Conecta ao servidor
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.server_host, self.server_port))
            
            # Prepara dados para envio
            json_data = json.dumps(data, ensure_ascii=False)
            
            # Cria pacote de dados
            packet = {
                'device_id': self.device_id,
                'timestamp': datetime.now().isoformat(),
                'data': json_data,
                'original_data': json_data
            }
            
            # Aplicar criptografia se solicitado
            if use_encryption:
                encrypted_data = self.encrypt_aes(json_data)
                if encrypted_data:
                    packet['data'] = encrypted_data
                    packet['encrypted'] = True
                    print(f"[{self.device_id}] 🔒 Dados criptografados")
                else:
                    print(f"[{self.device_id}] ⚠️  Falha na criptografia, enviando sem criptografia")
            
            # Aplicar hash se solicitado
            if use_hash:
                data_hash = self.calculate_hash(json_data)
                packet['hash'] = data_hash
                print(f"[{self.device_id}] #️⃣ Hash calculado: {data_hash[:16]}...")
            
            # Envia dados
            packet_json = json.dumps(packet, ensure_ascii=False)
            self.socket.send(packet_json.encode('utf-8'))
            
            print(f"[{self.device_id}] ✅ Dados enviados: {data.get('type', 'unknown')} = {data.get('value', 'N/A')}")
            
            # Reset counter on success
            self.connection_attempts = 0
            return True
            
        except ConnectionRefusedError:
            self.connection_attempts += 1
            print(f"[{self.device_id}] 🔴 ERRO: Conexão recusada!")
            print(f"[{self.device_id}] 💡 SOLUÇÃO: Execute 'python app.py' primeiro")
            print(f"[{self.device_id}] 📊 Tentativa {self.connection_attempts}/{self.max_attempts}")
            return False
            
        except socket.timeout:
            self.connection_attempts += 1
            print(f"[{self.device_id}] ⏱️  Timeout na conexão (tentativa {self.connection_attempts}/{self.max_attempts})")
            return False
            
        except Exception as e:
            self.connection_attempts += 1
            print(f"[{self.device_id}] ❌ Erro ao enviar dados: {e}")
            print(f"[{self.device_id}] 📊 Tentativa {self.connection_attempts}/{self.max_attempts}")
            return False
            
        finally:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
    
    def start_simulation(self, interval=2, use_encryption=False, use_hash=False, max_iterations=None):
        """Inicia simulação contínua"""
        self.running = True
        self.connection_attempts = 0
        iteration = 0
        
        print(f"[{self.device_id}] 🚀 Simulação iniciada")
        print(f"[{self.device_id}] 📡 Servidor: {self.server_host}:{self.server_port}")
        print(f"[{self.device_id}] ⏱️  Intervalo: {interval}s")
        print(f"[{self.device_id}] 🔐 Criptografia: {'Sim' if use_encryption else 'Não'}")
        print(f"[{self.device_id}] #️⃣ Hash: {'Sim' if use_hash else 'Não'}")
        
        while self.running:
            try:
                # Verifica limite de iterações
                if max_iterations and iteration >= max_iterations:
                    print(f"[{self.device_id}] 🏁 Limite de iterações atingido ({max_iterations})")
                    break
                
                # Verifica se excedeu tentativas
                if self.connection_attempts >= self.max_attempts:
                    print(f"[{self.device_id}] 🛑 Parando devido a muitas falhas de conexão")
                    print(f"[{self.device_id}] 💡 Execute 'python app.py' e tente novamente")
                    break
                
                # Gera dados do sensor
                sensor_data = self.generate_sensor_data()
                
                # Envia dados
                success = self.send_data(sensor_data, use_encryption, use_hash)
                
                if not success:
                    # Aguarda mais tempo em caso de falha
                    wait_time = interval * (self.connection_attempts + 1)
                    print(f"[{self.device_id}] ⏳ Aguardando {wait_time}s antes da próxima tentativa...")
                    time.sleep(wait_time)
                else:
                    # Aguarda intervalo normal
                    time.sleep(interval)
                
                iteration += 1
                
            except KeyboardInterrupt:
                print(f"[{self.device_id}] 🛑 Simulação interrompida pelo usuário")
                self.running = False
                break
            except Exception as e:
                print(f"[{self.device_id}] ❌ Erro na simulação: {e}")
                time.sleep(interval * 2)
        
        print(f"[{self.device_id}] 🏁 Simulação finalizada")
    
    def stop_simulation(self):
        """Para a simulação"""
        self.running = False

class DeviceManager:
    def __init__(self):
        self.devices = []
        self.threads = []
    
    def add_device(self, device_id, device_type):
        """Adiciona um dispositivo à simulação"""
        device = IoTDevice(device_id, device_type)
        self.devices.append(device)
        print(f"[MANAGER] ➕ Dispositivo {device_id} ({device_type}) adicionado")
        return device
    
    def test_server_connection(self):
        """Testa se o servidor está rodando antes de iniciar dispositivos"""
        print("[MANAGER] 🔍 Testando conexão com servidor...")
        
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            test_socket.connect(('127.0.0.1', 65432))
            test_socket.close()
            print("[MANAGER] ✅ Servidor está rodando!")
            return True
        except:
            print("[MANAGER] ❌ ERRO: Servidor não está rodando!")
            print("[MANAGER] 💡 SOLUÇÃO: Execute 'python app.py' primeiro")
            print("[MANAGER] 📋 Passos:")
            print("[MANAGER]   1. Abra outro terminal")
            print("[MANAGER]   2. Execute: python app.py")
            print("[MANAGER]   3. Aguarde 'Servidor IoT iniciado'")
            print("[MANAGER]   4. Execute este simulador novamente")
            return False
    
    def start_all_devices(self, interval=2, use_encryption=False, use_hash=False, max_iterations=None):
        """Inicia todos os dispositivos"""
        if not self.test_server_connection():
            print("[MANAGER] 🛑 Não é possível iniciar dispositivos sem servidor")
            return
        
        print(f"[MANAGER] 🚀 Iniciando {len(self.devices)} dispositivos...")
        
        for device in self.devices:
            thread = threading.Thread(
                target=device.start_simulation,
                args=(interval, use_encryption, use_hash, max_iterations),
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
            time.sleep(0.5)  # Pequeno delay entre dispositivos
        
        print(f"[MANAGER] ✅ Todos os dispositivos iniciados")
    
    def stop_all_devices(self):
        """Para todos os dispositivos"""
        print("[MANAGER] 🛑 Parando todos os dispositivos...")
        for device in self.devices:
            device.stop_simulation()
        print("[MANAGER] ✅ Todos os dispositivos parados")

def main():
    """Função principal para demonstração"""
    print("=" * 70)
    print("🤖 SIMULADOR DE DISPOSITIVOS IoT")
    print("UNISC - Trabalho 3 - Prof. Charles Neu")
    print("=" * 70)
    print("")
    print("⚠️  IMPORTANTE: Execute 'python app.py' ANTES deste simulador!")
    print("")
    
    print("Escolha o modo de operação:")
    print("1. Dispositivo único (temperatura)")
    print("2. Múltiplos dispositivos (básico)")
    print("3. Múltiplos dispositivos (com segurança)")
    print("4. Teste rápido (5 envios por dispositivo)")
    print("5. Demonstração completa")
    
    try:
        choice = input("\nOpção (1-5): ").strip()
    except KeyboardInterrupt:
        print("\n👋 Programa interrompido")
        return
    
    if choice == '1':
        # Dispositivo único
        device = IoTDevice('TEMP_001', 'temperature')
        print("\n🌡️  Iniciando dispositivo de temperatura...")
        device.start_simulation(interval=3)
    
    elif choice == '2':
        # Múltiplos dispositivos básicos
        manager = DeviceManager()
        
        # Adiciona dispositivos
        manager.add_device('TEMP_001', 'temperature')
        manager.add_device('HUM_001', 'humidity')
        manager.add_device('PRES_001', 'pressure')
        
        print("\n🔗 Iniciando múltiplos dispositivos...")
        manager.start_all_devices(interval=4)
        
        try:
            print("\n✅ Dispositivos rodando! Pressione Ctrl+C para parar.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Parando simulação...")
            manager.stop_all_devices()
    
    elif choice == '3':
        # Múltiplos dispositivos com segurança
        manager = DeviceManager()
        
        manager.add_device('TEMP_SEC_001', 'temperature')
        manager.add_device('HUM_SEC_001', 'humidity')
        manager.add_device('PRES_SEC_001', 'pressure')
        
        print("\n🔒 Iniciando dispositivos com segurança completa...")
        manager.start_all_devices(interval=5, use_encryption=True, use_hash=True)
        
        try:
            print("\n✅ Dispositivos seguros rodando! Pressione Ctrl+C para parar.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Parando simulação...")
            manager.stop_all_devices()
    
    elif choice == '4':
        # Teste rápido
        manager = DeviceManager()
        
        manager.add_device('TEMP_TEST', 'temperature')
        manager.add_device('HUM_TEST', 'humidity')
        
        print("\n⚡ Teste rápido (5 envios por dispositivo)...")
        manager.start_all_devices(interval=2, use_encryption=True, use_hash=True, max_iterations=5)
        
        # Aguarda threads terminarem
        print("\n⏳ Aguardando conclusão dos testes...")
        for thread in manager.threads:
            thread.join()
        
        print("\n✅ Teste rápido concluído!")
    
    elif choice == '5':
        # Demonstração completa
        print("\n🎭 DEMONSTRAÇÃO COMPLETA")
        print("Esta demonstração mostra todos os recursos de segurança")
        
        device = IoTDevice('DEMO_001', 'temperature')
        
        # Teste 1: Dados sem proteção
        print("\n1️⃣ Enviando dados sem proteção:")
        data = device.generate_sensor_data()
        device.send_data(data)
        time.sleep(2)
        
        # Teste 2: Dados com hash
        print("\n2️⃣ Enviando dados com hash:")
        data = device.generate_sensor_data()
        device.send_data(data, use_hash=True)
        time.sleep(2)
        
        # Teste 3: Dados criptografados
        print("\n3️⃣ Enviando dados criptografados:")
        data = device.generate_sensor_data()
        device.send_data(data, use_encryption=True)
        time.sleep(2)
        
        # Teste 4: Dados criptografados com hash
        print("\n4️⃣ Enviando dados com criptografia + hash:")
        data = device.generate_sensor_data()
        device.send_data(data, use_encryption=True, use_hash=True)
        
        print("\n🎉 Demonstração completa finalizada!")
    
    else:
        print("❌ Opção inválida!")

if __name__ == '__main__':
    main()