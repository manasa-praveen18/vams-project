import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

const API = 'http://localhost:8000';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#ff7f7f', '#a4de6c', '#d0ed57'];

function ResourceAlerts({ alerts }) {
  if (!alerts || alerts.length === 0) return (
    <div style={{ ...cardStyle, borderLeft: '4px solid #00C49F', marginBottom: '20px' }}>
      <p style={{ margin: 0, color: '#00C49F', fontWeight: 'bold' }}>✓ No resource spikes in the last hour</p>
    </div>
  );

  const color = (type) => type === 'CPU' ? '#0088FE' : type === 'Memory' ? '#FF8042' : '#ffcc00';

  return (
    <div style={{ ...cardStyle, marginBottom: '20px', borderLeft: '4px solid #FF4444' }}>
      <h3 style={{ ...cardTitle, color: '#FF4444', marginBottom: '12px' }}>⚠ Resource Spike Alerts (Last Hour)</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {alerts.map((a, i) => (
          <div key={i} style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            backgroundColor: '#fff8f8', padding: '8px 12px', borderRadius: '6px',
            borderLeft: `3px solid ${color(a.type)}`
          }}>
            <span style={{ fontWeight: 'bold', color: color(a.type) }}>{a.type}</span>
            <span>{a.app.replace('.exe', '')}</span>
            <span style={{ color: '#FF4444', fontWeight: 'bold' }}>{a.value}% (threshold: {a.threshold}%)</span>
            <span style={{ color: '#999', fontSize: '12px' }}>{a.time}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
function Overview({ data }) {
  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '20px', marginBottom: '30px' }}>
        <div style={cardStyle}>
          <h3 style={cardTitle}>Active Users Today</h3>
          <p style={cardValue}>{data.active_users_today}</p>
        </div>
        <div style={cardStyle}>
          <h3 style={cardTitle}>Total Apps Tracked</h3>
          <p style={cardValue}>{data.total_apps}</p>
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
      <div style={{ marginTop: '20px' }}>
        <a 
          href={`${API}/api/reports/activity-csv`}
          download="activity_report.csv"
          style={{
            backgroundColor: '#0088FE',
            color: 'white',
            padding: '10px 20px',
            borderRadius: '4px',
            textDecoration: 'none',
            fontSize: '14px'
          }}
        >
          Download Activity Report (CSV)
        </a>
      </div>
    </div>
  );
}

function TopAppsBar({ data, period, onPeriodChange }) {
  const formatted = data.map(d => ({
    name: d.app_name.replace('.exe', ''),
    minutes: Math.round(d.total_duration / 60)
  }));

  return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <h3 style={{ ...cardTitle, margin: 0 }}>Top Applications (minutes)</h3>
        <select
          value={period}
          onChange={e => onPeriodChange(e.target.value)}
          style={{
            background: '#2a2a4a',
            color: 'white',
            border: '1px solid #444',
            padding: '5px 10px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '13px'
          }}
        >
          <option value="">All Time</option>
          <option value="day">Today</option>
          <option value="week">This Week</option>
          <option value="month">This Month</option>
        </select>
      </div>
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

function Devices({ data, sessionHistory }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
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
      <div style={cardStyle}>
        <h3 style={cardTitle}>Login/Logout History</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ backgroundColor: '#f0f0f0' }}>
              <th style={thStyle}>Login Time</th>
              <th style={thStyle}>Logout Time</th>
              <th style={thStyle}>Duration</th>
            </tr>
          </thead>
          <tbody>
            {sessionHistory.map((s, index) => (
              <tr key={index}>
                <td style={tdStyle}>{new Date(s.login_time + 'Z').toLocaleString()}</td>
                <td style={tdStyle}>{s.logout_time === 'Still active' ? <span style={{ color: '#00C49F' }}>Still active</span> : new Date(s.logout_time + 'Z').toLocaleString()}</td>
                <td style={tdStyle}>{s.duration_minutes ? `${s.duration_minutes} min` : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
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
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
        <div style={cardStyle}>
          <h3 style={cardTitle}>Current Application</h3>
          <p style={cardValue}>{data.current_app || 'No data'}</p>
          <p style={{ margin: '5px 0 0 0', color: '#666', fontSize: '12px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{data.window_title}</p>
        </div>
        <div style={cardStyle}>
          <h3 style={cardTitle}>Current User</h3>
          <p style={cardValue}>{data.username || 'Unknown'}</p>
          <p style={{ margin: '5px 0 0 0', color: '#666', fontSize: '12px' }}>{data.device_name}</p>
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
function TopTitlesBar({ data, period, onPeriodChange }) {
  return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <h3 style={{ ...cardTitle, margin: 0 }}>Top Window Titles</h3>
        <select
          value={period}
          onChange={e => onPeriodChange(e.target.value)}
          style={{
            background: '#2a2a4a',
            color: 'white',
            border: '1px solid #444',
            padding: '5px 10px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '13px'
          }}
        >
          <option value="day">Today</option>
          <option value="week">This Week</option>
          <option value="month">This Month</option>
          <option value="">All Time</option>
        </select>
      </div>
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={data} layout="vertical" margin={{ left: 20, right: 40 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" unit=" min" />
          <YAxis type="category" dataKey="title" width={220} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v) => `${v} min`} />
          <Bar dataKey="minutes" fill="#8884d8" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

const CATEGORY_COLORS = {
  "Teams Meeting": "#FF4444",
  "Communication": "#FF8042",
  "Development": "#0088FE",
  "Browser - Work": "#00C49F",
  "Browser - Entertainment": "#FFBB28",
  "Documents": "#A28DFF",
  "System": "#888888",
  "Other": "#cccccc"
};

function CategoryBreakdown({ data, period, onPeriodChange }) {
  const colored = data.map(d => ({ ...d, fill: CATEGORY_COLORS[d.category] || "#aaa" }));
  return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <h3 style={{ ...cardTitle, margin: 0 }}>Activity Categories</h3>
        <select
          value={period}
          onChange={e => onPeriodChange(e.target.value)}
          style={{
            background: '#2a2a4a',
            color: 'white',
            border: '1px solid #444',
            padding: '5px 10px',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '13px'
          }}
        >
          <option value="day">Today</option>
          <option value="week">This Week</option>
          <option value="month">This Month</option>
          <option value="">All Time</option>
        </select>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie data={colored} dataKey="minutes" nameKey="category" cx="50%" cy="50%" outerRadius={100}
            label={({ category, percent }) => `${category} ${(percent * 100).toFixed(0)}%`}>
            {colored.map((entry, i) => (
              <Cell key={i} fill={entry.fill} />
            ))}
          </Pie>
          <Tooltip formatter={(v) => `${v} min`} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
function Analytics({ topApps, dailyUsage, heatmapData, timelineData, weeklyTrends, topTitles, categories, topTitlesPeriod, setTopTitlesPeriod, categoriesPeriod, setCategoriesPeriod   }) {
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
        <Heatmap data={heatmapData} />
        <Timeline data={timelineData} />
        <WeeklyTrends data={weeklyTrends} />
        <TopTitlesBar data={topTitles} period={topTitlesPeriod} onPeriodChange={setTopTitlesPeriod} />
        <CategoryBreakdown data={categories} period={categoriesPeriod} onPeriodChange={setCategoriesPeriod} />
      </div>
    </div>
  );
}
function Heatmap({ data }) {
  const dates = [...new Set(data.map(d => d.date))].sort();
  const hours = Array.from({ length: 24 }, (_, i) => i);
  
  const getColor = (minutes) => {
    if (!minutes) return '#f0f0f0';
    if (minutes < 5) return '#c6e48b';
    if (minutes < 15) return '#7bc96f';
    if (minutes < 30) return '#239a3b';
    return '#196127';
  };

  const getValue = (date, hour) => {
    const entry = data.find(d => d.date === date && d.hour === hour);
    return entry ? entry.duration_minutes : 0;
  };

  return (
    <div style={cardStyle}>
      <h3 style={cardTitle}>Active Hours Heatmap (minutes per hour)</h3>
      <div style={{ overflowX: 'auto' }}>
        <div style={{ display: 'flex', marginBottom: '5px', marginLeft: '60px' }}>
          {hours.map(h => (
            <div key={h} style={{ width: '40px', textAlign: 'center', fontSize: '10px', color: '#666' }}>
              {h}
            </div>
          ))}
        </div>
        {dates.map(date => (
          <div key={date} style={{ display: 'flex', alignItems: 'center', marginBottom: '4px' }}>
            <div style={{ width: '70px', fontSize: '12px', color: '#666' }}>{date.slice(5)}</div>
            {hours.map(hour => (
              <div
                key={hour}
                style={{
                  width: '38px',
                  height: '25px',
                  backgroundColor: getColor(getValue(date, hour)),
                  margin: '1px',
                  borderRadius: '3px',
                  cursor: 'pointer',
                  title: `${getValue(date, hour)} min`
                }}
                title={`${date} ${hour}:00 — ${getValue(date, hour)} min`}
              />
            ))}
          </div>
        ))}
        <div style={{ display: 'flex', gap: '10px', marginTop: '10px', alignItems: 'center', fontSize: '12px', color: '#666' }}>
          <span>Less</span>
          {['#f0f0f0', '#c6e48b', '#7bc96f', '#239a3b', '#196127'].map(c => (
            <div key={c} style={{ width: '15px', height: '15px', backgroundColor: c, borderRadius: '2px' }} />
          ))}
          <span>More</span>
        </div>
      </div>
    </div>
  );
}
const generateColor = (str) => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const h = Math.abs(hash) % 360;
  return `hsl(${h}, 65%, 50%)`;
};

function Timeline({ data }) {
  const getColor = (app) => generateColor(app);
  const uniqueApps = [...new Set(data.map(d => d.app))];

  return (
    <div style={cardStyle}>
      <h3 style={cardTitle}>Today's Activity Timeline</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '500px', overflowY: 'auto' }}>
        {data.map((entry, index) => (
          <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ width: '80px', fontSize: '11px', color: '#666', flexShrink: 0, minWidth: '80px' }}>
              {entry.start}
            </div>
            <div style={{
              height: '24px',
              width: `${Math.max(entry.duration * 2, 4)}px`,
              backgroundColor: getColor(entry.app),
              borderRadius: '3px',
              minWidth: '4px',
              flexShrink: 0
            }} title={`${entry.app} — ${entry.duration}s`} />
            <div style={{ fontSize: '11px', color: '#333', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {entry.app} {entry.duration > 10 ? `(${entry.duration}s)` : ''}
            </div>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: '15px', marginTop: '15px', flexWrap: 'wrap' }}>
        {uniqueApps.map(app => (
          <div key={app} style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '12px' }}>
            <div style={{ width: '12px', height: '12px', backgroundColor: generateColor(app), borderRadius: '2px' }} />
            {app}
          </div>
        ))}
      </div>
    </div>
  );
}
function IdleReport({ data }) {
  if (!data.daily) return null;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
        <div style={cardStyle}>
          <h3 style={cardTitle}>Total Hours</h3>
          <p style={cardValue}>{data.total_hours}h</p>
        </div>
        <div style={cardStyle}>
          <h3 style={cardTitle}>Active Hours</h3>
          <p style={{ ...cardValue, color: '#00C49F' }}>{data.active_hours}h</p>
        </div>
        <div style={cardStyle}>
          <h3 style={cardTitle}>Idle Hours</h3>
          <p style={{ ...cardValue, color: '#FF8042' }}>{data.idle_hours}h</p>
        </div>
        <div style={cardStyle}>
          <h3 style={cardTitle}>Idle Percentage</h3>
          <p style={{ ...cardValue, color: '#FF8042' }}>{data.idle_percentage}%</p>
        </div>
      </div>
      <div style={cardStyle}>
        <h3 style={cardTitle}>Daily Idle Sessions</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data.daily}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="total_hours" fill="#00C49F" name="Total Hours" />
            <Bar dataKey="idle_sessions" fill="#FF8042" name="Idle Sessions" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
function WeeklyTrends({ data }) {
  return (
    <div style={cardStyle}>
      <h3 style={cardTitle}>Weekly Trends (hours)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="week" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="hours" fill="#0088FE" name="Hours" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.post(`${API}/api/admin/login`, { username, password });
      localStorage.setItem('vams_token', res.data.token);
      onLogin(res.data.token);
    } catch {
      setError('Invalid username or password');
    }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0d0d1a' }}>
      <div style={{ background: '#1a1a2e', padding: '40px', borderRadius: '12px', width: '360px', boxShadow: '0 4px 20px rgba(0,0,0,0.5)' }}>
        <h2 style={{ color: 'white', textAlign: 'center', marginBottom: '8px' }}>VAMS</h2>
        <p style={{ color: '#888', textAlign: 'center', marginBottom: '30px', fontSize: '14px' }}>Admin Dashboard</p>
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={e => setUsername(e.target.value)}
          style={{ width: '100%', padding: '12px', marginBottom: '12px', borderRadius: '6px', border: '1px solid #333', background: '#0d0d1a', color: 'white', boxSizing: 'border-box' }}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleLogin()}
          style={{ width: '100%', padding: '12px', marginBottom: '16px', borderRadius: '6px', border: '1px solid #333', background: '#0d0d1a', color: 'white', boxSizing: 'border-box' }}
        />
        {error && <p style={{ color: '#FF4444', fontSize: '13px', marginBottom: '12px' }}>{error}</p>}
        <button
          onClick={handleLogin}
          disabled={loading}
          style={{ width: '100%', padding: '12px', background: '#0088FE', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '15px', fontWeight: 'bold' }}
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </div>
    </div>
  );
}
function LiveActivityTable({ data }) {
  return (
    <div style={{ ...cardStyle, marginBottom: '20px', marginTop: '20px' }}>
      <h3 style={cardTitle}>Live User Activity</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ backgroundColor: '#f0f0f0' }}>
            <th style={thStyle}>User</th>
            <th style={thStyle}>Device</th>
            <th style={thStyle}>Current App</th>
            <th style={thStyle}>Window Title</th>
            <th style={thStyle}>Status</th>
            <th style={thStyle}>Last Updated</th>
          </tr>
        </thead>
        <tbody>
          {data.map((d, i) => (
            <tr key={i}>
              <td style={tdStyle}>{d.username}</td>
              <td style={tdStyle}>{d.device_name}</td>
              <td style={tdStyle}>{d.current_app || '-'}</td>
              <td style={{ ...tdStyle, maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {d.in_call
                  ? <span style={{ color: '#0088FE', fontWeight: 'bold' }}>📹 In call with {d.call_with}</span>
                  : d.window_title || '-'}
              </td>
              <td style={tdStyle}>
                {!d.is_online
                  ? <span style={{ color: '#999' }}>🔴 Offline</span>
                  : d.is_idle
                  ? <span style={{ color: '#FF8042' }}>🟡 Idle</span>
                  : <span style={{ color: '#00C49F' }}>🟢 Active</span>}
              </td>
              <td style={{ ...tdStyle, fontSize: '12px', color: '#999' }}>{d.last_updated || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
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
  const [heatmapData, setHeatmapData] = useState([]);
  const [timelineData, setTimelineData] = useState([]);
  const [idleReport, setIdleReport] = useState({});
  const [sessionHistory, setSessionHistory] = useState([]);
  const [weeklyTrends, setWeeklyTrends] = useState([]);
  const [selectedDevice, setSelectedDevice] = useState('');
  const [users, setUsers] = useState([]);
  const [topAppsPeriod, setTopAppsPeriod] = useState('');
  const [resourceAlerts, setResourceAlerts] = useState([]);
  const [topTitles, setTopTitles] = useState([]);
  const [categories, setCategories] = useState([]);
  const [topTitlesPeriod, setTopTitlesPeriod] = useState('day');
  const [categoriesPeriod, setCategoriesPeriod] = useState('day');
  const [adminToken, setAdminToken] = useState(localStorage.getItem('vams_token'));
  const [allLiveData, setAllLiveData] = useState([]);

  useEffect(() => {
    const fetchData = () => {
      const deviceParam = selectedDevice ? `?device_id=${selectedDevice}` : '';
      axios.get(`${API}/api/analytics/overview${deviceParam}`).then(r => setOverview(r.data));
      axios.get(`${API}/api/analytics/resources${deviceParam}`).then(r => setResources(r.data));
      axios.get(`${API}/api/analytics/daily-usage${deviceParam}`).then(r => setDailyUsage(r.data));
      axios.get(`${API}/api/analytics/heatmap${deviceParam}`).then(r => setHeatmapData(r.data));
      axios.get(`${API}/api/analytics/weekly-trends${deviceParam}`).then(r => setWeeklyTrends(r.data));
      axios.get(`${API}/api/analytics/timeline${deviceParam}`).then(r => setTimelineData(r.data));
      axios.get(`${API}/api/analytics/idle-report${deviceParam}`).then(r => setIdleReport(r.data));
      axios.get(`${API}/api/live${deviceParam}`).then(r => setLiveData(r.data));
      axios.get(`${API}/api/devices/status${deviceParam}`).then(r => setDeviceStatus(r.data));
      axios.get(`${API}/api/session/history${deviceParam}`).then(r => setSessionHistory(r.data));
      axios.get(`${API}/api/users`).then(r => setUsers(r.data));
      axios.get(`${API}/api/analytics/resource-alerts${deviceParam}`).then(r => setResourceAlerts(r.data));
      axios.get(`${API}/api/live/all`).then(r => setAllLiveData(r.data));
    };
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [selectedDevice]);

  useEffect(() => {
    console.log('Fetching top apps, period:', topAppsPeriod);
    const params = new URLSearchParams();
    if (selectedDevice) params.append('device_id', selectedDevice);
    if (topAppsPeriod) params.append('period', topAppsPeriod);
    const paramStr = params.toString() ? `?${params.toString()}` : '';
    console.log('URL:', `${API}/api/analytics/top-apps${paramStr}`);
    axios.get(`${API}/api/analytics/top-apps${paramStr}`).then(r => setTopApps(r.data));
  }, [selectedDevice, topAppsPeriod]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (selectedDevice) params.append('device_id', selectedDevice);
    if (topTitlesPeriod) params.append('period', topTitlesPeriod);
    const paramStr = params.toString() ? `?${params.toString()}` : '';
    axios.get(`${API}/api/analytics/top-titles${paramStr}`).then(r => setTopTitles(r.data));
  }, [selectedDevice, topTitlesPeriod]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (selectedDevice) params.append('device_id', selectedDevice);
    if (categoriesPeriod) params.append('period', categoriesPeriod);
    const paramStr = params.toString() ? `?${params.toString()}` : '';
    axios.get(`${API}/api/analytics/categories${paramStr}`).then(r => setCategories(r.data));
  }, [selectedDevice, categoriesPeriod]);

  if (!adminToken) {
    return <LoginPage onLogin={setAdminToken} />;
  }

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      <div style={{ backgroundColor: '#1a1a2e', color: 'white', padding: '15px 30px', display: 'flex', alignItems: 'center', gap: '30px' }}>
        <h1 style={{ margin: 0, fontSize: '20px' }}>VAMS Dashboard</h1>
        {['overview', 'live', 'analytics', 'resources', 'idle', 'devices'].map(page => (
          <button key={page} onClick={() => setActivePage(page)} style={{
            background: activePage === page ? '#0088FE' : 'transparent',
            color: 'white', border: 'none', padding: '8px 16px',
            borderRadius: '4px', cursor: 'pointer', textTransform: 'capitalize'
          }}>{page}</button>
        ))}
        <select
          value={selectedDevice}
          onChange={e => setSelectedDevice(e.target.value)}
          style={{
            marginLeft: 'auto',
            background: '#2a2a4a',
            color: 'white',
            border: '1px solid #444',
            padding: '6px 12px',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          <option value="">All Devices</option>
          {deviceStatus.map(d => (
            <option key={d.id} value={d.id}>{d.device_name}</option>
          ))}
        </select>
        <button
          onClick={() => { localStorage.removeItem('vams_token'); setAdminToken(null); }}
          style={{ background: 'transparent', border: '1px solid #555', color: '#ccc', padding: '6px 14px', borderRadius: '6px', cursor: 'pointer', fontSize: '13px' }}
        >
          Logout
        </button>
      </div>

      <div style={{ padding: '30px' }}>
        {activePage === 'overview' && (
          <>
            <Overview data={overview} />
            <LiveActivityTable data={allLiveData} />
            <ResourceAlerts alerts={resourceAlerts} />
            <TopAppsBar data={topApps} period={topAppsPeriod} onPeriodChange={setTopAppsPeriod} />
          </>
        )}
        {activePage === 'resources' && <Resources data={resources} />}
        {activePage === 'devices' && <Devices data={deviceStatus} sessionHistory={sessionHistory} />}
        {activePage === 'live' && <LiveMonitoring data={liveData} />}
        {activePage === 'analytics' && <Analytics topApps={topApps} dailyUsage={dailyUsage} heatmapData={heatmapData} timelineData={timelineData} weeklyTrends={weeklyTrends} topTitles={topTitles} categories={categories} topTitlesPeriod={topTitlesPeriod} setTopTitlesPeriod={setTopTitlesPeriod} categoriesPeriod={categoriesPeriod} setCategoriesPeriod={setCategoriesPeriod} />}
        {activePage === 'idle' && <IdleReport data={idleReport} />}
      </div>
    </div>
  );
}
const cardStyle = { backgroundColor: 'white', borderRadius: '8px', padding: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' };
const cardTitle = { margin: '0 0 10px 0', color: '#666', fontSize: '14px' };
const cardValue = { margin: 0, fontSize: '32px', fontWeight: 'bold', color: '#1a1a2e' };
const thStyle = { padding: '10px', textAlign: 'left', borderBottom: '1px solid #ddd' };
const tdStyle = { padding: '10px', borderBottom: '1px solid #eee' };
