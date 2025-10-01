import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './App.css';
import Dashboard from './Dashboard';

interface SystemStatus {
  status: string;
  files_monitored: number;
  threats_detected: number;
  backups_count: number;
  cpu_usage: number;
  memory_usage: number;
}

interface ThreatAlert {
  timestamp: string;
  score: number;
  description: string;
  file_path: string;
  threat_type: string;
}

function App() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [alerts, setAlerts] = useState<ThreatAlert[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch status every 2 seconds
    const fetchStatus = async () => {
      try {
        const response = await axios.get('/api/status');
        setStatus(response.data);
        setConnected(true);
        setError(null);
      } catch (err) {
        setConnected(false);
        setError('Unable to connect to MedGuard backend');
      }
    };

    // Fetch alerts every 3 seconds
    const fetchAlerts = async () => {
      try {
        const response = await axios.get('/api/alerts');
        setAlerts(response.data.alerts);
      } catch (err) {
        console.error('Failed to fetch alerts:', err);
      }
    };

    fetchStatus();
    fetchAlerts();

    const statusInterval = setInterval(fetchStatus, 2000);
    const alertsInterval = setInterval(fetchAlerts, 3000);

    return () => {
      clearInterval(statusInterval);
      clearInterval(alertsInterval);
    };
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1>🏥 MedGuard</h1>
          <p className="subtitle">Medical Ransomware Defense System</p>
          <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
            <span className="status-dot"></span>
            {connected ? 'System Active' : 'Disconnected'}
          </div>
        </div>
      </header>

      <main className="App-main">
        {error && (
          <div className="error-banner">
            <p>⚠️ {error}</p>
            <p className="error-help">
              Make sure the backend is running: <code>cd backend && cargo run --release</code>
            </p>
          </div>
        )}

        {status && <Dashboard status={status} alerts={alerts} />}
      </main>

      <footer className="App-footer">
        <p>MedGuard v0.1.0 - Built with Rust & React</p>
        <p>Protecting medical data with sub-millisecond response times</p>
      </footer>
    </div>
  );
}

export default App;
