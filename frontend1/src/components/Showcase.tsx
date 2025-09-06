import React from 'react';
import { ArrowRight } from 'lucide-react';

const showcaseItems = [
  {
    title: 'From Simulation to Real Locomotives',
    description: 'Advanced AI training on synthetic and real-world railway data ensures robust performance across all scenarios.',
    image: 'https://images.pexels.com/photos/258330/pexels-photo-258330.jpeg?auto=compress&cs=tinysrgb&w=800'
  },
  {
    title: 'Fusion of Vision + DAS Data',
    description: 'Combining computer vision with Distributed Acoustic Sensing for comprehensive track monitoring.',
    image: 'https://images.pexels.com/photos/2226458/pexels-photo-2226458.jpeg?auto=compress&cs=tinysrgb&w=800'
  },
  {
    title: 'Edge Computing Integration',
    description: 'On-board processing ensures real-time response even in areas with limited connectivity.',
    image: 'https://images.pexels.com/photos/3862365/pexels-photo-3862365.jpeg?auto=compress&cs=tinysrgb&w=800'
  }
];

const Showcase = () => {
  return (
    <section id="showcase" className="py-20 bg-gradient-to-b from-gray-900 to-black">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Technology <span className="text-green-400">Showcase</span>
          </h2>
          <p className="text-gray-300 text-xl max-w-3xl mx-auto">
            See how TrackGuard transforms railway safety through advanced AI and cutting-edge technology integration
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {showcaseItems.map((item, index) => (
            <div
              key={index}
              className="group bg-gray-800/30 backdrop-blur-sm rounded-2xl overflow-hidden border border-gray-700 hover:border-green-400/40 transition-all duration-500 transform hover:scale-[1.02] hover:shadow-xl hover:shadow-green-400/10"
            >
              <div className="relative overflow-hidden">
                <img
                  src={item.image}
                  alt={item.title}
                  className="w-full h-48 object-cover transition-transform duration-500 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-gray-900/80 to-transparent"></div>
                <div className="absolute bottom-4 left-4 right-4">
                  <h3 className="text-lg font-bold text-white mb-1">
                    {item.title}
                  </h3>
                </div>
              </div>
              
              <div className="p-6">
                <p className="text-gray-300 text-sm leading-relaxed mb-4">
                  {item.description}
                </p>
                
                <div className="flex items-center text-green-400 text-sm font-medium group-hover:text-green-300 transition-colors">
                  Learn more
                  <ArrowRight className="w-4 h-4 ml-2 transform group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center mt-16">
          <div className="inline-flex px-8 py-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-bold text-lg hover:from-green-600 hover:to-emerald-700 transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-green-500/25 cursor-pointer">
            Request Full Technical Demo
          </div>
        </div>
      </div>
    </section>
  );
};

export default Showcase;