import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import AddResident from './pages/AddResident';
import ResidentsList from './pages/ResidentsList';
import AidForm from './pages/AidForm';
import AidHistory from './pages/AidHistory';
import Statistics from './pages/Statistics';
import Settings from './pages/Settings';
import Dashboard from './pages/Dashboard';
import ChildrenRecord from './pages/ChildrenRecord';
import Notifications from './components/Notifications';
import AdminDashboard from './pages/AdminDashboard';
import { Toaster } from 'react-hot-toast';

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/service-worker.js') 
      .then((registration) => {
        console.log('Service Worker registered with scope:', registration.scope);
      })
      .catch((error) => {
        console.log('Service Worker registration failed:', error);
      });
  });
}

const PrivateRoute = ({ children }) => {
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  return isLoggedIn ? children : <Navigate to="/dash" />;
};

function App() {
  return (
    <Router>
      <Navbar />
      <div style={{ marginTop: '80px' }}>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/add" element={<PrivateRoute><AddResident /></PrivateRoute>} />
          <Route path="/residents" element={<PrivateRoute><ResidentsList /></PrivateRoute>} />
          <Route path="/aid" element={<PrivateRoute><AidForm /></PrivateRoute>} />
          <Route path="/history" element={<PrivateRoute><AidHistory /></PrivateRoute>} />
          <Route path="/Child" element={<PrivateRoute><ChildrenRecord /></PrivateRoute>} />
          <Route path="/stats" element={<PrivateRoute><Statistics /></PrivateRoute>} />
          <Route path="/dash" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/admin-dashboard" element={<AdminDashboard />} />
          <Route path="/settings" element={<PrivateRoute><Settings /><Toaster position="top-center" reverseOrder={false} /></PrivateRoute>} />
          <Route path="/notifications" element={<PrivateRoute><Notifications /></PrivateRoute>} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
