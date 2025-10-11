import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

function SimpleApp() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="*" element={
          <div style={{ padding: '50px', textAlign: 'center' }}>
            <h1>React App is Working!</h1>
            <p>This is a simple test without any context providers.</p>
            <p>Current path: {window.location.pathname}</p>
          </div>
        } />
      </Routes>
    </BrowserRouter>
  )
}

export default SimpleApp