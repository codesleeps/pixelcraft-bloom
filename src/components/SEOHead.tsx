import { useEffect } from 'react';

interface SEOHeadProps {
  title?: string;
  description?: string;
  keywords?: string;
  ogImage?: string;
  canonical?: string;
  schema?: object;
  noIndex?: boolean;
}

const SEOHead = ({
  title = "Digital Marketing Agency - Transform Your Digital Presence | AgentsFlowAI",
  description = "Award-winning digital marketing agency helping businesses scale with SEO, social media, web design, and data-driven strategies. 300% average ROI guaranteed.",
  keywords = "digital marketing, SEO, social media marketing, web design, PPC, content marketing, marketing strategy, business growth",
  ogImage = "/hero-marketing.jpg",
  canonical,
  schema,
  noIndex = false
}: SEOHeadProps) => {
  
  useEffect(() => {
    // Update document title
    document.title = title;
    
    // Update meta description
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute('content', description);
    }
    
    // Update keywords
    let metaKeywords = document.querySelector('meta[name="keywords"]');
    if (!metaKeywords) {
      metaKeywords = document.createElement('meta');
      metaKeywords.setAttribute('name', 'keywords');
      document.head.appendChild(metaKeywords);
    }
    metaKeywords.setAttribute('content', keywords);
    
    // Update Open Graph tags
    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle) {
      ogTitle.setAttribute('content', title);
    }
    
    const ogDescription = document.querySelector('meta[property="og:description"]');
    if (ogDescription) {
      ogDescription.setAttribute('content', description);
    }
    
    const ogImageMeta = document.querySelector('meta[property="og:image"]');
    if (ogImageMeta) {
      ogImageMeta.setAttribute('content', ogImage);
    }
    
    // Add canonical URL
    if (canonical) {
      let canonicalLink = document.querySelector('link[rel="canonical"]');
      if (!canonicalLink) {
        canonicalLink = document.createElement('link');
        canonicalLink.setAttribute('rel', 'canonical');
        document.head.appendChild(canonicalLink);
      }
      canonicalLink.setAttribute('href', canonical);
    }
    
    // Add robots meta tag
    let robotsMeta = document.querySelector('meta[name="robots"]');
    if (!robotsMeta) {
      robotsMeta = document.createElement('meta');
      robotsMeta.setAttribute('name', 'robots');
      document.head.appendChild(robotsMeta);
    }
    robotsMeta.setAttribute('content', noIndex ? 'noindex, nofollow' : 'index, follow');
    
    // Add structured data
    if (schema) {
      let schemaScript = document.querySelector('script[type="application/ld+json"]');
      if (!schemaScript) {
        schemaScript = document.createElement('script');
        schemaScript.setAttribute('type', 'application/ld+json');
        document.head.appendChild(schemaScript);
      }
      schemaScript.textContent = JSON.stringify(schema);
    }
    
    // Performance optimizations
    // Add preconnect for external domains
    const preconnects = [
      'https://fonts.googleapis.com',
      'https://fonts.gstatic.com'
    ];
    
    preconnects.forEach(url => {
      let preconnectLink = document.querySelector(`link[rel="preconnect"][href="${url}"]`);
      if (!preconnectLink) {
        preconnectLink = document.createElement('link');
        preconnectLink.setAttribute('rel', 'preconnect');
        preconnectLink.setAttribute('href', url);
        if (url.includes('gstatic')) {
          preconnectLink.setAttribute('crossorigin', '');
        }
        document.head.appendChild(preconnectLink);
      }
    });
    
  }, [title, description, keywords, ogImage, canonical, schema, noIndex]);

  return null;
};

export default SEOHead;