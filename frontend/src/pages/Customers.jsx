import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  TextField,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Snackbar,
  Alert,
  CircularProgress,
  MenuItem
} from '@mui/material';
import {
  Add,
  Search,
  Edit,
  Delete,
  History,
  Close
} from '@mui/icons-material';
import api from '../services/api';

const Customers = () => {
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  
  // History Modal
  const [historyOpen, setHistoryOpen] = useState(false);
  const [customerHistory, setCustomerHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Toast notifications
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm();

  const fetchCustomers = async (searchVal = '') => {
    setLoading(true);
    try {
      const response = await api.get(`/customers?search=${searchVal}`);
      setCustomers(response.data);
    } catch (err) {
      console.error(err);
      showToast('Failed to fetch customers', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers(search);
  }, [search]);

  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  const handleOpenDialog = (customer = null) => {
    setSelectedCustomer(customer);
    reset({
      company_name: '',
      contact_person: '',
      mobile: '',
      email: '',
      gst_number: '',
      pan_number: '',
      address: '',
      city: '',
      state: '',
      pincode: '',
      shipping_address: ''
    });

    if (customer) {
      Object.keys(customer).forEach(key => {
        setValue(key, customer[key]);
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedCustomer(null);
  };

  const onSubmit = async (data) => {
    try {
      if (selectedCustomer) {
        // Edit Customer
        await api.put(`/customers/${selectedCustomer.id}`, data);
        showToast('Customer updated successfully');
      } else {
        // Add Customer
        await api.post('/customers', data);
        showToast('Customer added successfully');
      }
      fetchCustomers(search);
      handleCloseDialog();
    } catch (err) {
      console.error(err);
      showToast(err.response?.data?.detail || 'Failed to save customer', 'error');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this customer?')) {
      try {
        await api.delete(`/customers/${id}`);
        showToast('Customer deleted successfully');
        fetchCustomers(search);
      } catch (err) {
        console.error(err);
        showToast(err.response?.data?.detail || 'Failed to delete customer', 'error');
      }
    }
  };

  const handleViewHistory = async (customer) => {
    setSelectedCustomer(customer);
    setHistoryOpen(true);
    setHistoryLoading(true);
    try {
      const response = await api.get(`/customers/${customer.id}/history`);
      setCustomerHistory(response.data);
    } catch (err) {
      console.error(err);
      showToast('Failed to fetch invoice history', 'error');
    } finally {
      setHistoryLoading(false);
    }
  };

  const handleCloseHistory = () => {
    setHistoryOpen(false);
    setCustomerHistory([]);
    setSelectedCustomer(null);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, flexDirection: { xs: 'column', sm: 'row' }, gap: 2, mb: { xs: 2.5, sm: 4 } }}>
        <Box>
          <Typography variant="h4" sx={{ fontFamily: '"Outfit", sans-serif', fontWeight: 700, fontSize: { xs: '1.55rem', sm: '2.125rem' }, mb: 0.5 }}>
            Customers List
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage customer directories, addresses, GSTIN records, and lookup history.
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpenDialog()}
          sx={{ background: 'linear-gradient(45deg, #2563eb, #0d9488)', width: { xs: '100%', sm: 'auto' } }}
        >
          Add Customer
        </Button>
      </Box>

      {/* Filter and Search */}
      <Card sx={{ mb: 4 }}>
        <CardContent sx={{ py: 2 }}>
          <TextField
            placeholder="Search by Company Name, Contact Person or GSTIN..."
            fullWidth
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search color="action" />
                </InputAdornment>
              ),
            }}
          />
        </CardContent>
      </Card>

      {/* Main Table */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper} sx={{ maxWidth: '100%' }}>
          <Table sx={{ minWidth: 650 }} aria-label="simple table">
            <TableHead sx={{ bgcolor: '#f8fafc' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Company Name</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Contact Person</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Mobile</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>GSTIN</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>City & State</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {customers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                    No customers found. Click "Add Customer" to insert record.
                  </TableCell>
                </TableRow>
              ) : (
                customers.map((cust) => (
                  <TableRow key={cust.id} hover>
                    <TableCell sx={{ fontWeight: 600 }}>{cust.company_name}</TableCell>
                    <TableCell>{cust.contact_person || '-'}</TableCell>
                    <TableCell>{cust.mobile || '-'}</TableCell>
                    <TableCell sx={{ fontFamily: 'monospace', fontWeight: 500 }}>
                      {cust.gst_number || '-'}
                    </TableCell>
                    <TableCell>{cust.city ? `${cust.city}, ${cust.state}` : '-'}</TableCell>
                    <TableCell align="right">
                      <IconButton 
                        color="secondary" 
                        size="small" 
                        title="Billing History" 
                        onClick={() => handleViewHistory(cust)}
                        sx={{ mr: 0.5 }}
                      >
                        <History />
                      </IconButton>
                      <IconButton 
                        color="primary" 
                        size="small" 
                        title="Edit Customer" 
                        onClick={() => handleOpenDialog(cust)}
                        sx={{ mr: 0.5 }}
                      >
                        <Edit />
                      </IconButton>
                      <IconButton 
                        color="error" 
                        size="small" 
                        title="Delete Customer" 
                        onClick={() => handleDelete(cust.id)}
                      >
                        <Delete />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Add / Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle sx={{ fontFamily: '"Outfit", sans-serif', fontWeight: 600 }}>
          {selectedCustomer ? 'Edit Customer Details' : 'Create New Customer'}
        </DialogTitle>
        <DialogContent dividers>
          <form id="customer-form" onSubmit={handleSubmit(onSubmit)}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Company Name"
                  fullWidth
                  required
                  {...register('company_name', { required: 'Company name is required' })}
                  error={!!errors.company_name}
                  helperText={errors.company_name?.message}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Contact Person"
                  fullWidth
                  {...register('contact_person')}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Mobile Number"
                  fullWidth
                  {...register('mobile')}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Email Address"
                  type="email"
                  fullWidth
                  {...register('email')}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="GSTIN (GST Number)"
                  fullWidth
                  placeholder="e.g. 24AAAAA0000A1Z5"
                  {...register('gst_number')}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="PAN Number"
                  fullWidth
                  placeholder="e.g. ABCDE1234F"
                  {...register('pan_number')}
                />
              </Grid>
              <Grid item xs={12} sm={8}>
                <TextField
                  label="Billing Address"
                  fullWidth
                  multiline
                  rows={2}
                  {...register('address')}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  label="Pincode"
                  fullWidth
                  {...register('pincode')}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="City"
                  fullWidth
                  {...register('city')}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  select
                  label="State"
                  fullWidth
                  required
                  defaultValue=""
                  {...register('state', { required: 'State is required for GST calculations' })}
                  error={!!errors.state}
                  helperText={errors.state?.message || 'Must match your company state for CGST/SGST'}
                >
                  {[
                    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
                    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
                    'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
                    'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
                    'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
                    'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
                    'Andaman and Nicobar Islands', 'Chandigarh', 'Dadra and Nagar Haveli and Daman and Diu',
                    'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
                  ].map(s => (
                    <MenuItem key={s} value={s}>{s}</MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Shipping Address (If different from billing)"
                  fullWidth
                  multiline
                  rows={2}
                  {...register('shipping_address')}
                />
              </Grid>
            </Grid>
          </form>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} color="inherit">Cancel</Button>
          <Button type="submit" form="customer-form" variant="contained" color="primary">
            Save Customer
          </Button>
        </DialogActions>
      </Dialog>

      {/* Billing History Dialog */}
      <Dialog open={historyOpen} onClose={handleCloseHistory} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" sx={{ fontFamily: '"Outfit", sans-serif', fontWeight: 600 }}>
            Billing History: {selectedCustomer?.company_name}
          </Typography>
          <IconButton onClick={handleCloseHistory} size="small">
            <Close />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          {historyLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : customerHistory.length === 0 ? (
            <Box sx={{ py: 4, textAlign: 'center' }}>
              <Typography color="text.secondary">No invoices generated for this customer.</Typography>
            </Box>
          ) : (
            <TableContainer component={Paper} sx={{ boxShadow: 'none', border: '1px solid #e2e8f0' }}>
              <Table size="small">
                <TableHead sx={{ bgcolor: '#f8fafc' }}>
                  <TableRow>
                    <TableCell>Invoice No</TableCell>
                    <TableCell>Date</TableCell>
                    <TableCell align="right">Subtotal</TableCell>
                    <TableCell align="right">GST Total</TableCell>
                    <TableCell align="right">Grand Total</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {customerHistory.map((inv) => (
                    <TableRow key={inv.id}>
                      <TableCell sx={{ fontWeight: 600 }}>{inv.invoice_number}</TableCell>
                      <TableCell>{new Date(inv.invoice_date).toLocaleDateString('en-IN')}</TableCell>
                      <TableCell align="right">₹{inv.subtotal.toFixed(2)}</TableCell>
                      <TableCell align="right">
                        ₹{(inv.cgst + inv.sgst + inv.igst).toFixed(2)}
                      </TableCell>
                      <TableCell align="right" sx={{ fontWeight: 600 }}>
                        ₹{inv.grand_total.toFixed(2)}
                      </TableCell>
                      <TableCell>
                        <Box
                          sx={{
                            display: 'inline-block',
                            px: 1,
                            py: 0.25,
                            borderRadius: 1,
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            bgcolor: inv.status === 'paid' ? 'success.light' : 'warning.light',
                            color: inv.status === 'paid' ? 'success.contrastText' : 'warning.contrastText',
                          }}
                        >
                          {inv.status?.toUpperCase()}
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseHistory} variant="contained" color="inherit">Close</Button>
        </DialogActions>
      </Dialog>

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

export default Customers;
