# Stage 1: Build the Vue app
FROM node:22-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# Note: If using Vite, this is usually 'npm run build'
RUN npm run build 

# Stage 2: Serve with Nginx
FROM nginx:alpine AS production-stage
# Copy the built files from the previous stage
# Vue CLI puts files in /dist, Vite puts them in /dist as well.
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy our custom Nginx config (we will make this next)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]