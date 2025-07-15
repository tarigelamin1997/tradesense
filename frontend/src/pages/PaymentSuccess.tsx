import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, ArrowRight, Zap, BookOpen, TrendingUp } from 'lucide-react';
import confetti from 'canvas-confetti';

export default function PaymentSuccess() {
  const navigate = useNavigate();

  useEffect(() => {
    // Celebrate with confetti!
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 }
    });
  }, []);

  const nextSteps = [
    {
      icon: <Zap className="w-6 h-6" />,
      title: 'Import Your Trades',
      description: 'Upload your trading history to start tracking performance',
      action: () => navigate('/trades/import')
    },
    {
      icon: <BookOpen className="w-6 h-6" />,
      title: 'Create Your First Journal Entry',
      description: 'Document your trading strategy and goals',
      action: () => navigate('/journal')
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: 'View Your Analytics',
      description: 'See insights about your trading performance',
      action: () => navigate('/analytics')
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-2xl w-full">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
            <CheckCircle className="w-10 h-10 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to TradeSense Pro! 🎉
          </h1>
          <p className="text-lg text-gray-600">
            Your subscription is now active. Let's get you started.
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            What's Next?
          </h2>
          <div className="space-y-4">
            {nextSteps.map((step, idx) => (
              <button
                key={idx}
                onClick={step.action}
                className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md transition-all group"
              >
                <div className="flex items-start">
                  <div className="flex-shrink-0 text-blue-600 mr-4">
                    {step.icon}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 mb-1 group-hover:text-blue-600">
                      {step.title}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {step.description}
                    </p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-transform" />
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="bg-blue-50 rounded-lg p-6 text-center">
          <h3 className="font-semibold text-blue-900 mb-2">
            Need Help Getting Started?
          </h3>
          <p className="text-blue-700 mb-4">
            Check out our quick start guide or reach out to support.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={() => navigate('/docs/quickstart')}
              className="px-6 py-2 bg-white text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition-colors"
            >
              View Quick Start Guide
            </button>
            <button
              onClick={() => navigate('/support')}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Contact Support
            </button>
          </div>
        </div>

        <div className="text-center mt-8">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-gray-600 hover:text-gray-900"
          >
            Skip for now →
          </button>
        </div>
      </div>
    </div>
  );
}