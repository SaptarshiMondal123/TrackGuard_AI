import React from 'react';
import Header from './components/Header';
import HeroSection from './components/HeroSection';
import Features from './components/Features';
import VideoUpload from './components/VideoUpload';
import Showcase from './components/Showcase';
import Footer from './components/Footer';

function App() {
  return (
    <div className="min-h-screen bg-black text-white">
      <Header />
      <HeroSection />
      <Features />
      <VideoUpload />
      <Showcase />
      <Footer />
    </div>
  );
}

export default App;