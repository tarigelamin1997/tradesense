
# Trading Analytics Metrics Documentation

## Overview

This document describes the comprehensive trading analytics system implemented in TradeSense, detailing all metrics, calculations, and interpretations.

## Core Trade Metrics

### Individual Trade Metrics

Each trade is analyzed with the following metrics:

#### Duration Metrics
- **Duration (Minutes/Hours)**: Time between entry and exit
- **Formula**: `exit_time - entry_time`

#### Profit/Loss Metrics
- **Gross P&L**: Raw profit/loss before commissions
- **Net P&L**: Profit/loss after commissions
- **Return %**: Percentage return on capital at risk
- **Formula**: `(net_pnl / (entry_price * quantity)) * 100`

#### Risk Metrics
- **Commission Impact**: Percentage of returns consumed by commissions
- **Risk-Reward Ratio**: Ratio of potential reward to risk (if stop/target set)
- **Win/Loss Flag**: Boolean indicator of trade profitability

## Aggregate Performance Metrics

### Basic Statistics
- **Total Trades**: Count of all executed trades
- **Winning Trades**: Count of profitable trades
- **Losing Trades**: Count of unprofitable trades
- **Win Rate**: Percentage of profitable trades
- **Formula**: `(winning_trades / total_trades) * 100`

### Profit/Loss Analysis
- **Total P&L**: Sum of all trade P&L
- **Gross Profit**: Sum of all winning trades
- **Gross Loss**: Absolute sum of all losing trades
- **Average Win**: Mean profit of winning trades
- **Average Loss**: Mean loss of losing trades
- **Largest Win/Loss**: Maximum single trade profit/loss

### Performance Ratios

#### Profit Factor
Ratio of gross profit to gross loss
- **Formula**: `gross_profit / gross_loss`
- **Interpretation**: 
  - >1.0: Profitable system
  - >1.5: Good system
  - >2.0: Excellent system

#### Expectancy
Average expected return per trade
- **Formula**: `total_pnl / total_trades`
- **Interpretation**: Positive values indicate profitable system

#### Average Win/Loss Ratio
Ratio of average win to average loss
- **Formula**: `average_win / average_loss`
- **Interpretation**: Higher values indicate better reward/risk profile

### Risk Metrics

#### Maximum Drawdown
Largest peak-to-trough decline in equity
- **Dollar Drawdown**: Absolute dollar amount
- **Percentage Drawdown**: Percentage of peak equity
- **Formula**: `max(peak_equity - current_equity)`

#### Recovery Factor
Ratio of total return to maximum drawdown
- **Formula**: `total_return / max_drawdown`
- **Interpretation**: Higher values indicate better risk-adjusted returns

#### Sharpe Ratio
Risk-adjusted return metric
- **Formula**: `(portfolio_return - risk_free_rate) / portfolio_volatility`
- **Interpretation**:
  - >1.0: Good risk-adjusted returns
  - >2.0: Excellent risk-adjusted returns

#### Sortino Ratio
Modified Sharpe ratio using downside deviation
- **Formula**: `(portfolio_return - risk_free_rate) / downside_deviation`
- **Interpretation**: Similar to Sharpe but focuses on downside risk

### Streak Analysis

#### Win/Loss Streaks
- **Max Win Streak**: Longest consecutive winning trades
- **Max Loss Streak**: Longest consecutive losing trades
- **Current Streak**: Current consecutive wins/losses

### Duration Analysis
- **Average Trade Duration**: Mean time held per trade
- **Median Trade Duration**: Middle value of trade durations
- **Duration Distribution**: Histogram of holding periods

## Advanced Analytics

### Equity Curve Analysis
- **Cumulative P&L**: Running sum of all trade P&L
- **Peak Equity**: Highest point reached in equity curve
- **Underwater Equity**: Current drawdown from peak

### Behavioral Analytics

#### Execution Type Analysis
Comparison of manual vs automated trade execution:
- Win rates by execution type
- Average returns by execution type
- P&L distribution by execution type

#### Confidence Score Analysis
Performance correlation with trader confidence (1-10 scale):
- Win rate by confidence level
- Average returns by confidence level
- Overconfidence bias detection

#### Strategy Performance
Analysis by strategy/setup tags:
- Performance by strategy type
- Best/worst performing strategies
- Strategy consistency metrics

### Time-Based Analytics

#### Intraday Performance
- Performance by hour of day
- Best/worst trading hours
- Activity heatmaps

#### Day-of-Week Analysis
- Performance by day of week
- Trading frequency patterns
- Seasonal performance patterns

#### Session Analysis
- Performance by trading session
- Frequency patterns
- Daily P&L distributions

## Chart Types and Visualizations

### Equity Curve Charts
- **Main Equity Line**: Cumulative P&L over time
- **Drawdown Chart**: Underwater equity visualization
- **Streak Coloring**: Win/loss streak identification
- **Peak Markers**: Equity high points

### Distribution Charts
- **P&L Histogram**: Distribution of trade outcomes
- **Duration Distribution**: Trade holding period analysis
- **Return Distribution**: Percentage return analysis

### Performance Heatmaps
- **Time-based Heatmaps**: Performance by hour/day
- **Strategy Heatmaps**: Performance by strategy/symbol
- **Risk Heatmaps**: Risk exposure analysis

### Correlation Analysis
- **Metric Correlations**: Relationships between performance metrics
- **Time Correlations**: Performance patterns over time
- **Behavioral Correlations**: Psychology vs performance

## Interpretation Guidelines

### Performance Assessment
- **Win Rate**: 40-60% typical for swing trading, 60%+ for scalping
- **Profit Factor**: >1.5 for sustainable profitability
- **Sharpe Ratio**: >1.0 indicates good risk-adjusted returns
- **Max Drawdown**: Should be <20% of account for conservative trading

### Risk Management
- **Consecutive Losses**: >5 consecutive losses may indicate system issues
- **Drawdown Duration**: Extended drawdowns may require strategy review
- **Volatility**: High return volatility indicates need for position sizing review

### Behavioral Insights
- **Overconfidence**: High confidence trades performing worse than expected
- **Execution Bias**: Manual trades significantly underperforming systematic trades
- **Time Patterns**: Consistent poor performance at specific times

## Calculations and Formulas

### Return Calculations
```python
# Percentage return
return_pct = (exit_price - entry_price) / entry_price * 100 * direction_multiplier

# Direction multiplier: 1 for long, -1 for short
direction_multiplier = 1 if direction == 'long' else -1

# Risk-adjusted return
risk_adjusted_return = trade_return / trade_risk
```

### Risk Calculations
```python
# Value at Risk (VaR)
var_95 = np.percentile(returns, 5)  # 5th percentile

# Maximum Drawdown
running_max = cumulative_returns.expanding().max()
drawdown = running_max - cumulative_returns
max_drawdown = drawdown.max()
```

### Statistical Calculations
```python
# Sharpe Ratio
excess_returns = returns - risk_free_rate
sharpe_ratio = excess_returns.mean() / returns.std() * sqrt(252)

# Sortino Ratio
downside_returns = returns[returns < 0]
sortino_ratio = excess_returns.mean() / downside_returns.std() * sqrt(252)
```

## Data Quality Requirements

### Required Fields
- Symbol
- Entry/Exit Times
- Entry/Exit Prices
- Quantity
- Direction (Long/Short)
- P&L

### Optional Fields
- Commission
- Strategy Tags
- Confidence Scores
- Execution Type
- Notes

### Data Validation
- All prices must be positive
- Exit time must be after entry time
- P&L should be consistent with price differences
- Quantities must be positive

## Best Practices

### Analysis Workflow
1. Import trade data
2. Validate data quality
3. Calculate individual trade metrics
4. Compute aggregate performance metrics
5. Generate equity curve analysis
6. Review behavioral patterns
7. Export results and insights

### Interpretation Guidelines
- Always consider sample size when interpreting results
- Look for statistically significant patterns
- Consider market conditions during analysis period
- Compare against relevant benchmarks
- Focus on risk-adjusted metrics for decision making

### Continuous Improvement
- Regular performance reviews
- Strategy optimization based on analytics
- Risk management adjustments
- Behavioral pattern awareness
- Market condition adaptations
