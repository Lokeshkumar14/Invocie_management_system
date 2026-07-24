import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  MenuItem,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Divider,
  Snackbar,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Add,
  Delete,
  Save,
  Cancel
} from '@mui/icons-material';
import api from '../services/api';
import { numberToWords } from '../utils/numberToWords';

const InvoiceCreate = () => {
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [companyDetails, setCompanyDetails] = useState(null);
  
  // Form fields
  const [selectedCustomerId, setSelectedCustomerId] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [invoiceNumber, setInvoiceNumber] = useState('AUTO');
  const [invoiceDate, setInvoiceDate] = useState(new Date().toISOString().split('T')[0]);
  const [transport, setTransport] = useState('');
  const [saleOrder, setSaleOrder] = useState('');
  const [paymentTerms, setPaymentTerms] = useState('Net 30');
  const [challanNumber, setChallanNumber] = useState('');
  const [jobWorkReference, setJobWorkReference] = useState('');
  const [jobWorkDescription, setJobWorkDescription] = useState('');
  const [remarks, setRemarks] = useState('');
  
  // Invoiced line items
  const [items, setItems] = useState([
    { product_id: '', quantity: 1, rate: 0, hsn: '', color: '', gst_percentage: 0, amount: 0, gst_amount: 0, dc_number: '', dc_date: '', dia: '', rolls: '' }
  ]);

  // Loading & alerts
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

  const navigate = useNavigate();
  const location = useLocation();
  const isJobWork = location.pathname === '/invoice/job-work';

  useEffect(() => {
    const loadMetadata = async () => {
      try {
        const [custRes, prodRes, compRes] = await Promise.all([
          api.get('/customers'),
          api.get('/products'),
          api.get('/settings/company')
        ]);
        setCustomers(custRes.data);
        setProducts(prodRes.data);
        setCompanyDetails(compRes.data);
      } catch (err) {
        console.error(err);
        showToast('Failed to fetch product or customer data', 'error');
      } finally {
        setLoading(false);
      }
    };
    loadMetadata();
  }, []);

  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  const handleCustomerChange = (customerId) => {
    setSelectedCustomerId(customerId);
    const client = customers.find(c => c.id === customerId);
    setSelectedCustomer(client || null);
  };

  const handleAddRow = () => {
    setItems([
      ...items,
      { product_id: '', quantity: 1, rate: 0, hsn: '', color: '', gst_percentage: 0, amount: 0, gst_amount: 0, dc_number: '', dc_date: '', dia: '', rolls: '' }
    ]);
  };

  const handleRemoveRow = (index) => {
    const list = [...items];
    list.splice(index, 1);
    setItems(list);
  };

  const handleItemChange = (index, field, value) => {
    const list = [...items];
    const item = { ...list[index] };

    if (field === 'product_id') {
      const prod = products.find(p => p.id === value);
      if (prod) {
        item.product_id = value;
        item.hsn = prod.hsn || '';
        item.color = prod.color || '';
        item.gst_percentage = prod.gst_percentage || 0;
        item.rate = prod.price || 0;
      }
    } else {
      item[field] = value;
    }

    // Inline totals calculation for item row
    const qty = parseFloat(item.quantity) || 0;
    const rate = parseFloat(item.rate) || 0;
    item.amount = qty * rate;
    item.gst_amount = item.amount * ((item.gst_percentage || 0) / 100);

    list[index] = item;
    setItems(list);
  };

  // Tallies aggregates
  const calculateTotals = () => {
    const subtotal = items.reduce((sum, item) => sum + (item.amount || 0), 0);
    const totalGst = items.reduce((sum, item) => sum + (item.gst_amount || 0), 0);
    
    // GST engine logic comparison
    const companyState = (companyDetails?.state || '').trim().toLowerCase();
    const customerState = (selectedCustomer?.state || '').trim().toLowerCase();
    
    const isSameState = !!(companyState && customerState && companyState === customerState);
    
    let cgst = 0;
    let sgst = 0;
    let igst = 0;
    
    if (isSameState) {
      cgst = totalGst / 2;
      sgst = totalGst / 2;
    } else {
      igst = totalGst;
    }
    
    const grandTotal = subtotal + cgst + sgst + igst;
    
    return {
      subtotal,
      cgst,
      sgst,
      igst,
      grandTotal,
      amountWords: numberToWords(grandTotal)
    };
  };

  const totals = calculateTotals();

  const getValidItems = () => {
    return items.filter(item => item.product_id && item.quantity > 0 && item.rate > 0);
  };

  const handleSaveInvoice = async () => {
    // Validations
    if (!selectedCustomerId) {
      showToast('Please select a customer', 'error');
      return;
    }
    
    const validItems = items.filter(item => item.product_id && item.quantity > 0);
    if (validItems.length === 0) {
      showToast('Please add at least one product line item', 'error');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        invoice_number: invoiceNumber,
        invoice_date: invoiceDate,
        customer_id: parseInt(selectedCustomerId),
        transport,
        sale_order: saleOrder,
        payment_terms: paymentTerms,
        invoice_type: isJobWork ? 'job_work' : 'tax_invoice',
        challan_number: challanNumber,
        job_work_reference: jobWorkReference,
        job_work_description: jobWorkDescription,
        remarks,
        status: 'unpaid',
        items: validItems.map(item => ({
          product_id: parseInt(item.product_id),
          quantity: parseFloat(item.quantity),
          rate: parseFloat(item.rate),
          dc_number: isJobWork ? item.dc_number || null : null,
          dc_date: isJobWork ? item.dc_date || null : null,
          dia: isJobWork ? item.dia || null : null,
          rolls: isJobWork && item.rolls !== '' ? parseFloat(item.rolls) : null
        }))
      };

      await api.post('/invoice', payload);
      showToast('Invoice created successfully', 'success');
      // Redirect to history
      setTimeout(() => navigate('/invoice/history'), 1500);
    } catch (err) {
      console.error(err);
      showToast(err.response?.data?.detail || 'Failed to generate invoice', 'error');
    } finally {
      setSubmitting(false);
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: { xs: 'flex-start', sm: 'center' }, flexDirection: { xs: 'column', sm: 'row' }, gap: 1, mb: { xs: 2.5, sm: 4 } }}>
        <Box>
          <Typography variant="h4" sx={{ fontFamily: '"Outfit", sans-serif', fontWeight: 700, fontSize: { xs: '1.55rem', sm: '2.125rem' }, mb: 0.5 }}>
            {isJobWork ? 'Create Job Work Invoice' : 'Create GST Invoice'}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {isJobWork
              ? 'Bill processing and job-work charges with challan and job references.'
              : 'Select products, compute automatic CGST/SGST/IGST, and compile billing documentation.'}
          </Typography>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Left Side - Invoice Inputs */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ mb: 3 }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>Invoice Header</Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    select
                    label="Customer / Client Company"
                    fullWidth
                    required
                    value={selectedCustomerId}
                    onChange={(e) => handleCustomerChange(e.target.value)}
                  >
                    {customers.map(c => (
                      <MenuItem key={c.id} value={c.id}>{c.company_name}</MenuItem>
                    ))}
                  </TextField>
                </Grid>
                {isJobWork && (
                  <>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        label="Customer Challan Number"
                        fullWidth
                        value={challanNumber}
                        onChange={(e) => setChallanNumber(e.target.value)}
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        label="Job Work Reference"
                        fullWidth
                        placeholder="e.g. JW/2026/014"
                        value={jobWorkReference}
                        onChange={(e) => setJobWorkReference(e.target.value)}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        label="Job Work Description"
                        fullWidth
                        placeholder="e.g. Dyeing, embroidery, stitching or processing charges"
                        value={jobWorkDescription}
                        onChange={(e) => setJobWorkDescription(e.target.value)}
                      />
                    </Grid>
                  </>
                )}
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Invoice Number"
                    fullWidth
                    helperText='Type "AUTO" for automatic serial numbering'
                    value={invoiceNumber}
                    onChange={(e) => setInvoiceNumber(e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Invoice Date"
                    type="date"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    value={invoiceDate}
                    onChange={(e) => setInvoiceDate(e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Transport Details"
                    fullWidth
                    placeholder="e.g. VRL Logistics, Self"
                    value={transport}
                    onChange={(e) => setTransport(e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Sale Order Reference"
                    fullWidth
                    value={saleOrder}
                    onChange={(e) => setSaleOrder(e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    select
                    label="Payment Terms"
                    fullWidth
                    value={paymentTerms}
                    onChange={(e) => setPaymentTerms(e.target.value)}
                  >
                    {[
                      'Immediate',
                      'COD',
                      'Net 7',
                      'Net 15',
                      'Net 30',
                      'Net 45',
                      'Net 60',
                      'Net 90',
                    ].map(term => (
                      <MenuItem key={term} value={term}>{term}</MenuItem>
                    ))}
                  </TextField>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Items Section */}
          <Card>
            <CardContent sx={{ p: { xs: 1.5, sm: 3 } }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 1, mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>{isJobWork ? 'Job Charges' : 'Items & Rates'}</Typography>
                <Button 
                  variant="outlined" 
                  startIcon={<Add />} 
                  onClick={handleAddRow}
                  size="small"
                >
                  Add Row
                </Button>
              </Box>

              <TableContainer component={Paper} sx={{ boxShadow: 'none', border: '1px solid #f1f5f9', maxWidth: '100%' }}>
                <Table size="small" sx={{ minWidth: isJobWork ? 980 : 760 }} aria-label="Invoice items. Scroll sideways on small screens to see all columns.">
                  <TableHead sx={{ bgcolor: '#f8fafc' }}>
                    <TableRow>
                      {isJobWork && <TableCell sx={{ fontWeight: 600 }}>DC No.</TableCell>}
                      {isJobWork && <TableCell sx={{ fontWeight: 600 }}>DC Date</TableCell>}
                      <TableCell sx={{ minWidth: 160, fontWeight: 600 }}>{isJobWork ? 'Fabric / Work' : 'Product Name'}</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>HSN</TableCell>
                      {isJobWork && <TableCell sx={{ fontWeight: 600 }}>Dia</TableCell>}
                      {isJobWork && <TableCell sx={{ fontWeight: 600 }}>Rolls</TableCell>}
                      <TableCell sx={{ fontWeight: 600 }}>{isJobWork ? 'Weight' : 'Qty'}</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Rate</TableCell>
                      {!isJobWork && <TableCell sx={{ fontWeight: 600 }}>GST %</TableCell>}
                      <TableCell align="right" sx={{ fontWeight: 600 }}>Amount</TableCell>
                      <TableCell align="center" sx={{ width: 50 }}></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {items.map((item, idx) => (
                      <TableRow key={idx}>
                        {isJobWork && <TableCell><TextField size="small" value={item.dc_number} onChange={(e) => handleItemChange(idx, 'dc_number', e.target.value)} sx={{ width: 70 }} /></TableCell>}
                        {isJobWork && <TableCell><TextField type="date" size="small" value={item.dc_date} onChange={(e) => handleItemChange(idx, 'dc_date', e.target.value)} sx={{ width: 125 }} /></TableCell>}
                        <TableCell>
                          <TextField
                            select
                            fullWidth
                            size="small"
                            value={item.product_id}
                            onChange={(e) => handleItemChange(idx, 'product_id', e.target.value)}
                          >
                            {products.map(p => (
                              <MenuItem key={p.id} value={p.id}>
                                {p.product_name} {p.color ? `(${p.color})` : ''}
                              </MenuItem>
                            ))}
                          </TextField>
                        </TableCell>
                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                          {item.hsn || '-'}
                        </TableCell>
                        {isJobWork && <TableCell><TextField size="small" value={item.dia} onChange={(e) => handleItemChange(idx, 'dia', e.target.value)} sx={{ width: 65 }} /></TableCell>}
                        {isJobWork && <TableCell><TextField type="number" size="small" inputProps={{ min: '0', step: 'any' }} value={item.rolls} onChange={(e) => handleItemChange(idx, 'rolls', e.target.value)} sx={{ width: 65 }} /></TableCell>}
                        <TableCell>
                          <TextField
                            type="number"
                            size="small"
                            inputProps={{ min: "0.1", step: "any" }}
                            value={item.quantity}
                            onChange={(e) => handleItemChange(idx, 'quantity', e.target.value)}
                            sx={{ width: 80 }}
                          />
                        </TableCell>
                        <TableCell>
                          <TextField
                            type="number"
                            size="small"
                            inputProps={{ min: "0", step: "0.01" }}
                            value={item.rate}
                            onChange={(e) => handleItemChange(idx, 'rate', e.target.value)}
                            sx={{ width: 100 }}
                          />
                        </TableCell>
                        {!isJobWork && <TableCell sx={{ fontSize: '0.85rem' }}>{item.gst_percentage}%</TableCell>}
                        <TableCell align="right" sx={{ fontWeight: 500, fontSize: '0.9rem' }}>
                          ₹{item.amount.toFixed(2)}
                        </TableCell>
                        <TableCell align="center">
                          <IconButton 
                            size="small" 
                            color="error" 
                            disabled={items.length === 1}
                            onClick={() => handleRemoveRow(idx)}
                          >
                            <Delete fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Right Side - Invoice Preview & Tallies Summary */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ position: { xs: 'static', lg: 'sticky' }, top: 96, mb: 3 }}>
            <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>Billing Summary</Typography>
              
              {/* Customer Details Display */}
              {selectedCustomer ? (
                <Box sx={{ mb: 3, p: 2, bgcolor: '#f8fafc', borderRadius: 2 }}>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>{selectedCustomer.company_name}</Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    GSTIN: {selectedCustomer.gst_number || 'N/A'}
                  </Typography>
                  <Typography variant="caption" display="block" color="text.secondary">
                    State: {selectedCustomer.state || 'N/A'}
                  </Typography>
                </Box>
              ) : (
                <Alert severity="info" sx={{ mb: 3 }}>
                  Select customer to determine GST distribution.
                </Alert>
              )}

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2" color="text.secondary">Subtotal</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>₹{totals.subtotal.toFixed(2)}</Typography>
                </Box>

                {totals.cgst > 0 && (
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">CGST</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>₹{totals.cgst.toFixed(2)}</Typography>
                  </Box>
                )}

                {totals.sgst > 0 && (
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">SGST</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>₹{totals.sgst.toFixed(2)}</Typography>
                  </Box>
                )}

                {totals.igst > 0 && (
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2" color="text.secondary">IGST (Interstate)</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>₹{totals.igst.toFixed(2)}</Typography>
                  </Box>
                )}

                <Divider sx={{ my: 1 }} />

                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700, color: 'primary.main' }}>Grand Total</Typography>
                  <Typography variant="subtitle1" sx={{ fontWeight: 700, color: 'primary.main' }}>
                    ₹{totals.grandTotal.toFixed(2)}
                  </Typography>
                </Box>

                {totals.grandTotal > 0 && (
                  <Box sx={{ mt: 1, p: 1.5, bgcolor: '#f0fdf4', borderRadius: 1.5, border: '1px solid #dcfce7' }}>
                    <Typography variant="caption" color="success.dark" sx={{ fontStyle: 'italic', fontWeight: 500, display: 'block' }}>
                      {totals.amountWords}
                    </Typography>
                  </Box>
                )}
              </Box>

              <TextField
                label="Remarks / Terms & Conditions"
                fullWidth
                multiline
                rows={2}
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                sx={{ mt: 3 }}
              />

              <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, gap: 1.5, mt: 4 }}>
                <Button
                  variant="contained"
                  fullWidth
                  color="primary"
                  startIcon={<Save />}
                  onClick={handleSaveInvoice}
                  disabled={submitting}
                >
                  {submitting ? 'Generating...' : 'Save & Print'}
                </Button>
                <Button
                  variant="outlined"
                  fullWidth
                  color="inherit"
                  startIcon={<Cancel />}
                  onClick={() => navigate('/invoice/history')}
                  disabled={submitting}
                >
                  Cancel
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

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

export default InvoiceCreate;
