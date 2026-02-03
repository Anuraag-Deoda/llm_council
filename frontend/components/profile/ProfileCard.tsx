'use client';

import { useState } from 'react';
import { useAuth } from '@/lib/auth-context';

export default function ProfileCard() {
  const { user, updateProfile } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [displayName, setDisplayName] = useState(user?.display_name || '');
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || '');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSave = async () => {
    setError(null);
    setSuccess(false);
    setIsLoading(true);

    try {
      await updateProfile({
        display_name: displayName || undefined,
        avatar_url: avatarUrl || undefined,
      });
      setSuccess(true);
      setIsEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setDisplayName(user?.display_name || '');
    setAvatarUrl(user?.avatar_url || '');
    setIsEditing(false);
    setError(null);
  };

  if (!user) return null;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Cover */}
      <div className="h-32 bg-gradient-to-r from-indigo-500 to-purple-600"></div>

      {/* Profile content */}
      <div className="relative px-6 pb-6">
        {/* Avatar */}
        <div className="absolute -top-12 left-6">
          {user.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={user.display_name || user.email}
              className="w-24 h-24 rounded-full border-4 border-white shadow-lg object-cover"
            />
          ) : (
            <div className="w-24 h-24 rounded-full border-4 border-white shadow-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <span className="text-white text-3xl font-bold">
                {(user.display_name || user.email)[0].toUpperCase()}
              </span>
            </div>
          )}
        </div>

        {/* Edit button */}
        <div className="flex justify-end pt-4">
          {!isEditing ? (
            <button
              onClick={() => setIsEditing(true)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Edit Profile
            </button>
          ) : (
            <div className="flex space-x-2">
              <button
                onClick={handleCancel}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={isLoading}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {isLoading ? 'Saving...' : 'Save'}
              </button>
            </div>
          )}
        </div>

        {/* Profile info */}
        <div className="mt-8">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm text-green-600">Profile updated successfully!</p>
            </div>
          )}

          {isEditing ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Display Name
                </label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Your name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Avatar URL
                </label>
                <input
                  type="url"
                  value={avatarUrl}
                  onChange={(e) => setAvatarUrl(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="https://example.com/avatar.jpg"
                />
              </div>
            </div>
          ) : (
            <>
              <h2 className="text-2xl font-bold text-gray-900">
                {user.display_name || 'No name set'}
              </h2>
              <p className="text-gray-600">{user.email}</p>
            </>
          )}
        </div>

        {/* Stats */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {user.email_verified ? (
                  <span className="text-green-600">✓</span>
                ) : (
                  <span className="text-yellow-600">!</span>
                )}
              </p>
              <p className="text-sm text-gray-500">
                {user.email_verified ? 'Verified' : 'Unverified'}
              </p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {user.has_password ? '✓' : '✗'}
              </p>
              <p className="text-sm text-gray-500">Password Set</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900">
                {new Date(user.created_at).toLocaleDateString('en-US', {
                  month: 'short',
                  year: 'numeric',
                })}
              </p>
              <p className="text-sm text-gray-500">Joined</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
