#!/usr/bin/env python3
"""
Script untuk debug Redis connection
"""
import redis
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_redis_connection():
    """Test Redis connection dengan berbagai URL"""
    
    redis_urls = [
        os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        'redis://localhost:6379/0',
        'redis://127.0.0.1:6379/0',
        'redis://localhost:6379',
        'redis://127.0.0.1:6379',
    ]
    
    print("Testing Redis connections...")
    print("=" * 50)
    
    for redis_url in redis_urls:
        print(f"Testing: {redis_url}")
        try:
            r = redis.from_url(redis_url, socket_connect_timeout=5)
            result = r.ping()
            print(f"✅ SUCCESS: {result}")
            print(f"Redis Info: {r.info('server')['redis_version']}")
            return redis_url
        except redis.ConnectionError as e:
            print(f"❌ Connection Error: {str(e)}")
        except redis.TimeoutError as e:
            print(f"❌ Timeout Error: {str(e)}")
        except Exception as e:
            print(f"❌ General Error: {str(e)}")
        print("-" * 30)
    
    return None

def check_redis_process():
    """Check if Redis process is running"""
    import subprocess
    import platform
    
    print("\nChecking Redis processes...")
    print("=" * 50)
    
    try:
        if platform.system() == "Windows":
            # Check Windows processes
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq redis-server.exe'],
                capture_output=True, text=True
            )
            if 'redis-server.exe' in result.stdout:
                print("✅ Redis server process found")
            else:
                print("❌ Redis server process not found")
                print("Try: redis-server")
        else:
            # Check Linux/WSL processes
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if 'redis-server' in result.stdout:
                print("✅ Redis server process found")
            else:
                print("❌ Redis server process not found")
                print("Try: sudo service redis-server start")
                
    except Exception as e:
        print(f"Error checking processes: {str(e)}")

def check_ports():
    """Check if Redis port is listening"""
    import socket
    
    print("\nChecking port availability...")
    print("=" * 50)
    
    def check_port(host, port):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    hosts_ports = [
        ('localhost', 6379),
        ('127.0.0.1', 6379),
    ]
    
    for host, port in hosts_ports:
        if check_port(host, port):
            print(f"✅ Port {host}:{port} is open")
        else:
            print(f"❌ Port {host}:{port} is closed")

def try_start_redis():
    """Try to start Redis server"""
    import subprocess
    import platform
    
    print("\nTrying to start Redis...")
    print("=" * 50)
    
    try:
        if platform.system() == "Windows":
            print("Windows detected. Try these commands manually:")
            print("1. redis-server")
            print("2. redis-server --port 6379")
            print("3. Docker: docker run -d -p 6379:6379 --name redis redis:alpine")
        else:
            print("Linux/WSL detected. Trying to start Redis...")
            result = subprocess.run(['sudo', 'service', 'redis-server', 'start'], 
                                  capture_output=True, text=True)
            print(f"Command output: {result.stdout}")
            if result.stderr:
                print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"Error starting Redis: {str(e)}")

if __name__ == "__main__":
    print("Redis Connection Debug Script")
    print("=" * 50)
    
    # Check environment
    print(f"Environment REDIS_URL: {os.getenv('REDIS_URL', 'Not set')}")
    
    # Check if Redis process is running
    check_redis_process()
    
    # Check ports
    check_ports()
    
    # Test connections
    working_url = test_redis_connection()
    
    if working_url:
        print(f"\n✅ Redis is working with URL: {working_url}")
        print("You can now start your FastAPI application")
    else:
        print("\n❌ Redis is not accessible")
        print("\nSolutions to try:")
        print("1. Start Redis server: redis-server")
        print("2. Use Docker: docker run -d -p 6379:6379 --name redis redis:alpine")
        print("3. Install Redis: https://redis.io/download")
        print("4. Check firewall settings")
        try_start_redis()