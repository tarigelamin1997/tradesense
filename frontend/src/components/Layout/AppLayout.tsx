import React, { useEffect } from 'react';
import Navbar from './Navbar';
import { accessibility } from '../../utils/accessibility';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  useEffect(() => {
    // Add skip link for accessibility
    accessibility.addSkipLink();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main 
        id="main-content" 
        className="main-content"
        role="main"
        aria-label="Main content area"
      >
        {children}
      </main>
    </div>
  );
};

export default AppLayout;