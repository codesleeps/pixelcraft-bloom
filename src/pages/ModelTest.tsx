import ModelTester from '@/components/ModelTester';
import SEOHead from '@/components/SEOHead';

export default function ModelTest() {
  return (
    <>
      <SEOHead 
        title="Model Testing | AgentsFlowAI Bloom"
        description="Test and evaluate AI model performance"
      />
      <ModelTester />
    </>
  );
}