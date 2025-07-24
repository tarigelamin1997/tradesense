import { browser } from '$app/environment';

// Intersection Observer for lazy loading components
let observer: IntersectionObserver | null = null;

if (browser) {
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const element = entry.target as HTMLElement;
          const callback = element.__lazyLoadCallback as () => void;
          if (callback) {
            callback();
            observer?.unobserve(element);
          }
        }
      });
    },
    {
      rootMargin: '50px'
    }
  );
}

// Lazy load component when it comes into view
export function lazyLoad(node: HTMLElement, load: () => void) {
  if (!browser || !observer) return;

  (node as any).__lazyLoadCallback = load;
  observer.observe(node);

  return {
    destroy() {
      observer?.unobserve(node);
    }
  };
}

// Image lazy loading with placeholder
export function lazyImage(node: HTMLImageElement, src: string) {
  if (!browser) return;

  const placeholder = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect width="400" height="300" fill="%23ddd"/%3E%3C/svg%3E';
  
  // Set placeholder
  node.src = placeholder;
  node.style.filter = 'blur(5px)';
  node.style.transition = 'filter 0.3s';

  const loadImage = () => {
    const img = new Image();
    img.src = src;
    
    img.onload = () => {
      node.src = src;
      node.style.filter = 'none';
    };
    
    img.onerror = () => {
      node.src = placeholder;
      node.alt = 'Failed to load image';
    };
  };

  // Use Intersection Observer
  if (observer) {
    (node as any).__lazyLoadCallback = loadImage;
    observer.observe(node);

    return {
      destroy() {
        observer?.unobserve(node);
      }
    };
  } else {
    // Fallback for older browsers
    loadImage();
  }
}

// Route-based code splitting helper
export async function loadRoute(routeName: string) {
  switch (routeName) {
    case 'dashboard':
      return import('../../routes/dashboard/+page.svelte');
    case 'trades':
      return import('../../routes/trades/+page.svelte');
    case 'analytics':
      return import('../../routes/analytics/+page.svelte');
    case 'settings':
      return import('../../routes/settings/+page.svelte');
    case 'admin':
      return import('../../routes/admin/+page.svelte');
    default:
      throw new Error(`Unknown route: ${routeName}`);
  }
}

// Component lazy loading with loading state
export function createLazyComponent<T extends Record<string, any>>(
  loader: () => Promise<{ default: any }>
) {
  let Component: any = null;
  let loading = true;
  let error: Error | null = null;

  const load = async () => {
    try {
      const module = await loader();
      Component = module.default;
      loading = false;
    } catch (e) {
      error = e as Error;
      loading = false;
    }
  };

  return {
    Component: () => Component,
    loading: () => loading,
    error: () => error,
    load
  };
}

// Prefetch links on hover
export function prefetchOnHover(node: HTMLAnchorElement) {
  if (!browser) return;

  let prefetched = false;

  const prefetch = () => {
    if (prefetched) return;
    prefetched = true;

    const href = node.getAttribute('href');
    if (!href || href.startsWith('http') || href.startsWith('#')) return;

    // Create a link element for prefetching
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = href;
    document.head.appendChild(link);
  };

  node.addEventListener('mouseenter', prefetch);
  node.addEventListener('touchstart', prefetch, { passive: true });

  return {
    destroy() {
      node.removeEventListener('mouseenter', prefetch);
      node.removeEventListener('touchstart', prefetch);
    }
  };
}

// Resource hints for critical resources
export function addResourceHints() {
  if (!browser) return;

  const hints = [
    { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
    { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: true },
    { rel: 'dns-prefetch', href: 'https://api.tradesense.com' },
  ];

  hints.forEach(hint => {
    const link = document.createElement('link');
    link.rel = hint.rel;
    link.href = hint.href;
    if (hint.crossorigin) {
      link.crossOrigin = 'anonymous';
    }
    document.head.appendChild(link);
  });
}

// Defer non-critical scripts
export function deferScript(src: string, onLoad?: () => void) {
  if (!browser) return;

  const script = document.createElement('script');
  script.src = src;
  script.defer = true;
  
  if (onLoad) {
    script.onload = onLoad;
  }
  
  document.body.appendChild(script);
}

// Progressive enhancement for heavy features
export function progressiveEnhance(
  node: HTMLElement,
  enhance: () => void | Promise<void>,
  options: { delay?: number; threshold?: number } = {}
) {
  if (!browser) return;

  const { delay = 1000, threshold = 0.1 } = options;

  // Wait for main thread to be idle
  const enhance_wrapped = async () => {
    if ('requestIdleCallback' in window) {
      (window as any).requestIdleCallback(() => {
        setTimeout(() => enhance(), delay);
      });
    } else {
      setTimeout(() => enhance(), delay);
    }
  };

  // Use Intersection Observer to trigger enhancement
  const observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) {
        enhance_wrapped();
        observer.disconnect();
      }
    },
    { threshold }
  );

  observer.observe(node);

  return {
    destroy() {
      observer.disconnect();
    }
  };
}

// Batch DOM updates
export function batchUpdates(updates: Array<() => void>) {
  if (!browser) return;

  if ('requestAnimationFrame' in window) {
    requestAnimationFrame(() => {
      updates.forEach(update => update());
    });
  } else {
    updates.forEach(update => update());
  }
}