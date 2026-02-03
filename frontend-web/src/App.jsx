import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { Bar, Pie } from 'react-chartjs-2';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import './App.css';

// Register ChartJS components
ChartJS.register(
  CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement
);

function App() {
  // --- State ---
  // Intro State
  const [showIntro, setShowIntro] = useState(true);

  // Persistence: Initialize state from localStorage
  const [authToken, setAuthToken] = useState(localStorage.getItem('authToken') || '');
  const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('authToken'));
  const [username, setUsername] = useState(localStorage.getItem('username') || '');
  
  const [isRegistering, setIsRegistering] = useState(false);
  const [password, setPassword] = useState('');
  
  const [file, setFile] = useState(null);
  const [data, setData] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);

  // --- Effect: Load history on login ---
  useEffect(() => {
    if (isLoggedIn && authToken) {
      fetchHistory();
    }
  }, [isLoggedIn, authToken]);

  const fetchHistory = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:8000/api/upload/', {
        headers: { 'Authorization': `Token ${authToken}` }
      });
      setHistory(res.data.history);
    } catch (err) {
      console.error("Failed to fetch history", err);
    }
  };

  // --- Auth Handler ---
  const handleAuth = async (e) => {
    e.preventDefault();
    setError('');

    if (!username || !password) {
      setError('Please enter both username and password.');
      return;
    }

    const endpoint = isRegistering ? 'register/' : 'login/';
    const url = `http://127.0.0.1:8000/api/${endpoint}`;

    try {
      const response = await axios.post(url, {
        username: username,
        password: password
      });

      if (response.status === 200) {
        const token = response.data.token;
        const user = response.data.username;

        setAuthToken(token);
        setIsLoggedIn(true);
        setUsername(user);
        setError('');
        
        localStorage.setItem('authToken', token);
        localStorage.setItem('username', user);
      }
    } catch (err) {
      console.error(err);
      if (err.response && err.response.data) {
        const msg = err.response.data.error || JSON.stringify(err.response.data);
        setError(`Error: ${msg}`);
      } else {
        setError('Connection to backend failed.');
      }
    }
  };

  // --- Logout Handler ---
  const handleLogout = () => {
    setIsLoggedIn(false);
    setUsername('');
    setPassword('');
    setAuthToken('');
    setData([]);
    setStats(null);
    setHistory([]);
    setFile(null);
    setIsRegistering(false); 
    setShowIntro(true); // Show intro again on logout

    localStorage.removeItem('authToken');
    localStorage.removeItem('username');
  };

  // --- History Handler ---
  const loadHistoryItem = async (id) => {
    setLoading(true);
    try {
      const res = await axios.get(`http://127.0.0.1:8000/api/history/${id}/`, {
         headers: { 'Authorization': `Token ${authToken}` }
      });
      setData(res.data.data);
      setStats(res.data.stats);
      setError('');
    } catch (err) {
      console.error(err);
      setError('Failed to load history item.');
    }
    setLoading(false);
  };

  // --- File Handler ---
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError('');
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a CSV file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    try {
      const res = await axios.post('http://127.0.0.1:8000/api/upload/', formData, {
        headers: { 
          'Content-Type': 'multipart/form-data',
          'Authorization': `Token ${authToken}` 
        }
      });

      setData(res.data.data);
      setStats(res.data.stats);
      setHistory(res.data.history);
      setError('');
    } catch (err) {
      console.error(err);
      if (err.response && err.response.status === 403) {
        setError('Session expired or invalid. Please logout and login again.');
      } else {
        setError('Upload failed. Is the Django server running?');
      }
    }
    setLoading(false);
  };

  // --- PDF Generator ---
  const generatePDF = () => {
    const doc = new jsPDF();
    doc.text("Chemical Equipment Report", 14, 20);
    doc.setFontSize(10);
    doc.text(`Generated on: ${new Date().toLocaleString()}`, 14, 28);
    
    if (stats) {
      doc.text(`Total Count: ${stats.total_count}`, 14, 40);
      doc.text(`Avg Pressure: ${stats.avg_pressure} psi`, 14, 46);
      doc.text(`Avg Temperature: ${stats.avg_temp} C`, 14, 52);
    }

    const tableColumn = ["Name", "Type", "Pressure", "Temp", "Status"];
    const tableRows = [];

    data.forEach(row => {
      const rowData = [
        row['Equipment Name'] || row.name,
        row['Type'] || row.type,
        row['Pressure'] || row.pressure,
        row['Temperature'] || row.temp,
        row.Status || 'UNKNOWN'
      ];
      tableRows.push(rowData);
    });

    autoTable(doc, {
      head: [tableColumn],
      body: tableRows,
      startY: 60,
    });

    doc.save("equipment_report.pdf");
  };

  // --- Chart Data ---
  const barChartData = {
    labels: data.map(d => d['Equipment Name'] || d.name),
    datasets: [
      {
        label: 'Pressure (psi)',
        data: data.map(d => d['Pressure'] || d.pressure),
        backgroundColor: 'rgba(53, 162, 235, 0.5)',
      },
      {
        label: 'Temperature (C)',
        data: data.map(d => d['Temperature'] || d.temp),
        backgroundColor: 'rgba(255, 99, 132, 0.5)',
      },
    ],
  };

  const getPieData = () => {
    if (!stats || !stats.type_distribution) return { labels: [], datasets: [] };
    return {
      labels: Object.keys(stats.type_distribution),
      datasets: [
        {
          data: Object.values(stats.type_distribution),
          backgroundColor: [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'
          ],
        },
      ],
    };
  };

  // --- Chart Options ---
  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      },
    },
  };

  // --- 1. Intro Page View ---
  if (showIntro) {
    return (
      <div className="intro-container">
        <div className="intro-content">
          <div className="logo-icon">⚗️</div>
          <h1>ChemVis Pro</h1>
          <h2>Chemical Equipment Parameter Visualizer</h2>
          
          <p className="intro-text">
            A comprehensive hybrid solution for monitoring, analyzing, and reporting on chemical equipment performance.
            Seamlessly visualize data across Web and Desktop environments.
          </p>

          <div className="feature-grid">
            <div className="feature-item">
              <span>📊</span>
              <h3>Real-Time Analytics</h3>
              <p>Visualize Pressure vs. Temperature correlations instantly.</p>
            </div>
            <div className="feature-item">
              <span>🛡️</span>
              <h3>Health Monitoring</h3>
              <p>Automatic detection of critical parameter violations.</p>
            </div>
            <div className="feature-item">
              <span>📂</span>
              <h3>Secure History</h3>
              <p>Track uploads and generate PDF reports for compliance.</p>
            </div>
          </div>

          <button className="start-btn" onClick={() => setShowIntro(false)}>
            {isLoggedIn ? "Go to Dashboard" : "Login / Register"}
          </button>
        </div>
      </div>
    );
  }

  // --- 2. Login View ---
  if (!isLoggedIn) {
    return (
      <div className="login-container">
        <div className="login-box">
          <div className="login-header">
            <h2>{isRegistering ? 'Create Account' : 'Welcome Back'}</h2>
            <p>Please enter your details to continue</p>
          </div>
          <form onSubmit={handleAuth}>
            <input 
              type="text" placeholder="Username" 
              value={username} onChange={e => setUsername(e.target.value)} 
            />
            <input 
              type="password" placeholder="Password" 
              value={password} onChange={e => setPassword(e.target.value)} 
            />
            <button type="submit" style={{ backgroundColor: isRegistering ? '#27ae60' : '#3498db' }}>
              {isRegistering ? 'Create Account' : 'Login'}
            </button>
            {error && <p className="error-text">{error}</p>}
            <p style={{ marginTop: '15px', fontSize: '0.9rem', color: '#666' }}>
              {isRegistering ? "Already have an account?" : "Don't have an account?"}
              <span 
                onClick={() => { setIsRegistering(!isRegistering); setError(''); }}
                style={{ color: '#3498db', cursor: 'pointer', marginLeft: '5px', fontWeight: 'bold' }}
              >
                {isRegistering ? 'Login here' : 'Register here'}
              </span>
            </p>
          </form>
        </div>
      </div>
    );
  }

  // --- 3. Dashboard View ---
  return (
    <div className="app-container">
      <header className="navbar">
        <h1>⚗️ ChemVis Pro</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <span style={{ fontSize: '0.9rem' }}>Welcome, <strong>{username}</strong></span>
          <button className="logout-btn" onClick={handleLogout}>Logout</button>
        </div>
      </header>

      <main className="main-content">
        <section className="controls">
          <div className="card upload-card">
            <h3>📂 Upload CSV</h3>
            <input type="file" onChange={handleFileChange} accept=".csv" />
            <button onClick={handleUpload} disabled={loading}>
              {loading ? 'Processing...' : 'Upload & Analyze'}
            </button>
            {error && <p className="error-text">{error}</p>}
          </div>

          <div className="card history-card">
            <h3>📜 History</h3>
            <ul className="history-list">
              {history.map((h, i) => (
                <li key={h.id || i} onClick={() => loadHistoryItem(h.id)} className="history-item">
                  <div style={{display:'flex', flexDirection:'column'}}>
                    <span className="file-name">{h.file_name}</span>
                    <span className="file-date">{new Date(h.uploaded_at).toLocaleDateString()}</span>
                  </div>
                </li>
              ))}
              {history.length === 0 && <small style={{color:'#999'}}>No history yet</small>}
            </ul>
          </div>
        </section>

        <section className="analytics">
          {stats && (
            <div className="kpi-row">
              <div className="kpi-card">
                <h4>Total Equipment</h4>
                <p>{stats.total_count}</p>
              </div>
              <div className="kpi-card">
                <h4>Avg Pressure</h4>
                <p>{stats.avg_pressure} <small>psi</small></p>
              </div>
              <div className="kpi-card">
                <h4>Avg Temp</h4>
                <p>{stats.avg_temp} <small>°C</small></p>
              </div>
              <div className="kpi-card action-card" onClick={generatePDF}>
                <h4>📄 Download Report</h4>
                <p>Click to PDF</p>
              </div>
            </div>
          )}

          {data.length > 0 ? (
            <div className="charts-grid">
              <div className="chart-card">
                <h4>Pressure vs Temperature</h4>
                <Bar data={barChartData} />
              </div>
              <div className="chart-card">
                <h4>Equipment Type Distribution</h4>
                <div className="pie-container" style={{ position: 'relative', height: '300px', width: '100%' }}>
                  <Pie data={getPieData()} options={pieOptions} />
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <p>Upload a CSV file to view analytics.</p>
            </div>
          )}

          {data.length > 0 && (
            <div className="data-table-card">
              <h3>Live Data Grid</h3>
              <div className="table-responsive">
                <table>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Type</th>
                      <th>Pressure</th>
                      <th>Temp</th>
                      <th>Health Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.map((row, idx) => (
                      <tr key={idx}>
                        <td>{row['Equipment Name'] || row.name}</td>
                        <td>{row['Type'] || row.type}</td>
                        <td>{row['Pressure'] || row.pressure}</td>
                        <td>{row['Temperature'] || row.temp}</td>
                        <td>
                          <span className={`badge ${row.Status}`}>
                            {row.Status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;