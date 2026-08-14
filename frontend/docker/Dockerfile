# Stage 1: Build static assets with Node.js
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . ./
RUN npm run build

# Stage 2: Serve static assets with Nginx
FROM nginx:alpine

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
