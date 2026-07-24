import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';
import {
  TrendingUp,
  Receipt,
  People,
  Inventory,
  RequestQuote,
  AddCircleOutline
} from '@mui/icons-material';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';
import api from '../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [trend, setTrend] = useState([]);
  const [monthly, setMonthly] = useState([]);
  const [topCustomers, setTopCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [statsRes, trendRes, monthlyRes, custRes] = await Promise.all([
          api.get('/reports/dashboard-stats'),
          api.get('/reports/sales/trend?days=30'),
          api.get('/reports/sales/monthly'),
          api.get('/reports/sales/customers')
        ]);
        
        setStats(statsRes.data);
        setTrend(trendRes.data);
        setMonthly(monthlyRes.data.reverse()); // Chronological order
        setTopCustomers(custRes.data.slice(0, 5)); // Take top 5
      } catch (err) {
        console.error('Error fetching dashboard metrics', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  const statCards = [
    { title: "Today's Sales", value: `₹${stats?.today_sales?.toLocaleString('en-IN')}`, icon: <TrendingUp fontSize="large" />, color: '#3b82f6' },
    { title: "Monthly Sales", value: `₹${stats?.monthly_sales?.toLocaleString('en-IN')}`, icon: <RequestQuote fontSize="large" />, color: '#10b981' },
    { title: "Paid Amount", value: `₹${stats?.paid_amount?.toLocaleString('en-IN')}`, subtitle: `${stats?.paid_count} invoices`, icon: <Receipt fontSize="large" />, color: '#16a34a' },
    { title: "Unpaid Amount", value: `₹${stats?.unpaid_amount?.toLocaleString('en-IN')}`, subtitle: `${stats?.unpaid_count} invoices`, icon: <Receipt fontSize="large" />, color: '#dc2626' },
    { title: "Total Invoices", value: stats?.invoices_count, icon: <Receipt fontSize="large" />, color: '#8b5cf6' },
    { title: "Active Customers", value: stats?.customers_count, icon: <People fontSize="large" />, color: '#ec4899' },
    { title: "Products Catalog", value: stats?.products_count, icon: <Inventory fontSize="large" />, color: '#06b6d4' },
    { title: "GST Collected", value: `₹${stats?.gst_collected?.toLocaleString('en-IN')}`, icon: <RequestQuote fontSize="large" />, color: '#f59e0b' },
  ];

  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Welcome Banner / Action */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, flexDirection: { xs: 'column', sm: 'row' }, gap: 2, mb: { xs: 2.5, sm: 4 } }}>
        <Box>
          <Typography variant="h4" sx={{ fontFamily: '"Outfit", sans-serif', fontWeight: 700, fontSize: { xs: '1.55rem', sm: '2.125rem' }, mb: 0.5 }}>
            Dashboard Overview
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Real-time billing activity, sales trends, and GST metrics.
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddCircleOutline />}
          onClick={() => navigate('/invoice/create')}
          sx={{ background: 'linear-gradient(45deg, #2563eb, #0d9488)', width: { xs: '100%', sm: 'auto' } }}
        >
          Create New Invoice
        </Button>
      </Box>

      {/* Stats Cards Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {statCards.map((card, idx) => (
          <Grid item xs={12} sm={6} md={3} key={idx}>
            <Card sx={{ height: '100%', position: 'relative', overflow: 'hidden' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 3 }}>
                <Box 
                  sx={{ 
                    bgcolor: `${card.color}15`, 
                    color: card.color, 
                    p: 1.5, 
                    borderRadius: 3,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  {card.icon}
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                    {card.title}
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 700, fontFamily: '"Outfit", sans-serif', mt: 0.5 }}>
                    {card.value}
                  </Typography>
                  {card.subtitle && (
                    <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 500 }}>
                      {card.subtitle}
                    </Typography>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Charts Section */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Sales Trend */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                Sales Trend (Past 30 Days)
              </Typography>
              <Box sx={{ width: '100%', height: { xs: 230, sm: 300 } }}>
                {trend.length === 0 ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                    <Typography color="text.secondary">No sales recorded in the past 30 days.</Typography>
                  </Box>
                ) : (
                  <ResponsiveContainer>
                    <AreaChart data={trend} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="date" tickLine={false} axisLine={false} style={{ fontSize: '0.75rem', fill: '#64748b' }} />
                      <YAxis tickLine={false} axisLine={false} style={{ fontSize: '0.75rem', fill: '#64748b' }} />
                      <Tooltip formatter={(value) => [`₹${value}`, 'Sales']} />
                      <Area type="monotone" dataKey="sales" stroke="#2563eb" strokeWidth={2} fillOpacity={1} fill="url(#colorSales)" />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Monthly Revenue Bar Chart */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                Monthly Comparison
              </Typography>
              <Box sx={{ width: '100%', height: { xs: 230, sm: 300 } }}>
                {monthly.length === 0 ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                    <Typography color="text.secondary">No monthly details available.</Typography>
                  </Box>
                ) : (
                  <ResponsiveContainer>
                    <BarChart data={monthly} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="month" tickLine={false} axisLine={false} style={{ fontSize: '0.75rem', fill: '#64748b' }} />
                      <YAxis tickLine={false} axisLine={false} style={{ fontSize: '0.75rem', fill: '#64748b' }} />
                      <Tooltip formatter={(value) => [`₹${value}`, 'Revenue']} />
                      <Bar dataKey="sales" fill="#0d9488" radius={[4, 4, 0, 0]} barSize={25} />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Bottom Row - Top Customers */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            Top Customers by Spending
          </Typography>
          {topCustomers.length === 0 ? (
            <Box sx={{ py: 4, textAlign: 'center' }}>
              <Typography color="text.secondary">No customer transactions available yet.</Typography>
            </Box>
          ) : (
            <TableContainer component={Paper} sx={{ boxShadow: 'none', border: '1px solid #f1f5f9' }}>
              <Table size="small">
                <TableHead sx={{ bgcolor: '#f8fafc' }}>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 600 }}>Company Name</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600 }}>Invoices Count</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 600 }}>Total Spent (INR)</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {topCustomers.map((row) => (
                    <TableRow key={row.customer_id} hover>
                      <TableCell sx={{ fontWeight: 500 }}>{row.company_name}</TableCell>
                      <TableCell align="right">{row.count}</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 600, color: 'success.main' }}>
                        ₹{row.sales.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default Dashboard;
