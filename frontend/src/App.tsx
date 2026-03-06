import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import ServiceDirectory from './pages/ServiceDirectory';
import Security from './pages/Security';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/security" element={<Security />} />
        <Route path="/" element={<ServiceDirectory />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
