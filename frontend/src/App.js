import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import '@/App.css';
import ChatInterface from './pages/ChatInterface';
import Dashboard from './pages/Dashboard';
import ProjectView from './pages/ProjectView';
import BackendLogs from './pages/BackendLogs';
import CostVisualization from './components/CostVisualization';
import Status from './pages/Status';
import { RunProvider } from './contexts/RunContext';

function App() {
  return (
    <div className="App">
      <RunProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<ChatInterface />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/project/:id" element={<ProjectView />} />
            <Route path="/logs" element={<BackendLogs />} />
            <Route path="/costs" element={<CostVisualization />} />
            <Route path="/status" element={<Status />} />
          </Routes>
        </BrowserRouter>
      </RunProvider>
    </div>
  );
}

export default App;