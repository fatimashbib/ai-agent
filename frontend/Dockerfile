# Stage 1: Build
FROM node:16-alpine AS builder

WORKDIR /app

# Install dependencies first for better caching
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy all files (excluding what's in .dockerignore)
COPY . .

# Debug: Verify critical files were copied correctly
RUN echo "Verifying file structure..." && \
    ls -l src/context/ && \
    [ -f "src/context/AuthContext.js" ] || (echo "ERROR: AuthContext.js missing!" && exit 1)

# Build the app with explicit production settings
ENV NODE_ENV=production
RUN npm run build

# Stage 2: Serve
FROM nginx:1.23-alpine

# Remove default config and static files
RUN rm -rf /etc/nginx/conf.d/default.conf && \
    rm -rf /usr/share/nginx/html/*

# Copy built app from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget --quiet --tries=1 --spider http://localhost || exit 1

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]