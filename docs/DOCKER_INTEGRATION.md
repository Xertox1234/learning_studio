# Docker Integration for Code Execution

This document describes the Docker-based code execution system implemented in the Python Learning Studio platform.

## Overview

The platform uses Docker containers to provide secure, isolated code execution for student submissions. This approach ensures:

- **Security**: Code runs in isolated containers with no access to the host system
- **Resource Control**: CPU, memory, and execution time limits are enforced
- **Consistency**: Same execution environment for all users
- **Scalability**: Can handle multiple concurrent executions

## Architecture

### Components

1. **DockerCodeExecutor**: Core executor that manages Docker containers
2. **CachedCodeExecutor**: Wrapper that adds caching capabilities
3. **Python Executor Container**: Specialized container for Python code execution
4. **API Endpoints**: REST API for code execution and exercise submission

### Security Features

- **Network Isolation**: Containers run with `--network=none`
- **Read-only Filesystem**: Container filesystem is read-only
- **Non-root User**: Code executes as unprivileged user
- **Resource Limits**: Memory, CPU, and process limits enforced
- **Code Validation**: Dangerous patterns detected and blocked
- **Timeout Protection**: Execution time limits prevent infinite loops

## Configuration

### Environment Variables

```bash
# Docker Executor Settings
DOCKER_EXECUTOR_ENABLED=true
DOCKER_EXECUTOR_IMAGE=python-learning-studio-executor
DOCKER_EXECUTOR_NETWORK=none
DOCKER_EXECUTOR_MEMORY_LIMIT=256m
DOCKER_EXECUTOR_CPU_LIMIT=0.5
DOCKER_EXECUTOR_TIME_LIMIT=30
```

### Docker Container Limits

- **Memory**: 256MB maximum
- **CPU**: 0.5 cores maximum
- **Execution Time**: 30 seconds maximum
- **Processes**: 50 maximum
- **File Descriptors**: 1024 maximum

## Usage

### Basic Code Execution

```python
from apps.learning.docker_executor import get_code_executor

executor = get_code_executor()
result = executor.execute_code(
    code="print('Hello, World!')",
    time_limit=30,
    memory_limit="256m"
)
```

### Exercise Submission

```python
test_cases = [
    {
        'name': 'Test 1',
        'test_code': 'print(add(2, 3))',
        'expected_output': '5'
    }
]

result = executor.execute_code(
    code=student_code,
    test_cases=test_cases,
    use_cache=False
)
```

### API Endpoints

#### Execute Code
```http
POST /api/v1/execute/
Content-Type: application/json
Authorization: Bearer <token>

{
    "code": "print('Hello, World!')",
    "time_limit": 30,
    "memory_limit": 256
}
```

#### Submit Exercise
```http
POST /api/v1/exercises/{exercise_id}/submit/
Content-Type: application/json
Authorization: Bearer <token>

{
    "code": "def add(a, b):\n    return a + b"
}
```

#### Docker Status
```http
GET /api/v1/docker/status/
Authorization: Bearer <token>
```

## Security Considerations

### Restricted Operations

The executor blocks the following dangerous patterns:

- File system access (`open`, `file`)
- Network operations (`socket`, `urllib`, `requests`)
- System operations (`os`, `sys`, `subprocess`)
- Code injection (`eval`, `exec`, `compile`)
- Introspection (`globals`, `locals`, `vars`)

### Safe Modules

Only these modules are available in the execution environment:

- `math`, `random`, `datetime`
- `collections`, `itertools`, `functools`
- `operator`, `string`, `re`, `json`

### Container Security

- Containers run with minimal privileges
- No new privileges can be acquired
- Filesystem is read-only except for temporary directories
- Network access is completely disabled
- Resource limits prevent resource exhaustion attacks

## Deployment

### Development

```bash
# Start with Docker Compose
docker-compose up -d

# Build executor image
docker build -t python-learning-studio-executor docker/python-executor/
```

### Production

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Scale web service
docker-compose -f docker-compose.prod.yml up -d --scale web=3
```

### Kubernetes

For Kubernetes deployment, use the provided manifests in `/k8s/`:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

## Monitoring

### Health Checks

The system provides health check endpoints:

- `/api/v1/docker/status/` - Docker system status
- `/health/` - Application health check

### Metrics

Monitor these key metrics:

- Code execution success rate
- Average execution time
- Memory usage patterns
- Container creation/destruction rate
- Cache hit rates

### Logging

Docker executor logs include:

- Execution requests and results
- Security violations
- Performance metrics
- Error details

## Troubleshooting

### Common Issues

#### Docker Not Available
```
Error: Docker not available. Code execution will be limited.
```
**Solution**: Ensure Docker is installed and the service is running.

#### Image Build Failures
```
Error: Failed to build Docker image
```
**Solution**: Check Dockerfile syntax and build context permissions.

#### Container Timeout
```
Error: Container execution failed: timeout
```
**Solution**: Code may have infinite loops or be too complex for time limit.

#### Memory Limit Exceeded
```
Error: Container killed due to memory limit
```
**Solution**: Code may be allocating too much memory.

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('apps.learning.docker_executor').setLevel(logging.DEBUG)
```

### Performance Tuning

- Adjust memory limits based on typical exercise requirements
- Monitor cache hit rates and adjust cache timeouts
- Scale container resources based on concurrent usage
- Use Redis for caching in production

## Testing

### Unit Tests

Run the test suite:

```bash
python manage.py test tests.test_docker_execution
```

### Integration Tests

Test with real Docker:

```bash
python manage.py test tests.test_docker_execution.APIEndpointTests
```

### Load Testing

Use the provided load test script:

```bash
python scripts/load_test_executor.py
```

## Future Enhancements

### Planned Features

- Support for additional programming languages
- Advanced resource monitoring
- Container orchestration with Kubernetes
- Distributed execution across multiple nodes
- Enhanced security with custom seccomp profiles
- Real-time execution monitoring and alerts

### Performance Improvements

- Container pooling to reduce startup overhead
- Optimized base images for faster startup
- Advanced caching strategies
- Load balancing across multiple executor nodes

## Security Audit

The code execution system has been designed with security as a top priority:

- ✅ Network isolation
- ✅ Filesystem restrictions
- ✅ Resource limits
- ✅ Code pattern analysis
- ✅ Non-root execution
- ✅ Timeout protection
- ✅ Memory limits
- ✅ Process limits

Regular security audits should be performed to ensure continued protection against new attack vectors.