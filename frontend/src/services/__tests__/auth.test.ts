import { authService } from '../auth';
import { server } from '../../test/mocks/server';
import { rest } from 'msw';

describe('Auth Service', () => {
  describe('login', () => {
    it('should login successfully with valid credentials', async () => {
      const result = await authService.login('test@example.com', 'password');

      expect(result).toEqual({
        access_token: 'mock_token',
        token_type: 'bearer',
        user: { id: 1, email: 'test@example.com' }
      });
    });

    it('should handle login failure', async () => {
      server.use(
        rest.post('/api/v1/auth/login', (req, res, ctx) => {
          return res(ctx.status(401), ctx.json({ detail: 'Invalid credentials' }));
        })
      );

      await expect(authService.login('wrong@example.com', 'wrong')).rejects.toThrow();
    });
  });

  describe('logout', () => {
    it('should logout successfully', async () => {
      localStorage.setItem('token', 'mock_token');

      await authService.logout();

      expect(localStorage.getItem('token')).toBeNull();
    });
  });

  describe('getCurrentUser', () => {
    it('should return current user when token exists', async () => {
      localStorage.setItem('token', 'mock_token');

      const user = await authService.getCurrentUser();

      expect(user).toBeDefined();
    });

    it('should return null when no token exists', async () => {
      localStorage.removeItem('token');

      const user = await authService.getCurrentUser();

      expect(user).toBeNull();
    });
  });
});