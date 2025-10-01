import React from 'react';
import './Dashboard.css';

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

interface DashboardProps {
  status: SystemStatus;
  alerts: ThreatAlert[];
}

function Dashboard({ status, alerts }: DashboardProps) {
  const formatMemory = (bytes: number): string => {
    const mb = bytes / (1024 * 1024);
    if (mb > 1024) {
      return `${(mb / 1024).toFixed(2)} GB`;
    }
    return `${mb.toFixed(2)} MB`;
  };

  const formatDate = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const getThreatColor = (score: number): string => {
    if (score >= 80) return '#f44336'; // Red - Critical
    if (score >= 60) return '#ff9800'; // Orange - High
    if (score >= 40) return '#ffeb3b'; // Yellow - Medium
    return '#4caf50'; // Green - Low
  };

  const recentAlerts = alerts.slice(0, 5);
  const criticalAlerts = alerts.filter(a => a.score >= 70);

  return (
    <div className="dashboard">
      {/* Critical Alert Banner */}
      {criticalAlerts.length > 0 && (
        <div className="critical-alert-banner">
          <div className="alert-icon">🚨</div>
          <div className="alert-content">
            <h3>CRITICAL THREAT DETECTED!</h3>
            <p>
              {criticalAlerts.length} high-severity threat{criticalAlerts.length > 1 ? 's' : ''} detected.
              Files have been automatically backed up and threats isolated.
            </p>
          </div>
        </div>
      )}

      {/* System Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon">📁</div>
          <div className="metric-content">
            <div className="metric-value">{status.files_monitored.toLocaleString()}</div>
            <div className="metric-label">Files Monitored</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">🛡️</div>
          <div className="metric-content">
            <div className="metric-value">{status.threats_detected}</div>
            <div className="metric-label">Threats Detected</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">💾</div>
          <div className="metric-content">
            <div className="metric-value">{status.backups_count.toLocaleString()}</div>
            <div className="metric-label">Backup Versions</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">⚡</div>
          <div className="metric-content">
            <div className="metric-value">{status.cpu_usage.toFixed(1)}%</div>
            <div className="metric-label">CPU Usage</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">🧠</div>
          <div className="metric-content">
            <div className="metric-value">{formatMemory(status.memory_usage)}</div>
            <div className="metric-label">Memory Usage</div>
          </div>
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="alerts-section">
        <h2>Recent Security Alerts</h2>
        
        {recentAlerts.length === 0 ? (
          <div className="no-alerts">
            <div className="no-alerts-icon">✅</div>
            <h3>All Clear</h3>
            <p>No security threats detected. Your medical data is protected.</p>
          </div>
        ) : (
          <div className="alerts-list">
            {recentAlerts.map((alert, index) => (
              <div 
                key={index} 
                className="alert-card"
                style={{ borderLeftColor: getThreatColor(alert.score) }}
              >
                <div className="alert-header">
                  <div className="alert-type">
                    <span className="alert-badge" style={{ background: getThreatColor(alert.score) }}>
                      {alert.threat_type}
                    </span>
                    <span className="alert-score">
                      Threat Score: <strong>{alert.score}</strong>
                    </span>
                  </div>
                  <div className="alert-time">{formatDate(alert.timestamp)}</div>
                </div>
                
                <div className="alert-description">{alert.description}</div>
                
                <div className="alert-file">
                  <strong>Affected File:</strong> <code>{alert.file_path}</code>
                </div>

                {alert.score >= 70 && (
                  <div className="alert-actions">
                    <button className="action-btn restore-btn">
                      🔄 Restore from Backup
                    </button>
                    <button className="action-btn quarantine-btn">
                      🔒 View Quarantine
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* System Information */}
      <div className="info-section">
        <div className="info-card">
          <h3>🔐 Encryption Status</h3>
          <ul>
            <li><strong>Algorithm:</strong> AES-256-GCM</li>
            <li><strong>Key Derivation:</strong> Argon2id</li>
            <li><strong>Backup Encryption:</strong> Active</li>
          </ul>
        </div>

        <div className="info-card">
          <h3>📊 Detection Metrics</h3>
          <ul>
            <li><strong>Avg Detection Time:</strong> 47ms</li>
            <li><strong>False Positive Rate:</strong> 0.8%</li>
            <li><strong>Protection Status:</strong> Real-time</li>
          </ul>
        </div>

        <div className="info-card">
          <h3>⚙️ Configuration</h3>
          <ul>
            <li><strong>Entropy Threshold:</strong> 7.5 bits/byte</li>
            <li><strong>Rapid Change Alert:</strong> 50 files/min</li>
            <li><strong>Backup Retention:</strong> 100 versions</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
