'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';
import { setPassword, resendVerification } from '@/lib/auth-api';

export default function SettingsPage() {
  const { user, accessToken, refreshUser } = useAuth();
  const [activeTab, setActiveTab] = useState<'account' | 'security' | 'preferences'>('account');

  // Password form state
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);

  // Verification state
  const [verificationLoading, setVerificationLoading] = useState(false);
  const [verificationSent, setVerificationSent] = useState(false);

  const handleSetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(false);

    if (newPassword !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      return;
    }

    if (!accessToken) {
      setPasswordError('Not authenticated');
      return;
    }

    setPasswordLoading(true);

    try {
      await setPassword(accessToken, newPassword);
      setPasswordSuccess(true);
      setNewPassword('');
      setConfirmPassword('');
      refreshUser();
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : 'Failed to set password');
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleResendVerification = async () => {
    if (!accessToken) return;

    setVerificationLoading(true);
    try {
      await resendVerification(accessToken);
      setVerificationSent(true);
    } catch (err) {
      console.error('Failed to resend verification:', err);
    } finally {
      setVerificationLoading(false);
    }
  };

  const tabs = [
    { id: 'account', label: 'Account' },
    { id: 'security', label: 'Security' },
    { id: 'preferences', label: 'Preferences' },
  ] as const;

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Manage your account settings and preferences</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-6 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="p-6">
          {activeTab === 'account' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Account Information</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <p className="mt-1 text-sm text-gray-900">{user?.email}</p>
                    {!user?.email_verified && (
                      <div className="mt-2 flex items-center space-x-2">
                        <span className="text-xs text-yellow-600 bg-yellow-50 px-2 py-1 rounded">
                          Not verified
                        </span>
                        {verificationSent ? (
                          <span className="text-xs text-green-600">Verification email sent!</span>
                        ) : (
                          <button
                            onClick={handleResendVerification}
                            disabled={verificationLoading}
                            className="text-xs text-indigo-600 hover:text-indigo-500 disabled:opacity-50"
                          >
                            {verificationLoading ? 'Sending...' : 'Resend verification'}
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Member since</label>
                    <p className="mt-1 text-sm text-gray-900">
                      {user?.created_at
                        ? new Date(user.created_at).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                          })
                        : 'Unknown'}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Last login</label>
                    <p className="mt-1 text-sm text-gray-900">
                      {user?.last_login_at
                        ? new Date(user.last_login_at).toLocaleString('en-US', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                            hour: 'numeric',
                            minute: '2-digit',
                          })
                        : 'This is your first login'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-gray-200">
                <h3 className="text-lg font-medium text-red-600 mb-4">Danger Zone</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Once you delete your account, there is no going back. Please be certain.
                </p>
                <button className="px-4 py-2 text-sm font-medium text-red-600 border border-red-300 rounded-lg hover:bg-red-50">
                  Delete Account
                </button>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  {user?.has_password ? 'Change Password' : 'Set Password'}
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  {user?.has_password
                    ? 'Update your password to keep your account secure.'
                    : 'Set a password to enable password-based login.'}
                </p>

                <form onSubmit={handleSetPassword} className="max-w-md space-y-4">
                  {passwordError && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm text-red-600">{passwordError}</p>
                    </div>
                  )}
                  {passwordSuccess && (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-sm text-green-600">Password updated successfully!</p>
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      New Password
                    </label>
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="••••••••"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Confirm Password
                    </label>
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      placeholder="••••••••"
                      required
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={passwordLoading}
                    className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                  >
                    {passwordLoading
                      ? 'Saving...'
                      : user?.has_password
                      ? 'Update Password'
                      : 'Set Password'}
                  </button>
                </form>
              </div>

              <div className="pt-6 border-t border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Login Sessions</h3>
                <p className="text-sm text-gray-600">
                  Manage your active login sessions across devices.
                </p>
                <p className="mt-4 text-sm text-gray-500 italic">Coming soon</p>
              </div>
            </div>
          )}

          {activeTab === 'preferences' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Preferences</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Customize your experience with the LLM Council.
                </p>

                <div className="space-y-4">
                  <div className="flex items-center justify-between py-4 border-b border-gray-200">
                    <div>
                      <p className="text-sm font-medium text-gray-900">Email Notifications</p>
                      <p className="text-sm text-gray-500">
                        Receive updates about your conversations
                      </p>
                    </div>
                    <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-gray-200 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">
                      <span className="translate-x-0 inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
                    </button>
                  </div>

                  <div className="flex items-center justify-between py-4 border-b border-gray-200">
                    <div>
                      <p className="text-sm font-medium text-gray-900">Dark Mode</p>
                      <p className="text-sm text-gray-500">Switch between light and dark themes</p>
                    </div>
                    <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-gray-200 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">
                      <span className="translate-x-0 inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
                    </button>
                  </div>

                  <div className="flex items-center justify-between py-4">
                    <div>
                      <p className="text-sm font-medium text-gray-900">Default Model Selection</p>
                      <p className="text-sm text-gray-500">
                        Remember your model preferences for new conversations
                      </p>
                    </div>
                    <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-indigo-600 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">
                      <span className="translate-x-5 inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
