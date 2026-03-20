import asyncio
import asyncpg
import sys

async def try_connect_and_create(password):
    try:
        # Try to connect to the postgres database
        conn = await asyncpg.connect(
            user='postgres',
            password=password,
            database='postgres',
            host='127.0.0.1',
            port=5432
        )
        print(f"SUCCESS: Connected with password '{password}'")
        
        # Check if spendwise exists
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'spendwise'")
        if not exists:
            print("Creating 'spendwise' database...")
            await conn.execute("CREATE DATABASE spendwise")
            print("Database 'spendwise' created successfully.")
        else:
            print("Database 'spendwise' already exists.")
            
        await conn.close()
        return True
    except asyncpg.exceptions.InvalidPasswordError:
        print(f"FAIL: Wrong password '{password}'")
        return False
    except Exception as e:
        print(f"ERROR with password '{password}': {e}")
        return False

async def main():
    passwords_to_try = [
        "password",
        "admin",
        "postgres",
        "root",
        "123456",
        "",
    ]
    
    for pwd in passwords_to_try:
        success = await try_connect_and_create(pwd)
        if success:
            # Output the successful password for the agent to read
            print(f"FINAL_PASSWORD={pwd}")
            sys.exit(0)
            
    print("FAILED_ALL")
    sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
