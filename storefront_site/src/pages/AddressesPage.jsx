import React, { useState, useEffect, useContext } from 'react';
import { authService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { AuthContext } from '../context/AuthContext';
import { Modal, ConfirmDialog, EmptyState, LoadingSkeleton } from '../components/common/UIComponents';
import { Plus } from 'lucide-react';
import { Link } from 'react-router-dom';

const COUNTRIES = [
  'United States',
  'United Kingdom',
  'Canada',
  'Australia',
  'Ethiopia',
  'Germany',
  'France',
  'Italy',
  'Spain',
  'Japan',
  'China',
  'India',
  'Brazil',
  'Mexico',
  'United Arab Emirates',
  'Saudi Arabia',
  'Netherlands',
  'Sweden',
  'Norway',
  'Denmark',
  'Switzerland',
  'South Africa',
  'Nigeria',
  'Kenya',
  'Egypt',
  'Singapore',
  'New Zealand',
  'Other',
];

export default function AddressesPage() {
  const { user } = useContext(AuthContext);
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);
  const [deleteId, setDeleteId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const { showSuccess, showError } = useToast();

  const [formData, setFormData] = useState({
    title: 'Home',
    full_name: '',
    address_line_1: '',
    address_line_2: '',
    city: '',
    state: '',
    postal_code: '',
    country: 'United States',
    phone_number: '',
    is_default: false,
  });

  const fetchAddresses = async () => {
    setLoading(true);
    try {
      const res = await authService.getAddresses();
      const list = Array.isArray(res?.data) ? res.data : (res?.data?.results || []);
      setAddresses(list);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAddresses();
  }, []);

  const autoFillFromProfile = () => {
    const profileName = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.username || '';
    const profilePhone = user?.phone_number || user?.phone || '';
    const profileCountry = user?.country || 'United States';

    setFormData((prev) => ({
      ...prev,
      full_name: profileName || prev.full_name,
      phone_number: profilePhone || prev.phone_number,
      country: profileCountry || prev.country,
    }));
    showSuccess('Auto-filled contact info from your user profile!');
  };

  const handleOpenModal = (addr = null) => {
    if (addr) {
      setEditingAddress(addr);
      setFormData({
        title: addr.title || 'Home',
        full_name: addr.full_name || '',
        address_line_1: addr.address_line_1 || '',
        address_line_2: addr.address_line_2 || '',
        city: addr.city || '',
        state: addr.state || '',
        postal_code: addr.postal_code || '',
        country: addr.country || user?.country || 'United States',
        phone_number: addr.phone_number || '',
        is_default: addr.is_default || false,
      });
    } else {
      const profileName = [user?.first_name, user?.last_name].filter(Boolean).join(' ') || user?.username || '';
      const profilePhone = user?.phone_number || user?.phone || '';
      setEditingAddress(null);
      setFormData({
        title: 'Home',
        full_name: profileName,
        address_line_1: '',
        address_line_2: '',
        city: '',
        state: '',
        postal_code: '',
        country: user?.country || 'United States',
        phone_number: profilePhone,
        is_default: addresses.length === 0,
      });
    }
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.full_name.trim()) return showError('Full name is required.');
    if (!formData.address_line_1.trim()) return showError('Street address is required.');
    if (!formData.city.trim()) return showError('City is required.');
    if (!formData.postal_code.trim()) return showError('ZIP / Postal code is required.');
    if (!formData.country.trim()) return showError('Country is required.');
    
    setSubmitting(true);
    try {
      if (editingAddress) {
        await authService.updateAddress(editingAddress.id, formData);
        showSuccess('Address updated successfully');
      } else {
        await authService.createAddress(formData);
        showSuccess('New address saved successfully');
      }
      setModalOpen(false);
      fetchAddresses();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await authService.deleteAddress(deleteId);
      showSuccess('Address deleted');
      fetchAddresses();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setDeleteId(null);
    }
  };

  if (loading) {
    return (
      <div className="w-full bg-white min-h-[calc(100vh-140px)] py-6 px-4 md:px-6 text-[#111]">
        <div className="max-w-[1000px] mx-auto space-y-6">
          <h1 className="text-3xl font-normal">Your Addresses</h1>
          <LoadingSkeleton count={3} type="table" />
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-white min-h-[calc(100vh-140px)] py-6 px-4 md:px-6 text-[#111]">
      <div className="max-w-[1000px] mx-auto">
        <div className="mb-6">
          <Link to="/profile" className="text-sm text-amazon-link-teal hover:text-amazon-orange hover:underline mb-2 block">
            Your Account
          </Link>
          <h1 className="text-3xl font-normal">Your Addresses</h1>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {/* Add Address Card */}
          <div 
            onClick={() => handleOpenModal()} 
            className="border-2 border-dashed border-[#D5D9D9] rounded-lg p-6 flex flex-col items-center justify-center text-[#565959] hover:bg-[#F0F2F2] transition-colors cursor-pointer min-h-[250px]"
          >
            <Plus className="w-12 h-12 mb-2 text-[#C7C7C7]" />
            <h2 className="text-xl font-bold">Add Address</h2>
          </div>

          {addresses.map((addr) => (
            <div key={addr.id} className="border border-[#D5D9D9] rounded-lg p-5 flex flex-col justify-between min-h-[250px]">
              <div>
                {addr.is_default && (
                  <div className="text-xs font-bold text-[#565959] uppercase tracking-wider mb-2 pb-2 border-b border-[#D5D9D9]">
                    Default: {addr.title}
                  </div>
                )}
                {!addr.is_default && (
                   <div className="text-xs font-bold text-[#565959] uppercase tracking-wider mb-2 pb-2 border-b border-[#D5D9D9]">
                     {addr.title || 'Address'}
                   </div>
                )}
                <p className="font-bold text-base mt-2">{addr.full_name}</p>
                <p className="text-sm">{addr.address_line_1}</p>
                {addr.address_line_2 && <p className="text-sm">{addr.address_line_2}</p>}
                <p className="text-sm">
                  {addr.city}{addr.state ? `, ${addr.state}` : ''} {addr.postal_code || ''}
                </p>
                <p className="text-sm mt-1">{addr.country}</p>
                <p className="text-sm mt-1 text-[#565959]">Phone number: {addr.phone_number}</p>
              </div>

              <div className="flex items-center gap-3 mt-4 pt-4 text-sm text-amazon-link-teal">
                <button onClick={() => handleOpenModal(addr)} className="hover:text-amazon-orange hover:underline">
                  Edit
                </button>
                <span className="text-[#D5D9D9]">|</span>
                <button onClick={() => setDeleteId(addr.id)} className="hover:text-amazon-orange hover:underline">
                  Remove
                </button>
                {!addr.is_default && (
                  <>
                    <span className="text-[#D5D9D9]">|</span>
                    <button onClick={() => {
                        const newAddr = {...addr, is_default: true};
                        authService.updateAddress(addr.id, newAddr).then(() => fetchAddresses());
                      }} 
                      className="hover:text-amazon-orange hover:underline"
                    >
                      Set as Default
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Add / Edit Modal */}
        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title={editingAddress ? 'Edit Address' : 'Add a new address'}
        >
          <form onSubmit={handleSubmit} className="space-y-4 text-[#111]">
            <div className="bg-[#F0F2F2] p-3 rounded border border-[#D5D9D9] text-sm flex justify-between items-center">
              <span>Auto-fill from profile?</span>
              <button
                type="button"
                onClick={autoFillFromProfile}
                className="btn-secondary py-1 px-3 text-xs"
              >
                Auto-fill
              </button>
            </div>

            <div>
              <label className="block text-sm font-bold mb-1">Country/Region</label>
              <select
                value={formData.country}
                onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                required
                className="w-full border border-[#949494] bg-[#F0F2F2] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
              >
                {COUNTRIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-bold mb-1">Full name (First and Last name)</label>
              <input
                type="text"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                required
                className="w-full border border-[#949494] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
              />
            </div>
            
            <div>
              <label className="block text-sm font-bold mb-1">Phone number</label>
              <input
                type="text"
                value={formData.phone_number}
                onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                className="w-full border border-[#949494] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
              />
            </div>

            <div>
              <label className="block text-sm font-bold mb-1">Address</label>
              <input
                type="text"
                value={formData.address_line_1}
                onChange={(e) => setFormData({ ...formData, address_line_1: e.target.value })}
                placeholder="Street address, P.O. box, company name, c/o"
                required
                className="w-full border border-[#949494] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow mb-2"
              />
              <input
                type="text"
                value={formData.address_line_2}
                onChange={(e) => setFormData({ ...formData, address_line_2: e.target.value })}
                placeholder="Apartment, suite, unit, building, floor, etc."
                className="w-full border border-[#949494] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-bold mb-1">City</label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  required
                  className="w-full border border-[#949494] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
                />
              </div>
              <div>
                <label className="block text-sm font-bold mb-1">State / Province</label>
                <input
                  type="text"
                  value={formData.state}
                  onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                  className="w-full border border-[#949494] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-bold mb-1">ZIP Code</label>
              <input
                type="text"
                value={formData.postal_code}
                onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
                required
                className="w-full border border-[#949494] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
              />
            </div>
            
            <div>
              <label className="block text-sm font-bold mb-1">Address Label</label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="Home, Office, Vacation, etc."
                required
                className="w-full border border-[#949494] rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
              />
            </div>

            <div className="flex items-center gap-2 mt-4">
              <input
                type="checkbox"
                id="is_default"
                checked={formData.is_default}
                onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                className="w-4 h-4"
              />
              <label htmlFor="is_default" className="text-sm">Make this my default address</label>
            </div>

            <div className="flex gap-3 pt-4 border-t border-[#D5D9D9]">
              <button type="submit" disabled={submitting} className="btn-buy-now shadow-sm py-2 px-6 rounded-lg text-sm disabled:opacity-50">
                {submitting ? 'Saving...' : (editingAddress ? 'Save Changes' : 'Add address')}
              </button>
            </div>
          </form>
        </Modal>

        {/* Delete Confirmation */}
        <ConfirmDialog
          isOpen={!!deleteId}
          onClose={() => setDeleteId(null)}
          onConfirm={handleDelete}
          title="Delete Address"
          message="Are you sure you want to delete this address?"
        />
      </div>
    </div>
  );
}
