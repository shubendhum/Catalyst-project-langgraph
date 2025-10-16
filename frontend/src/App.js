import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import '@/App.css';
import Dashboard from './pages/Dashboard';
import ProjectView from './pages/ProjectView';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/project/:id" element={<ProjectView />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;