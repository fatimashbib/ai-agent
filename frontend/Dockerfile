# Development Dockerfile (live reload, port 3000)
FROM node:16-alpine

WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy all source files
COPY . .

# Expose port 3000 (React default)
EXPOSE 3000

# Start the app in development mode
CMD ["npm", "start"]