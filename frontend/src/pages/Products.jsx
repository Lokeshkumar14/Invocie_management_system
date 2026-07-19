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
  Delete
} from '@mui/icons-material';
import api from '../services/api';

const units = ['Meters', 'Pcs', 'Kgs', 'Rolls', 'Yards', 'Boxes'];
const gstRates = [0, 5, 12, 18, 28];

const Products = () => {
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);

  // Toast notifications
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm();

  const fetchProducts = async (searchVal = '') => {
    setLoading(true);
    try {
      const response = await api.get(`/products?search=${searchVal}`);
      setProducts(response.data);
    } catch (err) {
      console.error(err);
      showToast('Failed to fetch products', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts(search);
  }, [search]);

  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  const handleOpenDialog = (product = null) => {
    setSelectedProduct(product);
    reset({
      product_name: '',
      hsn: '',
      description: '',
      unit: 'Meters',
      color: '',
      gst_percentage: 5,
      price: 0
    });

    if (product) {
      Object.keys(product).forEach(key => {
        setValue(key, product[key]);
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedProduct(null);
  };

  const onSubmit = async (data) => {
    try {
      // Cast numbers to proper types
      const payload = {
        ...data,
        price: parseFloat(data.price),
        gst_percentage: parseFloat(data.gst_percentage)
      };

      if (selectedProduct) {
        // Edit Product
        await api.put(`/products/${selectedProduct.id}`, payload);
        showToast('Product updated successfully');
      } else {
        // Add Product
        await api.post('/products', payload);
        showToast('Product added successfully');
      }
      fetchProducts(search);
      handleCloseDialog();
    } catch (err) {
      console.error(err);
      showToast(err.response?.data?.detail || 'Failed to save product', 'error');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this product?')) {
      try {
        await api.delete(`/products/${id}`);
        showToast('Product deleted successfully');
        fetchProducts(search);
      } catch (err) {
        console.error(err);
        showToast(err.response?.data?.detail || 'Failed to delete product', 'error');
      }
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h4" sx={{ fontFamily: '"Outfit", sans-serif', fontWeight: 700, mb: 0.5 }}>
            Product Catalog
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage fabric and yarn materials, colors, unit rules, prices, and HSN/GST configurations.
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpenDialog()}
          sx={{ background: 'linear-gradient(45deg, #2563eb, #0d9488)' }}
        >
          Add Product
        </Button>
      </Box>

      {/* Filter and Search */}
      <Card sx={{ mb: 4 }}>
        <CardContent sx={{ py: 2 }}>
          <TextField
            placeholder="Search by Product Name, HSN Code or Color..."
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
        <TableContainer component={Paper}>
          <Table sx={{ minWidth: 650 }}>
            <TableHead sx={{ bgcolor: '#f8fafc' }}>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Product Name</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>HSN Code</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Color</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Unit</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>Base Price (INR)</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>GST Rate</TableCell>
                <TableCell align="right" sx={{ fontWeight: 600 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {products.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                    No products found. Click "Add Product" to populate details.
                  </TableCell>
                </TableRow>
              ) : (
                products.map((prod) => (
                  <TableRow key={prod.id} hover>
                    <TableCell sx={{ fontWeight: 600 }}>{prod.product_name}</TableCell>
                    <TableCell sx={{ fontFamily: 'monospace' }}>{prod.hsn || '-'}</TableCell>
                    <TableCell>{prod.color || '-'}</TableCell>
                    <TableCell>{prod.unit || 'Meters'}</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 500 }}>
                      ₹{prod.price.toFixed(2)}
                    </TableCell>
                    <TableCell align="right">
                      {prod.gst_percentage}%
                    </TableCell>
                    <TableCell align="right">
                      <IconButton 
                        color="primary" 
                        size="small" 
                        title="Edit Product" 
                        onClick={() => handleOpenDialog(prod)}
                        sx={{ mr: 0.5 }}
                      >
                        <Edit />
                      </IconButton>
                      <IconButton 
                        color="error" 
                        size="small" 
                        title="Delete Product" 
                        onClick={() => handleDelete(prod.id)}
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
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ fontFamily: '"Outfit", sans-serif', fontWeight: 600 }}>
          {selectedProduct ? 'Edit Product Details' : 'Add New Product'}
        </DialogTitle>
        <DialogContent dividers>
          <form id="product-form" onSubmit={handleSubmit(onSubmit)}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  label="Product / Material Name"
                  fullWidth
                  required
                  {...register('product_name', { required: 'Product name is required' })}
                  error={!!errors.product_name}
                  helperText={errors.product_name?.message}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="HSN Code"
                  fullWidth
                  {...register('hsn')}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Color / Shade"
                  fullWidth
                  placeholder="e.g. Royal Blue, Crimson"
                  {...register('color')}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  select
                  label="Measuring Unit"
                  fullWidth
                  defaultValue="Meters"
                  {...register('unit')}
                >
                  {units.map((unit) => (
                    <MenuItem key={unit} value={unit}>
                      {unit}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  select
                  label="GST Percentage"
                  fullWidth
                  defaultValue={5}
                  {...register('gst_percentage')}
                >
                  {gstRates.map((rate) => (
                    <MenuItem key={rate} value={rate}>
                      {rate}%
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Base Price (Per Unit)"
                  type="number"
                  inputProps={{ step: "0.01", min: "0" }}
                  fullWidth
                  required
                  {...register('price', { required: 'Price is required' })}
                  error={!!errors.price}
                  helperText={errors.price?.message}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Detailed Description"
                  fullWidth
                  multiline
                  rows={2}
                  {...register('description')}
                />
              </Grid>
            </Grid>
          </form>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} color="inherit">Cancel</Button>
          <Button type="submit" form="product-form" variant="contained" color="primary">
            Save Product
          </Button>
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

export default Products;
