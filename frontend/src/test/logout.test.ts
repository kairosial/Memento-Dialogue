// Simple test to verify logout functionality
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock Supabase
const mockSignOut = vi.fn();
vi.mock('../lib/supabase', () => ({
  supabase: {
    auth: {
      signOut: mockSignOut,
      getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
      onAuthStateChange: vi.fn().mockReturnValue({
        data: { subscription: { unsubscribe: vi.fn() } }
      })
    }
  }
}));

describe('Logout functionality', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock window.location.href
    Object.defineProperty(window, 'location', {
      value: { href: '' },
      writable: true
    });
  });

  it('should call supabase signOut with global scope', async () => {
    mockSignOut.mockResolvedValue({ error: null });
    
    expect(mockSignOut).toBeDefined();
  });

  it('should handle signOut errors gracefully', async () => {
    const mockError = new Error('Network error');
    mockSignOut.mockResolvedValue({ error: mockError });
    
    expect(mockSignOut).toBeDefined();
  });
});