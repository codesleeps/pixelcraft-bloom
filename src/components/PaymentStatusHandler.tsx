import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, CheckCircle, Loader2, XCircle } from 'lucide-react';

interface PaymentStatusHandlerProps {
  status: 'idle' | 'processing' | 'success' | 'failed' | 'cancelled';
  message: string;
  onRetry?: () => void;
  onGoBack?: () => void;
}

const PaymentStatusHandler: React.FC<PaymentStatusHandlerProps> = ({ 
  status, 
  message, 
  onRetry, 
  onGoBack 
}) => {
  const renderContent = () => {
    switch (status) {
      case 'processing':
        return (
          <div className="flex flex-col items-center justify-center py-8">
            <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
            <h3 className="text-xl font-semibold mb-2">Processing Payment</h3>
            <p className="text-muted-foreground text-center">
              {message || 'Please wait while we process your payment...'}
            </p>
          </div>
        );
      
      case 'success':
        return (
          <div className="flex flex-col items-center justify-center py-8">
            <CheckCircle className="h-12 w-12 text-green-500 mb-4" />
            <h3 className="text-xl font-semibold mb-2">Payment Successful!</h3>
            <p className="text-muted-foreground text-center mb-4">
              {message || 'Your payment has been processed successfully.'}
            </p>
            <Button onClick={onGoBack}>Return to Dashboard</Button>
          </div>
        );
      
      case 'failed':
        return (
          <div className="flex flex-col items-center justify-center py-8">
            <XCircle className="h-12 w-12 text-destructive mb-4" />
            <h3 className="text-xl font-semibold mb-2">Payment Failed</h3>
            <p className="text-muted-foreground text-center mb-4">
              {message || 'There was an error processing your payment.'}
            </p>
            {onRetry && (
              <Button onClick={onRetry} className="mr-2">
                Try Again
              </Button>
            )}
            {onGoBack && (
              <Button variant="outline" onClick={onGoBack}>
                Go Back
              </Button>
            )}
          </div>
        );
      
      case 'cancelled':
        return (
          <div className="flex flex-col items-center justify-center py-8">
            <AlertCircle className="h-12 w-12 text-yellow-500 mb-4" />
            <h3 className="text-xl font-semibold mb-2">Payment Cancelled</h3>
            <p className="text-muted-foreground text-center mb-4">
              {message || 'Your payment was cancelled.'}
            </p>
            {onRetry && (
              <Button onClick={onRetry} className="mr-2">
                Try Again
              </Button>
            )}
            {onGoBack && (
              <Button variant="outline" onClick={onGoBack}>
                Go Back
              </Button>
            )}
          </div>
        );
      
      default:
        return (
          <div className="flex flex-col items-center justify-center py-8">
            <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-xl font-semibold mb-2">Payment Status</h3>
            <p className="text-muted-foreground text-center">
              {message || 'Ready to process your payment.'}
            </p>
          </div>
        );
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Payment Status</CardTitle>
        <CardDescription>
          {status === 'processing' && 'Processing your payment securely'}
          {status === 'success' && 'Payment completed successfully'}
          {status === 'failed' && 'Payment processing error'}
          {status === 'cancelled' && 'Payment was cancelled'}
          {status === 'idle' && 'Ready to process payment'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {renderContent()}
      </CardContent>
    </Card>
  );
};

export default PaymentStatusHandler;