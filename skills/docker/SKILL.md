# Docker Skill

Manage Docker containers, images, and resources with live status.

## Live Docker Context

**Running Containers:**
!`docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | head -10`

**Container Resource Usage:**
!`docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}' | head -10`

**Images:**
!`docker images --format 'table {{.Repository}}\t{{.Tag}}\t{{.Size}}' | head -10`

**Disk Usage:**
!`docker system df`

**Networks:**
!`docker network ls --format 'table {{.Name}}\t{{.Driver}}\t{{.Scope}}'`

**Volumes:**
!`docker volume ls --format 'table {{.Name}}\t{{.Driver}}'`

## Common Operations

### Container Management
```bash
# Start container
docker start <container>

# Stop container
docker stop <container>

# Restart container
docker restart <container>

# View logs
docker logs -f <container>

# Execute command in container
docker exec -it <container> /bin/bash
```

### Image Management
```bash
# Pull image
docker pull <image>

# Build image
docker build -t <name>:<tag> .

# Remove unused images
docker image prune -a

# Tag image
docker tag <source> <target>
```

### Compose Operations
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild service
docker-compose up -d --build <service>
```

### Cleanup
```bash
# Remove stopped containers
docker container prune

# Remove unused networks
docker network prune

# Remove unused volumes
docker volume prune

# Full cleanup
docker system prune -a --volumes
```

## Health Checks

**Check container health:**
!`docker ps --filter "health=unhealthy" --format '{{.Names}}: {{.Status}}'`

**Check for restarts:**
!`docker ps --format '{{.Names}}: {{.Status}}' | grep -i restart`

**Memory pressure:**
!`docker stats --no-stream | awk 'NR>1 && $7+0 > 80 {print $2": "$7" memory"}'`

## Troubleshooting

**Container not starting:**
- Check logs: `docker logs <container>`
- Check events: `docker events --since 1h`
- Inspect: `docker inspect <container>`

**Out of disk space:**
- Check usage: `docker system df`
- Prune: `docker system prune -a --volumes`

**Network issues:**
- List networks: `docker network ls`
- Inspect network: `docker network inspect <network>`
- Check DNS: `docker exec <container> nslookup google.com`
