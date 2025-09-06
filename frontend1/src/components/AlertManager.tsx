import React, { useEffect, useState } from 'react';
import { Bell, X, AlertTriangle, Info, AlertCircle, Zap, Volume2 } from 'lucide-react';
import { useTrackGuardStore } from '../store/trackguard';

interface AlertNotificationProps {
  alert: {
    type: 'INFO' | 'WARNING' | 'CRITICAL' | 'EMERGENCY';
    message: string;
    timestamp: number;
  };
  onClose: () => void;
}

const AlertNotification: React.FC<AlertNotificationProps> = ({ alert, onClose }) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    // Auto-dismiss INFO and WARNING alerts after 5 seconds
    if (alert.type === 'INFO' || alert.type === 'WARNING') {
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(onClose, 300); // Allow fade out animation
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [alert.type, onClose]);

  const getIcon = () => {
    switch (alert.type) {
      case 'EMERGENCY': return <Zap className="w-5 h-5" />;
      case 'CRITICAL': return <AlertCircle className="w-5 h-5" />;
      case 'WARNING': return <AlertTriangle className="w-5 h-5" />;
      default: return <Info className="w-5 h-5" />;
    }
  };

  const getStyle = () => {
    switch (alert.type) {
      case 'EMERGENCY':
        return 'bg-red-900/90 border-red-500 text-red-100';
      case 'CRITICAL':
        return 'bg-orange-900/90 border-orange-500 text-orange-100';
      case 'WARNING':
        return 'bg-yellow-900/90 border-yellow-500 text-yellow-100';
      default:
        return 'bg-blue-900/90 border-blue-500 text-blue-100';
    }
  };

  return (
    <div className={`
      fixed top-4 right-4 z-50 min-w-80 max-w-md p-4 rounded-lg border-l-4 backdrop-blur-sm shadow-lg
      transform transition-all duration-300 ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
      ${getStyle()}
    `}>
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3">
          {getIcon()}
          <div>
            <div className="font-semibold text-sm">
              {alert.type} ALERT
            </div>
            <div className="text-sm mt-1">
              {alert.message}
            </div>
            <div className="text-xs mt-2 opacity-75">
              {new Date(alert.timestamp).toLocaleTimeString()}
            </div>
          </div>
        </div>
        <button
          onClick={() => {
            setIsVisible(false);
            setTimeout(onClose, 300);
          }}
          className="ml-4 hover:bg-white/20 rounded p-1 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

const AlertManager: React.FC = () => {
  const { alerts, unreadAlerts, markAlertsRead, addAlert } = useTrackGuardStore();
  const [visibleAlerts, setVisibleAlerts] = useState<Array<{alert: any, id: number}>>([]);
  const [alertSound, setAlertSound] = useState(true);

  // Show new alerts as notifications
  useEffect(() => {
    if (alerts.length > visibleAlerts.length) {
      const newAlerts = alerts.slice(visibleAlerts.length);
      newAlerts.forEach((alert, index) => {
        const alertWithId = { alert, id: Date.now() + index };
        setVisibleAlerts(prev => [...prev, alertWithId]);
        
        // Play sound for critical alerts
        if (alertSound && (alert.type === 'CRITICAL' || alert.type === 'EMERGENCY')) {
          playAlertSound();
        }
      });
    }
  }, [alerts, visibleAlerts.length, alertSound]);

  const playAlertSound = () => {
    // Create a simple beep sound using Web Audio API
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
      gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
      console.log('Alert sound not supported');
    }
  };

  const removeNotification = (id: number) => {
    setVisibleAlerts(prev => prev.filter(item => item.id !== id));
  };

  // Demo: Add sample alerts for testing
  const addSampleAlert = (type: 'INFO' | 'WARNING' | 'CRITICAL' | 'EMERGENCY') => {
    const messages = {
      INFO: 'System status update: All systems operational',
      WARNING: 'Track inspection scheduled in 30 minutes',
      CRITICAL: 'High risk situation detected - obstacle on track',
      EMERGENCY: 'EMERGENCY: Person on track detected - immediate action required'
    };
    
    addAlert({
      type,
      message: messages[type],
      timestamp: Date.now()
    });
  };

  return (
    <>
      {/* Alert Notifications */}
      {visibleAlerts.map(({ alert, id }) => (
        <AlertNotification
          key={id}
          alert={alert}
          onClose={() => removeNotification(id)}
        />
      ))}

      {/* Alert Controls (for demo) */}
      <div className="fixed bottom-4 right-4 z-40">
        <div className="bg-gray-800/90 backdrop-blur-sm rounded-lg p-4 border border-gray-700 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Bell className="w-4 h-4 text-green-400" />
              <span className="text-white text-sm font-medium">Alert System</span>
              {unreadAlerts > 0 && (
                <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                  {unreadAlerts}
                </span>
              )}
            </div>
            <button
              onClick={() => setAlertSound(!alertSound)}
              className={`p-1 rounded ${alertSound ? 'text-green-400' : 'text-gray-500'}`}
              title={`Sound ${alertSound ? 'ON' : 'OFF'}`}
            >
              <Volume2 className="w-4 h-4" />
            </button>
          </div>
          
          {/* Demo Alert Buttons */}
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => addSampleAlert('INFO')}
              className="px-3 py-2 bg-blue-600/20 text-blue-400 text-xs rounded hover:bg-blue-600/30 transition-colors"
            >
              Test INFO
            </button>
            <button
              onClick={() => addSampleAlert('WARNING')}
              className="px-3 py-2 bg-yellow-600/20 text-yellow-400 text-xs rounded hover:bg-yellow-600/30 transition-colors"
            >
              Test WARNING
            </button>
            <button
              onClick={() => addSampleAlert('CRITICAL')}
              className="px-3 py-2 bg-orange-600/20 text-orange-400 text-xs rounded hover:bg-orange-600/30 transition-colors"
            >
              Test CRITICAL
            </button>
            <button
              onClick={() => addSampleAlert('EMERGENCY')}
              className="px-3 py-2 bg-red-600/20 text-red-400 text-xs rounded hover:bg-red-600/30 transition-colors"
            >
              Test EMERGENCY
            </button>
          </div>
          
          {unreadAlerts > 0 && (
            <button
              onClick={markAlertsRead}
              className="w-full mt-2 px-3 py-2 bg-gray-600/20 text-gray-400 text-xs rounded hover:bg-gray-600/30 transition-colors"
            >
              Mark All Read
            </button>
          )}
        </div>
      </div>
    </>
  );
};

export default AlertManager;