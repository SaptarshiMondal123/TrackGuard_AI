import React from 'react';
import { Train, Shield, Github, Linkedin, Mail, ExternalLink } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-black border-t border-gray-800">
      <div className="container mx-auto px-6 py-12">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          {/* Logo and Description */}
          <div className="md:col-span-2">
            <div className="flex items-center space-x-3 mb-4">
              <div className="relative">
                <Train className="w-8 h-8 text-green-400" />
                <Shield className="w-4 h-4 text-amber-400 absolute -top-1 -right-1" />
              </div>
              <span className="text-2xl font-bold text-white">TrackGuard</span>
            </div>
            <p className="text-gray-300 mb-6 max-w-md leading-relaxed">
              Revolutionary AI-powered train pre-collision detection system ensuring safer railways through advanced hazard awareness and predictive analytics.
            </p>
            <div className="text-lg font-semibold bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
              Safety Beyond Sight — Powered by AI
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-bold text-lg mb-4">Quick Links</h3>
            <ul className="space-y-2">
              <li><a href="#features" className="text-gray-300 hover:text-green-400 transition-colors">Features</a></li>
              <li><a href="#showcase" className="text-gray-300 hover:text-green-400 transition-colors">Technology</a></li>
              <li><a href="#demo" className="text-gray-300 hover:text-green-400 transition-colors">Demo</a></li>
              <li><a href="#" className="text-gray-300 hover:text-green-400 transition-colors">Documentation</a></li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-white font-bold text-lg mb-4">Connect</h3>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <Mail className="w-5 h-5 text-green-400" />
                <a href="mailto:contact@trackguard.ai" className="text-gray-300 hover:text-green-400 transition-colors">
                  contact@trackguard.ai
                </a>
              </div>
              <div className="flex space-x-4 mt-4">
                <a href="#" className="p-2 bg-gray-800 hover:bg-green-500 rounded-lg transition-all duration-300 transform hover:scale-110">
                  <Github className="w-5 h-5 text-gray-300 hover:text-white" />
                </a>
                <a href="#" className="p-2 bg-gray-800 hover:bg-green-500 rounded-lg transition-all duration-300 transform hover:scale-110">
                  <Linkedin className="w-5 h-5 text-gray-300 hover:text-white" />
                </a>
                <a href="#" className="p-2 bg-gray-800 hover:bg-green-500 rounded-lg transition-all duration-300 transform hover:scale-110">
                  <ExternalLink className="w-5 h-5 text-gray-300 hover:text-white" />
                </a>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center">
          <div className="text-gray-400 text-sm mb-4 md:mb-0">
            © 2025 TrackGuard. All rights reserved. Built for railway safety innovation.
          </div>
          <div className="flex space-x-6 text-sm">
            <a href="#" className="text-gray-400 hover:text-green-400 transition-colors">Privacy Policy</a>
            <a href="#" className="text-gray-400 hover:text-green-400 transition-colors">Terms of Service</a>
            <a href="#" className="text-gray-400 hover:text-green-400 transition-colors">Safety Standards</a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;