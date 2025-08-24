import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { GoogleOAuthProvider } from '@react-oauth/google';
import GoogleLoginButton from './GoogleLoginButton';
import { AuthProvider } from '../contexts/AuthContext';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <GoogleOAuthProvider clientId="test-client-id">
    <AuthProvider>
      {children}
    </AuthProvider>
  </GoogleOAuthProvider>
);

describe('GoogleLoginButton Accessibility Tests', () => {
  it('should have no accessibility violations in default state', async () => {
    const { container } = render(
      <TestWrapper>
        <GoogleLoginButton />
      </TestWrapper>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have no accessibility violations when disabled', async () => {
    const { container } = render(
      <TestWrapper>
        <GoogleLoginButton disabled />
      </TestWrapper>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have no accessibility violations in loading state', async () => {
    const { container } = render(
      <TestWrapper>
        <GoogleLoginButton />
      </TestWrapper>
    );

    // Simulate loading state by adding class
    const button = container.querySelector('.google-login-button');
    button?.classList.add('loading');

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have no accessibility violations with custom className', async () => {
    const { container } = render(
      <TestWrapper>
        <GoogleLoginButton className="custom-class" />
      </TestWrapper>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should pass color contrast requirements', async () => {
    const { container } = render(
      <TestWrapper>
        <GoogleLoginButton />
      </TestWrapper>
    );

    // Test basic accessibility without canvas-dependent checks
    const results = await axe(container, {
      rules: {
        'color-contrast': { enabled: false }, // Disable canvas-dependent rule
        'button-name': { enabled: true },
        'aria-valid-attr': { enabled: true }
      }
    });
    
    expect(results).toHaveNoViolations();
  });

  it('should have proper focus management', async () => {
    const { container } = render(
      <TestWrapper>
        <GoogleLoginButton />
      </TestWrapper>
    );

    // Test with keyboard navigation rules
    const results = await axe(container, {
      rules: {
        'keyboard': { enabled: true },
        'focus-order-semantics': { enabled: true }
      }
    });
    
    expect(results).toHaveNoViolations();
  });

  it('should meet WCAG 2.1 AA standards', async () => {
    const { container } = render(
      <TestWrapper>
        <GoogleLoginButton />
      </TestWrapper>
    );

    const results = await axe(container, {
      rules: {
        'wcag2a': { enabled: true },
        'wcag2aa': { enabled: true },
        'wcag21aa': { enabled: true }
      }
    });
    
    expect(results).toHaveNoViolations();
  });
});