import React from 'react';

export interface HeaderProps {
  title: string;
  subtitle?: string;
}

/**
 * Top navigation and banner header component.
 */
export const Header: React.FC<HeaderProps> = ({ title, subtitle }) => {
  return (
    <header className="app-header">
      <div className="header-container">
        <h1>{title}</h1>
        {subtitle && <p className="header-subtitle">{subtitle}</p>}
      </div>
    </header>
  );
};
