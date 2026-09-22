# ==========================================
	# Stage 1: Build Environment
# ==========================================
FROM node:20-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy dependency files first to leverage Docker caching layers
COPY package*.json ./

# Install development dependencies required for building the application
RUN npm install

# Copy the rest of the application source code
COPY . .



# Document that the container intends to listen on this port
EXPOSE 3000

# Define the command to start the application when the container launches
CMD ["node", "app.js"]
