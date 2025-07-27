FROM postgres:15-alpine

# Install required tools
RUN apk add --no-cache \
    bash \
    curl \
    aws-cli \
    postgresql-client \
    tzdata

# Set timezone
ENV TZ=UTC

# Copy backup scripts
COPY scripts/backup.sh /usr/local/bin/backup.sh
COPY scripts/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/*.sh

# Create backup directory
RUN mkdir -p /backups

# Health check
HEALTHCHECK --interval=30m --timeout=10s --start-period=5s --retries=3 \
    CMD /usr/local/bin/health-check.sh || exit 1

# Run backup script
CMD ["/usr/local/bin/backup.sh"]
