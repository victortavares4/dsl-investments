import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Wifi, 
  Lock, 
  Key, 
  Hash, 
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Thermometer,
  Droplets,
  Gauge,
  Server,
  Eye,
  EyeOff
} from 'lucide-react';

interface DeviceData {
  device_id: string;
  timestamp: string;
  device_address: string;
  data?: string;
  encrypted?: boolean;
  hash_valid?: boolean;
  signature_valid?: boolean;
  decrypted_data?: any;
}

interface SecurityLog {
  timestamp: string;
  device: string;
  action: string;
  encrypted: boolean;
  hash_valid?: boolean;
  signature_valid?: boolean;
}

interface SystemStatus {
  status: string;
  connected_devices: number;
  total_data_received: number;
  security_logs: number;
}

const IoTSecurityDashboard: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [devices, setDevices] = useState<Record<string, any>>({});
  const [deviceData, setDeviceData] = useState<DeviceData[]>([]);
  const [securityLogs, setSecurityLogs] = useState<SecurityLog[]>([]);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'devices' | 'data' | 'security' | 'crypto'>('dashboard');
  const [cryptoTest, setCryptoTest] = useState({ data: '', encrypted: '', decrypted: '', signature: '' });
  const [showRawData, setShowRawData] = useState(false);

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusRes, devicesRes, dataRes, logsRes] = await Promise.all([
          fetch('/api/status'),
          fetch('/api/devices'),
          fetch('/api/data'),
          fetch('/api/security-logs')
        ]);

        if (statusRes.ok) setStatus(await statusRes.json());
        if (devicesRes.ok) setDevices(await devicesRes.json());
        if (dataRes.ok) setDeviceData(await dataRes.json());
        if (logsRes.ok) setSecurityLogs(await logsRes.json());
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleEncrypt = async () => {
    try {
      const response = await fetch('/api/encrypt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: cryptoTest.data })
      });
      
      if (response.ok) {
        const result = await response.json();
        setCryptoTest(prev => ({ ...prev, encrypted: result.encrypted }));
      }
    } catch (error) {
      console.error('Error encrypting data:', error);
    }
  };

  const handleDecrypt = async () => {
    try {
      const response = await fetch('/api/decrypt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ encrypted_data: cryptoTest.encrypted })
      });
      
      if (response.ok) {
        const result = await response.json();
        setCryptoTest(prev => ({ ...prev, decrypted: result.decrypted }));
      }
    } catch (error) {
      console.error('Error decrypting data:', error);
    }
  };

  const handleSign = async () => {
    try {
      const response = await fetch('/api/sign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: cryptoTest.data })
      });
      
      if (response.ok) {
        const result = await response.json();
        setCryptoTest(prev => ({ ...prev, signature: result.signature }));
      }
    } catch (error) {
      console.error('Error signing data:', error);
    }
  };

  const getDeviceIcon = (deviceId: string) => {
    if (deviceId.includes('TEMP')) return <Thermometer className="w-5 h-5 text-red-500" />;
    if (deviceId.includes('HUM')) return <Droplets className="w-5 h-5 text-blue-500" />;
    if (deviceId.includes('PRES')) return <Gauge className="w-5 h-5 text-green-500" />;
    return <Activity className="w-5 h-5 text-gray-500" />;
  };

  const getSecurityStatusIcon = (encrypted?: boolean, hashValid?: boolean, signatureValid?: boolean) => {
    if (encrypted && hashValid && signatureValid) {
      return <Shield className="w-5 h-5 text-green-500" />;
    } else if (encrypted || hashValid || signatureValid) {
      return <Shield className="w-5 h-5 text-yellow-500" />;
    } else {
      return <AlertTriangle className="w-5 h-5 text-red-500" />;
    }
  };

  const TabButton: React.FC<{ tab: string; icon: React.ReactNode; active: boolean; onClick: () => void }> = 
    ({ tab, icon, active, onClick }) => (
      <button
        onClick={onClick}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
          active 
            ? 'bg-blue-600 text-white' 
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }`}
      >
        {icon}
        {tab}
      </button>
    );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            IoT Security Dashboard
          </h1>
          <p className="text-gray-600">
            Monitoramento e teste de segurança para dispositivos IoT
          </p>
        </div>

        {/* Navigation */}
        <div className="flex flex-wrap gap-2 mb-8">
          <TabButton 
            tab="Dashboard" 
            icon={<Activity />} 
            active={activeTab === 'dashboard'} 
            onClick={() => setActiveTab('dashboard')} 
          />
          <TabButton 
            tab="Dispositivos" 
            icon={<Wifi />} 
            active={activeTab === 'devices'} 
            onClick={() => setActiveTab('devices')} 
          />
          <TabButton 
            tab="Dados" 
            icon={<Server />} 
            active={activeTab === 'data'} 
            onClick={() => setActiveTab('data')} 
          />
          <TabButton 
            tab="Segurança" 
            icon={<Shield />} 
            active={activeTab === 'security'} 
            onClick={() => setActiveTab('security')} 
          />
          <TabButton 
            tab="Criptografia" 
            icon={<Lock />} 
            active={activeTab === 'crypto'} 
            onClick={() => setActiveTab('crypto')} 
          />
        </div>

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Status do Sistema</p>
                  <p className="text-2xl font-bold text-green-600">
                    {status?.status === 'running' ? 'Ativo' : 'Inativo'}
                  </p>
                </div>
                <Server className="w-10 h-10 text-green-500" />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Dispositivos Conectados</p>
                  <p className="text-2xl font-bold text-blue-600">{status?.connected_devices || 0}</p>
                </div>
                <Wifi className="w-10 h-10 text-blue-500" />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Dados Recebidos</p>
                  <p className="text-2xl font-bold text-purple-600">{status?.total_data_received || 0}</p>
                </div>
                <Activity className="w-10 h-10 text-purple-500" />
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Logs de Segurança</p>
                  <p className="text-2xl font-bold text-orange-600">{status?.security_logs || 0}</p>
                </div>
                <Shield className="w-10 h-10 text-orange-500" />
              </div>
            </div>
          </div>
        )}

        {/* Devices Tab */}
        {activeTab === 'devices' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b">
              <h2 className="text-xl font-semibold text-gray-900">Dispositivos Conectados</h2>
            </div>
            <div className="p-6">
              {Object.keys(devices).length === 0 ? (
                <div className="text-center py-8">
                  <Wifi className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">Nenhum dispositivo conectado</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {Object.entries(devices).map(([address, device]: [string, any]) => (
                    <div key={address} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                        <div>
                          <p className="font-medium text-gray-900">{address}</p>
                          <p className="text-sm text-gray-600">
                            Conectado em: {new Date(device.connected_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-600">Último contato:</p>
                        <p className="text-sm font-medium">
                          {new Date(device.last_seen).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Data Tab */}
        {activeTab === 'data' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b flex items-center justify-between">
              <h2 className="text-xl font-semibold text-gray-900">Dados dos Dispositivos</h2>
              <button
                onClick={() => setShowRawData(!showRawData)}
                className="flex items-center gap-2 px-3 py-1 text-sm bg-gray-100 rounded-md hover:bg-gray-200"
              >
                {showRawData ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                {showRawData ? 'Ocultar Raw' : 'Mostrar Raw'}
              </button>
            </div>
            <div className="p-6 max-h-96 overflow-y-auto">
              {deviceData.length === 0 ? (
                <div className="text-center py-8">
                  <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">Nenhum dado recebido</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {deviceData.slice().reverse().map((data, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {getDeviceIcon(data.device_id || '')}
                          <span className="font-medium">{data.device_id || data.device_address}</span>
                          {getSecurityStatusIcon(data.encrypted, data.hash_valid, data.signature_valid)}
                        </div>
                        <span className="text-sm text-gray-600">
                          {new Date(data.timestamp).toLocaleString()}
                        </span>
                      </div>
                      
                      {data.encrypted && (
                        <div className="mb-2">
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                            <Lock className="w-3 h-3" />
                            Criptografado
                          </span>
                        </div>
                      )}

                      {data.hash_valid !== undefined && (
                        <div className="mb-2">
                          <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded ${
                            data.hash_valid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            <Hash className="w-3 h-3" />
                            Hash {data.hash_valid ? 'Válido' : 'Inválido'}
                          </span>
                        </div>
                      )}

                      {data.signature_valid !== undefined && (
                        <div className="mb-2">
                          <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded ${
                            data.signature_valid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            <Key className="w-3 h-3" />
                            Assinatura {data.signature_valid ? 'Válida' : 'Inválida'}
                          </span>
                        </div>
                      )}

                      <div className="bg-gray-50 rounded p-3 text-sm">
                        {data.decrypted_data ? (
                          <pre>{JSON.stringify(data.decrypted_data, null, 2)}</pre>
                        ) : showRawData ? (
                          <pre>{JSON.stringify(data, null, 2)}</pre>
                        ) : (
                          <p>{data.data || 'Dados não disponíveis'}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Security Tab */}
        {activeTab === 'security' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b">
              <h2 className="text-xl font-semibold text-gray-900">Logs de Segurança</h2>
            </div>
            <div className="p-6 max-h-96 overflow-y-auto">
              {securityLogs.length === 0 ? (
                <div className="text-center py-8">
                  <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">Nenhum log de segurança</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {securityLogs.slice().reverse().map((log, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${
                          log.encrypted ? 'bg-green-500' : 'bg-yellow-500'
                        }`}></div>
                        <div>
                          <p className="font-medium text-sm">{log.device}</p>
                          <p className="text-xs text-gray-600">{log.action}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {log.encrypted && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                            <Lock className="w-3 h-3" />
                            Criptografado
                          </span>
                        )}
                        {log.hash_valid && (
                          <CheckCircle className="w-4 h-4 text-green-500" />
                        )}
                        {log.signature_valid && (
                          <Key className="w-4 h-4 text-green-500" />
                        )}
                        <span className="text-xs text-gray-600">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Crypto Tab */}
        {activeTab === 'crypto' && (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Teste de Criptografia</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Dados para criptografar:
                  </label>
                  <input
                    type="text"
                    value={cryptoTest.data}
                    onChange={(e) => setCryptoTest(prev => ({ ...prev, data: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Digite os dados para testar..."
                  />
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={handleEncrypt}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    <Lock className="w-4 h-4" />
                    Criptografar
                  </button>
                  <button
                    onClick={handleDecrypt}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                    disabled={!cryptoTest.encrypted}
                  >
                    <Key className="w-4 h-4" />
                    Descriptografar
                  </button>
                  <button
                    onClick={handleSign}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                  >
                    <Hash className="w-4 h-4" />
                    Assinar
                  </button>
                </div>

                {cryptoTest.encrypted && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Dados criptografados:
                    </label>
                    <textarea
                      value={cryptoTest.encrypted}
                      readOnly
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-sm font-mono"
                      rows={3}
                    />
                  </div>
                )}

                {cryptoTest.decrypted && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Dados descriptografados:
                    </label>
                    <input
                      type="text"
                      value={cryptoTest.decrypted}
                      readOnly
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-green-50"
                    />
                  </div>
                )}

                {cryptoTest.signature && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Assinatura digital:
                    </label>
                    <textarea
                      value={cryptoTest.signature}
                      readOnly
                      className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-sm font-mono"
                      rows={3}
                    />
                  </div>
                )}
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Algoritmos Implementados</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">Criptografia Simétrica</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• AES-256-GCM</li>
                    <li>• ChaCha20-Poly1305</li>
                    <li>• Salsa20</li>
                  </ul>
                </div>
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">Criptografia Assimétrica</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• RSA-2048</li>
                    <li>• ECDSA</li>
                    <li>• Ed25519</li>
                  </ul>
                </div>
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">Funções Hash</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• SHA-256</li>
                    <li>• SHA-3</li>
                    <li>• BLAKE2b</li>
                  </ul>
                </div>
                <div className="p-4 border rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-2">Protocolos</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• TLS 1.3</li>
                    <li>• MQTT-S</li>
                    <li>• CoAP-DTLS</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default IoTSecurityDashboard;