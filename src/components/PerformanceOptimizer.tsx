import { useEffect } from 'react';

const PerformanceOptimizer = () => {
  useEffect(() => {
    // Preload critical resources
    const preloadCriticalResources = () => {
      const criticalImages = [
        '/hero-marketing.jpg'
      ];

      criticalImages.forEach(src => {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = 'image';
        link.href = src;
        document.head.appendChild(link);
      });
    };

    // Defer non-critical scripts
    const deferNonCriticalScripts = () => {
      const scripts = document.querySelectorAll('script[data-defer]');
      scripts.forEach(script => {
        script.setAttribute('defer', 'true');
      });
    };

    // Optimize images with intersection observer
    const optimizeImages = () => {
      const images = document.querySelectorAll('img[data-src]');
      
      if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const img = entry.target as HTMLImageElement;
              img.src = img.dataset.src || '';
              img.classList.remove('lazy');
              imageObserver.unobserve(img);
            }
          });
        });

        images.forEach(img => imageObserver.observe(img));
      }
    };

    // Optimize Web Vitals
    const optimizeWebVitals = () => {
      // Reduce layout shift by setting image dimensions
      const images = document.querySelectorAll('img:not([width]):not([height])');
      images.forEach(img => {
        const computedStyle = window.getComputedStyle(img);
        if (!img.getAttribute('width')) {
          img.setAttribute('width', computedStyle.width.replace('px', ''));
        }
        if (!img.getAttribute('height')) {
          img.setAttribute('height', computedStyle.height.replace('px', ''));
        }
      });

      // Preconnect to external domains
      const externalDomains = [
        'https://fonts.googleapis.com',
        'https://fonts.gstatic.com'
      ];

      externalDomains.forEach(domain => {
        if (!document.querySelector(`link[href="${domain}"]`)) {
          const link = document.createElement('link');
          link.rel = 'preconnect';
          link.href = domain;
          if (domain.includes('gstatic')) {
            link.crossOrigin = '';
          }
          document.head.appendChild(link);
        }
      });
    };

    // Service Worker registration for caching
    const registerServiceWorker = async () => {
      if ('serviceWorker' in navigator) {
        try {
          const registration = await navigator.serviceWorker.register('/sw.js');
          console.log('SW registered: ', registration);
        } catch (registrationError) {
          console.log('SW registration failed: ', registrationError);
        }
      }
    };

    // Resource hints for better performance
    const addResourceHints = () => {
      const hints = [
        { rel: 'dns-prefetch', href: '//fonts.googleapis.com' },
        { rel: 'dns-prefetch', href: '//fonts.gstatic.com' },
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: true }
      ];

      hints.forEach(hint => {
        const existing = document.querySelector(`link[rel="${hint.rel}"][href="${hint.href}"]`);
        if (!existing) {
          const link = document.createElement('link');
          link.rel = hint.rel;
          link.href = hint.href;
          if (hint.crossorigin) {
            link.crossOrigin = '';
          }
          document.head.appendChild(link);
        }
      });
    };

    // Execute optimizations
    preloadCriticalResources();
    deferNonCriticalScripts();
    optimizeImages();
    optimizeWebVitals();
    addResourceHints();
    
    // Register service worker with a delay to not block main thread
    setTimeout(registerServiceWorker, 1000);

    // Cleanup function
    return () => {
      // Clean up any observers or listeners if needed
    };
  }, []);

  return null;
};

export default PerformanceOptimizer;