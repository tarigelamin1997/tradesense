
import React, { useState, useEffect } from 'react';
import { marketDataService, EconomicEvent } from '../../services/marketData';

interface EconomicCalendarWidgetProps {
  daysAhead?: number;
  showHighImpactOnly?: boolean;
}

export const EconomicCalendarWidget: React.FC<EconomicCalendarWidgetProps> = ({
  daysAhead = 7,
  showHighImpactOnly = false
}) => {
  const [events, setEvents] = useState<EconomicEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        setLoading(true);
        const data = await marketDataService.getEconomicCalendar(daysAhead);
        const filteredEvents = showHighImpactOnly 
          ? data.filter(event => event.impact === 'high')
          : data;
        setEvents(filteredEvents);
      } catch (error) {
        console.error('Failed to fetch economic calendar:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchEvents();
    const interval = setInterval(fetchEvents, 60000); // Update every minute

    return () => clearInterval(interval);
  }, [daysAhead, showHighImpactOnly]);

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4">Economic Calendar</h3>
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-16 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Economic Calendar</h3>
        <span className="text-sm text-gray-500">
          Next {daysAhead} days
        </span>
      </div>
      
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {events.length === 0 ? (
          <p className="text-gray-500 text-center py-4">No upcoming events</p>
        ) : (
          events.map((event, index) => (
            <div key={index} className="border rounded-lg p-3 hover:bg-gray-50">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{event.name}</h4>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-sm text-gray-500">
                      {new Date(event.date).toLocaleDateString()} at {event.time}
                    </span>
                    <span className="text-xs font-medium text-gray-700">
                      {event.currency}
                    </span>
                  </div>
                  {event.forecast !== 'TBD' && (
                    <div className="text-xs text-gray-600 mt-1">
                      Forecast: {event.forecast} | Previous: {event.previous}
                    </div>
                  )}
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getImpactColor(event.impact)}`}>
                  {event.impact.toUpperCase()}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
