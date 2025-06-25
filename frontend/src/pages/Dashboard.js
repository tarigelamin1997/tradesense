
import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Chip
} from '@mui/material';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { useAuth } from '../contexts/AuthContext';
import { useData } from '../contexts/DataContext';
import MetricCard from '../components/Dashboard/MetricCard';
import TradingChart from '../components/Charts/TradingChart';
import axios from 'axios';

const Dashboard = () => {
  const { user } = useAuth();
  const { dashboardData, loading, fetchDashboardData } = useData();
  const [performanceData, setPerformanceData] = useState([]);

  useEffect(() => {
    if (user) {
      fetchDashboardData(user.user_id);
    }
  }, [user]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5
      }
    }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      style={{ padding: '2rem' }}
    >
      {/* Header */}
      <motion.div variants={itemVariants}>
        <Box mb={4}>
          <Typography variant="h1" gutterBottom sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            Trading Dashboard
          </Typography>
          <Typography variant="h6" color="text.secondary">
            Welcome back, {user?.username}! Here's your trading overview.
          </Typography>
        </Box>
      </motion.div>

      {/* Key Metrics */}
      <motion.div variants={itemVariants}>
        <Grid container spacing={3} mb={4}>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Total P&L"
              value={`$${dashboardData?.total_pnl?.toLocaleString() || '0'}`}
              change="+12.5%"
              positive={true}
              icon="💰"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Win Rate"
              value={`${dashboardData?.win_rate || 0}%`}
              change="+2.1%"
              positive={true}
              icon="🎯"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Total Trades"
              value={dashboardData?.total_trades?.toLocaleString() || '0'}
              change="+45"
              positive={true}
              icon="📊"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Profit Factor"
              value={dashboardData?.profit_factor || '0.00'}
              change="+0.15"
              positive={true}
              icon="⚡"
            />
          </Grid>
        </Grid>
      </motion.div>

      {/* Charts Section */}
      <Grid container spacing={3}>
        {/* Equity Curve */}
        <Grid item xs={12} lg={8}>
          <motion.div variants={itemVariants}>
            <Paper sx={{ p: 3, height: 400 }}>
              <Typography variant="h6" gutterBottom>
                Equity Curve
              </Typography>
              <TradingChart data={performanceData} />
            </Paper>
          </motion.div>
        </Grid>

        {/* Performance Breakdown */}
        <Grid item xs={12} lg={4}>
          <motion.div variants={itemVariants}>
            <Paper sx={{ p: 3, height: 400 }}>
              <Typography variant="h6" gutterBottom>
                Performance Breakdown
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">Best Day</Typography>
                  <Chip 
                    label={`$${dashboardData?.best_day?.toLocaleString() || '0'}`}
                    color="success"
                    size="small"
                  />
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">Worst Day</Typography>
                  <Chip 
                    label={`$${dashboardData?.worst_day?.toLocaleString() || '0'}`}
                    color="error"
                    size="small"
                  />
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">Average Trade</Typography>
                  <Chip 
                    label="$245.60"
                    color="primary"
                    size="small"
                  />
                </Box>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">Max Drawdown</Typography>
                  <Chip 
                    label="-8.2%"
                    color="warning"
                    size="small"
                  />
                </Box>
              </Box>
            </Paper>
          </motion.div>
        </Grid>
      </Grid>
    </motion.div>
  );
};

export default Dashboard;
