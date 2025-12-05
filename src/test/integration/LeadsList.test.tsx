import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import LeadsList from '@/pages/LeadsList';
import { AuthProvider } from '@/hooks/useAuth';

// Mock the API
global.fetch = vi.fn();
const mockFetch = global.fetch as ReturnType<typeof vi.fn>;

// Mock auth
vi.mock('@/lib/api', () => ({
    authenticatedFetch: vi.fn((url, options) => global.fetch(url, options)),
    getAuthHeaders: vi.fn(async () => ({
        'Content-Type': 'application/json',
        'Authorization': 'Bearer mock-token',
    })),
}));

const wrapper = ({ children }: { children: React.ReactNode }) => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
            mutations: { retry: false },
        },
    });

    return (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>
                <BrowserRouter>
                    <Routes>
                        <Route path="/" element={children} />
                    </Routes>
                </BrowserRouter>
            </AuthProvider>
        </QueryClientProvider>
    );
};

describe('LeadsList Integration', () => {
    beforeEach(() => {
        mockFetch.mockClear();
    });

    it('should load and display leads from API', async () => {
        const mockLeads = {
            items: [
                {
                    id: '1',
                    name: 'John Doe',
                    email: 'john@example.com',
                    company: 'Acme Corp',
                    status: 'received',
                    lead_score: 85,
                    services_interested: ['web_development'],
                    created_at: new Date().toISOString(),
                },
                {
                    id: '2',
                    name: 'Jane Smith',
                    email: 'jane@example.com',
                    company: 'Tech Inc',
                    status: 'qualified',
                    lead_score: 92,
                    services_interested: ['ecommerce_solutions'],
                    created_at: new Date().toISOString(),
                },
            ],
            total: 2,
        };

        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockLeads,
        });

        render(<LeadsList />, { wrapper });

        // Verify API was called
        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/leads?'),
                expect.any(Object)
            );
        });

        // Verify leads are displayed
        await waitFor(() => {
            expect(screen.getByText('John Doe')).toBeInTheDocument();
            expect(screen.getByText('Jane Smith')).toBeInTheDocument();
            expect(screen.getByText('Acme Corp')).toBeInTheDocument();
            expect(screen.getByText('Tech Inc')).toBeInTheDocument();
        });

        // Verify stats are calculated
        expect(screen.getByText('2')).toBeInTheDocument(); // Total leads
    });

    it('should handle API errors', async () => {
        mockFetch.mockRejectedValueOnce(new Error('Failed to fetch leads'));

        render(<LeadsList />, { wrapper });

        await waitFor(() => {
            expect(screen.getByText(/Failed to fetch leads/i)).toBeInTheDocument();
        });
    });

    it('should filter leads by status', async () => {
        const mockLeads = {
            items: [
                {
                    id: '1',
                    name: 'Qualified Lead',
                    email: 'qualified@example.com',
                    company: 'Test Co',
                    status: 'qualified',
                    lead_score: 90,
                    services_interested: [],
                    created_at: new Date().toISOString(),
                },
            ],
            total: 1,
        };

        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockLeads,
        });

        render(<LeadsList />, { wrapper });

        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('status=qualified'),
                expect.any(Object)
            );
        });
    });
});
