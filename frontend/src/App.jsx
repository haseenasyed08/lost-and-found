import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Login from './pages/Login';
import ReportForm from './pages/ReportForm';
import MyReports from './pages/MyReports';
import ReportDetail from './pages/ReportDetail';
import ClaimPage from './pages/ClaimPage';
import Notifications from './pages/Notifications';
import Admin from './pages/Admin';

function PrivateRoute({ children }) {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" replace />;
}

function ModeratorRoute({ children }) {
  const token = localStorage.getItem('token');
  const role = localStorage.getItem('role');
  if (!token) return <Navigate to="/login" replace />;
  if (role !== 'moderator') return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
        <Navbar />
        <main className="flex-1">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<PrivateRoute><Home /></PrivateRoute>} />
            <Route path="/report/:type" element={<PrivateRoute><ReportForm /></PrivateRoute>} />
            <Route path="/mine" element={<PrivateRoute><MyReports /></PrivateRoute>} />
            <Route path="/reports/:id" element={<PrivateRoute><ReportDetail /></PrivateRoute>} />
            <Route path="/claim/:matchId" element={<PrivateRoute><ClaimPage /></PrivateRoute>} />
            <Route path="/notifications" element={<PrivateRoute><Notifications /></PrivateRoute>} />
            <Route path="/admin" element={<ModeratorRoute><Admin /></ModeratorRoute>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <footer className="border-t border-slate-900/80 py-6 text-center text-xs text-slate-500">
          <p>Lost & Found Intelligence Platform • Multimodal AI Matching with Verified Handovers</p>
        </footer>
      </div>
    </BrowserRouter>
  );
}
