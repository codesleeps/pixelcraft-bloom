import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderWithProviders, waitForLoadingToFinish } from '@/test/utils/test-utils';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PricingSection from '../PricingSection';

// Mock Supabase
vi.mock('@/integrations/supabase/client');
import { mockSupabase } from '@/test/mocks/supabase';

describe('PricingSection', () => {
  const mockPackages = [
    {
      id: '1',
      name: 'Starter',
      description: 'Perfect for small businesses and startups',
      price_monthly: 99,
      price_yearly: 990,
      features: [
        { name: '1 Project', included: true },
        { name: '5 Team Members', included: true },
        { name: 'Basic AI Agents', included: true },
        { name: 'Email Support', included: true },
        { name: 'Analytics Dashboard', included: true },
        { name: 'API Access', included: false },
        { name: 'Custom Integrations', included: false }
      ],
      max_projects: 1,
      max_team_members: 5,
      priority: 1,
      is_active: true
    },
    {
      id: '2',
      name: 'Professional',
      description: 'Ideal for growing businesses',
      price_monthly: 299,
      price_yearly: 2990,
      features: [
        { name: '5 Projects', included: true },
        { name: '20 Team Members', included: true },
        { name: 'Advanced AI Agents', included: true },
        { name: 'Priority Support', included: true },
        { name: 'Advanced Analytics', included: true },
        { name: 'API Access', included: true },
        { name: 'Custom Integrations', included: false }
      ],
      max_projects: 5,
      max_team_members: 20,
      priority: 2,
      is_active: true
    },
    {
      id: '3',
      name: 'Enterprise',
      description: 'For large organizations and enterprises',
      price_monthly: 599,
      price_yearly: 5990,
      features: [
        { name: 'Unlimited Projects', included: true },
        { name: 'Unlimited Team Members', included: true },
        { name: 'Custom AI Models', included: true },
        { name: 'Dedicated Support', included: true },
        { name: 'Enterprise Analytics', included: true },
        { name: 'API Access', included: true },
        { name: 'Custom Integrations', included: true }
      ],
      max_projects: null,
      max_team_members: null,
      priority: 3,
      is_active: true
    }
  ];

  const mockCampaign = {
    id: '1',
    name: 'Test Campaign',
    code: 'TEST10',
    discount_type: 'percentage',
    discount_value: 10,
    max_uses: 100,
    used_count: 50,
    start_date: '2023-01-01',
    end_date: '2024-12-31',
    applicable_packages: ['1', '2', '3'],
    is_active: true
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('displays loading skeleton initially', () => {
    // Mock pending Supabase call
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          order: vi.fn().mockResolvedValue({ data: null, error: null })
        })
      })
    });

    renderWithProviders(<PricingSection />);
    
    expect(screen.getByText('Choose Your Plan')).toBeInTheDocument();
    expect(screen.getAllByRole('presentation')).toHaveLength(2); // Skeleton elements
  });

  it('renders packages successfully from Supabase', async () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          order: vi.fn().mockResolvedValue({ data: mockPackages, error: null })
        })
      })
    });

    renderWithProviders(<PricingSection />);
    
    await waitForLoadingToFinish();
    
    expect(screen.getByText('Starter')).toBeInTheDocument();
    expect(screen.getByText('Professional')).toBeInTheDocument();
    expect(screen.getByText('Enterprise')).toBeInTheDocument();
    expect(screen.getByText('£99')).toBeInTheDocument();
    expect(screen.getByText('£299')).toBeInTheDocument();
    expect(screen.getByText('£599')).toBeInTheDocument();
  });

  it('renders fallback data when Supabase returns no data', async () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          order: vi.fn().mockResolvedValue({ data: [], error: null })
        })
      })
    });

    renderWithProviders(<PricingSection />);
    
    await waitForLoadingToFinish();
    
    expect(screen.getByText('Starter')).toBeInTheDocument();
    expect(screen.getByText('Professional')).toBeInTheDocument();
    expect(screen.getByText('Enterprise')).toBeInTheDocument();
  });

  it('renders fallback data when Supabase returns error', async () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          order: vi.fn().mockResolvedValue({ data: null, error: new Error('Database error') })
        })
      })
    });

    renderWithProviders(<PricingSection />);
    
    await waitForLoadingToFinish();
    
    expect(screen.getByText('Starter')).toBeInTheDocument();
    expect(screen.getByText('Professional')).toBeInTheDocument();
    expect(screen.getByText('Enterprise')).toBeInTheDocument();
  });

  it('toggles billing cycle and updates prices', async () => {
    const user = userEvent.setup();

    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          order: vi.fn().mockResolvedValue({ data: mockPackages, error: null })
        })
      })
    });

    renderWithProviders(<PricingSection />);

    await waitForLoadingToFinish();

    // Initially monthly
    expect(screen.getByText('£99')).toBeInTheDocument();
    expect(screen.getByText('£299')).toBeInTheDocument();
    expect(screen.getByText('£599')).toBeInTheDocument();
    expect(screen.queryByText('Save 20%')).not.toBeInTheDocument();

    // Switch to yearly via Radix Select portal
    const trigger = screen.getByRole('button', { name: /Monthly|Yearly|billing/i });
    await user.click(trigger);
    const yearlyOption = await screen.findByText('Yearly');
    await user.click(yearlyOption);

    await waitFor(() => {
      expect(screen.getByText('£990')).toBeInTheDocument();
      expect(screen.getByText('£2990')).toBeInTheDocument();
      expect(screen.getByText('£5990')).toBeInTheDocument();
      expect(screen.getAllByText('Save 20% annually')).toHaveLength(3);
      expect(screen.getByText('Save 20%')).toBeInTheDocument(); // Badge
    });
  });

  it('applies discount code successfully', async () => {
    const user = userEvent.setup();
    
    mockSupabase.from
      .mockReturnValueOnce({
        select: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            order: vi.fn().mockResolvedValue({ data: mockPackages, error: null })
          })
        })
      })
      .mockReturnValueOnce({
        select: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            single: vi.fn().mockResolvedValue({ data: mockCampaign, error: null })
          })
        })
      });

    renderWithProviders(<PricingSection />);
    
    await waitForLoadingToFinish();
    
    const discountInput = screen.getByPlaceholderText('Discount code');
    const applyButton = screen.getByRole('button', { name: 'Apply' });
    
    await user.type(discountInput, 'TEST10');
    await user.click(applyButton);
    
    await waitFor(() => {
      expect(screen.getByText('Test Campaign Applied!')).toBeInTheDocument();
      expect(screen.getByText('10% discount - Save £9.9')).toBeInTheDocument();
    });
    
    // Check discounted price for Starter (99 - 9.9 = 89.1)
    expect(screen.getByText('£89.1')).toBeInTheDocument();
  });

  it('handles expired discount code', async () => {
    const user = userEvent.setup();
    
    const expiredCampaign = { ...mockCampaign, end_date: '2020-01-01' };
    
    mockSupabase.from
      .mockReturnValueOnce({
        select: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            order: vi.fn().mockResolvedValue({ data: mockPackages, error: null })
          })
        })
      })
      .mockReturnValueOnce({
        select: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            single: vi.fn().mockResolvedValue({ data: expiredCampaign, error: null })
          })
        })
      });

    renderWithProviders(<PricingSection />);
    
    await waitForLoadingToFinish();
    
    const discountInput = screen.getByPlaceholderText('Discount code');
    const applyButton = screen.getByRole('button', { name: 'Apply' });
    
    await user.type(discountInput, 'EXPIRED');
    await user.click(applyButton);
    
    await waitFor(() => {
      expect(screen.queryByText(/Applied!/)).not.toBeInTheDocument();
    });
  });

  it('handles not yet active discount code', async () => {
    const user = userEvent.setup();
    
    const futureCampaign = { ...mockCampaign, start_date: '2025-01-01' };
    
    mockSupabase.from
      .mockReturnValueOnce({
        select: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            order: vi.fn().mockResolvedValue({ data: mockPackages, error: null })
          })
        })
      })
      .mockReturnValueOnce({
        select: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            single: vi.fn().mockResolvedValue({ data: futureCampaign, error: null })
          })
        })
      });

    renderWithProviders(<PricingSection />);
    
    await waitForLoadingToFinish();
    
    const discountInput = screen.getByPlaceholderText('Discount code');
    const applyButton = screen.getByRole('button', { name: 'Apply' });
    
    await user.type(discountInput, 'FUTURE');
    await user.click(applyButton);
    
    await waitFor(() => {
      expect(screen.queryByText(/Applied!/)).not.toBeInTheDocument();
    });
  });

  it('handles max uses reached discount code', async () => {
    const user = userEvent.setup();
    
    const maxedCampaign = { ...mockCampaign, max_uses: 100, used_count: 100 };
    
    mockSupabase.from
      .mockReturnValueOnce({
        select: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            order: vi.fn().mockResolvedValue({ data: mockPackages, error: null })
          })
        })
      })
      .mockReturnValueOnce({
        select: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            single: vi.fn().mockResolvedValue({ data: maxedCampaign, error: null })
          })
        })
      });

    renderWithProviders(<PricingSection />);
    
    await waitForLoadingToFinish();
    
    const discountInput = screen.getByPlaceholderText('Discount code');
    const applyButton = screen.getByRole('button', { name: 'Apply' });
    
    await user.type(discountInput, 'MAXED');
    await user.click(applyButton);
    
    await waitFor(() => {
      expect(screen.queryByText(/Applied!/)).not.toBeInTheDocument();
    });
  });

  it('handles not applicable package discount code', async () => {
    const user = userEvent.setup();
    
    const restrictedCampaign = { ...mockCampaign, applicable_packages: ['2', '3'] };
    
    mockSupabase.from
      .mockReturnValueOnce({
        select: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            order: vi.fn().mockResolvedValue({ data: mockPackages, error: null })
          })
        })
      })
      .mockReturnValueOnce({
        select: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            single: vi.fn().mockResolvedValue({ data: restrictedCampaign, error: null })
          })
        })
      });

    renderWithProviders(<PricingSection />);
    
    await waitForLoadingToFinish();
    
    const discountInput = screen.getByPlaceholderText('Discount code');
    const applyButton = screen.getByRole('button', { name: 'Apply' });
    
    await user.type(discountInput, 'RESTRICTED');
    await user.click(applyButton);
    
    await waitFor(() => {
      expect(screen.queryByText(/Applied!/)).not.toBeInTheDocument();
    });
  });

  it('calculates fixed amount discount correctly', async () => {
    const user = userEvent.setup();
    
    const fixedCampaign = { ...mockCampaign, discount_type: 'fixed', discount_value: 50 };
    
    mockSupabase.from
      .mockReturnValueOnce({
        select: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            order: vi.fn().mockResolvedValue({ data: mockPackages, error: null })
          })
        })
      })
      .mockReturnValueOnce({
        select: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            single: vi.fn().mockResolvedValue({ data: fixedCampaign, error: null })
          })
        })
      });

    renderWithProviders(<PricingSection />);
    
    await waitForLoadingToFinish();
    
    const discountInput = screen.getByPlaceholderText('Discount code');
    const applyButton = screen.getByRole('button', { name: 'Apply' });
    
    await user.type(discountInput, 'FIXED50');
    await user.click(applyButton);
    
    await waitFor(() => {
      expect(screen.getByText('Test Campaign Applied!')).toBeInTheDocument();
      expect(screen.getByText('Save £50')).toBeInTheDocument();
    });
    
    // Check discounted price for Starter (99 - 50 = 49)
    expect(screen.getByText('£49')).toBeInTheDocument();
  });

  it('applies discount to correct package', async () => {
    const user = userEvent.setup();
    
    const packageSpecificCampaign = { ...mockCampaign, applicable_packages: ['2'] };
    
    mockSupabase.from
      .mockReturnValueOnce({
        select: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            order: vi.fn().mockResolvedValue({ data: mockPackages, error: null })
          })
        })
      })
      .mockReturnValueOnce({
        select: vi.fn().mockReturnValue({
          eq: vi.fn().mockReturnValue({
            single: vi.fn().mockResolvedValue({ data: packageSpecificCampaign, error: null })
          })
        })
      });

    renderWithProviders(<PricingSection />);
    
    await waitForLoadingToFinish();
    
    const discountInput = screen.getByPlaceholderText('Discount code');
    const applyButton = screen.getByRole('button', { name: 'Apply' });
    
    await user.type(discountInput, 'PROFESSIONAL');
    await user.click(applyButton);
    
    await waitFor(() => {
      expect(screen.getByText('Test Campaign Applied!')).toBeInTheDocument();
    });
    
    // Professional package should be discounted (299 - 29.9 = 269.1), others unchanged
    expect(screen.getByText('£269.1')).toBeInTheDocument();
    expect(screen.getByText('£99')).toBeInTheDocument();
    expect(screen.getByText('£599')).toBeInTheDocument();
  });

  it('calls handleSubscribe with correct parameters', async () => {
    const user = userEvent.setup();
    const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          order: vi.fn().mockResolvedValue({ data: mockPackages, error: null })
        })
      })
    });

    renderWithProviders(<PricingSection />);
    
    await waitForLoadingToFinish();
    
    const getStartedButtons = screen.getAllByRole('button', { name: 'Get Started' });
    await user.click(getStartedButtons[0]); // Starter package
    
    expect(consoleSpy).toHaveBeenCalledWith('Subscribe to package:', '1', 'with discount:', '');
    
    consoleSpy.mockRestore();
  });

  it('displays Most Popular badge on Professional package', async () => {
    mockSupabase.from.mockReturnValue({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          order: vi.fn().mockResolvedValue({ data: mockPackages, error: null })
        })
      })
    });

    renderWithProviders(<PricingSection />);
    
    await waitForLoadingToFinish();
    
    const mostPopularBadge = screen.getByText('Most Popular');
    expect(mostPopularBadge).toBeInTheDocument();
    
    // Verify it's positioned near Professional package
    const professionalCard = screen.getByText('Professional').closest('.group');
    expect(professionalCard).toContainElement(mostPopularBadge);
  });
});