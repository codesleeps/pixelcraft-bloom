import { vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';

export const mockUseLocation = vi.fn(() => ({
  pathname: '/',
  hash: '',
}));

export const mockUseNavigate = vi.fn(() => vi.fn());

export const Link = ({ to, children, ...props }: any) => (
  <a href={to} {...props}>
    {children}
  </a>
);

export { MemoryRouter };