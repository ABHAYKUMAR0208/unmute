# --- build stage ---
FROM node:20-alpine AS build
WORKDIR /app

ARG VITE_TOKEN_ENDPOINT=http://localhost:8081/token
ENV VITE_TOKEN_ENDPOINT=$VITE_TOKEN_ENDPOINT

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

# --- serve stage ---
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
