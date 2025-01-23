"use client";

import DashboardLayout from "@/components/DashboardLayout";
import { Web3Provider } from "@/components/Web3Provider";
import { AuthProvider } from "@/contexts/AuthContext";
import { StoryQueueProvider } from "@/contexts/StoryQueueContext";
import { StoryProvider } from "@/contexts/StoryContext";
import { StoreProvider } from "@/providers/StoreProvider";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <StoreProvider>
      <AuthProvider>
        <Web3Provider>
          <StoryQueueProvider>
            <StoryProvider>
              <DashboardLayout>{children}</DashboardLayout>
            </StoryProvider>
          </StoryQueueProvider>
        </Web3Provider>
      </AuthProvider>
    </StoreProvider>
  );
}
