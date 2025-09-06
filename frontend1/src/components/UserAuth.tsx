import React, { useState } from 'react';
import { LogIn, User, Lock, Shield } from 'lucide-react';
import { useTrackGuardStore } from '../store/trackguard';

interface User {
  id: string;
  username: string;
  email: string;
  role: 'Operator' | 'Supervisor' | 'Admin';
  permissions: string[];
}

const UserAuth: React.FC = () => {
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
    email: ''
  });
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Mock users for demonstration
  const mockUsers: User[] = [
    {
      id: '1',
      username: 'operator1',
      email: 'operator@trackguard.ai',
      role: 'Operator',
      permissions: ['view_videos', 'view_analytics']
    },
    {
      id: '2', 
      username: 'supervisor1',
      email: 'supervisor@trackguard.ai',
      role: 'Supervisor',
      permissions: ['view_videos', 'view_analytics', 'manage_alerts', 'view_gps']
    },
    {
      id: '3',
      username: 'admin',
      email: 'admin@trackguard.ai', 
      role: 'Admin',
      permissions: ['view_videos', 'view_analytics', 'manage_alerts', 'view_gps', 'manage_users', 'system_config']
    }
  ];

  const handleLogin = async () => {
    setIsLoading(true);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Mock authentication
    const user = mockUsers.find(u => u.username === credentials.username);
    if (user && credentials.password === 'trackguard123') {
      setCurrentUser(user);
      localStorage.setItem('trackguard_user', JSON.stringify(user));
    } else {
      alert('Invalid credentials. Try: operator1/supervisor1/admin with password: trackguard123');
    }
    
    setIsLoading(false);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    localStorage.removeItem('trackguard_user');
    setCredentials({ username: '', password: '', email: '' });
  };

  // Check for existing session on mount
  React.useEffect(() => {
    const savedUser = localStorage.getItem('trackguard_user');
    if (savedUser) {
      setCurrentUser(JSON.parse(savedUser));
    }
  }, []);

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'Admin': return 'text-red-400 bg-red-400/10';
      case 'Supervisor': return 'text-yellow-400 bg-yellow-400/10';
      case 'Operator': return 'text-green-400 bg-green-400/10';
      default: return 'text-gray-400 bg-gray-400/10';
    }
  };

  if (currentUser) {
    return (
      <div className="fixed top-4 left-4 z-50">
        <div className="bg-gray-800/90 backdrop-blur-sm rounded-lg p-4 border border-gray-700 shadow-lg min-w-64">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <User className="w-5 h-5 text-green-400" />
              <span className="text-white font-medium">{currentUser.username}</span>
            </div>
            <span className={`px-2 py-1 rounded text-xs ${getRoleColor(currentUser.role)}`}>
              {currentUser.role}
            </span>
          </div>
          
          <div className="space-y-2 mb-4">
            <div className="text-gray-400 text-sm">{currentUser.email}</div>
            <div className="text-gray-400 text-xs">
              ID: {currentUser.id}
            </div>
          </div>

          <div className="mb-4">
            <div className="text-gray-300 text-sm mb-2">Permissions:</div>
            <div className="space-y-1">
              {currentUser.permissions.map((permission, index) => (
                <div key={index} className="flex items-center space-x-2">
                  <Shield className="w-3 h-3 text-green-400" />
                  <span className="text-gray-400 text-xs">{permission.replace('_', ' ').toUpperCase()}</span>
                </div>
              ))}
            </div>
          </div>

          <button
            onClick={handleLogout}
            className="w-full px-3 py-2 bg-red-600/20 text-red-400 text-sm rounded hover:bg-red-600/30 transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-gray-900 rounded-2xl p-8 border border-gray-700 shadow-2xl max-w-md w-full mx-4">
        <div className="text-center mb-6">
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 bg-green-400/10 rounded-full flex items-center justify-center">
              <LogIn className="w-6 h-6 text-green-400" />
            </div>
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">
            {isLoginMode ? 'Sign In' : 'Create Account'}
          </h2>
          <p className="text-gray-400">
            Access TrackGuard AI Safety System
          </p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Username
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={credentials.username}
                onChange={(e) => setCredentials(prev => ({ ...prev, username: e.target.value }))}
                className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-green-400 focus:outline-none"
                placeholder="Enter username"
              />
            </div>
          </div>

          {!isLoginMode && (
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">
                Email
              </label>
              <input
                type="email"
                value={credentials.email}
                onChange={(e) => setCredentials(prev => ({ ...prev, email: e.target.value }))}
                className="w-full px-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-green-400 focus:outline-none"
                placeholder="Enter email"
              />
            </div>
          )}

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="password"
                value={credentials.password}
                onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
                className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:border-green-400 focus:outline-none"
                placeholder="Enter password"
              />
            </div>
          </div>

          <button
            onClick={handleLogin}
            disabled={isLoading || !credentials.username || !credentials.password}
            className="w-full py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg font-semibold hover:from-green-600 hover:to-emerald-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Authenticating...' : (isLoginMode ? 'Sign In' : 'Create Account')}
          </button>

          <div className="text-center">
            <button
              onClick={() => setIsLoginMode(!isLoginMode)}
              className="text-green-400 hover:text-green-300 text-sm transition-colors"
            >
              {isLoginMode ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
          </div>
        </div>

        {/* Demo Credentials */}
        <div className="mt-6 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
          <div className="text-gray-300 text-sm font-medium mb-2">Demo Credentials:</div>
          <div className="text-xs text-gray-400 space-y-1">
            <div>• <strong>operator1</strong> / trackguard123 (Operator)</div>
            <div>• <strong>supervisor1</strong> / trackguard123 (Supervisor)</div>
            <div>• <strong>admin</strong> / trackguard123 (Admin)</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserAuth;