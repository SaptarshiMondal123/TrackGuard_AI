import React, { useEffect, useState } from 'react';
import { MapPin, Navigation, AlertTriangle, Zap, Route } from 'lucide-react';

interface GPSPoint {
  lat: number;
  lng: number;
  timestamp?: number;
  risk_level?: 'low' | 'medium' | 'high';
  alert_type?: string;
}

const GPSMapping: React.FC = () => {
  const [currentLocation, setCurrentLocation] = useState<GPSPoint>({ lat: 22.5726, lng: 88.3639 });
  const [trainRoute, setTrainRoute] = useState<GPSPoint[]>([]);
  const [hazardLocations, setHazardLocations] = useState<GPSPoint[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<GPSPoint | null>(null);

  // Simulated GPS route from the original backend code
  const TRAIN_ROUTE_DATA = [
    {lat: 22.5726, lng: 88.3639, risk_level: 'low' as const},
    {lat: 22.5742, lng: 88.3658, risk_level: 'low' as const},
    {lat: 22.5760, lng: 88.3676, risk_level: 'medium' as const, alert_type: 'Track inspection needed'},
    {lat: 22.5775, lng: 88.3695, risk_level: 'low' as const},
    {lat: 22.5790, lng: 88.3714, risk_level: 'high' as const, alert_type: 'Obstacle detected'},
    {lat: 22.5805, lng: 88.3733, risk_level: 'low' as const}
  ];

  useEffect(() => {
    // Initialize route data
    setTrainRoute(TRAIN_ROUTE_DATA);
    
    // Set hazard locations (locations with medium/high risk)
    const hazards = TRAIN_ROUTE_DATA.filter(point => point.risk_level !== 'low');
    setHazardLocations(hazards);

    // Simulate train movement along route
    let currentIndex = 0;
    const moveInterval = setInterval(() => {
      if (currentIndex < TRAIN_ROUTE_DATA.length - 1) {
        currentIndex++;
        setCurrentLocation(TRAIN_ROUTE_DATA[currentIndex]);
      } else {
        currentIndex = 0; // Loop back to start
      }
    }, 5000); // Move every 5 seconds

    return () => clearInterval(moveInterval);
  }, []);

  const getRiskColor = (risk_level?: string) => {
    switch (risk_level) {
      case 'high': return '#EF4444';
      case 'medium': return '#F59E0B';
      case 'low': return '#10B981';
      default: return '#6B7280';
    }
  };

  const getRiskColorClass = (risk_level?: string) => {
    switch (risk_level) {
      case 'high': return 'text-red-400 bg-red-400/10';
      case 'medium': return 'text-yellow-400 bg-yellow-400/10';
      case 'low': return 'text-green-400 bg-green-400/10';
      default: return 'text-gray-400 bg-gray-400/10';
    }
  };

  return (
    <section className="py-20 bg-gray-900">
      <div className="container mx-auto px-6">
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            GPS <span className="text-green-400">Mapping</span>
          </h2>
          <p className="text-gray-300 text-xl max-w-2xl mx-auto">
            Real-time hazard location mapping and route optimization
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Map Visualization */}
          <div className="lg:col-span-2">
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-white">Route Overview</h3>
                <div className="flex items-center space-x-2">
                  <Navigation className="w-5 h-5 text-green-400" />
                  <span className="text-green-400 text-sm">GPS Active</span>
                </div>
              </div>

              {/* Simplified Map View */}
              <div className="relative bg-gray-900 rounded-lg p-8 h-96 overflow-hidden">
                {/* Grid background */}
                <div className="absolute inset-0 opacity-20">
                  <div className="grid grid-cols-8 grid-rows-6 h-full">
                    {Array.from({length: 48}).map((_, i) => (
                      <div key={i} className="border border-gray-600"></div>
                    ))}
                  </div>
                </div>

                {/* Route Path */}
                <svg className="absolute inset-0 w-full h-full">
                  <defs>
                    <linearGradient id="routeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" style={{stopColor: '#10B981', stopOpacity: 0.8}} />
                      <stop offset="50%" style={{stopColor: '#F59E0B', stopOpacity: 0.8}} />
                      <stop offset="100%" style={{stopColor: '#EF4444', stopOpacity: 0.8}} />
                    </linearGradient>
                  </defs>
                  <polyline
                    fill="none"
                    stroke="url(#routeGradient)"
                    strokeWidth="3"
                    strokeDasharray="5,5"
                    points={trainRoute.map((point, index) => 
                      `${50 + index * 60},${200 + Math.sin(index) * 50}`
                    ).join(' ')}
                  />
                </svg>

                {/* Route Points */}
                {trainRoute.map((point, index) => (
                  <div
                    key={index}
                    className={`absolute w-4 h-4 rounded-full border-2 border-white cursor-pointer transform -translate-x-2 -translate-y-2 transition-all duration-300 hover:scale-125 ${
                      currentLocation.lat === point.lat && currentLocation.lng === point.lng 
                        ? 'w-6 h-6 -translate-x-3 -translate-y-3 z-10' : ''
                    }`}
                    style={{
                      backgroundColor: getRiskColor(point.risk_level),
                      left: `${50 + index * 60}px`,
                      top: `${200 + Math.sin(index) * 50}px`
                    }}
                    onClick={() => setSelectedLocation(point)}
                  />
                ))}

                {/* Current Train Position */}
                <div
                  className="absolute w-8 h-8 transform -translate-x-4 -translate-y-4 z-20"
                  style={{
                    left: `${50 + trainRoute.findIndex(p => p.lat === currentLocation.lat && p.lng === currentLocation.lng) * 60}px`,
                    top: `${200 + Math.sin(trainRoute.findIndex(p => p.lat === currentLocation.lat && p.lng === currentLocation.lng)) * 50}px`
                  }}
                >
                  <div className="w-full h-full bg-blue-500 rounded-full border-4 border-white shadow-lg animate-pulse">
                    <div className="absolute inset-0 bg-blue-400 rounded-full animate-ping"></div>
                  </div>
                </div>

                {/* Legend */}
                <div className="absolute bottom-4 left-4 bg-black/70 backdrop-blur-sm rounded-lg p-3 text-xs">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 rounded-full bg-green-500"></div>
                      <span className="text-green-400">Safe</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                      <span className="text-yellow-400">Caution</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-3 h-3 rounded-full bg-red-500"></div>
                      <span className="text-red-400">Hazard</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-4 h-4 rounded-full bg-blue-500 border-2 border-white"></div>
                      <span className="text-blue-400">Train</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Side Panel */}
          <div className="space-y-6">
            {/* Current Location */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
              <h3 className="text-lg font-bold text-white mb-4">Current Position</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Latitude:</span>
                  <span className="text-white font-mono">{currentLocation.lat.toFixed(4)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Longitude:</span>
                  <span className="text-white font-mono">{currentLocation.lng.toFixed(4)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Risk Level:</span>
                  <span className={`px-2 py-1 rounded text-xs ${getRiskColorClass(currentLocation.risk_level)}`}>
                    {currentLocation.risk_level?.toUpperCase() || 'LOW'}
                  </span>
                </div>
              </div>
            </div>

            {/* Hazard Alerts */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-white">Hazard Zones</h3>
                <AlertTriangle className="w-5 h-5 text-yellow-400" />
              </div>
              
              <div className="space-y-3">
                {hazardLocations.map((hazard, index) => (
                  <div key={index} className="p-3 bg-gray-700/50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className={`px-2 py-1 rounded text-xs ${getRiskColorClass(hazard.risk_level)}`}>
                        {hazard.risk_level?.toUpperCase()}
                      </span>
                      <span className="text-gray-400 text-xs">
                        {hazard.lat.toFixed(4)}, {hazard.lng.toFixed(4)}
                      </span>
                    </div>
                    {hazard.alert_type && (
                      <p className="text-gray-300 text-sm">{hazard.alert_type}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Route Statistics */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
              <h3 className="text-lg font-bold text-white mb-4">Route Stats</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Total Points:</span>
                  <span className="text-white">{trainRoute.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Safe Zones:</span>
                  <span className="text-green-400">{trainRoute.filter(p => p.risk_level === 'low').length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Hazard Zones:</span>
                  <span className="text-red-400">{hazardLocations.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Route Status:</span>
                  <span className="text-green-400">Active</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Selected Location Details */}
        {selectedLocation && (
          <div className="mt-8 bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white">Location Details</h3>
              <button
                onClick={() => setSelectedLocation(null)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                ×
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <span className="text-gray-400">Coordinates:</span>
                <p className="text-white font-mono">{selectedLocation.lat.toFixed(6)}, {selectedLocation.lng.toFixed(6)}</p>
              </div>
              <div>
                <span className="text-gray-400">Risk Assessment:</span>
                <p className={getRiskColorClass(selectedLocation.risk_level)}>
                  {selectedLocation.risk_level?.toUpperCase() || 'LOW'} RISK
                </p>
              </div>
              <div>
                <span className="text-gray-400">Alert:</span>
                <p className="text-white">{selectedLocation.alert_type || 'No alerts'}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};

export default GPSMapping;