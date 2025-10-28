import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders, fillFormField, submitForm } from '@/test/utils/test-utils';
import ContactSection from '../ContactSection';

// Mock Supabase
vi.mock('@/integrations/supabase/client');
import { mockSupabase } from '@/test/mocks/supabase';

describe('ContactSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Form validation', () => {
    it('shows error messages for empty required fields', async () => {
      const user = userEvent.setup();
      renderWithProviders(<ContactSection />);

      // Submit without filling any fields
      await submitForm('Get My Free Strategy Session');

      expect(screen.getByText('First name is required')).toBeInTheDocument();
      expect(screen.getByText('Last name is required')).toBeInTheDocument();
      expect(screen.getByText('Email is required')).toBeInTheDocument();
      expect(screen.getByText('Message is required')).toBeInTheDocument();
    });

    it('shows error for invalid email formats', async () => {
      const user = userEvent.setup();
      renderWithProviders(<ContactSection />);

      // Test missing @
      await fillFormField('First Name *', 'John');
      await fillFormField('Last Name *', 'Doe');
      await fillFormField('Email Address *', 'invalidemail');
      await fillFormField('Tell us about your marketing goals *', 'Test message');
      await submitForm('Get My Free Strategy Session');

      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();

      // Test missing domain
      await fillFormField('Email Address *', 'test@');
      await submitForm('Get My Free Strategy Session');

      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();

      // Test invalid characters
      await fillFormField('Email Address *', 'test@invalid..com');
      await submitForm('Get My Free Strategy Session');

      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
    });

    it('clears validation errors when user starts typing', async () => {
      const user = userEvent.setup();
      renderWithProviders(<ContactSection />);

      // Submit to trigger errors
      await submitForm('Get My Free Strategy Session');

      expect(screen.getByText('First name is required')).toBeInTheDocument();

      // Start typing in firstName
      await fillFormField('First Name *', 'J');

      expect(screen.queryByText('First name is required')).not.toBeInTheDocument();
    });
  });

  describe('Successful form submission', () => {
    it('submits form successfully and resets fields', async () => {
      const user = userEvent.setup();

      // Mock successful Supabase response
      mockSupabase.from.mockReturnValue({
        insert: vi.fn().mockResolvedValue({ error: null })
      });

      renderWithProviders(<ContactSection />);

      // Fill required fields
      await fillFormField('First Name *', 'John');
      await fillFormField('Last Name *', 'Doe');
      await fillFormField('Email Address *', 'john@example.com');
      await fillFormField('Tell us about your marketing goals *', 'Test message');

      // Submit
      await submitForm('Get My Free Strategy Session');

      // Verify success message
      await waitFor(() => {
        expect(screen.getByText('Message sent successfully!')).toBeInTheDocument();
      });

      // Verify form reset
      expect(screen.getByLabelText('First Name *')).toHaveValue('');
      expect(screen.getByLabelText('Last Name *')).toHaveValue('');
      expect(screen.getByLabelText('Email Address *')).toHaveValue('');
      expect(screen.getByLabelText('Tell us about your marketing goals *')).toHaveValue('');
    });
  });

  describe('Error handling', () => {
    it('displays error message on submission failure', async () => {
      const user = userEvent.setup();

      // Mock Supabase error
      mockSupabase.from.mockReturnValue({
        insert: vi.fn().mockResolvedValue({ error: new Error('Database error') })
      });

      renderWithProviders(<ContactSection />);

      // Fill required fields
      await fillFormField('First Name *', 'John');
      await fillFormField('Last Name *', 'Doe');
      await fillFormField('Email Address *', 'john@example.com');
      await fillFormField('Tell us about your marketing goals *', 'Test message');

      // Submit
      await submitForm('Get My Free Strategy Session');

      // Verify error message
      await waitFor(() => {
        expect(screen.getByText('Failed to send message')).toBeInTheDocument();
      });
    });
  });

  describe('Service checkboxes', () => {
    it('updates services array when checkboxes are selected/deselected', async () => {
      const user = userEvent.setup();
      renderWithProviders(<ContactSection />);

      const seoCheckbox = screen.getByLabelText('SEO');
      const socialMediaCheckbox = screen.getByLabelText('Social Media');

      // Select SEO
      await user.click(seoCheckbox);
      expect(seoCheckbox).toBeChecked();

      // Select Social Media
      await user.click(socialMediaCheckbox);
      expect(socialMediaCheckbox).toBeChecked();

      // Deselect SEO
      await user.click(seoCheckbox);
      expect(seoCheckbox).not.toBeChecked();
      expect(socialMediaCheckbox).toBeChecked();
    });
  });

  describe('Loading state', () => {
    it('disables submit button and shows loading text during submission', async () => {
      const user = userEvent.setup();

      // Mock slow Supabase response
      mockSupabase.from.mockReturnValue({
        insert: vi.fn().mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ error: null }), 100)))
      });

      renderWithProviders(<ContactSection />);

      // Fill required fields
      await fillFormField('First Name *', 'John');
      await fillFormField('Last Name *', 'Doe');
      await fillFormField('Email Address *', 'john@example.com');
      await fillFormField('Tell us about your marketing goals *', 'Test message');

      // Submit
      await submitForm('Get My Free Strategy Session');

      // Verify button is disabled and shows 'Sending...'
      const submitButton = screen.getByRole('button', { name: /Sending\.\.\./ });
      expect(submitButton).toBeDisabled();

      // Wait for completion
      await waitFor(() => {
        expect(screen.getByText('Message sent successfully!')).toBeInTheDocument();
      });
    });
  });

  describe('Optional fields', () => {
    it('allows submission with only required fields filled', async () => {
      const user = userEvent.setup();

      // Mock successful Supabase response
      mockSupabase.from.mockReturnValue({
        insert: vi.fn().mockResolvedValue({ error: null })
      });

      renderWithProviders(<ContactSection />);

      // Fill only required fields
      await fillFormField('First Name *', 'John');
      await fillFormField('Last Name *', 'Doe');
      await fillFormField('Email Address *', 'john@example.com');
      await fillFormField('Tell us about your marketing goals *', 'Test message');

      // Leave company and phone empty
      expect(screen.getByLabelText('Company Name')).toHaveValue('');
      expect(screen.getByLabelText('Phone Number')).toHaveValue('');

      // Submit
      await submitForm('Get My Free Strategy Session');

      // Verify success
      await waitFor(() => {
        expect(screen.getByText('Message sent successfully!')).toBeInTheDocument();
      });
    });
  });

  describe('Form field updates', () => {
    it('updates state correctly when typing in fields', async () => {
      const user = userEvent.setup();
      renderWithProviders(<ContactSection />);

      // Test firstName
      await fillFormField('First Name *', 'John');
      expect(screen.getByLabelText('First Name *')).toHaveValue('John');

      // Test lastName
      await fillFormField('Last Name *', 'Doe');
      expect(screen.getByLabelText('Last Name *')).toHaveValue('Doe');

      // Test email
      await fillFormField('Email Address *', 'john@example.com');
      expect(screen.getByLabelText('Email Address *')).toHaveValue('john@example.com');

      // Test company
      await fillFormField('Company Name', 'Test Company');
      expect(screen.getByLabelText('Company Name')).toHaveValue('Test Company');

      // Test phone
      await fillFormField('Phone Number', '+1234567890');
      expect(screen.getByLabelText('Phone Number')).toHaveValue('+1234567890');

      // Test message
      await fillFormField('Tell us about your marketing goals *', 'Test message');
      expect(screen.getByLabelText('Tell us about your marketing goals *')).toHaveValue('Test message');
    });
  });
});