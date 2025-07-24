import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import ErrorBoundary from '$lib/components/ErrorBoundary.svelte';

// Mock component that throws an error
const ThrowError = {
  render: () => {
    throw new Error('Test error');
  }
};

// Mock component that works normally
const WorkingComponent = {
  render: () => {
    return {
      html: '<div>Working component</div>',
      css: { code: '', map: null },
      head: ''
    };
  }
};

describe('ErrorBoundary', () => {
  it('should render children when no error occurs', () => {
    const { container } = render(ErrorBoundary, {
      props: {
        fallback: 'Error occurred'
      },
      slots: {
        default: '<div>Child content</div>'
      }
    });

    expect(screen.getByText('Child content')).toBeInTheDocument();
    expect(screen.queryByText('Error occurred')).not.toBeInTheDocument();
  });

  it('should show error UI when error occurs', async () => {
    // Mock console.error to avoid test output noise
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const { container } = render(ErrorBoundary, {
      props: {
        fallback: undefined
      }
    });

    // Simulate an error
    const errorEvent = new ErrorEvent('error', {
      error: new Error('Test error'),
      message: 'Test error'
    });
    
    window.dispatchEvent(errorEvent);

    // Should show default error UI
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('An unexpected error occurred. Please try refreshing the page.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Refresh Page' })).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it('should show custom fallback when provided', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(ErrorBoundary, {
      props: {
        fallback: 'Custom error message'
      }
    });

    // Simulate an error
    const errorEvent = new ErrorEvent('error', {
      error: new Error('Test error'),
      message: 'Test error'
    });
    
    window.dispatchEvent(errorEvent);

    // Should show custom fallback
    expect(screen.getByText('Custom error message')).toBeInTheDocument();
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it('should reset error state when reset function is called', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const user = userEvent.setup();

    const { component } = render(ErrorBoundary, {
      props: {
        fallback: undefined
      },
      slots: {
        default: '<div>Child content</div>'
      }
    });

    // Initially should show child content
    expect(screen.getByText('Child content')).toBeInTheDocument();

    // Simulate an error
    const errorEvent = new ErrorEvent('error', {
      error: new Error('Test error'),
      message: 'Test error'
    });
    
    window.dispatchEvent(errorEvent);

    // Should show error UI
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.queryByText('Child content')).not.toBeInTheDocument();

    // Reset error state
    component.reset();

    // Should show child content again
    await screen.findByText('Child content');
    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it('should handle unhandled promise rejections', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(ErrorBoundary, {
      props: {
        fallback: undefined
      },
      slots: {
        default: '<div>Child content</div>'
      }
    });

    // Simulate unhandled rejection
    const rejectionEvent = new PromiseRejectionEvent('unhandledrejection', {
      promise: Promise.reject('Test rejection'),
      reason: 'Test rejection'
    });
    
    window.dispatchEvent(rejectionEvent);

    // Should show error UI
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it('should refresh page when refresh button is clicked', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const reloadSpy = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { reload: reloadSpy },
      writable: true
    });

    const user = userEvent.setup();

    render(ErrorBoundary, {
      props: {
        fallback: undefined
      }
    });

    // Simulate an error
    const errorEvent = new ErrorEvent('error', {
      error: new Error('Test error'),
      message: 'Test error'
    });
    
    window.dispatchEvent(errorEvent);

    // Click refresh button
    const refreshButton = screen.getByRole('button', { name: 'Refresh Page' });
    await user.click(refreshButton);

    // Should call window.location.reload
    expect(reloadSpy).toHaveBeenCalledTimes(1);

    consoleSpy.mockRestore();
  });

  it('should log errors to console in development', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const testError = new Error('Test error for logging');

    render(ErrorBoundary, {
      props: {
        fallback: undefined
      }
    });

    // Simulate an error
    const errorEvent = new ErrorEvent('error', {
      error: testError,
      message: testError.message
    });
    
    window.dispatchEvent(errorEvent);

    // Should log error
    expect(consoleSpy).toHaveBeenCalledWith('ErrorBoundary caught:', testError);

    consoleSpy.mockRestore();
  });

  it('should handle errors without stack trace', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(ErrorBoundary, {
      props: {
        fallback: undefined
      }
    });

    // Simulate an error without stack
    const errorEvent = new ErrorEvent('error', {
      error: { message: 'Error without stack' },
      message: 'Error without stack'
    });
    
    window.dispatchEvent(errorEvent);

    // Should still show error UI
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();

    consoleSpy.mockRestore();
  });

  it('should cleanup event listeners on destroy', () => {
    const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener');

    const { unmount } = render(ErrorBoundary, {
      props: {
        fallback: undefined
      }
    });

    unmount();

    // Should remove event listeners
    expect(removeEventListenerSpy).toHaveBeenCalledWith('error', expect.any(Function));
    expect(removeEventListenerSpy).toHaveBeenCalledWith('unhandledrejection', expect.any(Function));
  });
});