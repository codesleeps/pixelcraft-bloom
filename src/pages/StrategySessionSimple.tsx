import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const StrategySession = () => {
  return (
    <div className="min-h-screen bg-gradient-subtle p-8">
      <div className="container mx-auto">
        <Link 
          to="/" 
          className="inline-flex items-center gap-2 text-primary hover:text-primary/80 transition-colors mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>
        
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-6xl font-bold mb-6">
            Free Strategy Session
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Get a personalized consultation to grow your business.
          </p>
          <div className="bg-white p-8 rounded-lg shadow-lg">
            <h2 className="text-2xl font-bold mb-4">Coming Soon</h2>
            <p className="text-gray-600">
              This strategy session booking form is being built. 
              Please contact us directly for now.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StrategySession;