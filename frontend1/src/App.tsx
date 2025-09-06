import ErrorBoundary from './components/ErrorBoundary';
import Header from './components/Header';
import HeroSection from './components/HeroSection';
import Features from './components/Features';
import VideoUploadEnhanced from './components/VideoUploadEnhanced';
import Showcase from './components/Showcase';
import Footer from './components/Footer';
import AlertSystem from './components/AlertSystem';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-black text-white">
        <Header />
        <HeroSection />
        <Features />
        <VideoUploadEnhanced />
        <Showcase />
        <Footer />
        <AlertSystem />
        <Dashboard isVisible={true} />
      </div>
    </ErrorBoundary>
  );
}

export default App;