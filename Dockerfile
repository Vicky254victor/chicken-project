FROM nginx:alpine

# Copy all project files to the default Nginx html directory
COPY . /usr/share/nginx/html

# Expose port 80 for Dokploy to map traffic to
EXPOSE 80

# Start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
