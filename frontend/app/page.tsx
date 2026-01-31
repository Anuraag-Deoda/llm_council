import NewChatInterface from '@/components/NewChatInterface';
import { ThemeProvider } from '@/components/ThemeProvider';

export default function Home() {
  return (
    <ThemeProvider>
      <NewChatInterface />
    </ThemeProvider>
  );
}
