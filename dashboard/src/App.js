import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

const API = 'http://localhost:8000';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#ff7f7f', '#a4de6c', '#d0ed57'];

function Overview({ data }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '30px' }}>
      <div style={cardStyle}>
        <h3 style={cardTitle}>Total Logs</h3>
        <p style={cardValue}>{data.total_logs}</p>
      </div>
      <div style={cardStyle}>
        <h3 style={cardTitle}>Hours Tracked</h3>
        <p style={cardValue}>{data.total_duration_hours}h</p>
      </div>
      <div style={cardStyle}>
        <h3 style={cardTitle}>Devices</h3>
        <p style={cardValue}>{data.total_devices}</p>
      </div>
      <div style={cardStyle}>
        <h3 style={cardTitle}>Idle Sessions</h3>
        <p style={cardValue}>{data.idle_count}</p>
      </div>
    </div>
  );
}

function TopAppsBar({ data }) {
  const formatted = data.map(d => ({
    name: d.app_name.replace('.exe', ''),
    minutes: Math.round(d.total_duration / 60)
  }));

  return (
    <div style={cardStyle}>
      <h3 style={cardTitle}>Top Applications (minutes)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="minutes" fill="#0088FE" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function TopAppsPie({ data }) {
  const formatted = data.map(d => ({
    name: d.app_name.replace('.exe', ''),
    value: Math.round(d.total_duration / 60)
  }));

  return (
    <div style={cardStyle}>
      <h3 style={cardTitle}>Application Usage Breakdown</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie data={formatted} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
            {formatted.map((_, index) => (
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

function Devices({ data }) {
  return (
    <div style={cardStyle}>
      <h3 style={cardTitle}>Registered Devices</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ backgroundColor: '#f0f0f0' }}>
            <th style={thStyle}>Device Name</th>
            <th style={thStyle}>Last Seen</th>
            <th style={thStyle}>Status</th>
          </tr>
        </thead>
        <tbody>
          {data.map(d => (
            <tr key={d.id}>
              <td style={tdStyle}>{d.device_name}</td>
              <td style={tdStyle}>{new Date(d.last_seen + 'Z').toLocaleString()}</td>
              <td style={tdStyle}>
                <span style={{
                  backgroundColor: d.status === 'Online' ? '#00C49F' : '#FF8042',
                  color: 'white',
                  padding: '3px 10px',
                  borderRadius: '12px',
                  fontSize: '12px'
                }}>{d.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
function Resources({ data }) {
  const reversed = [...data].reverse();
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={cardStyle}>
        <h3 style={cardTitle}>CPU & Memory Usage Over Time (%)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={reversed}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="cpu" stroke="#0088FE" dot={false} name="CPU %" />
            <Line type="monotone" dataKey="memory" stroke="#00C49F" dot={false} name="Memory %" />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div style={cardStyle}>
        <h3 style={cardTitle}>Network Usage Over Time (KB/s)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={reversed}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="upload" stroke="#FF8042" dot={false} name="Upload KB/s" />
            <Line type="monotone" dataKey="download" stroke="#8884d8" dot={false} name="Download KB/s" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
function LiveMonitoring({ data }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
        <div style={cardStyle}>
          <h3 style={cardTitle}>Current Application</h3>
          <p style={cardValue}>{data.current_app || 'No data'}</p>
          <p style={{ margin: '5px 0 0 0', color: '#666', fontSize: '12px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{data.window_title}</p>
        </div>
        <div style={cardStyle}>
          <h3 style={cardTitle}>Status</h3>
          <p style={{ ...cardValue, color: data.is_idle ? '#FF8042' : '#00C49F' }}>
            {data.is_idle ? 'Idle' : 'Active'}
          </p>
          <p style={{ margin: '5px 0 0 0', color: '#666', fontSize: '12px' }}>Last updated: {data.last_updated}</p>
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
        <div style={cardStyle}>
          <h3 style={cardTitle}>CPU Usage</h3>
          <p style={cardValue}>{data.cpu_usage}%</p>
        </div>
        <div style={cardStyle}>
          <h3 style={cardTitle}>Memory Usage</h3>
          <p style={cardValue}>{data.memory_usage}%</p>
        </div>
        <div style={cardStyle}>
          <h3 style={cardTitle}>Upload</h3>
          <p style={cardValue}>{data.upload_kb} <span style={{ fontSize: '16px' }}>KB/s</span></p>
        </div>
        <div style={cardStyle}>
          <h3 style={cardTitle}>Download</h3>
          <p style={cardValue}>{data.download_kb} <span style={{ fontSize: '16px' }}>KB/s</span></p>
        </div>
      </div>
    </div>
  );
}
function Analytics({ topApps, dailyUsage }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={cardStyle}>
        <h3 style={cardTitle}>Application Usage Breakdown</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie data={topApps.map(d => ({ name: d.app_name.replace('.exe', ''), value: Math.round(d.total_duration / 60) }))} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label>
              {topApps.map((_, index) => (
                <Cell key={index} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div style={cardStyle}>
        <h3 style={cardTitle}>Daily Usage (hours)</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={dailyUsage}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="hours" fill="#0088FE" name="Active Hours" />
            <Bar dataKey="idle_hours" fill="#FF8042" name="Idle Hours" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div style={cardStyle}>
        <h3 style={cardTitle}>Sessions Per Day</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={dailyUsage}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="sessions" stroke="#00C49F" dot={true} name="Sessions" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function App() {
  const [overview, setOverview] = useState({});
  const [topApps, setTopApps] = useState([]);
  const [devices, setDevices] = useState([]);
  const [activePage, setActivePage] = useState('overview');
  const [resources, setResources] = useState([]);
  const [liveData, setLiveData] = useState({});
  const [dailyUsage, setDailyUsage] = useState([]);
  const [deviceStatus, setDeviceStatus] = useState([]);

  useEffect(() => {
    const fetchData = () => {
      axios.get(`${API}/api/analytics/overview`).then(r => setOverview(r.data));
      axios.get(`${API}/api/analytics/top-apps`).then(r => setTopApps(r.data));
      axios.get(`${API}/api/devices`).then(r => setDevices(r.data));
      axios.get(`${API}/api/analytics/resources`).then(r => setResources(r.data));
      axios.get(`${API}/api/live`).then(r => setLiveData(r.data));
      axios.get(`${API}/api/analytics/daily-usage`).then(r => setDailyUsage(r.data));
      axios.get(`${API}/api/devices/status`).then(r => setDeviceStatus(r.data));
    };
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      <div style={{ backgroundColor: '#1a1a2e', color: 'white', padding: '15px 30px', display: 'flex', alignItems: 'center', gap: '30px' }}>
        <h1 style={{ margin: 0, fontSize: '20px' }}>VAMS Dashboard</h1>
        {['overview', 'live', 'analytics', 'resources', 'devices'].map(page => (
          <button key={page} onClick={() => setActivePage(page)} style={{
            background: activePage === page ? '#0088FE' : 'transparent',
            color: 'white', border: 'none', padding: '8px 16px',
            borderRadius: '4px', cursor: 'pointer', textTransform: 'capitalize'
          }}>{page}</button>
        ))}
      </div>

      <div style={{ padding: '30px' }}>
        {activePage === 'overview' && (
          <>
            <Overview data={overview} />
            <TopAppsBar data={topApps} />
          </>
        )}
        {activePage === 'resources' && <Resources data={resources} />}
        {activePage === 'devices' && <Devices data={deviceStatus} />}
        {activePage === 'live' && <LiveMonitoring data={liveData} />}
        {activePage === 'analytics' && <Analytics topApps={topApps} dailyUsage={dailyUsage} />}
      </div>
    </div>
  );
}

const cardStyle = { backgroundColor: 'white', borderRadius: '8px', padding: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' };
const cardTitle = { margin: '0 0 10px 0', color: '#666', fontSize: '14px' };
const cardValue = { margin: 0, fontSize: '32px', fontWeight: 'bold', color: '#1a1a2e' };
const thStyle = { padding: '10px', textAlign: 'left', borderBottom: '1px solid #ddd' };
const tdStyle = { padding: '10px', borderBottom: '1px solid #eee' };