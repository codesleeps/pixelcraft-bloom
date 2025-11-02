import React from 'react';

const PaymentsSuccess: React.FC = () => {
  return (
    <section className="py-24 bg-gradient-subtle">
      <div className="container mx-auto px-4 text-center">
        <h1 className="text-3xl font-bold mb-4">Payment Successful</h1>
        <p className="text-muted-foreground mb-6">
          Thank you for your subscription. Your account will be updated shortly.
        </p>
        <a href="#/dashboard" className="underline">Go to Dashboard</a>
      </div>
    </section>
  );
};

export default PaymentsSuccess;

