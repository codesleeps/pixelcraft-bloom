import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from '@/test/utils/test-utils';
import { mockAuthenticatedUser, mockUnauthenticatedUser } from '@/test/mocks/useAuth';

// Mock React Router
vi.mock('react-router-dom', () => ({
  Link: ({ to, children, ...props }: any) => (
    <a href={to} {...props}>
      {children}
    </a>
  ),
  useLocation: vi.fn(() => ({
    pathname: '/',
    hash: '',
  })),
  useNavigate: vi.fn(() => vi.fn()),
}));

// Mock useAuth hook
vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(),
}));

import Navigation from '../Navigation';

describe('Navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Authenticated user rendering', () => {
    beforeEach(() => {
      const { useAuth } = vi.mocked('@/hooks/useAuth');
      useAuth.mockReturnValue(mockAuthenticatedUser());
    });

    it('renders Dashboard link and Sign Out button, not Sign In', () => {
      renderWithProviders(<Navigation />);
      expect(screen.getByRole('link', { name: /Dashboard/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Sign Out/i })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Sign In/i })).not.toBeInTheDocument();
    });
  });

  describe('Unauthenticated user rendering', () => {
    beforeEach(() => {
      const { useAuth } = vi.mocked('@/hooks/useAuth');
      useAuth.mockReturnValue(mockUnauthenticatedUser());
    });

    it('renders Sign In button, not Dashboard link or Sign Out button', () => {
      renderWithProviders(<Navigation />);
      expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /Dashboard/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /Sign Out/i })).not.toBeInTheDocument();
    });
  });

  describe('Active link highlighting', () => {
    it('highlights Home when pathname is /', () => {
      const { useLocation } = vi.mocked('react-router-dom');
      useLocation.mockReturnValue({ pathname: '/', hash: '' });
      renderWithProviders(<Navigation />);
      const homeLink = screen.getByRole('link', { name: 'Home' });
      expect(homeLink).toHaveClass('text-primary');
      // Others should have text-gray-600, but since it's conditional, check specific ones
      const servicesLink = screen.getByRole('link', { name: 'Services' });
      expect(servicesLink).toHaveClass('text-gray-600');
    });

    it('highlights Services when hash is #services', () => {
      const { useLocation } = vi.mocked('react-router-dom');
      useLocation.mockReturnValue({ pathname: '/', hash: '#services' });
      renderWithProviders(<Navigation />);
      const servicesLink = screen.getByRole('link', { name: 'Services' });
      expect(servicesLink).toHaveClass('text-primary');
      const homeLink = screen.getByRole('link', { name: 'Home' });
      expect(homeLink).toHaveClass('text-gray-600');
    });

    it('highlights Pricing when hash is #pricing', () => {
      const { useLocation } = vi.mocked('react-router-dom');
      useLocation.mockReturnValue({ pathname: '/', hash: '#pricing' });
      renderWithProviders(<Navigation />);
      const pricingLink = screen.getByRole('link', { name: 'Pricing' });
      expect(pricingLink).toHaveClass('text-primary');
    });

    it('highlights About when hash is #about', () => {
      const { useLocation } = vi.mocked('react-router-dom');
      useLocation.mockReturnValue({ pathname: '/', hash: '#about' });
      renderWithProviders(<Navigation />);
      const aboutLink = screen.getByRole('link', { name: 'About' });
      expect(aboutLink).toHaveClass('text-primary');
    });

    it('highlights Contact when hash is #contact', () => {
      const { useLocation } = vi.mocked('react-router-dom');
      useLocation.mockReturnValue({ pathname: '/', hash: '#contact' });
      renderWithProviders(<Navigation />);
      const contactLink = screen.getByRole('link', { name: 'Contact' });
      expect(contactLink).toHaveClass('text-primary');
    });

    it('highlights Dashboard when pathname is /dashboard', () => {
      const { useLocation } = vi.mocked('react-router-dom');
      useLocation.mockReturnValue({ pathname: '/dashboard', hash: '' });
      renderWithProviders(<Navigation />);
      const dashboardLink = screen.getByRole('link', { name: 'Dashboard' });
      expect(dashboardLink).toHaveClass('text-primary');
    });
  });

  describe('Mobile menu toggle', () => {
    it('opens and closes the mobile menu', async () => {
      renderWithProviders(<Navigation />);
      const menuButton = screen.getByRole('button', { name: /menu/i }); // Assuming aria-label or accessible name
      // Initially closed
      expect(screen.queryByText('Home')).not.toBeVisible(); // Assuming mobile items are not visible initially
      // Open menu
      await userEvent.click(menuButton);
      expect(screen.getByText('Home')).toBeVisible();
      // Close menu
      await userEvent.click(menuButton);
      expect(screen.queryByText('Home')).not.toBeVisible();
    });
  });

  describe('Mobile menu item click', () => {
    it('closes the menu when a nav item is clicked', async () => {
      renderWithProviders(<Navigation />);
      const menuButton = screen.getByRole('button', { name: /menu/i });
      await userEvent.click(menuButton);
      expect(screen.getByText('Home')).toBeVisible();
      const homeLink = screen.getByRole('link', { name: 'Home' });
      await userEvent.click(homeLink);
      expect(screen.queryByText('Home')).not.toBeVisible();
    });
  });

  describe('Sign Out functionality', () => {
    it('calls signOut when Sign Out button is clicked', async () => {
      const { useAuth } = vi.mocked('@/hooks/useAuth');
      const mockSignOut = vi.fn();
      useAuth.mockReturnValue({ ...mockAuthenticatedUser(), signOut: mockSignOut });
      renderWithProviders(<Navigation />);
      const signOutButton = screen.getByRole('button', { name: /Sign Out/i });
      await userEvent.click(signOutButton);
      expect(mockSignOut).toHaveBeenCalled();
    });
  });

  describe('Navigation items rendering', () => {
    it('renders all navigation items with correct href attributes', () => {
      renderWithProviders(<Navigation />);
      expect(screen.getByRole('link', { name: 'Home' })).toHaveAttribute('href', '/');
      expect(screen.getByRole('link', { name: 'Services' })).toHaveAttribute('href', '#services');
      expect(screen.getByRole('link', { name: 'Pricing' })).toHaveAttribute('href', '#pricing');
      expect(screen.getByRole('link', { name: 'About' })).toHaveAttribute('href', '#about');
      expect(screen.getByRole('link', { name: 'Contact' })).toHaveAttribute('href', '#contact');
      expect(screen.getByRole('link', { name: 'Dashboard' })).toHaveAttribute('href', '/dashboard');
    });
  });

  describe('Logo link', () => {
    it('links to /', () => {
      renderWithProviders(<Navigation />);
      const logoLink = screen.getByText('PixelCraft').closest('a');
      expect(logoLink).toHaveAttribute('href', '/');
    });
  });
});