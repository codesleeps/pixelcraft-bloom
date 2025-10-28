import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@/test/utils/test-utils';

// Mock React Router
vi.mock('react-router-dom', () => ({
  Link: ({ to, children, ...props }: any) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
}));

// Mock useAuth hook
vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({
    user: null,
    signOut: vi.fn(),
  })),
}));

// Mock LazyImage component
vi.mock('@/components/LazyImage', () => ({
  default: ({ src, alt, className, loading }: any) => (
    <img src={src} alt={alt} className={className} loading={loading} />
  ),
}));

import HeroSection from '../HeroSection';

describe('HeroSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the main headline', () => {
    renderWithProviders(<HeroSection />);
    expect(screen.getByText('Transform Your Digital Marketing')).toBeInTheDocument();
    expect(screen.getByText('Business Growth')).toBeInTheDocument();
  });

  it('renders the subheadline', () => {
    renderWithProviders(<HeroSection />);
    expect(
      screen.getByText(
        'Award-winning digital marketing agency helping ambitious businesses scale faster with data-driven SEO, social media marketing, web design, and proven growth systems.'
      )
    ).toBeInTheDocument();
  });

  it('renders the CTA buttons', () => {
    renderWithProviders(<HeroSection />);
    expect(screen.getByRole('link', { name: /Start Your Growth Journey/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Watch Success Stories/i })).toBeInTheDocument();
  });

  it('renders the "Start Your Growth Journey" button with correct link', () => {
    renderWithProviders(<HeroSection />);
    const link = screen.getByRole('link', { name: /Start Your Growth Journey/i });
    expect(link).toHaveAttribute('href', '/strategy-session');
  });

  it('renders the "Watch Success Stories" button correctly', () => {
    renderWithProviders(<HeroSection />);
    const button = screen.getByRole('button', { name: /Watch Success Stories/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('text-white hover:bg-white/10');
  });

  it('renders all four social proof statistics', () => {
    renderWithProviders(<HeroSection />);
    expect(screen.getByText('500+')).toBeInTheDocument();
    expect(screen.getByText('Happy Clients')).toBeInTheDocument();
    expect(screen.getByText('£50M+')).toBeInTheDocument();
    expect(screen.getByText('Revenue Generated')).toBeInTheDocument();
    expect(screen.getByText('300%')).toBeInTheDocument();
    expect(screen.getByText('Average ROI')).toBeInTheDocument();
    expect(screen.getByText('24/7')).toBeInTheDocument();
    expect(screen.getByText('Expert Support')).toBeInTheDocument();
  });

  it('renders the LazyImage with correct src and alt', () => {
    renderWithProviders(<HeroSection />);
    const img = screen.getByAltText('Digital marketing team collaborating on business growth strategies');
    expect(img).toHaveAttribute('src', 'https://images.unsplash.com/photo-1600880292203-757bb62b4baf?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80');
    expect(img).toHaveClass('w-full h-full object-cover');
  });

  it('renders the animated badge with correct text', () => {
    renderWithProviders(<HeroSection />);
    expect(screen.getByText('Growing 500+ businesses worldwide')).toBeInTheDocument();
  });
});