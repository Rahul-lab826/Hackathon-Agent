# Production Frontend Dockerfile
# Stage 1: Build Next.js application
FROM node:18-alpine AS builder
WORKDIR /app

# Copy dependency mappings
COPY package*.json ./
RUN npm ci

# Copy codebase and compile optimized production build
COPY . .
ENV NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
RUN npm run build

# Stage 2: Runtime image
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000

# Copy necessary build artifacts
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next

# Expose port and launch Next.js server
EXPOSE 3000
CMD ["npm", "start"]
