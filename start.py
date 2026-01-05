#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AWS Solution Architecture Recommendation Agent - 启动脚本
Startup script for AWS Solution Architecture Recommendation Agent
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_env_file():
    """检查.env文件是否存在"""
    env_path = project_root / '.env'
    if not env_path.exists():
        # .env is optional if env vars are already set (common in containers/CI).
        print("[WARNING] .env file not found (this is OK if you exported env vars).")
        return False
    return True

def check_required_env_vars():
    """检查必需的环境变量"""
    required_vars = []
    
    # 检查LLM API Key（至少需要一个）
    llm_keys = ['GROQ_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
    has_llm_key = any(os.getenv(key) for key in llm_keys)
    
    if not has_llm_key:
        required_vars.append("至少一个LLM API Key (GROQ_API_KEY, OPENAI_API_KEY, 或 ANTHROPIC_API_KEY)")
    
    # 数据库配置检查（根据 DATABASE_TYPE）
    database_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
    if database_type == "mysql":
        # MySQL配置（如果选择MySQL则必需）
        mysql_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE']
        missing_mysql = [var for var in mysql_vars if not os.getenv(var)]
        if missing_mysql:
            required_vars.append(f"MySQL配置: {', '.join(missing_mysql)}")
    # SQLite 不需要额外配置，使用默认路径即可
    
    if required_vars:
        print("[ERROR] Missing required environment variables:")
        for var in required_vars:
            print(f"  - {var}")
        return False
    
    return True

async def check_database_connection():
    """检查数据库连接（可选，不阻塞启动）"""
    database_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
    
    if database_type == "mysql":
        try:
            from src.utils.storage.mysql import MySQLClient
            
            mysql = MySQLClient()
            await mysql.connect()
            await mysql.close()
            print("[OK] MySQL connection: Success")
            return True
        except Exception as e:
            print(f"[WARNING] MySQL connection: Failed ({str(e)})")
            print("  Program will try to connect when needed.")
            return False
    else:
        # SQLite - 不需要连接检查，文件会在首次使用时创建
        print("[OK] Using SQLite database (default)")
        return True

def print_startup_info(llm_provider: str):
    """打印启动信息"""
    database_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
    
    print("=" * 60)
    print("AWS Solution Architecture Recommendation Agent")
    print("智能云解决方案推荐智能体")
    print("=" * 60)
    print(f"LLM Provider: {llm_provider.upper()}")
    print(f"Database Type: {database_type.upper()}")
    if database_type == "mysql":
        print(f"MySQL Host: {os.getenv('MYSQL_HOST', 'localhost')}")
        print(f"MySQL Database: {os.getenv('MYSQL_DATABASE', 'aws_arch_agent')}")
    else:
        db_path = os.getenv("SQLITE_DB_PATH", "./data/aws_arch_agent.db")
        print(f"SQLite Database: {db_path}")
    print("=" * 60)
    print()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='AWS Solution Architecture Recommendation Agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 start.py                    # Use default LLM (groq)
  python3 start.py --llm groq         # Use Groq
  python3 start.py --llm openai       # Use OpenAI
  python3 start.py --llm anthropic    # Use Anthropic
  python3 start.py --session-id <id>  # Resume conversation
        """
    )
    
    parser.add_argument(
        '--llm',
        type=str,
        default='groq',
        choices=['openai', 'anthropic', 'groq'],
        help='LLM provider (default: groq)'
    )
    
    parser.add_argument(
        '--session-id',
        type=str,
        default=None,
        help='Session ID to resume conversation'
    )
    
    parser.add_argument(
        '--skip-checks',
        action='store_true',
        help='Skip environment and connection checks'
    )
    
    args = parser.parse_args()
    
    # 加载环境变量（如果没有 python-dotenv，也允许继续使用已导出的环境变量）
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception as e:
        print(f"[WARNING] Could not load .env via python-dotenv: {e}")
        print("  Tip: install it with: pip install python-dotenv")
    
    # 检查环境配置
    if not args.skip_checks:
        print("Checking environment configuration...")
        
        # .env file is optional; only fail if required env vars are missing.
        check_env_file()
        
        if not check_required_env_vars():
            print("\nPlease configure required environment variables in .env file.")
            sys.exit(1)
        
        # 检查数据库连接（不阻塞）
        print("Checking database connection...")
        try:
            asyncio.run(check_database_connection())
        except Exception as e:
            print(f"[WARNING] Could not check database: {e}")
        
        print()
    
    # 打印启动信息
    print_startup_info(args.llm)
    
    # 启动CLI
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            from src.cli.chat import ChatSession
            from uuid import UUID
            
            session_id = UUID(args.session_id) if args.session_id else None
            session = ChatSession(session_id=session_id, llm_provider=args.llm)
            session.start()
            break  # Success, exit loop
        except KeyboardInterrupt:
            print("\n\n[INFO] Program interrupted by user. Goodbye!")
            sys.exit(0)
        except Exception as e:
            error_msg = str(e)
            retry_count += 1
            
            # Check if it's a database connection error
            database_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
            if database_type == "mysql" and ("Can't connect to MySQL" in error_msg or "2003" in error_msg):
                print(f"\n[ERROR] MySQL connection failed (attempt {retry_count}/{max_retries})")
                print(f"Error: {error_msg}\n")
                print("Tip: You can switch to SQLite by setting DATABASE_TYPE=sqlite in .env file")
                
                if retry_count < max_retries:
                    print("Trying to start MySQL service...")
                    # Try to start MySQL via different methods
                    mysql_started = False
                    
                    # Method 1: Try Docker (if available)
                    try:
                        import subprocess
                        result = subprocess.run(
                            ["docker", "ps"],
                            capture_output=True,
                            timeout=2
                        )
                        if result.returncode == 0:
                            print("  - Docker is available, attempting to start MySQL container...")
                            # Check if container exists
                            check_result = subprocess.run(
                                ["docker", "ps", "-a", "--filter", "name=mysql-aws-agent", "--format", "{{.Names}}"],
                                capture_output=True,
                                text=True,
                                timeout=2
                            )
                            if "mysql-aws-agent" in check_result.stdout:
                                # Container exists, try to start it
                                start_result = subprocess.run(
                                    ["docker", "start", "mysql-aws-agent"],
                                    capture_output=True,
                                    text=True,
                                    timeout=5
                                )
                                if start_result.returncode == 0:
                                    print("  [OK] MySQL container started, waiting for it to be ready...")
                                    import time
                                    time.sleep(5)
                                    mysql_started = True
                            else:
                                # Create new container
                                print("  - Creating new MySQL container...")
                                create_result = subprocess.run(
                                    [
                                        "docker", "run", "-d",
                                        "--name", "mysql-aws-agent",
                                        "-e", "MYSQL_ROOT_PASSWORD=test",
                                        "-e", "MYSQL_DATABASE=aws_arch_agent",
                                        "-p", "3306:3306",
                                        "mysql:8.0"
                                    ],
                                    capture_output=True,
                                    text=True,
                                    timeout=10
                                )
                                if create_result.returncode == 0:
                                    print("  [OK] MySQL container created, waiting for it to be ready...")
                                    import time
                                    time.sleep(10)
                                    mysql_started = True
                    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as de:
                        pass  # Docker not available or failed
                    
                    # Method 2: Try Windows service
                    if not mysql_started:
                        try:
                            import subprocess
                            # Check for MySQL Windows service
                            service_result = subprocess.run(
                                ["sc", "query", "MySQL"],
                                capture_output=True,
                                text=True,
                                timeout=2
                            )
                            if "RUNNING" not in service_result.stdout:
                                print("  - Attempting to start MySQL Windows service...")
                                start_service = subprocess.run(
                                    ["net", "start", "MySQL"],
                                    capture_output=True,
                                    text=True,
                                    timeout=5
                                )
                                if start_service.returncode == 0:
                                    print("  [OK] MySQL service started")
                                    import time
                                    time.sleep(3)
                                    mysql_started = True
                        except Exception:
                            pass
                    
                    if mysql_started:
                        print("\nRetrying connection...\n")
                        continue
                    else:
                        if retry_count < max_retries:
                            print("\nMySQL setup options:")
                            print("  1. Install MySQL: https://dev.mysql.com/downloads/mysql/")
                            print("  2. Use Docker: docker run -d --name mysql-aws-agent \\")
                            print("     -e MYSQL_ROOT_PASSWORD=test -e MYSQL_DATABASE=aws_arch_agent \\")
                            print("     -p 3306:3306 mysql:8.0")
                            print("  3. Start MySQL Windows service: net start MySQL")
                            print("  4. Or switch to SQLite: Set DATABASE_TYPE=sqlite in .env")
                            print(f"\nRetrying in 3 seconds... (attempt {retry_count + 1}/{max_retries})\n")
                            import time
                            time.sleep(3)
                            continue
                else:
                    print("\n[FAILED] Could not connect to MySQL after multiple attempts.")
                    print("\nPlease install and start MySQL:")
                    print("  1. Download: https://dev.mysql.com/downloads/mysql/")
                    print("  2. Or use Docker: docker run -d --name mysql-aws-agent \\")
                    print("     -e MYSQL_ROOT_PASSWORD=test -e MYSQL_DATABASE=aws_arch_agent \\")
                    print("     -p 3306:3306 mysql:8.0")
                    print("  3. Verify .env file has correct MySQL configuration")
                    print("  4. Or switch to SQLite: Set DATABASE_TYPE=sqlite in .env (no setup required)")
                    sys.exit(1)
            else:
                # Other errors
                print(f"\n[ERROR] Failed to start application: {e}")
                # Provide a very common first-step fix for fresh environments.
                if "No module named" in error_msg or "ModuleNotFoundError" in error_msg:
                    print("\nDependency help:")
                    print("  - Install dependencies: pip install -r requirements.txt")
                # Common Groq auth error (avoid printing secrets)
                if "invalid_api_key" in error_msg.lower() or "invalid api key" in error_msg.lower():
                    print("\nGroq auth help:")
                    print("  - Verify GROQ_API_KEY is set and valid")
                    print("  - Tip: do not include quotes or extra spaces in .env")
                print("\nTroubleshooting:")
                database_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
                if database_type == "mysql":
                    print("  1. Check if MySQL service is running")
                    print("  2. Or switch to SQLite: Set DATABASE_TYPE=sqlite in .env")
                print("  3. Verify .env file configuration")
                print("  4. Check LLM API key is valid")
                print("  5. See QUICKSTART.md for more help")
                sys.exit(1)

if __name__ == '__main__':
    main()

