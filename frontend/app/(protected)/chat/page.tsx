'use client';

import NewChatInterface from '@/components/NewChatInterface';
import { ThemeProvider } from '@/components/ThemeProvider';

export default function ChatPage() {
  return (
    <div className="h-full">
      <ThemeProvider>
        <NewChatInterface />
      </ThemeProvider>
    </div>
  );
}
