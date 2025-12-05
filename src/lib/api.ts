import { supabase } from '@/integrations/supabase/client';

export const getAuthHeaders = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };

    if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`;
    }

    return headers;
};

export const authenticatedFetch = async (url: string, options: RequestInit = {}) => {
    const headers = await getAuthHeaders();

    return fetch(url, {
        ...options,
        headers: {
            ...headers,
            ...options.headers,
        },
    });
};
