import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import './App.css';

// Constants
const MAX_ALERTS = 7;

function App() {
  // Socket and video states
  const [socketStatus, setSocketStatus] = useState('🔄 Connecting...');
  const [videoFrame, setVideoFrame] = useState('');

  // Alert states
  const [alerts, setAlerts] = useState([]);
  const [alertsReceived, setAlertsReceived] = useState(0);
  const [lastAlertTime, setLastAlertTime] = useState(null);

  // Performance states
  const [fps, setFps] = useState(0);

  // Refs for FPS calculation
  const frameCountRef = useRef(0);
  const lastTimeRef = useRef(Date.now());

  useEffect(() => {
    const socket = io('http://localhost:5000', {
      transports: ['websocket'],
      withCredentials: true
    });

    socket.on('connect', () => {
      setSocketStatus('✅ Connected to backend');
    });

    socket.on('disconnect', () => {
      setSocketStatus('❌ Disconnected');
    });

    socket.on('gas_leak_event', (data) => {
      const msg = `🚨 Alert: ${data.status}`;
      setAlerts(prev => [msg, ...prev].slice(0, MAX_ALERTS));
      setAlertsReceived(prev => prev + 1);
      setLastAlertTime(new Date().toLocaleTimeString());
    });

    socket.on('video_frame', (data) => {
      setVideoFrame(data.image);
      frameCountRef.current += 1;
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  // Calculate FPS
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      const deltaTime = (now - lastTimeRef.current) / 1000; // in seconds
      const currentFps = Math.round(frameCountRef.current / deltaTime);
      setFps(currentFps);
      frameCountRef.current = 0;
      lastTimeRef.current = now;
    }, 1000);
    return () => clearInterval(interval);
  }, []);



  return (
    <div className="App">
      <header className="App-header">
        <h1>Gas Leak Detection System</h1>
        <p>FPS: {fps} | Alerts Received: {alertsReceived} | Last Alert: {lastAlertTime || 'None'} | {socketStatus}</p>

        <div className="main-content">
          <div className="video-section">
            <h2>Monitoring Video</h2>
            {videoFrame ? (
              <img src={`data:image/jpeg;base64,${videoFrame}`} alt="Video Stream" />
            ) : (
              <p>Loading video...</p>
            )}
          </div>

          <div className="alerts">
            <h2>Detected Alerts:</h2>
            <ul>
              {alerts.length > 0 ? (
                alerts.map((alert, index) => (
                  <li key={index}>{alert}</li>
                ))
              ) : (
                <li>No alerts yet</li>
              )}
            </ul>
          </div>
        </div>
      </header>
    </div>
  );
}

export default App;
