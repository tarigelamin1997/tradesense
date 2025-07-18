# Frontend Dockerfile for Production
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
ARG VITE_API_BASE_URL
ARG VITE_STRIPE_PUBLISHABLE_KEY
ARG VITE_SENTRY_DSN
ARG VITE_GA_TRACKING_ID

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_STRIPE_PUBLISHABLE_KEY=$VITE_STRIPE_PUBLISHABLE_KEY
ENV VITE_SENTRY_DSN=$VITE_SENTRY_DSN
ENV VITE_GA_TRACKING_ID=$VITE_GA_TRACKING_ID

RUN npm run build

# Production stage - Nginx
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost || exit 1

# Expose port
EXPOSE 80

# Run nginx
CMD ["nginx", "-g", "daemon off;"]