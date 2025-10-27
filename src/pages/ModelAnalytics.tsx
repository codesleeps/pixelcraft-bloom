import ModelsDashboard from '@/components/ModelsDashboard';
import SEOHead from '@/components/SEOHead';

export default function ModelAnalytics() {
  return (
    <>
      <SEOHead 
        title="Model Analytics | PixelCraft Bloom"
        description="Monitor and analyze AI model performance metrics"
      />
      <ModelsDashboard />
    </>
  );
}