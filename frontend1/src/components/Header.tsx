import React from 'react';
import { Train, Shield } from 'lucide-react';

const Header = () => {
  return (
    <header className="bg-black/90 backdrop-blur-sm border-b border-gray-800 sticky top-0 z-50">
      <div className="container mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="relative">
            <Train className="w-8 h-8 text-green-400" />
            <Shield className="w-4 h-4 text-amber-400 absolute -top-1 -right-1" />
          </div>
          <span className="text-xl font-bold text-white">TrackGuard</span>
        </div>
        
        <nav className="hidden md:flex items-center space-x-8">
          <a href="#features" className="text-gray-300 hover:text-green-400 transition-colors">Features</a>
          <a href="#showcase" className="text-gray-300 hover:text-green-400 transition-colors">Showcase</a>
          <a href="#demo" className="text-gray-300 hover:text-green-400 transition-colors">Demo</a>
          <button className="bg-gradient-to-r from-green-500 to-emerald-600 text-white px-6 py-2 rounded-lg font-semibold hover:from-green-600 hover:to-emerald-700 transition-all duration-300 transform hover:scale-105">
            Get Started
          </button>
        </nav>
      </div>
    </header>
  );
};

export default Header;