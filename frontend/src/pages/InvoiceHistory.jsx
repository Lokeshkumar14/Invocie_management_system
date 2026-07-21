import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  CircularProgress,
  Snackbar,
  Alert,
  Tooltip
} from '@mui/material';
import {
  Download,
  Delete,
  Visibility,
  History
} from '@mui/icons-material';
import api from '../services/api';

const InvoiceHistory = () => {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState(null);

  // Toast notifications
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

  const navigate = useNavigate();

  const fetchInvoices = async () => {
    setLoading(true);
    try {
      const response = await api.get('/invoice');
      setInvoices(response.data);
    } catch (err) {
      console.error(err);
      showToast('Failed to fetch invoice history', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, []);

  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  const handleDownloadPDF = async (id, invoiceNumber) => {
    setDownloadingId(id);
    try {
      // Fetch PDF as a binary blob
      const response = await api.get(`/invoice/${id}/pdf`, {
        responseType: 'blob'
      });
      
      const file = new Blob([response.data], { type: 'application/pdf' });
      const fileURL = URL.createObjectURL(file);
      
      // Create a temporary link element to trigger the download
      const link = document.createElement('a');
      link.href = fileURL;
      link.setAttribute('download', `Invoice_${invoiceNumber}.pdf`);
      document.body.appendChild(link);
      link.click();
      
      // Clean up after the browser has started consuming the object URL.
      // Revoking it immediately can cancel the download in some browsers.
      document.body.removeChild(link);
      window.setTimeout(() => URL.revokeObjectURL(fileURL), 1000);
      
      showToast('PDF downloaded successfully');
    } catch (err) {
      console.error(err);
      showToast('Failed to download invoice PDF', 'error');
    } finally {
      setDownloadingId(null);
    }
  };

  const handleDeleteInvoice = async (id) => {
    if (window.confirm('Are you sure you want to delete this invoice? This will remove all records permanently.')) {
      try {
        await api.delete(`/invoice/${id}`);
        showToast('Invoice deleted successfully');
        fetchInvoices();
      } catch (err) {
        console.error(err);
        showToast('Failed to delete invoice', 'error');
      }
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, flexDirection: { xs: 'column', sm: 'row' }, gap: 1, mb: { xs: 2.5, sm: 4 } }}>
        <Box>
          <Typography variant="h4" sx={{ fontFamily: '"Outfit", sans-serif', fontWeight: 700, fontSize: { xs: '1.55rem', sm: '2.125rem' }, mb: 0.5 }}>
            Invoice History
          </Typography>
          <Typography variant="body2" color="text.secondary">
            View transaction logs, audit files, stream print files, or delete invoice ledger items.
          </Typography>
        </Box>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper} sx={{ maxWidth: '100%' }}>
          <Table sx={{ minWidth: 650 }}>
            <TableHead sx={{ bgcolor: '#f8fafc' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Invoice No</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Date</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Customer Name</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>Subtotal (INR)</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>GST (INR)</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>Grand Total (INR)</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {invoices.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                    No invoice transactions found. Create your first invoice!
                  </TableCell>
                </TableRow>
              ) : (
                invoices.map((inv) => {
                  const totalGst = inv.cgst + inv.sgst + inv.igst;
                  return (
                    <TableRow key={inv.id} hover>
                      <TableCell sx={{ fontWeight: 600 }}>{inv.invoice_number}</TableCell>
                      <TableCell>{inv.invoice_type === 'job_work' ? 'Job Work' : 'Tax Invoice'}</TableCell>
                      <TableCell>
                        {new Date(inv.invoice_date).toLocaleDateString('en-IN', {
                          day: '2-digit',
                          month: 'short',
                          year: 'numeric'
                        })}
                      </TableCell>
                      <TableCell sx={{ fontWeight: 500 }}>{inv.customer?.company_name}</TableCell>
                      <TableCell align="right">₹{inv.subtotal.toFixed(2)}</TableCell>
                      <TableCell align="right">₹{totalGst.toFixed(2)}</TableCell>
                      <TableCell align="right" sx={{ fontWeight: 700, color: 'primary.main' }}>
                        ₹{inv.grand_total.toFixed(2)}
                      </TableCell>
                      <TableCell>
                        <Box
                          sx={{
                            display: 'inline-block',
                            px: 1,
                            py: 0.25,
                            borderRadius: 1.5,
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            bgcolor: inv.status === 'paid' ? '#e6f4ea' : '#fef3c7',
                            color: inv.status === 'paid' ? '#137333' : '#b25e00',
                          }}
                        >
                          {inv.status?.toUpperCase()}
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Download PDF">
                          <IconButton
                            color="primary"
                            size="small"
                            onClick={() => handleDownloadPDF(inv.id, inv.invoice_number)}
                            disabled={downloadingId === inv.id}
                            sx={{ mr: 0.5 }}
                          >
                            {downloadingId === inv.id ? (
                              <CircularProgress size={20} />
                            ) : (
                              <Download fontSize="small" />
                            )}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete Invoice">
                          <IconButton
                            color="error"
                            size="small"
                            onClick={() => handleDeleteInvoice(inv.id)}
                          >
                            <Delete fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  );
                })
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

export default InvoiceHistory;
