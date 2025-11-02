import React from 'react';

const PaymentsCancel: React.FC = () => {
  return (
    <section className="py-24 bg-gradient-subtle">
      <div className="container mx-auto px-4 text-center">
        <h1 className="text-3xl font-bold mb-4">Payment Cancelled</h1>
        <p className="text-muted-foreground mb-6">
          Your payment was cancelled. You can try again or choose a different plan.
        </p>
        <a href="#/" className="underline">Return to Home</a>
      </div>
    </section>
  );
};

export default PaymentsCancel;

