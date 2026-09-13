import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { authService } from '../services/apiServices';
import { getErrorMessage } from '../services/api';
import { useToast } from '../context/ToastContext';
import { Link } from 'react-router-dom';
import { Package, MapPin, Bell, User, Shield, KeyRound, Save, History, AtSign, Mail } from 'lucide-react';
import { ActivityLogBadge, ActivityLogDetails } from '../components/ActivityLogFormatter';

export const UserProfilePage = () => {
  const { user, updateProfile } = useContext(AuthContext);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [address, setAddress] = useState('');
  const [bio, setBio] = useState('');
  const [saving, setSaving] = useState(false);

  const [activeTab, setActiveTab] = useState('profile');
  const [activityLogs, setActivityLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [profileLoading, setProfileLoading] = useState(true);

  const { showSuccess, showError } = useToast();

  useEffect(() => {
    fetchProfile();
  }, []);

  useEffect(() => {
    if (activeTab === 'activity') {
      fetchActivityLogs();
    }
  }, [activeTab]);

  const fetchProfile = async () => {
    setProfileLoading(true);
    try {
      const res = await authService.getProfile();
      setUsername(res.data.username || user?.username || '');
      setEmail(res.data.email || user?.email || '');
      setFirstName(res.data.first_name || '');
      setLastName(res.data.last_name || '');
      setPhoneNumber(res.data.phone_number || '');
      setAddress(res.data.address || '');
      setBio(res.data.bio || '');
    } catch (err) {
      console.error(err);
    } finally {
      setProfileLoading(false);
    }
  };

  const fetchActivityLogs = async () => {
    setLogsLoading(true);
    try {
      const res = await authService.getActivityLogs();
      const list = Array.isArray(res?.data) ? res.data : (res?.data?.results || []);
      setActivityLogs(list);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setLogsLoading(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await updateProfile({
        first_name: firstName,
        last_name: lastName,
        phone_number: phoneNumber,
        address,
        bio,
      });
      showSuccess('Profile updated & saved to database!');
      fetchProfile();
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="w-full bg-white min-h-[calc(100vh-140px)] py-6 px-4 md:px-6 text-[#111]">
      <div className="max-w-[1000px] mx-auto">
        <h1 className="text-3xl font-normal mb-6">Your Account</h1>
        
        {/* Navigation Grid Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 mb-8">
          <Link to="/orders" className="border border-[#D5D9D9] rounded-xl p-4 flex items-center gap-4 hover:bg-[#F0F2F2] transition-all cursor-pointer shadow-sm group">
            <div className="w-12 h-12 rounded-xl bg-amber-50 border border-amber-200/80 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <Package className="w-6 h-6 text-amber-600" />
            </div>
            <div className="min-w-0">
              <h2 className="font-bold text-base text-[#111] leading-tight truncate">Your Orders</h2>
              <p className="text-xs text-[#565959] mt-0.5 truncate">Track, return, or buy things again</p>
            </div>
          </Link>

          <Link to="/addresses" className="border border-[#D5D9D9] rounded-xl p-4 flex items-center gap-4 hover:bg-[#F0F2F2] transition-all cursor-pointer shadow-sm group">
            <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-200/80 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <MapPin className="w-6 h-6 text-blue-600" />
            </div>
            <div className="min-w-0">
              <h2 className="font-bold text-base text-[#111] leading-tight truncate">Your Addresses</h2>
              <p className="text-xs text-[#565959] mt-0.5 truncate">Edit addresses for orders</p>
            </div>
          </Link>

          <Link to="/notifications" className="border border-[#D5D9D9] rounded-xl p-4 flex items-center gap-4 hover:bg-[#F0F2F2] transition-all cursor-pointer shadow-sm group">
            <div className="w-12 h-12 rounded-xl bg-purple-50 border border-purple-200/80 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <Bell className="w-6 h-6 text-purple-600" />
            </div>
            <div className="min-w-0">
              <h2 className="font-bold text-base text-[#111] leading-tight truncate">Notifications</h2>
              <p className="text-xs text-[#565959] mt-0.5 truncate">View store alerts and updates</p>
            </div>
          </Link>
        </div>

        {/* Profile Content Box */}
        <div className="border border-[#D5D9D9] rounded-xl p-6 bg-white shadow-sm">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 border-b border-[#D5D9D9] pb-4">
            <div>
              <h2 className="text-xl font-bold text-[#111]">Login & security</h2>
              <p className="text-sm text-[#565959]">Manage username, profile information, and account details</p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setActiveTab('profile')}
                className={`px-4 py-2 text-sm rounded-lg transition-colors ${activeTab === 'profile' ? 'bg-[#F0F2F2] border border-[#D5D9D9] font-bold text-[#111]' : 'text-amazon-link-teal hover:underline'}`}
              >
                Profile Info
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('activity')}
                className={`px-4 py-2 text-sm rounded-lg transition-colors ${activeTab === 'activity' ? 'bg-[#F0F2F2] border border-[#D5D9D9] font-bold text-[#111]' : 'text-amazon-link-teal hover:underline'}`}
              >
                Activity Logs
              </button>
            </div>
          </div>

          {activeTab === 'profile' ? (
            profileLoading ? (
              <div className="py-8 text-center text-[#565959]">Loading profile...</div>
            ) : (
            <form onSubmit={handleUpdate} className="max-w-2xl space-y-5">
              {/* Username & Email Header Display */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-[#F0F2F2] p-4 rounded-xl border border-[#D5D9D9]">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-700 shrink-0">
                    <AtSign className="w-5 h-5" />
                  </div>
                  <div>
                    <label className="text-[11px] font-extrabold text-[#565959] uppercase tracking-wider block">Username</label>
                    <div className="font-bold text-sm text-[#111]">@{username || user?.username || 'user'}</div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-700 shrink-0">
                    <Mail className="w-5 h-5" />
                  </div>
                  <div>
                    <label className="text-[11px] font-extrabold text-[#565959] uppercase tracking-wider block">Email Address</label>
                    <div className="font-bold text-sm text-[#111] truncate">{email || user?.email || 'N/A'}</div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-bold block mb-1 text-[#111]">First Name</label>
                  <input
                    type="text"
                    className="w-full border border-[#949494] bg-white rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
                    placeholder="Enter first name..."
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                  />
                </div>

                <div>
                  <label className="text-sm font-bold block mb-1 text-[#111]">Last Name</label>
                  <input
                    type="text"
                    className="w-full border border-[#949494] bg-white rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
                    placeholder="Enter last name..."
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <label className="text-sm font-bold block mb-1 text-[#111]">Phone Number</label>
                <input
                  type="text"
                  className="w-full border border-[#949494] bg-white rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
                  placeholder="e.g. +1 (555) 000-0000"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                />
              </div>

              <div>
                <label className="text-sm font-bold block mb-1 text-[#111]">Primary Address</label>
                <input
                  type="text"
                  className="w-full border border-[#949494] bg-white rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow"
                  placeholder="Enter primary address..."
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                />
              </div>

              <div>
                <label className="text-sm font-bold block mb-1 text-[#111]">Bio / Preferences</label>
                <textarea
                  className="w-full border border-[#949494] bg-white rounded px-3 py-2 text-sm focus:outline-none focus:border-[#e77600] focus:shadow-[0_0_3px_2px_rgba(228,121,17,0.5)] transition-shadow min-h-[80px]"
                  placeholder="Shopping preferences or notes..."
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                />
              </div>

              <div className="pt-2">
                <button type="submit" disabled={saving} className="btn-secondary py-2 px-6 shadow-sm text-sm disabled:opacity-50 font-bold">
                  {saving ? 'Saving...' : 'Save changes'}
                </button>
              </div>
            </form>
            )
          ) : (
            <div className="space-y-4">
              <h3 className="font-bold text-[#111]">Recent Account Activity</h3>
              
              {logsLoading ? (
                <p className="text-sm text-[#565959]">Loading activity logs...</p>
              ) : activityLogs.length === 0 ? (
                <p className="text-sm text-[#565959]">No recent activity recorded.</p>
              ) : (
                <div className="border border-[#D5D9D9] rounded-lg overflow-hidden divide-y divide-[#D5D9D9]">
                  {activityLogs.map((log) => (
                    <div key={log.id} className="p-4 flex flex-col sm:flex-row items-start justify-between gap-4">
                      <div className="space-y-1">
                        <ActivityLogBadge action={log.action || log.event} />
                        <div className="mt-1">
                          <ActivityLogDetails details={log.details} />
                        </div>
                      </div>
                      <div className="text-sm text-[#565959] whitespace-nowrap">
                        {new Date(log.timestamp || log.created_at || Date.now()).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
