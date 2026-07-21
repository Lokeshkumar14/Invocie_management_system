import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  CircularProgress,
  Snackbar,
  Alert,
  Divider
} from '@mui/material';
import {
  Save,
  Business,
  AccountBalance
} from '@mui/icons-material';
import api from '../services/api';

const Settings = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

  const { register, handleSubmit, reset, setValue, formState: { errors } } = useForm();

  useEffect(() => {
    const fetchCompanyDetails = async () => {
      try {
        const response = await api.get('/settings/company');
        reset(response.data);
      } catch (err) {
        console.error(err);
        showToast('Failed to load company details', 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchCompanyDetails();
  }, [reset]);

  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  const onSubmit = async (data) => {
    setSaving(true);
    try {
      await api.put('/settings/company', data);
      showToast('Company settings saved successfully');
    } catch (err) {
      console.error(err);
      showToast('Failed to update company settings', 'error');
    } finally {
      setSaving(false);
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
            System Settings
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Configure your enterprise details, bank information, logo, and active GST state.
          </Typography>
        </Box>
      </Box>

      <form onSubmit={handleSubmit(onSubmit)}>
        <Grid container spacing={3}>
          {/* Company Details Form */}
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                  <Business color="primary" />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>Enterprise Branding</Typography>
                </Box>
                <Divider sx={{ mb: 3 }} />
                
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      label="Company Name"
                      fullWidth
                      required
                      {...register('company_name', { required: 'Company name is required' })}
                      error={!!errors.company_name}
                      helperText={errors.company_name?.message}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      label="Corporate Billing Address"
                      fullWidth
                      multiline
                      rows={4}
                      required
                      {...register('address', { required: 'Address is required' })}
                      error={!!errors.address}
                      helperText={errors.address?.message || 'Must contain state at the end (e.g. Surat, Gujarat - 395006)'}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="GSTIN (GST Number)"
                      fullWidth
                      required
                      {...register('gst', { required: 'GST Number is required' })}
                      error={!!errors.gst}
                      helperText={errors.gst?.message}
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="PAN Number"
                      fullWidth
                      required
                      {...register('pan', { required: 'PAN is required' })}
                      error={!!errors.pan}
                      helperText={errors.pan?.message}
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Bank & Remittance details */}
          <Grid item xs={12} md={6}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ display: 'flex', flexDirection: 'column', height: '100%', p: { xs: 2, sm: 3 } }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                  <AccountBalance color="primary" />
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>Bank Remittance Info</Typography>
                </Box>
                <Divider sx={{ mb: 3 }} />
                
                <Grid container spacing={2} sx={{ flexGrow: 1 }}>
                  <Grid item xs={12}>
                    <TextField
                      label="Beneficiary Bank Name"
                      fullWidth
                      required
                      {...register('bank_name', { required: 'Bank name is required' })}
                      error={!!errors.bank_name}
                      helperText={errors.bank_name?.message}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      label="Account Number"
                      fullWidth
                      required
                      {...register('account_number', { required: 'Account Number is required' })}
                      error={!!errors.account_number}
                      helperText={errors.account_number?.message}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      label="IFSC Routing Code"
                      fullWidth
                      required
                      {...register('ifsc', { required: 'IFSC is required' })}
                      error={!!errors.ifsc}
                      helperText={errors.ifsc?.message}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      label="Company Logo Base64 Data URI"
                      fullWidth
                      placeholder="data:image/png;base64,..."
                      {...register('logo')}
                    />
                  </Grid>
                </Grid>

                <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
                  <Button
                    type="submit"
                    variant="contained"
                    startIcon={<Save />}
                    disabled={saving}
                    sx={{ px: 4, width: { xs: '100%', sm: 'auto' } }}
                  >
                    {saving ? 'Saving...' : 'Save Settings'}
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </form>

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

export default Settings;
