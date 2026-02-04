'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth-context';
import { setPassword } from '@/lib/auth-api';

type TabType = 'profile' | 'personalization' | 'security' | 'preferences';

export default function SettingsPage() {
  const { user, updateProfile, accessToken, refreshUser } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('profile');

  // Profile form state
  const [displayName, setDisplayName] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');

  // AI Personalization state
  const [preferredName, setPreferredName] = useState('');
  const [role, setRole] = useState('');
  const [expertise, setExpertise] = useState<string[]>([]);
  const [newExpertise, setNewExpertise] = useState('');
  const [technicalLevel, setTechnicalLevel] = useState('');
  const [communicationStyle, setCommunicationStyle] = useState('');
  const [customInstructions, setCustomInstructions] = useState('');

  // Security state
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // UI state
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Initialize form data from user
  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name || '');
      setAvatarUrl(user.avatar_url || '');

      const mc = user.model_context || {};
      setPreferredName(mc.preferred_name || '');
      setRole(mc.role || '');
      setExpertise(mc.expertise || []);
      setTechnicalLevel(mc.technical_level || '');
      setCommunicationStyle(mc.communication_style || '');
      setCustomInstructions(mc.custom_instructions || '');
    }
  }, [user]);

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      await updateProfile({
        display_name: displayName || undefined,
        avatar_url: avatarUrl || undefined,
      });
      showMessage('success', 'Profile updated successfully');
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleSavePersonalization = async () => {
    setSaving(true);
    try {
      await updateProfile({
        model_context: {
          preferred_name: preferredName || undefined,
          role: role || undefined,
          expertise: expertise.length > 0 ? expertise : undefined,
          technical_level: technicalLevel || undefined,
          communication_style: communicationStyle || undefined,
          custom_instructions: customInstructions || undefined,
        },
      });
      await refreshUser();
      showMessage('success', 'AI personalization updated successfully');
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : 'Failed to update personalization');
    } finally {
      setSaving(false);
    }
  };

  const handleAddExpertise = () => {
    if (newExpertise.trim() && !expertise.includes(newExpertise.trim())) {
      setExpertise((prev) => [...prev, newExpertise.trim()]);
      setNewExpertise('');
    }
  };

  const handleRemoveExpertise = (item: string) => {
    setExpertise((prev) => prev.filter((e) => e !== item));
  };

  const handleSetPassword = async () => {
    if (newPassword !== confirmPassword) {
      showMessage('error', 'Passwords do not match');
      return;
    }
    if (newPassword.length < 8) {
      showMessage('error', 'Password must be at least 8 characters');
      return;
    }
    if (!accessToken) {
      showMessage('error', 'Not authenticated');
      return;
    }

    setSaving(true);
    try {
      await setPassword(accessToken, newPassword);
      setNewPassword('');
      setConfirmPassword('');
      showMessage('success', 'Password updated successfully');
    } catch (err) {
      showMessage('error', err instanceof Error ? err.message : 'Failed to update password');
    } finally {
      setSaving(false);
    }
  };

  const tabs = [
    { id: 'profile' as TabType, label: 'Profile', icon: '👤' },
    { id: 'personalization' as TabType, label: 'AI Personalization', icon: '✨' },
    { id: 'security' as TabType, label: 'Security', icon: '🔒' },
    { id: 'preferences' as TabType, label: 'Preferences', icon: '⚙️' },
  ];

  return (
    <div className="min-h-screen bg-mesh noise-bg">
      <div className="relative z-10 p-8">
        {/* Header */}
        <div className="mb-10 animate-slide-up">
          <div className="flex items-center gap-3 mb-2">
            <span
              className="px-3 py-1 rounded-full text-xs font-medium"
              style={{
                background: 'var(--color-accent-muted)',
                color: 'var(--color-accent)'
              }}
            >
              Settings
            </span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight" style={{ color: 'var(--color-text-primary)' }}>
            Account Settings
          </h1>
          <p className="mt-2 text-base" style={{ color: 'var(--color-text-secondary)' }}>
            Manage your account, personalization, and security preferences.
          </p>
        </div>

        {/* Message Toast */}
        {message && (
          <div
            className="fixed top-4 right-4 z-50 px-6 py-4 rounded-xl shadow-lg animate-slide-in-left"
            style={{
              background: message.type === 'success' ? 'var(--color-success-muted)' : 'var(--color-error-muted)',
              border: `1px solid ${message.type === 'success' ? 'rgba(0,255,136,0.2)' : 'rgba(255,68,102,0.2)'}`,
            }}
          >
            <div className="flex items-center gap-3">
              <span>{message.type === 'success' ? '✓' : '✕'}</span>
              <p
                className="text-sm font-medium"
                style={{ color: message.type === 'success' ? 'var(--color-success)' : 'var(--color-error)' }}
              >
                {message.text}
              </p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar Tabs */}
          <div className="lg:col-span-1 animate-slide-up stagger-1">
            <div
              className="rounded-2xl overflow-hidden"
              style={{
                background: 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border)'
              }}
            >
              <div className="p-4">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all duration-200 mb-1"
                    style={{
                      background: activeTab === tab.id ? 'var(--color-accent-muted)' : 'transparent',
                      color: activeTab === tab.id ? 'var(--color-accent)' : 'var(--color-text-secondary)',
                    }}
                  >
                    <span className="text-lg">{tab.icon}</span>
                    <span className="font-medium text-sm">{tab.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Content Area */}
          <div className="lg:col-span-3 animate-slide-up stagger-2">
            <div
              className="rounded-2xl overflow-hidden"
              style={{
                background: 'var(--color-bg-secondary)',
                border: '1px solid var(--color-border)'
              }}
            >
              {/* Profile Tab */}
              {activeTab === 'profile' && (
                <div className="p-8">
                  <h2 className="text-xl font-semibold mb-6" style={{ color: 'var(--color-text-primary)' }}>
                    Profile Information
                  </h2>

                  <div className="space-y-6">
                    {/* Avatar Preview */}
                    <div className="flex items-center gap-6">
                      <div
                        className="w-20 h-20 rounded-2xl flex items-center justify-center overflow-hidden"
                        style={{ background: 'var(--gradient-accent)' }}
                      >
                        {avatarUrl ? (
                          <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
                        ) : (
                          <span className="text-2xl font-bold" style={{ color: 'var(--color-bg-primary)' }}>
                            {(displayName || user?.email || '?')[0].toUpperCase()}
                          </span>
                        )}
                      </div>
                      <div>
                        <p className="font-medium" style={{ color: 'var(--color-text-primary)' }}>
                          {displayName || 'Set your display name'}
                        </p>
                        <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                          {user?.email}
                        </p>
                      </div>
                    </div>

                    {/* Display Name */}
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                        Display Name
                      </label>
                      <input
                        type="text"
                        value={displayName}
                        onChange={(e) => setDisplayName(e.target.value)}
                        placeholder="Your display name"
                        className="w-full px-4 py-3 rounded-xl text-sm"
                        style={{
                          background: 'var(--color-bg-tertiary)',
                          border: '1px solid var(--color-border)',
                          color: 'var(--color-text-primary)',
                        }}
                      />
                    </div>

                    {/* Avatar URL */}
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                        Avatar URL
                      </label>
                      <input
                        type="url"
                        value={avatarUrl}
                        onChange={(e) => setAvatarUrl(e.target.value)}
                        placeholder="https://example.com/avatar.jpg"
                        className="w-full px-4 py-3 rounded-xl text-sm"
                        style={{
                          background: 'var(--color-bg-tertiary)',
                          border: '1px solid var(--color-border)',
                          color: 'var(--color-text-primary)',
                        }}
                      />
                    </div>

                    {/* Save Button */}
                    <button
                      onClick={handleSaveProfile}
                      disabled={saving}
                      className="px-6 py-3 rounded-xl text-sm font-semibold transition-all duration-200 disabled:opacity-50"
                      style={{
                        background: 'var(--gradient-accent)',
                        color: 'var(--color-bg-primary)',
                      }}
                    >
                      {saving ? 'Saving...' : 'Save Changes'}
                    </button>
                  </div>
                </div>
              )}

              {/* AI Personalization Tab */}
              {activeTab === 'personalization' && (
                <div className="p-8">
                  <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--color-text-primary)' }}>
                    AI Personalization
                  </h2>
                  <p className="text-sm mb-8" style={{ color: 'var(--color-text-muted)' }}>
                    Help AI models understand you better for more personalized responses.
                  </p>

                  <div className="space-y-6">
                    {/* Preferred Name */}
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                        What should AI call you?
                      </label>
                      <input
                        type="text"
                        value={preferredName}
                        onChange={(e) => setPreferredName(e.target.value)}
                        placeholder="e.g., Alex, Dr. Smith, etc."
                        className="w-full px-4 py-3 rounded-xl text-sm"
                        style={{
                          background: 'var(--color-bg-tertiary)',
                          border: '1px solid var(--color-border)',
                          color: 'var(--color-text-primary)',
                        }}
                      />
                    </div>

                    {/* Role */}
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                        Your Role
                      </label>
                      <input
                        type="text"
                        value={role}
                        onChange={(e) => setRole(e.target.value)}
                        placeholder="e.g., Software Engineer, Product Manager"
                        className="w-full px-4 py-3 rounded-xl text-sm"
                        style={{
                          background: 'var(--color-bg-tertiary)',
                          border: '1px solid var(--color-border)',
                          color: 'var(--color-text-primary)',
                        }}
                      />
                    </div>

                    {/* Expertise */}
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                        Areas of Expertise
                      </label>
                      <div className="flex gap-2 mb-3 flex-wrap">
                        {expertise.map((item) => (
                          <span
                            key={item}
                            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
                            style={{
                              background: 'var(--color-accent-muted)',
                              color: 'var(--color-accent)',
                            }}
                          >
                            {item}
                            <button
                              onClick={() => handleRemoveExpertise(item)}
                              className="hover:opacity-70"
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={newExpertise}
                          onChange={(e) => setNewExpertise(e.target.value)}
                          onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddExpertise())}
                          placeholder="Add expertise (press Enter)"
                          className="flex-1 px-4 py-3 rounded-xl text-sm"
                          style={{
                            background: 'var(--color-bg-tertiary)',
                            border: '1px solid var(--color-border)',
                            color: 'var(--color-text-primary)',
                          }}
                        />
                        <button
                          onClick={handleAddExpertise}
                          className="px-4 py-3 rounded-xl text-sm font-medium"
                          style={{
                            background: 'var(--color-bg-tertiary)',
                            border: '1px solid var(--color-border)',
                            color: 'var(--color-text-primary)',
                          }}
                        >
                          Add
                        </button>
                      </div>
                    </div>

                    {/* Technical Level */}
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                        Technical Level
                      </label>
                      <div className="grid grid-cols-3 gap-3">
                        {['beginner', 'intermediate', 'expert'].map((level) => (
                          <button
                            key={level}
                            onClick={() => setTechnicalLevel(level)}
                            className="px-4 py-3 rounded-xl text-sm font-medium capitalize transition-all duration-200"
                            style={{
                              background: technicalLevel === level ? 'var(--color-accent-muted)' : 'var(--color-bg-tertiary)',
                              border: `1px solid ${technicalLevel === level ? 'var(--color-accent)' : 'var(--color-border)'}`,
                              color: technicalLevel === level ? 'var(--color-accent)' : 'var(--color-text-secondary)',
                            }}
                          >
                            {level}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Communication Style */}
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                        Preferred Communication Style
                      </label>
                      <div className="grid grid-cols-3 gap-3">
                        {['casual', 'formal', 'technical'].map((style) => (
                          <button
                            key={style}
                            onClick={() => setCommunicationStyle(style)}
                            className="px-4 py-3 rounded-xl text-sm font-medium capitalize transition-all duration-200"
                            style={{
                              background: communicationStyle === style ? 'var(--color-accent-muted)' : 'var(--color-bg-tertiary)',
                              border: `1px solid ${communicationStyle === style ? 'var(--color-accent)' : 'var(--color-border)'}`,
                              color: communicationStyle === style ? 'var(--color-accent)' : 'var(--color-text-secondary)',
                            }}
                          >
                            {style}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Custom Instructions */}
                    <div>
                      <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                        Custom Instructions
                      </label>
                      <textarea
                        value={customInstructions}
                        onChange={(e) => setCustomInstructions(e.target.value)}
                        placeholder="Any additional context or preferences for AI interactions..."
                        rows={4}
                        className="w-full px-4 py-3 rounded-xl text-sm resize-none"
                        style={{
                          background: 'var(--color-bg-tertiary)',
                          border: '1px solid var(--color-border)',
                          color: 'var(--color-text-primary)',
                        }}
                      />
                    </div>

                    {/* Save Button */}
                    <button
                      onClick={handleSavePersonalization}
                      disabled={saving}
                      className="px-6 py-3 rounded-xl text-sm font-semibold transition-all duration-200 disabled:opacity-50"
                      style={{
                        background: 'var(--gradient-accent)',
                        color: 'var(--color-bg-primary)',
                      }}
                    >
                      {saving ? 'Saving...' : 'Save Personalization'}
                    </button>
                  </div>
                </div>
              )}

              {/* Security Tab */}
              {activeTab === 'security' && (
                <div className="p-8">
                  <h2 className="text-xl font-semibold mb-6" style={{ color: 'var(--color-text-primary)' }}>
                    Security Settings
                  </h2>

                  <div className="space-y-6">
                    {/* Password Section */}
                    <div
                      className="p-6 rounded-xl"
                      style={{ background: 'var(--color-bg-tertiary)' }}
                    >
                      <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>
                        {user?.has_password ? 'Change Password' : 'Set Password'}
                      </h3>

                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                            New Password
                          </label>
                          <input
                            type="password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            placeholder="Enter new password"
                            className="w-full px-4 py-3 rounded-xl text-sm"
                            style={{
                              background: 'var(--color-bg-secondary)',
                              border: '1px solid var(--color-border)',
                              color: 'var(--color-text-primary)',
                            }}
                          />
                        </div>

                        <div>
                          <label className="block text-sm font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>
                            Confirm Password
                          </label>
                          <input
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            placeholder="Confirm new password"
                            className="w-full px-4 py-3 rounded-xl text-sm"
                            style={{
                              background: 'var(--color-bg-secondary)',
                              border: '1px solid var(--color-border)',
                              color: 'var(--color-text-primary)',
                            }}
                          />
                        </div>

                        <button
                          onClick={handleSetPassword}
                          disabled={saving || !newPassword || !confirmPassword}
                          className="px-6 py-3 rounded-xl text-sm font-semibold transition-all duration-200 disabled:opacity-50"
                          style={{
                            background: 'var(--gradient-accent)',
                            color: 'var(--color-bg-primary)',
                          }}
                        >
                          {saving ? 'Updating...' : user?.has_password ? 'Update Password' : 'Set Password'}
                        </button>
                      </div>
                    </div>

                    {/* Account Status */}
                    <div
                      className="p-6 rounded-xl"
                      style={{ background: 'var(--color-bg-tertiary)' }}
                    >
                      <h3 className="text-sm font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>
                        Account Status
                      </h3>

                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                            Email Verified
                          </span>
                          <span
                            className="px-3 py-1 rounded-full text-xs font-medium"
                            style={{
                              background: user?.email_verified ? 'var(--color-success-muted)' : 'var(--color-secondary-muted)',
                              color: user?.email_verified ? 'var(--color-success)' : 'var(--color-secondary)',
                            }}
                          >
                            {user?.email_verified ? 'Verified' : 'Not Verified'}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                            Password Set
                          </span>
                          <span
                            className="px-3 py-1 rounded-full text-xs font-medium"
                            style={{
                              background: user?.has_password ? 'var(--color-success-muted)' : 'var(--color-bg-hover)',
                              color: user?.has_password ? 'var(--color-success)' : 'var(--color-text-muted)',
                            }}
                          >
                            {user?.has_password ? 'Yes' : 'No'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Preferences Tab */}
              {activeTab === 'preferences' && (
                <div className="p-8">
                  <h2 className="text-xl font-semibold mb-6" style={{ color: 'var(--color-text-primary)' }}>
                    App Preferences
                  </h2>

                  <div
                    className="p-6 rounded-xl text-center"
                    style={{ background: 'var(--color-bg-tertiary)' }}
                  >
                    <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                      More preferences coming soon...
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
