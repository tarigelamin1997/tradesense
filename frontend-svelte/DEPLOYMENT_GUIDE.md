# SvelteKit Frontend Deployment Guide

## Quick Start

1. **Install dependencies**:
   ```bash
   cd frontend-svelte
   npm install
   ```

2. **Set environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env to set your API URL
   ```

3. **Run development server**:
   ```bash
   npm run dev
   # Visit http://localhost:3001
   ```

## Production Build

1. **Build for production**:
   ```bash
   npm run build
   ```

2. **Preview production build**:
   ```bash
   npm run preview
   ```

## Deployment Options

### Option 1: Node.js Server

```bash
# After building
node build
```

### Option 2: Static Hosting (Vercel/Netlify)

1. Connect your repository
2. Set build command: `npm run build`
3. Set output directory: `build`
4. Set environment variables

### Option 3: Docker

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/build build/
COPY --from=builder /app/package.json .
RUN npm ci --production
EXPOSE 3000
CMD ["node", "build"]
```

## Environment Variables

- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)

## Testing with Backend

1. Make sure FastAPI backend is running on port 8000
2. Create a test user via backend API or registration page
3. Login and verify all features work

## Parallel Development

Run both frontends simultaneously:
- React: http://localhost:3000
- SvelteKit: http://localhost:3001

## Staging Deployment

For beta testing:
1. Deploy to subdomain (e.g., beta.tradesense.com)
2. Use same backend API
3. Monitor performance and errors
4. Gather user feedback

## Production Checklist

- [ ] Environment variables set correctly
- [ ] API endpoints configured
- [ ] HTTPS enabled
- [ ] Error tracking configured
- [ ] Performance monitoring enabled
- [ ] Backup strategy in place