import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { User, Session } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signOut: () => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  isLoggingOut: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  loading: true,
  signOut: async () => {},
  signInWithGoogle: async () => {},
  isLoggingOut: false
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const navigate = useNavigate();

  // Note: User profile creation is now handled automatically by database trigger
  // when new users sign up via Supabase Auth (handle_new_user trigger)


  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      console.log('Initial session check:', session);
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (event, session) => {
      console.log('=== AUTH STATE CHANGE ===');
      console.log('Event:', event);
      console.log('Session:', session);
      console.log('User:', session?.user);
      
      // Handle different auth events
      if (event === 'SIGNED_OUT') {
        console.log('🚪 SIGNED_OUT event: Clearing all auth state...');
        setSession(null);
        setUser(null);
        setLoading(false);
        console.log('✓ Auth state cleared after SIGNED_OUT');
      } else if (event === 'SIGNED_IN') {
        console.log('🔑 SIGNED_IN event: Setting auth state...');
        setSession(session);
        setUser(session?.user ?? null);
        setLoading(false);
        console.log('✓ Auth state set after SIGNED_IN');
      } else if (event === 'TOKEN_REFRESHED') {
        console.log('🔄 TOKEN_REFRESHED event: Updating auth state...');
        setSession(session);
        setUser(session?.user ?? null);
        setLoading(false);
        console.log('✓ Auth state updated after TOKEN_REFRESHED');
      } else {
        // Handle other events
        console.log(`📝 ${event} event: Updating auth state...`);
        setSession(session);
        setUser(session?.user ?? null);
        setLoading(false);
        console.log(`✓ Auth state updated after ${event}`);
      }
      console.log('=== AUTH STATE CHANGE COMPLETE ===');
    });

    return () => subscription.unsubscribe();
  }, []);

  const signOut = useCallback(async () => {
    if (isLoggingOut) {
      console.log('Logout already in progress, skipping...');
      return;
    }

    console.log('=== LOGOUT PROCESS STARTED ===');
    
    try {
      setIsLoggingOut(true);
      
      // Step 1: Sign out from Supabase
      console.log('Step 1: Attempting Supabase signOut...');
      const { error } = await supabase.auth.signOut({ scope: 'global' });
      
      if (error) {
        console.error('Supabase logout error:', error.message);
        console.error('Error details:', error);
      } else {
        console.log('✓ Supabase signOut successful');
      }
      
      // Step 2: Force clear auth state immediately
      console.log('Step 2: Clearing local auth state...');
      setUser(null);
      setSession(null);
      console.log('✓ Local auth state cleared');
      
      // Step 3: Comprehensive storage cleanup
      console.log('Step 3: Cleaning up storage...');
      try {
        // Get current session to verify it's cleared
        const { data: { session: currentSession } } = await supabase.auth.getSession();
        console.log('Current session after signOut:', currentSession);
        
        // Clear localStorage
        const localKeys = Object.keys(localStorage);
        const authKeys = localKeys.filter(key => 
          key.startsWith('supabase.auth.') || 
          key.startsWith('sb-') ||
          key.includes('auth') || 
          key.includes('google') ||
          key.includes('oauth')
        );
        console.log('Clearing localStorage keys:', authKeys);
        authKeys.forEach(key => {
          console.log(`Removing localStorage key: ${key}`);
          localStorage.removeItem(key);
        });
        
        // Clear sessionStorage
        const sessionKeys = Object.keys(sessionStorage);
        const authSessionKeys = sessionKeys.filter(key => 
          key.startsWith('supabase.auth.') || 
          key.startsWith('sb-') ||
          key.includes('auth') || 
          key.includes('google') ||
          key.includes('oauth')
        );
        console.log('Clearing sessionStorage keys:', authSessionKeys);
        authSessionKeys.forEach(key => {
          console.log(`Removing sessionStorage key: ${key}`);
          sessionStorage.removeItem(key);
        });
        
        console.log('✓ Storage cleanup completed');
        
      } catch (storageError) {
        console.warn('Storage cleanup error:', storageError);
      }
      
      // Step 4: Force refresh auth state
      console.log('Step 4: Force refreshing auth state...');
      const { data: { session: finalSession } } = await supabase.auth.getSession();
      if (finalSession) {
        console.warn('⚠️  Session still exists after logout:', finalSession);
      } else {
        console.log('✓ Session successfully cleared');
      }
      
      // Step 5: Navigate to login page
      console.log('Step 5: Navigating to login page...');
      navigate('/login', { replace: true });
      console.log('✓ Navigation to login completed');
      
    } catch (error) {
      console.error('❌ Logout process error:', error);
      console.error('Error stack:', error instanceof Error ? error.stack : 'No stack available');
      
      // Emergency cleanup - ensure we clear state and redirect even if there's an error
      console.log('Emergency cleanup: Forcing auth state clear and redirect...');
      setUser(null);
      setSession(null);
      navigate('/login', { replace: true });
    } finally {
      setIsLoggingOut(false);
      console.log('=== LOGOUT PROCESS COMPLETED ===');
    }
  }, [isLoggingOut, navigate]);

  const signInWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/`,
        queryParams: {
          access_type: 'offline',
          prompt: 'select_account'
        }
      }
    });
    
    if (error) {
      throw new Error(`구글 로그인 실패: ${error.message}`);
    }
  };

  return (
    <AuthContext.Provider value={{ user, session, loading, signOut, signInWithGoogle, isLoggingOut }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};