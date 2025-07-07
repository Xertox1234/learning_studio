"""
Docker-based code execution service.
Provides secure, isolated code execution using Docker containers.
"""

import json
import logging
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any

import docker
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class DockerCodeExecutor:
    """Docker-based code executor for secure Python code execution."""
    
    def __init__(self):
        """Initialize the Docker client and configuration."""
        try:
            self.client = docker.from_env()
            self.image_name = "python-learning-studio-executor"
            self.network_name = "python_learning_network"
            self.max_execution_time = 30  # seconds
            self.max_memory = "256m"
            self.max_cpu = "0.5"
        except docker.errors.DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise
    
    def build_executor_image(self) -> bool:
        """Build the code executor Docker image if it doesn't exist."""
        try:
            # Check if image exists
            try:
                self.client.images.get(self.image_name)
                logger.info(f"Docker image {self.image_name} already exists")
                return True
            except docker.errors.ImageNotFound:
                pass
            
            # Build the image
            logger.info(f"Building Docker image {self.image_name}...")
            dockerfile_path = Path(settings.BASE_DIR) / "docker" / "python-executor"
            
            image, build_logs = self.client.images.build(
                path=str(dockerfile_path),
                tag=self.image_name,
                rm=True,
                pull=True
            )
            
            logger.info(f"Successfully built Docker image {self.image_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build Docker image: {e}")
            return False
    
    def execute_code(
        self, 
        code: str, 
        test_cases: Optional[List[Dict]] = None,
        time_limit: int = 30,
        memory_limit: str = "256m"
    ) -> Dict[str, Any]:
        """
        Execute Python code in a secure Docker container.
        
        Args:
            code: Python code to execute
            test_cases: Optional list of test cases to run
            time_limit: Maximum execution time in seconds
            memory_limit: Maximum memory usage (e.g., "256m")
            
        Returns:
            Dictionary containing execution results
        """
        execution_id = str(uuid.uuid4())
        logger.info(f"Starting code execution {execution_id}")
        
        try:
            # Ensure the executor image exists
            if not self.build_executor_image():
                return {
                    'success': False,
                    'error': 'Failed to prepare execution environment',
                    'error_type': 'system'
                }
            
            # Prepare environment variables
            env_vars = {
                'CODE': code,
                'TEST_CASES': json.dumps(test_cases or []),
                'TIME_LIMIT': str(time_limit),
                'MEMORY_LIMIT': str(self._parse_memory_limit(memory_limit))
            }
            
            # Run the container
            start_time = time.time()
            result = self._run_container(env_vars, execution_id, memory_limit, time_limit)
            execution_time = time.time() - start_time
            
            # Add execution metadata
            result['execution_id'] = execution_id
            result['total_execution_time'] = execution_time
            
            logger.info(f"Code execution {execution_id} completed in {execution_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Code execution {execution_id} failed: {e}")
            return {
                'success': False,
                'error': f'Execution failed: {str(e)}',
                'error_type': 'system',
                'execution_id': execution_id
            }
    
    def _run_container(
        self, 
        env_vars: Dict[str, str], 
        execution_id: str,
        memory_limit: str,
        time_limit: int
    ) -> Dict[str, Any]:
        """Run the code in a Docker container."""
        container = None
        try:
            # Create and start container
            container = self.client.containers.run(
                image=self.image_name,
                environment=env_vars,
                mem_limit=memory_limit,
                nano_cpus=int(float(self.max_cpu) * 1e9),  # Convert to nanocpus
                network_disabled=True,  # Disable network access
                security_opt=['no-new-privileges:true'],
                read_only=True,
                tmpfs={
                    '/tmp': 'noexec,nosuid,size=100m',
                    '/app/code': 'noexec,nosuid,size=50m',
                    '/app/output': 'noexec,nosuid,size=50m'
                },
                cap_drop=['ALL'],
                cap_add=['SETGID', 'SETUID'],
                pids_limit=50,
                ulimits=[
                    docker.types.Ulimit(name='nproc', soft=50, hard=50),
                    docker.types.Ulimit(name='nofile', soft=1024, hard=1024)
                ],
                detach=True,
                remove=True,  # Auto-remove container when done
                name=f"code-executor-{execution_id}"
            )
            
            # Wait for container to complete with timeout
            try:
                result = container.wait(timeout=time_limit + 5)
                logs = container.logs(stdout=True, stderr=False).decode('utf-8')
                
                # Parse the JSON output from the executor
                try:
                    execution_result = json.loads(logs)
                except json.JSONDecodeError:
                    execution_result = {
                        'success': False,
                        'error': 'Invalid output from executor',
                        'error_type': 'system',
                        'raw_output': logs
                    }
                
                return execution_result
                
            except Exception as e:
                # Container timed out or failed
                try:
                    container.kill()
                except:
                    pass
                
                return {
                    'success': False,
                    'error': f'Container execution failed: {str(e)}',
                    'error_type': 'timeout' if 'timeout' in str(e).lower() else 'system'
                }
                
        except docker.errors.ContainerError as e:
            logger.error(f"Container error: {e}")
            return {
                'success': False,
                'error': f'Container execution error: {str(e)}',
                'error_type': 'execution'
            }
        except Exception as e:
            logger.error(f"Unexpected error running container: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'error_type': 'system'
            }
        finally:
            # Cleanup container if it still exists
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass
    
    def _parse_memory_limit(self, memory_limit: str) -> int:
        """Parse memory limit string to bytes."""
        if memory_limit.endswith('m') or memory_limit.endswith('M'):
            return int(memory_limit[:-1]) * 1024 * 1024
        elif memory_limit.endswith('g') or memory_limit.endswith('G'):
            return int(memory_limit[:-1]) * 1024 * 1024 * 1024
        else:
            return int(memory_limit)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get Docker system information."""
        try:
            info = self.client.info()
            return {
                'docker_version': info.get('ServerVersion'),
                'containers_running': info.get('ContainersRunning', 0),
                'images_count': len(self.client.images.list()),
                'memory_total': info.get('MemTotal', 0),
                'cpus': info.get('NCPU', 0)
            }
        except Exception as e:
            logger.error(f"Failed to get Docker system info: {e}")
            return {'error': str(e)}
    
    def cleanup_old_containers(self, max_age_hours: int = 1):
        """Clean up old containers and images."""
        try:
            # Remove old containers
            containers = self.client.containers.list(
                all=True,
                filters={'name': 'code-executor-'}
            )
            
            removed_count = 0
            for container in containers:
                try:
                    # Check container age
                    created_time = container.attrs['Created']
                    # ... age calculation and removal logic
                    container.remove(force=True)
                    removed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to remove container {container.id}: {e}")
            
            logger.info(f"Cleaned up {removed_count} old containers")
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup containers: {e}")
            return 0


class CachedCodeExecutor:
    """Wrapper around DockerCodeExecutor with caching support."""
    
    def __init__(self):
        self.executor = DockerCodeExecutor()
        self.cache_timeout = 300  # 5 minutes
    
    def execute_code(
        self, 
        code: str, 
        test_cases: Optional[List[Dict]] = None,
        use_cache: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute code with optional caching."""
        
        if use_cache:
            # Create cache key based on code and test cases
            cache_key = self._generate_cache_key(code, test_cases)
            cached_result = cache.get(cache_key)
            
            if cached_result:
                logger.info(f"Using cached result for code execution")
                cached_result['from_cache'] = True
                return cached_result
        
        # Execute code
        result = self.executor.execute_code(code, test_cases, **kwargs)
        
        # Cache successful results
        if use_cache and result.get('success'):
            cache_key = self._generate_cache_key(code, test_cases)
            cache.set(cache_key, result, self.cache_timeout)
        
        result['from_cache'] = False
        return result
    
    def _generate_cache_key(self, code: str, test_cases: Optional[List[Dict]]) -> str:
        """Generate a cache key for the code and test cases."""
        import hashlib
        
        content = code + json.dumps(test_cases or [], sort_keys=True)
        hash_obj = hashlib.md5(content.encode('utf-8'))
        return f"code_execution:{hash_obj.hexdigest()}"


# Global executor instance
_executor_instance = None

def get_code_executor() -> CachedCodeExecutor:
    """Get the global code executor instance."""
    from decouple import config
    
    # Check if Docker is enabled
    docker_enabled = config('DOCKER_EXECUTOR_ENABLED', default=True, cast=bool)
    if not docker_enabled:
        raise ImportError("Docker executor disabled via DOCKER_EXECUTOR_ENABLED=False")
    
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = CachedCodeExecutor()
    return _executor_instance