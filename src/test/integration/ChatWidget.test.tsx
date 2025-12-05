import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { ChatWidget } from '@/components/ChatWidget';

// Mock the API
global.fetch = vi.fn();

const mockFetch = global.fetch as ReturnType<typeof vi.fn>;

const wrapper = ({ children }: { children: React.ReactNode }) => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
            mutations: { retry: false },
        },
    });

    return (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>{children}</BrowserRouter>
        </QueryClientProvider>
    );
};

describe('ChatWidget Integration', () => {
    beforeEach(() => {
        mockFetch.mockClear();
    });

    it('should send message and receive AI response', async () => {
        // Mock successful API response
        mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({
                response: 'Hello! I can help you with web development services.',
                conversation_id: 'test-conv-123',
                agent_type: 'chat_agent',
                metadata: {},
            }),
        });

        render(<ChatWidget initialOpen={true} />, { wrapper });

        // Wait for welcome message
        await waitFor(() => {
            expect(screen.getByText(/PixelCraft AI assistant/i)).toBeInTheDocument();
        });

        // Type and send message
        const input = screen.getByPlaceholderText(/Type your message/i);
        const sendButton = screen.getByRole('button', { name: /send/i });

        fireEvent.change(input, { target: { value: 'I need a website' } });
        fireEvent.click(sendButton);

        // Verify API was called
        await waitFor(() => {
            expect(mockFetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/chat/message'),
                expect.objectContaining({
                    method: 'POST',
                    headers: expect.objectContaining({
                        'Content-Type': 'application/json',
                    }),
                    body: expect.stringContaining('I need a website'),
                })
            );
        });

        // Verify AI response appears
        await waitFor(() => {
            expect(screen.getByText(/help you with web development/i)).toBeInTheDocument();
        });
    });

    it('should handle API errors gracefully', async () => {
        mockFetch.mockRejectedValueOnce(new Error('Network error'));

        render(<ChatWidget initialOpen={true} />, { wrapper });

        const input = screen.getByPlaceholderText(/Type your message/i);
        const sendButton = screen.getByRole('button', { name: /send/i });

        fireEvent.change(input, { target: { value: 'Test message' } });
        fireEvent.click(sendButton);

        // Verify error message appears
        await waitFor(() => {
            expect(screen.getByText(/encountered an error/i)).toBeInTheDocument();
        });
    });
});
