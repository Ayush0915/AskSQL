# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency files
COPY package.json ./
# If package-lock.json exists, copy it, else ignore
COPY package-lock.json* ./

# Install dependencies
RUN npm install

# Copy project files
COPY . .

# Build the React application
# Inject VITE_API_BASE_URL during build (can be overridden at runtime or default to empty for relative path)
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files from build stage to nginx html directory
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx configuration if needed, or default is fine
# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
