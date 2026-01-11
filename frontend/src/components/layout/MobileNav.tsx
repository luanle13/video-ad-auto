import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Film, Settings, X } from 'lucide-react';
import { useUIStore } from '@/stores/uiStore';

interface NavItem {
  name: string;
  icon: React.ElementType;
  path: string;
}

const navItems: NavItem[] = [
  { name: 'Dashboard', icon: Home, path: '/dashboard' },
  { name: 'New Video', icon: Film, path: '/videos/new' },
  { name: 'Settings', icon: Settings, path: '/settings' },
];

const MobileNav: React.FC = () => {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const location = useLocation();

  if (!sidebarOpen) return null;

  return (
    <div className="fixed inset-0 z-50 md:hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black bg-opacity-50"
        onClick={toggleSidebar}
      ></div>

      {/* Slide-out panel */}
      <div className="relative w-64 h-full bg-white shadow-lg">
        <div className="flex items-center justify-between p-4 border-b">
          <h1 className="text-xl font-bold text-primary-600">AI Video Platform</h1>
          <button 
            onClick={toggleSidebar}
            className="p-1 rounded-md text-gray-700 hover:bg-gray-100"
          >
            <X size={24} />
          </button>
        </div>
        
        <nav className="p-4">
          <ul className="space-y-1">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              return (
                <li key={item.name}>
                  <Link
                    to={item.path}
                    className={`flex items-center p-3 rounded-lg transition-colors ${
                      isActive 
                        ? 'bg-primary-100 text-primary-700' 
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                    onClick={toggleSidebar}
                  >
                    <item.icon className="mr-3" size={20} />
                    <span>{item.name}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </div>
  );
};

export default MobileNav;