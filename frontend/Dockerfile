# Frontend Dockerfile for Next.js application
# Node 20 LTS

ARG NODE_VERSION=20

FROM node:${NODE_VERSION}-alpine as base

# Set working directory
WORKDIR /app

# Install dependencies only when needed
FROM base as deps

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
# Use npm install instead of npm ci to handle missing/outdated lock file
RUN npm install

# Development stage
FROM base as dev

# Copy node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Set environment variable for Next.js
ENV PORT=3000 \
    HOSTNAME="0.0.0.0"

# Default command for development
CMD ["npm", "run", "dev"]

# Production builder stage
FROM base as builder

# Copy node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy application code
COPY . .

# Set production environment
ENV NODE_ENV=production

# Build the application
RUN npm run build

# Production runner stage
FROM base as runner

# Set production environment
ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => {process.exit(r.statusCode === 200 ? 0 : 1)})"

# Start the application
CMD ["node", "server.js"]
