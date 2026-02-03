'use client';

import ProfileCard from '@/components/profile/ProfileCard';
import ConversationHistory from '@/components/profile/ConversationHistory';

export default function ProfilePage() {
  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
        <p className="text-gray-600 mt-1">Manage your account and view your activity</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile Card */}
        <div className="lg:col-span-1">
          <ProfileCard />
        </div>

        {/* Conversation History */}
        <div className="lg:col-span-2">
          <ConversationHistory />
        </div>
      </div>
    </div>
  );
}
