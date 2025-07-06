"""
Implementação dos algoritmos de criptografia para IoT Security
Tarefas 2, 3, 4 e 5 do trabalho
"""

import os
import base64
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 = PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
import json

class CryptoTester:
    """Classe para testar e comparar algoritmos de criptografia"""
    
    def __init__(self):
        self.test_data = "Este é um texto de teste para criptografia IoT - Temperatura: 25.5°C"
        self.results = {}
    
    def test_aes_256_gcm(self):
        """Teste AES-256-GCM"""
        print("=== Testando AES-256-GCM ===")
        
        # Gera chave de 256 bits
        key = os.urandom(32)
        iv = os.urandom(16)
        
        start_time = time.time()
        
        # Criptografia
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(self.test_data.encode()) + encryptor.finalize()
        
        # Descriptografia
        decryptor = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, encryptor.tag),
            backend=default_backend()
        ).decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        end_time = time.time()
        
        result = {
            'algorithm': 'AES-256-GCM',
            'key_size': 256,
            'iv_size': 128,
            'encrypted_size': len(ciphertext),
            'original_size': len(self.test_data.encode()),
            'overhead': len(ciphertext) - len(self.test_data.encode()),
            'time_ms': (end_time - start_time) * 1000,
            'security_level': 'Alto',
            'authenticated': True,
            'success': plaintext.decode() == self.test_data
        }
        
        self.results['AES-256-GCM'] = result
        print(f"Resultado: {result}")
        return result
    
    def test_chacha20_poly1305(self):
        """Teste ChaCha20-Poly1305"""
        print("=== Testando ChaCha20-Poly1305 ===")
        
        # Gera chave de 256 bits e nonce de 96 bits
        key = os.urandom(32)
        nonce = os.urandom(12)
        
        start_time = time.time()
        
        # Criptografia
        cipher = Cipher(
            algorithms.ChaCha20(key, nonce),
            modes.ChaCha20Poly1305.tag_length = 16,
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(self.test_data.encode()) + encryptor.finalize()
        
        # Descriptografia
        decryptor = Cipher(
            algorithms.ChaCha20(key, nonce),
            modes.ChaCha20Poly1305.tag_length = 16,
            backend=default_backend()
        ).decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        end_time = time.time()
        
        result = {
            'algorithm': 'ChaCha20-Poly1305',
            'key_size': 256,
            'nonce_size': 96,
            'encrypted_size': len(ciphertext),
            'original_size': len(self.test_data.encode()),
            'overhead': len(ciphertext) - len(self.test_data.encode()),
            'time_ms': (end_time - start_time) * 1000,
            'security_level': 'Alto',
            'authenticated': True,
            'success': plaintext.decode() == self.test_data
        }
        
        self.results['ChaCha20-Poly1305'] = result
        print(f"Resultado: {result}")
        return result
    
    def test_aes_128_ctr(self):
        """Teste AES-128-CTR"""
        print("=== Testando AES-128-CTR ===")
        
        # Gera chave de 128 bits
        key = os.urandom(16)
        iv = os.urandom(16)
        
        start_time = time.time()
        
        # Criptografia
        cipher = Cipher(
            algorithms.AES(key),
            modes.CTR(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(self.test_data.encode()) + encryptor.finalize()
        
        # Descriptografia
        decryptor = Cipher(
            algorithms.AES(key),
            modes.CTR(iv),
            backend=default_backend()
        ).decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        end_time = time.time()
        
        result = {
            'algorithm': 'AES-128-CTR',
            'key_size': 128,
            'iv_size': 128,
            'encrypted_size': len(ciphertext),
            'original_size': len(self.test_data.encode()),
            'overhead': len(ciphertext) - len(self.test_data.encode()),
            'time_ms': (end_time - start_time) * 1000,
            'security_level': 'Médio-Alto',
            'authenticated': False,
            'success': plaintext.decode() == self.test_data
        }
        
        self.results['AES-128-CTR'] = result
        print(f"Resultado: {result}")
        return result
    
    def test_aes_256_cbc(self):
        """Teste AES-256-CBC com PKCS7 padding"""
        print("=== Testando AES-256-CBC ===")
        
        from cryptography.hazmat.primitives import padding as sym_padding
        
        # Gera chave de 256 bits
        key = os.urandom(32)
        iv = os.urandom(16)
        
        start_time = time.time()
        
        # Padding PKCS7
        padder = sym_padding.PKCS7(128).padder()
        padded_data = padder.update(self.test_data.encode()) + padder.finalize()
        
        # Criptografia
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Descriptografia
        decryptor = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        ).decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Remove padding
        unpadder = sym_padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        end_time = time.time()
        
        result = {
            'algorithm': 'AES-256-CBC',
            'key_size': 256,
            'iv_size': 128,
            'encrypted_size': len(ciphertext),
            'original_size': len(self.test_data.encode()),
            'overhead': len(ciphertext) - len(self.test_data.encode()),
            'time_ms': (end_time - start_time) * 1000,
            'security_level': 'Alto',
            'authenticated': False,
            'success': plaintext.decode() == self.test_data
        }
        
        self.results['AES-256-CBC'] = result
        print(f"Resultado: {result}")
        return result
    
    def run_all_tests(self):
        """Executa todos os testes de criptografia"""
        print("=== TESTE DE ALGORITMOS DE CRIPTOGRAFIA ===\n")
        
        self.test_aes_256_gcm()
        print()
        
        self.test_chacha20_poly1305()
        print()
        
        self.test_aes_128_ctr()
        print()
        
        self.test_aes_256_cbc()
        print()
        
        self.print_comparison()
    
    def print_comparison(self):
        """Imprime comparação dos algoritmos"""
        print("=== COMPARAÇÃO DOS ALGORITMOS ===")
        print(f"{'Algoritmo':<20} {'Tempo(ms)':<10} {'Overhead':<10} {'Segurança':<15} {'Auth':<6}")
        print("-" * 70)
        
        for algo, result in self.results.items():
            print(f"{algo:<20} {result['time_ms']:<10.2f} {result['overhead']:<10} "
                  f"{result['security_level']:<15} {'Sim' if result['authenticated'] else 'Não':<6}")

class HashTester:
    """Implementação e teste de funções hash - Tarefa 3"""
    
    def __init__(self):
        self.test_data = "Pacote IoT - Dispositivo: TEMP_001, Valor: 25.5°C, Timestamp: 2025-07-06T10:30:00"
    
    def sha256_hash(self, data):
        """Implementação SHA-256"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def sha3_256_hash(self, data):
        """Implementação SHA3-256"""
        digest = hashes.Hash(hashes.SHA3_256(), backend=default_backend())
        digest.update(data.encode())
        return digest.finalize().hex()
    
    def blake2b_hash(self, data):
        """Implementação BLAKE2b"""
        digest = hashes.Hash(hashes.BLAKE2b(64), backend=default_backend())
        digest.update(data.encode())
        return digest.finalize().hex()
    
    def hmac_sha256(self, data, key):
        """HMAC com SHA-256"""
        return hmac.new(key.encode(), data.encode(), hashlib.sha256).hexdigest()
    
    def test_integrity_verification(self):
        """Testa verificação de integridade"""
        print("=== TESTE DE FUNÇÕES HASH E INTEGRIDADE ===")
        
        # Testa diferentes algoritmos
        sha256_hash = self.sha256_hash(self.test_data)
        sha3_hash = self.sha3_256_hash(self.test_data)
        blake2b_hash = self.blake2b_hash(self.test_data)
        
        print(f"Dados originais: {self.test_data}")
        print(f"SHA-256: {sha256_hash}")
        print(f"SHA3-256: {sha3_hash}")
        print(f"BLAKE2b: {blake2b_hash}")
        
        # Simula dados corrompidos
        corrupted_data = self.test_data.replace("25.5", "26.0")
        corrupted_hash = self.sha256_hash(corrupted_data)
        
        print(f"\nDados corrompidos: {corrupted_data}")
        print(f"Hash corrompido: {corrupted_hash}")
        
        # Verifica integridade
        print(f"\nVerificação de integridade:")
        print(f"Dados íntegros: {sha256_hash == self.sha256_hash(self.test_data)}")
        print(f"Dados corrompidos detectados: {sha256_hash != corrupted_hash}")
        
        # Teste HMAC para autenticação
        key = "chave_secreta_iot"
        hmac_original = self.hmac_sha256(self.test_data, key)
        hmac_corrupted = self.hmac_sha256(corrupted_data, key)
        
        print(f"\nHMAC original: {hmac_original}")
        print(f"HMAC corrompido: {hmac_corrupted}")
        print(f"Autenticação bem-sucedida: {hmac_original != hmac_corrupted}")

class DigitalCertificateManager:
    """Gerenciador de certificados digitais - Tarefa 4"""
    
    def __init__(self):
        self.ca_private_key = None
        self.ca_public_key = None
        self.ca_certificate = None
    
    def generate_ca_keys(self):
        """Gera par de chaves para CA (Certificate Authority)"""
        print("=== GERANDO CHAVES DA AUTORIDADE CERTIFICADORA ===")
        
        # Gera chave privada RSA de 2048 bits
        self.ca_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.ca_public_key = self.ca_private_key.public_key()
        
        print("Chaves da CA geradas com sucesso!")
        return self.ca_private_key, self.ca_public_key
    
    def create_ca_certificate(self):
        """Cria certificado autoassinado da CA"""
        print("=== CRIANDO CERTIFICADO DA CA ===")
        
        if not self.ca_private_key:
            self.generate_ca_keys()
        
        # Informações do certificado
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Rio Grande do Sul"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Santa Cruz do Sul"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "UNISC IoT Security Lab"),
            x509.NameAttribute(NameOID.COMMON_NAME, "IoT CA Root"),
        ])
        
        # Cria certificado
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            self.ca_public_key
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("iot-ca.local"),
            ]),
            critical=False,
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        ).sign(self.ca_private_key, hashes.SHA256(), default_backend())
        
        self.ca_certificate = cert
        print("Certificado da CA criado com sucesso!")
        
        # Salva certificado em arquivo
        with open("ca_certificate.pem", "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        return cert
    
    def generate_device_certificate(self, device_id, device_type="sensor"):
        """Gera certificado para dispositivo IoT"""
        print(f"=== GERANDO CERTIFICADO PARA DISPOSITIVO {device_id} ===")
        
        if not self.ca_certificate:
            self.create_ca_certificate()
        
        # Gera chaves do dispositivo
        device_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        device_public_key = device_private_key.public_key()
        
        # Informações do dispositivo
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "BR"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "UNISC IoT Device"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, device_type),
            x509.NameAttribute(NameOID.COMMON_NAME, device_id),
        ])
        
        # Cria certificado do dispositivo
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            self.ca_certificate.subject
        ).public_key(
            device_public_key
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=90)  # Certificados IoT com validade menor
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(f"{device_id}.iot.local"),
                x509.RFC822Name(f"{device_id}@iot.unisc.br"),
            ]),
            critical=False,
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                content_commitment=False,
                data_encipherment=False,
                encipher_only=False,
                decipher_only=False
            ),
            critical=True,
        ).sign(self.ca_private_key, hashes.SHA256(), default_backend())
        
        print(f"Certificado para {device_id} criado com sucesso!")
        
        # Salva certificado e chave do dispositivo
        cert_filename = f"{device_id}_certificate.pem"
        key_filename = f"{device_id}_private_key.pem"
        
        with open(cert_filename, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        with open(key_filename, "wb") as f:
            f.write(device_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        return cert, device_private_key, device_public_key
    
    def verify_certificate(self, device_cert):
        """Verifica certificado do dispositivo"""
        print("=== VERIFICANDO CERTIFICADO ===")
        
        try:
            # Verifica assinatura do certificado
            self.ca_public_key.verify(
                device_cert.signature,
                device_cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                device_cert.signature_hash_algorithm,
            )
            
            # Verifica validade temporal
            now = datetime.utcnow()
            if device_cert.not_valid_before <= now <= device_cert.not_valid_after:
                print("✓ Certificado válido!")
                return True
            else:
                print("✗ Certificado expirado!")
                return False
                
        except Exception as e:
            print(f"✗ Certificado inválido: {e}")
            return False

class DigitalSignature:
    """Implementação de assinatura digital - Tarefa 5"""
    
    def __init__(self, private_key=None, public_key=None):
        if private_key and public_key:
            self.private_key = private_key
            self.public_key = public_key
        else:
            self.generate_keys()
    
    def generate_keys(self):
        """Gera par de chaves RSA"""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
    
    def sign_data(self, data):
        """Assina dados com chave privada"""
        signature = self.private_key.sign(
            data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode()
    
    def verify_signature(self, data, signature):
        """Verifica assinatura com chave pública"""
        try:
            signature_bytes = base64.b64decode(signature)
            self.public_key.verify(
                signature_bytes,
                data.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except:
            return False
    
    def test_digital_signature(self):
        """Testa assinatura digital"""
        print("=== TESTE DE ASSINATURA DIGITAL ===")
        
        # Dados do pacote IoT
        iot_packet = json.dumps({
            "device_id": "TEMP_001",
            "temperature": 25.5,
            "humidity": 60.2,
            "timestamp": datetime.now().isoformat()
        })
        
        print(f"Dados do pacote: {iot_packet}")
        
        # Assina o pacote
        signature = self.sign_data(iot_packet)
        print(f"Assinatura: {signature[:50]}...")
        
        # Verifica assinatura
        is_valid = self.verify_signature(iot_packet, signature)
        print(f"Assinatura válida: {is_valid}")
        
        # Testa com dados alterados
        tampered_packet = iot_packet.replace("25.5", "30.0")
        is_tampered_valid = self.verify_signature(tampered_packet, signature)
        print(f"Dados alterados detectados: {not is_tampered_valid}")
        
        return signature, is_valid

class SecureProtocol:
    """Protocolo de comunicação segura - Tarefa 6"""
    
    def __init__(self):
        self.session_key = None
        self.sequence_number = 0
        self.signature_manager = DigitalSignature()
    
    def establish_secure_session(self):
        """Estabelece sessão segura"""
        print("=== ESTABELECENDO SESSÃO SEGURA ===")
        
        # Gera chave de sessão
        self.session_key = os.urandom(32)  # AES-256
        self.sequence_number = 0
        
        print("Sessão segura estabelecida!")
        return base64.b64encode(self.session_key).decode()
    
    def create_secure_packet(self, device_id, data):
        """Cria pacote seguro com criptografia + hash + assinatura"""
        print(f"=== CRIANDO PACOTE SEGURO PARA {device_id} ===")
        
        if not self.session_key:
            self.establish_secure_session()
        
        # Incrementa número de sequência
        self.sequence_number += 1
        
        # Cria payload
        payload = {
            "device_id": device_id,
            "sequence": self.sequence_number,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        payload_json = json.dumps(payload)
        
        # 1. Calcula hash para integridade
        data_hash = hashlib.sha256(payload_json.encode()).hexdigest()
        
        # 2. Criptografa dados
        iv = os.urandom(16)
        cipher = Cipher(
            algorithms.AES(self.session_key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(payload_json.encode()) + encryptor.finalize()
        
        # 3. Assina o pacote
        packet_for_signature = f"{device_id}:{self.sequence_number}:{data_hash}"
        signature = self.signature_manager.sign_data(packet_for_signature)
        
        # Cria pacote final
        secure_packet = {
            "device_id": device_id,
            "sequence": self.sequence_number,
            "timestamp": datetime.now().isoformat(),
            "encrypted_data": base64.b64encode(iv + encryptor.tag + ciphertext).decode(),
            "hash": data_hash,
            "signature": signature,
            "protocol_version": "IoTSecure-1.0"
        }
        
        print("Pacote seguro criado com sucesso!")
        return secure_packet
    
    def verify_secure_packet(self, packet):
        """Verifica e decodifica pacote seguro"""
        print("=== VERIFICANDO PACOTE SEGURO ===")
        
        try:
            # 1. Verifica assinatura
            packet_for_signature = f"{packet['device_id']}:{packet['sequence']}:{packet['hash']}"
            signature_valid = self.signature_manager.verify_signature(
                packet_for_signature, 
                packet['signature']
            )
            
            if not signature_valid:
                print("✗ Assinatura inválida!")
                return None, False
            
            # 2. Descriptografa dados
            encrypted_bytes = base64.b64decode(packet['encrypted_data'])
            iv = encrypted_bytes[:16]
            tag = encrypted_bytes[16:32]
            ciphertext = encrypted_bytes[32:]
            
            cipher = Cipher(
                algorithms.AES(self.session_key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # 3. Verifica integridade (hash)
            calculated_hash = hashlib.sha256(plaintext).hexdigest()
            hash_valid = calculated_hash == packet['hash']
            
            if not hash_valid:
                print("✗ Hash inválido - dados corrompidos!")
                return None, False
            
            # 4. Decodifica JSON
            decrypted_data = json.loads(plaintext.decode())
            
            print("✓ Pacote verificado com sucesso!")
            return decrypted_data, True
            
        except Exception as e:
            print(f"✗ Erro ao verificar pacote: {e}")
            return None, False

def main():
    """Função principal para executar todos os testes"""
    print("=" * 60)
    print("TRABALHO 3 - SEGURANÇA EM IoT")
    print("Implementação de Criptografia, Hash e Certificados Digitais")
    print("=" * 60)
    
    # Tarefa 2: Teste de algoritmos de criptografia
    print("\nTAREFA 2: ALGORITMOS DE CRIPTOGRAFIA")
    crypto_tester = CryptoTester()
    crypto_tester.run_all_tests()
    
    # Tarefa 3: Teste de funções hash
    print("\n" + "=" * 60)
    print("\nTAREFA 3: FUNÇÕES HASH E INTEGRIDADE")
    hash_tester = HashTester()
    hash_tester.test_integrity_verification()
    
    # Tarefa 4: Certificados digitais
    print("\n" + "=" * 60)
    print("\nTAREFA 4: CERTIFICADOS DIGITAIS")
    cert_manager = DigitalCertificateManager()
    ca_cert = cert_manager.create_ca_certificate()
    device_cert, device_key, device_pub = cert_manager.generate_device_certificate("TEMP_001", "temperature")
    cert_manager.verify_certificate(device_cert)
    
    # Tarefa 5: Assinatura digital
    print("\n" + "=" * 60)
    print("\nTAREFA 5: ASSINATURA DIGITAL")
    signature_manager = DigitalSignature(device_key, device_pub)
    signature_manager.test_digital_signature()
    
    # Tarefa 6: Protocolo seguro
    print("\n" + "=" * 60)
    print("\nTAREFA 6: PROTOCOLO DE COMUNICAÇÃO SEGURA")
    protocol = SecureProtocol()
    
    # Teste do protocolo completo
    test_data = {
        "temperature": 25.5,
        "humidity": 60.2,
        "pressure": 1013.25
    }
    
    secure_packet = protocol.create_secure_packet("TEMP_001", test_data)
    decrypted_data, is_valid = protocol.verify_secure_packet(secure_packet)
    
    print(f"Dados originais: {test_data}")
    print(f"Dados decriptografados: {decrypted_data['data'] if decrypted_data else 'Erro'}")
    print(f"Verificação bem-sucedida: {is_valid}")
    
    print("\n" + "=" * 60)
    print("TODOS OS TESTES CONCLUÍDOS!")
    print("=" * 60)

if __name__ == "__main__":
    main()