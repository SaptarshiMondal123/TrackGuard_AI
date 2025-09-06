import React from 'react';
import Header from './components/Header';
import HeroSection from './components/HeroSection';
import Features from './components/Features';
import VideoUpload from './components/VideoUpload';
import Analytics from './components/Analytics';
import GPSMapping from './components/GPSMapping';
import AlertManager from './components/AlertManager';
import Showcase from './components/Showcase';
import Footer from './components/Footer';

function App() {
  return (
    <div className="min-h-screen bg-black text-white">
      <Header />
      <HeroSection />
      <Features />
      <VideoUpload />
      <Analytics />
      <GPSMapping />
      <Showcase />
      <Footer />
      <AlertManager />
    </div>
  );
}

export default App;