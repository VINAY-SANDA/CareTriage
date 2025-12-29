import React from 'react';

/**
 * Header Component
 */
export default function Header() {
  return (
    <header className="header">
      <div className="container header-content">
        <div className="logo">
          <div className="logo-icon">🏥</div>
          <span className="logo-text">AI Clinical Pipeline</span>
        </div>
        <nav className="nav-links">
          <a href="#" className="nav-link active">Chat</a>
          <a href="#" className="nav-link">About</a>
          <a href="#" className="nav-link">Help</a>
        </nav>
      </div>
    </header>
  );
}
