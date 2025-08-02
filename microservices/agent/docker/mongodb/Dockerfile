FROM mongo:6.0

# Environment variables
ENV MONGO_INITDB_DATABASE="agent_context"

# Copy the initialization script
COPY init-mongo.js /docker-entrypoint-initdb.d/

# Expose MongoDB port
EXPOSE 27017

# Set the command to run when starting the container
CMD ["mongod"] 