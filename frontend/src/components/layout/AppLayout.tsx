import React, { useState } from 'react';
import { useUIStore } from '@/stores/uiStore';
import { useAuth } from '@/hooks/useAuth';
import { Link } from 'react-router-dom';
import { Menu, X, Home, Package, Film, Settings, LogOut } from 'lucide-react';

const AppLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const { user, logout } = useAuth();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navItems = [
    { name: 'Dashboard', icon: Home, path: '/dashboard' },
    { name: 'Products', icon: Package, path: '/products' },
    { name: 'Videos', icon: Film, path: '/videos' },
    { name: 'Settings', icon: Settings, path: '/settings' },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile menu button */}
      <div className="fixed top-4 left-4 z-50 md:hidden">
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 rounded-md text-gray-700 bg-white shadow-md"
        >
          {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Sidebar - Desktop */}
      <aside 
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } md:translate-x-0 md:static md:inset-0`}
      >
        <div className="flex items-center justify-between p-4 border-b">
          <h1 className="text-xl font-bold text-primary-600">AI Video Platform</h1>
          <button 
            onClick={toggleSidebar}
            className="md:hidden p-1 rounded-md text-gray-700 hover:bg-gray-100"
          >
            <X size={24} />
          </button>
        </div>
        
        <nav className="p-4">
          <ul className="space-y-2">
            {navItems.map((item) => (
              <li key={item.name}>
                <Link
                  to={item.path}
                  className="flex items-center p-3 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
                  onClick={() => {
                    if (window.innerWidth < 768) {
                      setIsMobileMenuOpen(false);
                    }
                  }}
                >
                  <item.icon className="mr-3" size={20} />
                  <span>{item.name}</span>
                </Link>
              </li>
            ))}
          </ul>
          
          <div className="mt-8 pt-4 border-t">
            <div className="flex items-center p-3">
              <div className="mr-3 bg-gray-200 border-2 border-dashed rounded-xl w-10 h-10" />
              <div>
                <p className="font-medium">{user?.email}</p>
                <button 
                  onClick={logout}
                  className="flex items-center text-sm text-error-600 hover:text-error-800 mt-1"
                >
                  <LogOut size={16} className="mr-1" />
                  Logout
                </button>
              </div>
            </div>
          </div>
        </nav>
      </aside>

      {/* Mobile sidebar overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 z-30 bg-black bg-opacity-50 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        ></div>
      )}

      {/* Mobile sidebar */}
      {isMobileMenuOpen && (
        <div className="fixed top-0 left-0 right-0 z-40 w-full h-auto bg-white shadow-lg md:hidden">
          <div className="p-4">
            <div className="flex flex-col space-y-4">
              {navItems.map((item) => (
                <Link
                  key={item.name}
                  to={item.path}
                  className="flex items-center p-3 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <item.icon className="mr-3" size={20} />
                  <span>{item.name}</span>
                </Link>
              ))}
              <button 
                onClick={logout}
                className="flex items-center p-3 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <LogOut className="mr-3" size={20} />
                Logout
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="flex-1 overflow-auto md:ml-0 transition-all duration-300">
        <div className="p-4 md:p-6">
          {children}
        </div>
      </main>
    </div>
  );
};

export default AppLayout;