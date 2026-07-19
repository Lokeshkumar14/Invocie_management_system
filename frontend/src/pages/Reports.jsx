import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  CircularProgress,
  Snackbar,
  Alert
} from '@mui/material';
import {
  FileDownload,
  ReceiptLong,
  PersonPin,
  Inventory
} from '@mui/icons-material';
import api from '../services/api';

const Reports = () => {
  const [tabIndex, setTabIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [csvDownloading, setCsvDownloading] = useState(false);
  
  // Datasets
  const [gstReport, setGstReport] = useState([]);
  const [customerSales, setCustomerSales] = useState([]);
  const [productSales, setProductSales] = useState([]);

  // Toast notifications
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

  const loadReportData = async () => {
    setLoading(true);
    try {
      const [gstRes, custRes, prodRes] = await Promise.all([
        api.get('/reports/gst'),
        api.get('/reports/sales/customers'),
        api.get('/reports/sales/products')
      ]);
      setGstReport(gstRes.data);
      setCustomerSales(custRes.data);
      setProductSales(prodRes.data);
    } catch (err) {
      console.error(err);
      showToast('Failed to load reporting database', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReportData();
  }, []);

  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  const handleTabChange = (event, newValue) => {
    setTabIndex(newValue);
  };

  const handleExportCSV = async () => {
    setCsvDownloading(true);
    try {
      const response = await api.get('/reports/export-csv', {
        responseType: 'blob'
      });
      
      const file = new Blob([response.data], { type: 'text/csv' });
      const fileURL = URL.createObjectURL(file);
      
      const link = document.createElement('a');
      link.href = fileURL;
      link.setAttribute('download', `Sales_GST_Report_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      
      document.body.removeChild(link);
      URL.revokeObjectURL(fileURL);
      
      showToast('CSV report exported successfully');
    } catch (err) {
      console.error(err);
      showToast('Failed to download CSV export', 'error');
    } finally {
      setCsvDownloading(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontFamily: '"Outfit", sans-serif', fontWeight: 700, mb: 0.5 }}>
            GST & Sales Reports
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Inspect billing ledgers, analyze product metrics, and compile audits.
          </Typography>
        </Box>
        <Button
          variant="contained"
          color="secondary"
          startIcon={<FileDownload />}
          onClick={handleExportCSV}
          disabled={csvDownloading}
        >
          {csvDownloading ? 'Exporting...' : 'Export CSV Report'}
        </Button>
      </Box>

      {/* Tabs Menu */}
      <Tabs 
        value={tabIndex} 
        onChange={handleTabChange} 
        sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}
        textColor="primary"
        indicatorColor="primary"
      >
        <Tab icon={<ReceiptLong fontSize="small" />} iconPosition="start" label="GST Sales Ledger" />
        <Tab icon={<PersonPin fontSize="small" />} iconPosition="start" label="Customer-wise Sales" />
        <Tab icon={<Inventory fontSize="small" />} iconPosition="start" label="Product Performance" />
      </Tabs>

      {/* Tab Panel 1: GST Sales Ledger */}
      {tabIndex === 0 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead sx={{ bgcolor: '#f8fafc' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Invoice No</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Date</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Customer Name</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>GSTIN</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>Taxable Value (INR)</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>CGST</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>SGST</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>IGST</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>Grand Total</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {gstReport.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                    No transactions recorded.
                  </TableCell>
                </TableRow>
              ) : (
                gstReport.map((row, idx) => (
                  <TableRow key={idx} hover>
                    <TableCell sx={{ fontWeight: 600 }}>{row.invoice_number}</TableCell>
                    <TableCell>{new Date(row.invoice_date).toLocaleDateString('en-IN')}</TableCell>
                    <TableCell sx={{ fontWeight: 500 }}>{row.customer_name}</TableCell>
                    <TableCell sx={{ fontFamily: 'monospace' }}>{row.gst_number || 'Unregistered'}</TableCell>
                    <TableCell align="right">₹{row.subtotal.toFixed(2)}</TableCell>
                    <TableCell align="right" sx={{ color: row.cgst > 0 ? 'text.primary' : 'text.disabled' }}>
                      ₹{row.cgst.toFixed(2)}
                    </TableCell>
                    <TableCell align="right" sx={{ color: row.sgst > 0 ? 'text.primary' : 'text.disabled' }}>
                      ₹{row.sgst.toFixed(2)}
                    </TableCell>
                    <TableCell align="right" sx={{ color: row.igst > 0 ? 'text.primary' : 'text.disabled' }}>
                      ₹{row.igst.toFixed(2)}
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700, color: 'primary.main' }}>
                      ₹{row.grand_total.toFixed(2)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Tab Panel 2: Customer-wise Sales */}
      {tabIndex === 1 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead sx={{ bgcolor: '#f8fafc' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Customer / Company</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>Total Invoices Generated</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>Total Value Billing (INR)</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {customerSales.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                    No customer logs.
                  </TableCell>
                </TableRow>
              ) : (
                customerSales.map((row) => (
                  <TableRow key={row.customer_id} hover>
                    <TableCell sx={{ fontWeight: 600 }}>{row.company_name}</TableCell>
                    <TableCell align="right">{row.count}</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700, color: 'success.main' }}>
                      ₹{row.sales.toFixed(2)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Tab Panel 3: Product Performance */}
      {tabIndex === 2 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead sx={{ bgcolor: '#f8fafc' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Product Name</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>Units Dispatched</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>Total Revenue Contribution (INR)</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {productSales.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                    No product transactions.
                  </TableCell>
                </TableRow>
              ) : (
                productSales.map((row) => (
                  <TableRow key={row.product_id} hover>
                    <TableCell sx={{ fontWeight: 600 }}>{row.product_name}</TableCell>
                    <TableCell align="right">{row.quantity.toFixed(1)}</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700, color: 'primary.main' }}>
                      ₹{row.sales.toFixed(2)}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Notifications Toast */}
      <Snackbar
        open={toast.open}
        autoHideDuration={4000}
        onClose={() => setToast({ ...toast, open: false })}
      >
        <Alert severity={toast.severity} sx={{ width: '100%' }}>
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Reports;
