import { describe, it, expect, vi } from 'vitest';
import { renderWithProviders, fillFormField, submitForm } from '@/test/utils/test-utils';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ROICalculator from '../ROICalculator';

describe('ROICalculator', () => {
  it('renders with default values and placeholder text', () => {
    renderWithProviders(<ROICalculator />);

    // Check header elements
    expect(screen.getByText('Calculate Your Potential ROI')).toBeInTheDocument();
    expect(screen.getByText(/See how much PixelCraft's AI-powered strategies could increase your revenue/)).toBeInTheDocument();

    // Check default input values
    expect(screen.getByDisplayValue('10000')).toBeInTheDocument(); // monthlyRevenue
    expect(screen.getByDisplayValue('100')).toBeInTheDocument(); // monthlyLeads
    expect(screen.getByDisplayValue('3')).toBeInTheDocument(); // conversionRate
    expect(screen.getByDisplayValue('2000')).toBeInTheDocument(); // currentSpend

    // Check industry select has default value
    expect(screen.getByText('SaaS')).toBeInTheDocument(); // Since value is 'saas'

    // Check calculate button
    expect(screen.getByRole('button', { name: /Calculate My ROI/i })).toBeInTheDocument();

    // Check results section is not shown initially
    expect(screen.queryByText('Current Monthly Revenue')).not.toBeInTheDocument();
    expect(screen.queryByText('Potential Monthly Revenue')).not.toBeInTheDocument();
  });

  it('updates form inputs correctly', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ROICalculator />);

    // Update monthlyRevenue
    await fillFormField(/Monthly Revenue/i, '15000');
    expect(screen.getByDisplayValue('15000')).toBeInTheDocument();

    // Update monthlyLeads
    await fillFormField(/Monthly Leads/i, '200');
    expect(screen.getByDisplayValue('200')).toBeInTheDocument();

    // Update conversionRate
    await fillFormField(/Conversion Rate/i, '5');
    expect(screen.getByDisplayValue('5')).toBeInTheDocument();

    // Update currentSpend
    await fillFormField(/Current Monthly Marketing Spend/i, '3000');
    expect(screen.getByDisplayValue('3000')).toBeInTheDocument();

    // Update industry
    const select = screen.getByRole('combobox');
    await user.click(select);
    await user.click(screen.getByText('E-commerce'));
    expect(screen.getByText('E-commerce')).toBeInTheDocument();
  });

  it('calculates ROI correctly with default values', async () => {
    renderWithProviders(<ROICalculator />);

    await submitForm(/Calculate My ROI/i);

    // Check results are displayed
    expect(screen.getByText('Current Monthly Revenue')).toBeInTheDocument();
    expect(screen.getByText('Potential Monthly Revenue')).toBeInTheDocument();

    // Verify calculated values
    // Current revenue: 10000 * (3/100) = 300
    expect(screen.getByText('300')).toBeInTheDocument(); // Current Monthly Revenue

    // Improved: multiplier 3.2, improvedLeads=320, improvedConv=5.4, improvedCustomers=17.28, improvedRevenue=1728
    expect(screen.getByText('1,728')).toBeInTheDocument(); // Potential Monthly Revenue

    // Revenue increase: 1728 - 300 = 1428
    expect(screen.getByText('+£1,428')).toBeInTheDocument();

    // New spend: 2000 * 1.5 = 3000
    expect(screen.getByText('£3,000')).toBeInTheDocument();

    // Net profit: 1428 - 3000 = -1572
    expect(screen.getByText('+£-1,572')).toBeInTheDocument();

    // ROI: (-1572 / 3000) * 100 ≈ -52.4, rounded to -52
    expect(screen.getByText('-52%')).toBeInTheDocument();
  });

  it('calculates ROI accurately with custom values', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ROICalculator />);

    // Fill custom values
    await fillFormField(/Monthly Revenue/i, '20000');
    await fillFormField(/Monthly Leads/i, '150');
    await fillFormField(/Conversion Rate/i, '4');
    await fillFormField(/Current Monthly Marketing Spend/i, '2500');

    // Change industry to ecommerce (multiplier 2.5)
    const select = screen.getByRole('combobox');
    await user.click(select);
    await user.click(screen.getByText('E-commerce'));

    await submitForm(/Calculate My ROI/i);

    // Calculations:
    // avgRevenuePerLead = 20000 / 150 ≈ 133.33
    // currentRevenue = 20000 * (4/100) = 800
    // improvedLeads = 150 * 2.5 = 375
    // improvedConv = min(4*1.8, 15) = 7.2
    // improvedCustomers = 375 * (7.2/100) = 27
    // improvedRevenue = 27 * 133.33 ≈ 3600
    // revenueIncrease = 3600 - 800 = 2800
    // newSpend = 2500 * 1.5 = 3750
    // netProfit = 2800 - 3750 = -950
    // roi = (-950 / 3750) * 100 ≈ -25.33, rounded to -25

    expect(screen.getByText('800')).toBeInTheDocument(); // Current
    expect(screen.getByText('3,600')).toBeInTheDocument(); // Potential
    expect(screen.getByText('+£2,800')).toBeInTheDocument();
    expect(screen.getByText('£3,750')).toBeInTheDocument();
    expect(screen.getByText('+£-950')).toBeInTheDocument();
    expect(screen.getByText('-25%')).toBeInTheDocument();
  });

  it('handles different industry multipliers correctly', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ROICalculator />);

    // Keep other defaults, change industry to technology (multiplier 3.5)
    const select = screen.getByRole('combobox');
    await user.click(select);
    await user.click(screen.getByText('Technology'));

    await submitForm(/Calculate My ROI/i);

    // With tech multiplier 3.5:
    // improvedLeads = 100 * 3.5 = 350
    // improvedConv = 5.4
    // improvedCustomers = 350 * 0.054 = 18.9
    // improvedRevenue = 18.9 * 100 = 1890
    // revenueIncrease = 1890 - 300 = 1590
    // newSpend = 3000
    // netProfit = 1590 - 3000 = -1410
    // roi = (-1410 / 3000) * 100 = -47

    expect(screen.getByText('1,890')).toBeInTheDocument();
    expect(screen.getByText('+£1,590')).toBeInTheDocument();
    expect(screen.getByText('-47%')).toBeInTheDocument();
  });

  it('handles edge cases: zero values', async () => {
    const user = userEvent.setup();
    renderWithProviders(<ROICalculator />);

    await fillFormField(/Monthly Revenue/i, '0');
    await fillFormField(/Monthly Leads/i, '0');
    await fillFormField(/Conversion Rate/i, '0');
    await fillFormField(/Current Monthly Marketing Spend/i, '0');

    await submitForm(/Calculate My ROI/i);

    // All calculations should result in 0
    expect(screen.getByText('0')).toBeInTheDocument(); // Current revenue
    expect(screen.getByText('0')).toBeInTheDocument(); // Potential revenue
    expect(screen.getByText('+£0')).toBeInTheDocument();
    expect(screen.getByText('£0')).toBeInTheDocument();
    expect(screen.getByText('+£0')).toBeInTheDocument();
    expect(screen.getByText('0%')).toBeInTheDocument(); // Since newSpend=0, roi=0
  });

  it('handles edge cases: large numbers', async () => {
    renderWithProviders(<ROICalculator />);

    await fillFormField(/Monthly Revenue/i, '1000000');
    await fillFormField(/Monthly Leads/i, '10000');
    await fillFormField(/Conversion Rate/i, '10');
    await fillFormField(/Current Monthly Marketing Spend/i, '50000');

    await submitForm(/Calculate My ROI/i);

    // currentRevenue = 1000000 * 0.1 = 100000
    // improvedLeads = 10000 * 3.2 = 32000
    // improvedConv = min(18, 15) = 15
    // improvedCustomers = 32000 * 0.15 = 4800
    // improvedRevenue = 4800 * 100 = 480000
    // revenueIncrease = 480000 - 100000 = 380000
    // newSpend = 50000 * 1.5 = 75000
    // netProfit = 380000 - 75000 = 305000
    // roi = (305000 / 75000) * 100 ≈ 406.67, rounded to 407

    expect(screen.getByText('100,000')).toBeInTheDocument();
    expect(screen.getByText('480,000')).toBeInTheDocument();
    expect(screen.getByText('+£380,000')).toBeInTheDocument();
    expect(screen.getByText('£75,000')).toBeInTheDocument();
    expect(screen.getByText('+£305,000')).toBeInTheDocument();
    expect(screen.getByText('407%')).toBeInTheDocument();
  });

  it('handles conversion rate cap at 15%', async () => {
    renderWithProviders(<ROICalculator />);

    await fillFormField(/Conversion Rate/i, '10'); // 10 * 1.8 = 18, but capped at 15

    await submitForm(/Calculate My ROI/i);

    // improvedConv should be 15, not 18
    // improvedCustomers = (100 * 3.2) * (15/100) = 320 * 0.15 = 48
    // improvedRevenue = 48 * 100 = 4800
    // revenueIncrease = 4800 - 300 = 4500
    // newSpend = 3000
    // netProfit = 4500 - 3000 = 1500
    // roi = (1500 / 3000) * 100 = 50

    expect(screen.getByText('4,800')).toBeInTheDocument();
    expect(screen.getByText('+£4,500')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('shows results section after calculation', async () => {
    renderWithProviders(<ROICalculator />);

    // Initially hidden
    expect(screen.queryByText('Your Potential Results')).not.toBeInTheDocument();

    await submitForm(/Calculate My ROI/i);

    // Now visible
    expect(screen.getByText('Your Potential Results')).toBeInTheDocument();
  });

  it('renders CTA links correctly', async () => {
    renderWithProviders(<ROICalculator />);

    await submitForm(/Calculate My ROI/i);

    const strategyLink = screen.getByRole('link', { name: /Get Free Strategy Session/i });
    expect(strategyLink).toHaveAttribute('href', '/strategy-session');

    const learnMoreLink = screen.getByRole('link', { name: /Learn More/i });
    expect(learnMoreLink).toHaveAttribute('href', '#contact');
  });
});