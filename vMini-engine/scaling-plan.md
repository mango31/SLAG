# vMini Engine Scaling Plan

## Current Infrastructure

### ECS Service
- Service Name: vmini-engine-service-production
- Launch Type: FARGATE
- Desired Count: 1
- Platform Version: LATEST
- No auto-scaling configured
- Task Definition: vmini-engine-production:86
- CPU: 2048
- Memory: 4096

### Redis (ElastiCache)
- Instance: cache.t4g.micro
- Version: Redis 7.0.7
- Single node in us-west-2a
- No encryption or auth token
- Maintenance Window: sun:05:00-sun:09:00
- Snapshot Window: 10:00-11:00

### Load Balancer
- Type: Application Load Balancer (internet-facing)
- DNS: vmini-engine-alb-production-943444221.us-west-2.elb.amazonaws.com
- Target Group:
  - Health Check Path: /health
  - Interval: 60 seconds
  - Timeout: 10 seconds
  - Healthy threshold: 2
  - Unhealthy threshold: 3
  - Port: 8000

### Network
- VPC: vpc-084087a335373ed6c
- Availability Zones: us-west-2a, us-west-2b
- Public Subnets: 
  - subnet-08e2f4a63424670d9 (us-west-2a)
  - subnet-07754accd2f3042f7 (us-west-2b)
- Security Groups:
  - ALB: sg-0f3bf2797c727a53b
  - App: sg-04515fc78b0af01dd
  - Redis: sg-0b0664e5fa92bbb6d

### Current Limitations
1. Single-threaded request handling
2. Long-running synchronous operations block health checks
3. No concurrent request handling
4. In-memory state lost on container restarts
5. No request queuing system
6. Single Redis node (no failover)
7. Tasks failing health checks during story generation
8. No auto-scaling configuration

## Proposed Architecture

### 1. API Layer (FastAPI)
- Convert `/generate` endpoint to return immediate request ID
- Add `/status/{request_id}` endpoint for progress checking
- Move state management to Redis
- Keep health checks responsive during processing

### 2. Queue Management (Redis)
- Upgrade to cache.t4g.small or medium for better performance
- Consider Redis cluster mode for scalability
- Request queue for story generation jobs
- State management for ongoing requests
- Progress tracking per request
- Result caching
- Rate limiting implementation

### 3. Worker Layer
- Separate worker processes/containers
- Background task processing
- Parallel story generation
- Independent scaling from API layer

### 4. Data Flow
User Request → API → Redis Queue → Workers → Redis State → API → User


## Implementation Phases

### Phase 1: Redis State Migration (1-2 weeks)
1. **Redis Schema Design**
   - Design key structure for request tracking
   - Define TTL policies
   - Plan data serialization format

2. **Redis Implementation**
   ```
   Keys Structure:
   request:{id}:status      # String: pending|processing|completed|failed
   request:{id}:progress    # Hash: {stage, step, total_steps, timestamp}
   request:{id}:result      # String: JSON story data
   request:{id}:metadata    # Hash: {prompt, user_id, created_at}
   active_requests          # Sorted Set: score=timestamp
   ```

3. **API Updates**
   - Modify `/generate` endpoint
   - Add `/status/{request_id}` endpoint
   - Implement request ID generation
   - Add Redis state management

4. **Testing**
   - Unit tests for Redis operations
   - Integration tests for state management
   - Load testing with concurrent requests

### Phase 2: Worker Architecture (2-3 weeks)
1. **Worker Service Setup**
   - Create worker service in ECS
   - Configure worker task definition
   - Set up worker security groups
   - Implement worker health monitoring

2. **Queue Implementation**
   ```
   Keys Structure:
   queue:pending           # List: pending request IDs
   queue:processing        # Hash: {request_id: worker_id}
   queue:failed           # List: failed request IDs
   worker:{id}:heartbeat  # String: timestamp
   ```

3. **Worker Logic**
   - Implement queue polling
   - Add story generation logic
   - Handle failures and retries
   - Implement progress updates

4. **Deployment**
   - Deploy worker containers
   - Configure auto-scaling
   - Set up monitoring
   - Test failover scenarios

### Phase 3: API Layer Updates (1-2 weeks)
1. **FastAPI Modifications**
   - Update request handling
   - Implement async endpoints
   - Add request validation
   - Implement rate limiting

2. **Health Check Improvements**
   - Separate health check thread
   - Add Redis health check
   - Add worker health check
   - Implement graceful degradation

3. **Monitoring Setup**
   - Configure CloudWatch metrics
   - Set up alarms
   - Add request tracing
   - Implement logging strategy

### Phase 4: Scaling & Optimization (1-2 weeks)
1. **Auto-scaling Configuration**
   ```
   Metrics:
   - CPU Utilization (target: 70%)
   - Queue Length
   - Memory Usage
   - Request Latency
   ```

2. **Redis Optimization**
   - Upgrade to cache.t4g.small
   - Configure eviction policies
   - Set up backup strategy
   - Implement cache warming

3. **Load Testing**
   - Test concurrent requests
   - Verify scaling behavior
   - Measure latency
   - Validate error handling

4. **Documentation & Runbooks**
   - Update API documentation
   - Create operational runbooks
   - Document scaling policies
   - Create troubleshooting guides

## Success Metrics
1. **Performance**
   - Support 100+ concurrent requests
   - < 5s response time for status checks
   - < 1s for request acceptance
   - 99.9% uptime

2. **Scalability**
   - Auto-scale to handle load
   - No failed health checks during scaling
   - Graceful degradation under load
   - Even load distribution

3. **Reliability**
   - No data loss on failures
   - Successful request recovery
   - Consistent state management
   - Proper error handling

4. **Monitoring**
   - Real-time queue metrics
   - Worker health status
   - Resource utilization
   - Error rate tracking

## Future Considerations
1. Multi-AZ Redis deployment
2. Request prioritization
3. Caching layer for completed stories
4. Advanced rate limiting
5. Request cost optimization
