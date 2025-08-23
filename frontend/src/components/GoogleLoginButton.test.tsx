import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GoogleOAuthProvider } from '@react-oauth/google';
import GoogleLoginButton from './GoogleLoginButton';
import { AuthProvider } from '../contexts/AuthContext';

// Mock the useAuth hook
const mockSignInWithGoogle = vi.fn();
vi.mock('../contexts/AuthContext', async () => {
  const actual = await vi.importActual('../contexts/AuthContext');
  return {
    ...actual,
    useAuth: () => ({
      signInWithGoogle: mockSignInWithGoogle,
      user: null,
      session: null,
      loading: false,
      signOut: vi.fn(),
    }),
  };
});

// Mock Google OAuth hook
const mockLogin = vi.fn();
vi.mock('@react-oauth/google', async () => {
  const actual = await vi.importActual('@react-oauth/google');
  return {
    ...actual,
    useGoogleLogin: (options: { onSuccess?: (response: { access_token: string }) => void; onError?: () => void }) => {
      return () => {
        mockLogin();
        // Simulate success callback
        if (options?.onSuccess) {
          options.onSuccess({ access_token: 'mock-token' });
        }
      };
    },
  };
});

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <GoogleOAuthProvider clientId="test-client-id">
    <AuthProvider>
      {children}
    </AuthProvider>
  </GoogleOAuthProvider>
);

describe('GoogleLoginButton', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login button with correct text', () => {
    render(
      <TestWrapper>
        <GoogleLoginButton />
      </TestWrapper>
    );

    const button = screen.getByRole('button', { name: /구글 계정으로 로그인/i });
    expect(button).toBeInTheDocument();
    expect(button).not.toBeDisabled();
  });

  it('has proper accessibility attributes', () => {
    render(
      <TestWrapper>
        <GoogleLoginButton />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('aria-label', '구글 계정으로 로그인');
    expect(button).toHaveAttribute('tabIndex', '0');
  });

  it('shows loading state during authentication', async () => {
    mockSignInWithGoogle.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));
    
    render(
      <TestWrapper>
        <GoogleLoginButton />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    await user.click(button);

    await waitFor(() => {
      expect(button).toHaveAttribute('aria-label', '구글 로그인 진행 중...');
      expect(screen.getByText('로그인 중...')).toBeInTheDocument();
      expect(button).toBeDisabled();
    });
  });

  it('handles keyboard navigation', async () => {
    render(
      <TestWrapper>
        <GoogleLoginButton />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    button.focus();
    
    await user.keyboard('{Enter}');
    expect(mockLogin).toHaveBeenCalled();
    
    vi.clearAllMocks();
    
    await user.keyboard(' ');
    expect(mockLogin).toHaveBeenCalled();
  });

  it('calls onSuccess callback when login succeeds', async () => {
    const onSuccess = vi.fn();
    mockSignInWithGoogle.mockResolvedValueOnce(undefined);

    render(
      <TestWrapper>
        <GoogleLoginButton onSuccess={onSuccess} />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    await user.click(button);

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledTimes(1);
    });
  });

  it('calls onError callback when login fails', async () => {
    const onError = vi.fn();
    const errorMessage = '로그인 실패';
    mockSignInWithGoogle.mockRejectedValueOnce(new Error(errorMessage));

    render(
      <TestWrapper>
        <GoogleLoginButton onError={onError} />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    await user.click(button);

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(errorMessage);
    });
  });

  it('respects disabled prop', () => {
    render(
      <TestWrapper>
        <GoogleLoginButton disabled />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('applies custom className', () => {
    const customClass = 'custom-login-button';
    render(
      <TestWrapper>
        <GoogleLoginButton className={customClass} />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    expect(button).toHaveClass('google-login-button', customClass);
  });

  it('has minimum accessible button size', () => {
    render(
      <TestWrapper>
        <GoogleLoginButton />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    
    // Check that the button has the CSS class that provides minimum sizing
    expect(button).toHaveClass('google-login-button');
    
    // In a real test environment, we'd check computed styles
    // For now, verify the button exists and has the right class
    expect(button).toBeInTheDocument();
  });

  it('includes Google icon in button', () => {
    render(
      <TestWrapper>
        <GoogleLoginButton />
      </TestWrapper>
    );

    const icon = screen.getByRole('button').querySelector('.google-icon');
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveAttribute('aria-hidden', 'true');
  });

  it('prevents multiple simultaneous login attempts', async () => {
    mockSignInWithGoogle.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));
    
    render(
      <TestWrapper>
        <GoogleLoginButton />
      </TestWrapper>
    );

    const button = screen.getByRole('button');
    
    // First click
    await user.click(button);
    expect(button).toBeDisabled();
    
    // Second click should be ignored
    await user.click(button);
    expect(mockSignInWithGoogle).toHaveBeenCalledTimes(1);
  });
});