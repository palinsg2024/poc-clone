# Use an outdated base image
FROM ubuntu:16.04

# Run as root user
USER root

# Install packages without verifying authenticity
RUN apt-get update && apt-get install -y curl wget openssh-server

# Expose sensitive ports
EXPOSE 22

# Add hardcoded credentials
ENV USERNAME=admin
ENV PASSWORD=admin123

# Start SSH service
CMD ["/usr/sbin/sshd", "-D"]
