import React, { useMemo, useState } from 'react';
import { 
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, ReferenceLine, Cell,
  ZAxis, Legend
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Target, TrendingUp, TrendingDown, Info } from 'lucide-react';

interface Trade {
  id: number;
  symbol: string;
  pnl: number;
  entry_price: number;
  exit_price?: number;
  quantity: number;
  status: 'open' | 'closed';
  exit_date?: string;
  close_date?: string;
}

interface RiskRewardScatterProps {
  trades: Trade[];
  onTradeClick?: (trade: Trade) => void;
}

interface ScatterPoint {
  trade: Trade;
  risk: number;
  reward: number;
  ratio: number;
  isWin: boolean;
  size: number;
  symbol: string;
}

const RiskRewardScatter: React.FC<RiskRewardScatterProps> = ({ trades, onTradeClick }) => {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('all');
  const [hoveredTrade, setHoveredTrade] = useState<Trade | null>(null);
  
  // Process trades into scatter points
  const { scatterData, symbols, stats } = useMemo(() => {
    const closedTrades = trades.filter(t => t.status === 'closed' && t.exit_price);
    
    const points: ScatterPoint[] = closedTrades.map(trade => {
      // Calculate risk and reward
      // Risk: Distance from entry to assumed stop (using 2% as default)
      const stopDistance = trade.entry_price * 0.02;
      const risk = stopDistance * trade.quantity;
      
      // Reward: Actual P&L
      const reward = Math.abs(trade.pnl);
      
      // Risk/Reward ratio
      const ratio = risk > 0 ? reward / risk : 0;
      
      return {
        trade,
        risk: risk,
        reward: trade.pnl > 0 ? reward : -reward,
        ratio,
        isWin: trade.pnl > 0,
        size: Math.sqrt(trade.quantity * trade.entry_price) / 10, // Size based on position value
        symbol: trade.symbol
      };
    });
    
    // Get unique symbols
    const uniqueSymbols = Array.from(new Set(points.map(p => p.symbol))).sort();
    
    // Calculate statistics by quadrant
    const quadrants = {
      highRiskHighReward: points.filter(p => p.risk > 50 && p.reward > 50),
      highRiskLowReward: points.filter(p => p.risk > 50 && p.reward <= 50 && p.reward > -50),
      lowRiskHighReward: points.filter(p => p.risk <= 50 && p.reward > 50),
      lowRiskLowReward: points.filter(p => p.risk <= 50 && p.reward <= 50 && p.reward > -50),
      losses: points.filter(p => p.reward < 0)
    };
    
    const avgRatio = points.length > 0
      ? points.reduce((sum, p) => sum + p.ratio, 0) / points.length
      : 0;
    
    const winRateByQuadrant = {
      highRiskHighReward: quadrants.highRiskHighReward.filter(p => p.isWin).length / 
                          (quadrants.highRiskHighReward.length || 1) * 100,
      highRiskLowReward: quadrants.highRiskLowReward.filter(p => p.isWin).length / 
                         (quadrants.highRiskLowReward.length || 1) * 100,
      lowRiskHighReward: quadrants.lowRiskHighReward.filter(p => p.isWin).length / 
                         (quadrants.lowRiskHighReward.length || 1) * 100,
      lowRiskLowReward: quadrants.lowRiskLowReward.filter(p => p.isWin).length / 
                        (quadrants.lowRiskLowReward.length || 1) * 100
    };
    
    return {
      scatterData: points,
      symbols: uniqueSymbols,
      stats: {
        avgRatio,
        quadrants,
        winRateByQuadrant,
        totalTrades: points.length,
        winningTrades: points.filter(p => p.isWin).length,
        losingTrades: points.filter(p => !p.isWin).length
      }
    };
  }, [trades]);
  
  // Filter data by selected symbol
  const filteredData = useMemo(() => {
    if (selectedSymbol === 'all') return scatterData;
    return scatterData.filter(p => p.symbol === selectedSymbol);
  }, [scatterData, selectedSymbol]);
  
  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload[0]) {
      const point: ScatterPoint = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="font-medium">{point.symbol}</p>
          <p className="text-sm text-gray-600">
            Risk: ${point.risk.toFixed(0)}
          </p>
          <p className={`text-sm ${point.isWin ? 'text-green-600' : 'text-red-600'}`}>
            {point.isWin ? 'Reward' : 'Loss'}: ${Math.abs(point.reward).toFixed(0)}
          </p>
          <p className="text-sm font-medium">
            R:R Ratio: {point.ratio.toFixed(2)}:1
          </p>
          <p className="text-xs text-gray-500">
            Position: {point.trade.quantity} @ ${point.trade.entry_price.toFixed(2)}
          </p>
        </div>
      );
    }
    return null;
  };
  
  // Get color for point
  const getPointColor = (point: ScatterPoint) => {
    if (point.isWin) {
      // Green shades based on R:R ratio
      if (point.ratio > 3) return '#006400';
      if (point.ratio > 2) return '#228B22';
      if (point.ratio > 1) return '#32CD32';
      return '#90EE90';
    } else {
      // Red shades for losses
      return '#DC143C';
    }
  };
  
  return (
    <div className="space-y-6">
      {/* Statistics Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg R:R Ratio</p>
              <p className="text-xl font-bold">
                {stats.avgRatio.toFixed(2)}:1
              </p>
            </div>
            <Target className="w-5 h-5 text-blue-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Optimal Zone</p>
              <p className="text-xl font-bold text-green-600">
                {stats.winRateByQuadrant.lowRiskHighReward.toFixed(0)}%
              </p>
              <p className="text-xs text-gray-500">win rate</p>
            </div>
            <TrendingUp className="w-5 h-5 text-green-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Danger Zone</p>
              <p className="text-xl font-bold text-red-600">
                {stats.quadrants.losses.length}
              </p>
              <p className="text-xs text-gray-500">losing trades</p>
            </div>
            <TrendingDown className="w-5 h-5 text-red-500" />
          </div>
        </Card>
        
        <Card className="p-4">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Trades</p>
              <p className="text-xl font-bold">
                {stats.totalTrades}
              </p>
              <p className="text-xs text-gray-500">
                {((stats.winningTrades / stats.totalTrades) * 100).toFixed(0)}% wins
              </p>
            </div>
            <Info className="w-5 h-5 text-gray-500" />
          </div>
        </Card>
      </div>
      
      {/* Main Scatter Plot */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Risk vs Reward Analysis</CardTitle>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="px-3 py-1 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Symbols</option>
              {symbols.map(symbol => (
                <option key={symbol} value={symbol}>{symbol}</option>
              ))}
            </select>
          </div>
        </CardHeader>
        <CardContent>
          {filteredData.length > 0 ? (
            <ResponsiveContainer width="100%" height={500}>
              <ScatterChart margin={{ top: 20, right: 20, bottom: 60, left: 60 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  type="number"
                  dataKey="risk"
                  name="Risk ($)"
                  unit="$"
                  label={{ value: 'Risk ($)', position: 'insideBottom', offset: -10 }}
                />
                <YAxis
                  type="number"
                  dataKey="reward"
                  name="Reward ($)"
                  unit="$"
                  label={{ value: 'Reward ($)', angle: -90, position: 'insideLeft' }}
                />
                <ZAxis type="number" dataKey="size" range={[20, 400]} />
                
                {/* Reference lines for R:R ratios */}
                <ReferenceLine 
                  segment={[{ x: 0, y: 0 }, { x: 500, y: 500 }]} 
                  stroke="#666" 
                  strokeDasharray="5 5"
                  label="1:1"
                />
                <ReferenceLine 
                  segment={[{ x: 0, y: 0 }, { x: 250, y: 500 }]} 
                  stroke="#10B981" 
                  strokeDasharray="3 3"
                  label="2:1"
                />
                <ReferenceLine 
                  segment={[{ x: 0, y: 0 }, { x: 167, y: 500 }]} 
                  stroke="#059669" 
                  strokeDasharray="3 3"
                  label="3:1"
                />
                
                {/* Zero line */}
                <ReferenceLine y={0} stroke="#DC143C" strokeWidth={2} />
                
                <Tooltip content={<CustomTooltip />} />
                
                <Scatter
                  data={filteredData}
                  fill="#8884d8"
                  onMouseEnter={(data: any) => setHoveredTrade(data.trade)}
                  onMouseLeave={() => setHoveredTrade(null)}
                  onClick={(data: any) => onTradeClick && onTradeClick(data.trade)}
                  style={{ cursor: 'pointer' }}
                >
                  {filteredData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={getPointColor(entry)}
                      fillOpacity={0.8}
                      stroke={hoveredTrade?.id === entry.trade.id ? '#000' : 'none'}
                      strokeWidth={2}
                    />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[500px] text-gray-500">
              No data available for risk/reward analysis
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Quadrant Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Quadrant Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700">Low Risk, High Reward</p>
              <p className="text-2xl font-bold text-green-600">
                {stats.quadrants.lowRiskHighReward.length}
              </p>
              <p className="text-xs text-gray-500">
                {stats.winRateByQuadrant.lowRiskHighReward.toFixed(0)}% win rate
              </p>
              <p className="text-xs text-green-600 font-medium mt-1">Optimal Zone</p>
            </div>
            
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700">High Risk, High Reward</p>
              <p className="text-2xl font-bold text-yellow-600">
                {stats.quadrants.highRiskHighReward.length}
              </p>
              <p className="text-xs text-gray-500">
                {stats.winRateByQuadrant.highRiskHighReward.toFixed(0)}% win rate
              </p>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700">Low Risk, Low Reward</p>
              <p className="text-2xl font-bold text-gray-600">
                {stats.quadrants.lowRiskLowReward.length}
              </p>
              <p className="text-xs text-gray-500">
                {stats.winRateByQuadrant.lowRiskLowReward.toFixed(0)}% win rate
              </p>
            </div>
            
            <div className="text-center p-4 bg-red-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700">Losses</p>
              <p className="text-2xl font-bold text-red-600">
                {stats.quadrants.losses.length}
              </p>
              <p className="text-xs text-gray-500">
                {((stats.quadrants.losses.length / stats.totalTrades) * 100).toFixed(0)}% of trades
              </p>
              <p className="text-xs text-red-600 font-medium mt-1">Avoid Zone</p>
            </div>
          </div>
          
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>💡 Insight:</strong> Focus on trades in the "Low Risk, High Reward" quadrant. 
              Your current win rate there is {stats.winRateByQuadrant.lowRiskHighReward.toFixed(0)}%. 
              Aim for a minimum 2:1 risk/reward ratio on all trades.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default RiskRewardScatter;