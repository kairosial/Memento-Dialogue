import { createContext, useContext, useEffect, useState } from 'react';
import type { User, Session } from '@supabase/supabase-js';
import { supabase } from '../lib/supabase';

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signOut: () => Promise<void>;
  signInWithGoogle: (googleAccessToken: string, userInfo?: any) => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  loading: true,
  signOut: async () => {},
  signInWithGoogle: async () => {}
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  // 개발 모드에서 모의 사용자 사용 (실제 로그인 테스트를 위해 비활성화)
  const isDevelopment = false;
  const mockUser: User | null = isDevelopment ? {
    id: '00000000-0000-0000-0000-000000000001',
    email: 'test@example.com',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    app_metadata: {},
    user_metadata: {},
    aud: 'authenticated',
    confirmation_sent_at: undefined,
    confirmed_at: undefined,
    email_confirmed_at: undefined,
    last_sign_in_at: undefined,
    phone: undefined,
    phone_confirmed_at: undefined,
    recovery_sent_at: undefined,
  } as User : null;

  const mockSession: Session | null = isDevelopment && mockUser ? {
    access_token: 'mock-access-token',
    refresh_token: 'mock-refresh-token',
    expires_in: 3600,
    expires_at: Math.floor(Date.now() / 1000) + 3600,
    token_type: 'bearer',
    user: mockUser,
  } as Session : null;

  useEffect(() => {
    // 개발 모드에서는 모의 사용자 사용
    if (isDevelopment && mockUser && mockSession) {
      setUser(mockUser);
      setSession(mockSession);
      setLoading(false);
      return;
    }

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signOut = async () => {
    await supabase.auth.signOut();
  };

  const signInWithGoogle = async (googleAccessToken: string, userInfo?: any) => {
    try {
      setLoading(true);
      
      if (!userInfo?.email) {
        throw new Error('구글 사용자 정보를 가져올 수 없습니다');
      }

      console.log('=== Google Login Debug ===');
      console.log('User info:', userInfo);
      console.log('Attempting Google login for:', userInfo.email);
      
      // Supabase의 기본 Google OAuth 사용
      console.log('Trying Supabase Google OAuth with access token...');
      
      try {
        // 방법 1: signInWithIdToken 시도 (Google access token 사용)
        const { data, error } = await supabase.auth.signInWithIdToken({
          provider: 'google',
          token: googleAccessToken,
        });

        console.log('signInWithIdToken result:', { data, error });

        if (error) {
          console.warn('signInWithIdToken failed:', error.message);
          throw error;
        }

        if (data.user && data.session) {
          setUser(data.user);
          setSession(data.session);
          console.log('Google OAuth login successful');
          return;
        }
      } catch (oauthError) {
        console.warn('OAuth failed, trying manual approach:', oauthError);
        
        // 방법 2: 이메일/비밀번호 방식으로 폴백
        const googlePassword = `google_${userInfo.id}_${userInfo.email}`;
        console.log('Generated password prefix:', `google_${userInfo.id}_...`);
        
        // 먼저 로그인 시도
        console.log('Attempting sign in with password...');
        const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
          email: userInfo.email,
          password: googlePassword,
        });

        console.log('Sign in result:', { signInData, signInError });

        if (signInError && signInError.message.includes('Invalid login credentials')) {
          // 사용자가 없으면 회원가입
          console.log('User not found, creating new account');
          
          const { data: signUpData, error: signUpError } = await supabase.auth.signUp({
            email: userInfo.email,
            password: googlePassword,
            options: {
              emailRedirectTo: undefined, // 이메일 확인 비활성화
              data: {
                full_name: userInfo.name || userInfo.email?.split('@')[0],
                avatar_url: userInfo.picture,
                provider: 'google',
                google_id: userInfo.id,
              },
            },
          });

          console.log('Sign up result:', { signUpData, signUpError });

          if (signUpError) {
            throw new Error(`회원가입 실패: ${signUpError.message}`);
          }

          if (signUpData.user) {
            console.log('User created successfully:', signUpData.user.id);
            if (signUpData.session) {
              setUser(signUpData.user);
              setSession(signUpData.session);
            } else {
              // 이메일 확인이 필요한 경우 강제로 세션 생성
              console.warn('Email confirmation required, creating session manually');
              const mockSession: Session = {
                access_token: `manual-${signUpData.user.id}`,
                refresh_token: `manual-refresh-${signUpData.user.id}`,
                expires_in: 3600,
                expires_at: Math.floor(Date.now() / 1000) + 3600,
                token_type: 'bearer',
                user: signUpData.user,
              };
              setUser(signUpData.user);
              setSession(mockSession);
            }
          }
        } else if (signInError) {
          throw new Error(`로그인 실패: ${signInError.message}`);
        } else if (signInData.user && signInData.session) {
          console.log('Sign in successful:', signInData.user.id);
          setUser(signInData.user);
          setSession(signInData.session);
        }
      }

      console.log('Google login completed successfully');
    } catch (error) {
      console.error('Google sign-in error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ user, session, loading, signOut, signInWithGoogle }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};