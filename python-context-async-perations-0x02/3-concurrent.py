import asyncio
import aiosqlite
from typing import List, Tuple
import time


async def async_fetch_users() -> List[Tuple]:
    """
    Asynchronously fetch all users from the database.
    
    Returns:
        List[Tuple]: List of all user records
    """
    try:
        # Connect to the database asynchronously
        async with aiosqlite.connect("database.db") as db:
            print("📊 Fetching all users...")
            
            # Execute the query to fetch all users
            async with db.execute("SELECT * FROM users") as cursor:
                users = await cursor.fetchall()
                
            print(f"✅ Fetched {len(users)} users")
            return users
            
    except Exception as e:
        print(f"❌ Error fetching all users: {e}")
        return []


async def async_fetch_older_users() -> List[Tuple]:
    """
    Asynchronously fetch users older than 40 from the database.
    
    Returns:
        List[Tuple]: List of user records where age > 40
    """
    try:
        # Connect to the database asynchronously
        async with aiosqlite.connect("database.db") as db:
            print("👥 Fetching users older than 40...")
            
            # Execute the query to fetch users older than 40
            async with db.execute("SELECT * FROM users WHERE age > ?", (40,)) as cursor:
                older_users = await cursor.fetchall()
                
            print(f"✅ Fetched {len(older_users)} users older than 40")
            return older_users
            
    except Exception as e:
        print(f"❌ Error fetching older users: {e}")
        return []


async def fetch_concurrently():
    """
    Execute both fetch operations concurrently using asyncio.gather().
    """
    print("🚀 Starting concurrent database queries...")
    start_time = time.time()
    
    try:
        # Use asyncio.gather to run both queries concurrently
        all_users, older_users = await asyncio.gather(
            async_fetch_users(),
            async_fetch_older_users()
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"\n⏱️ Concurrent execution completed in {execution_time:.4f} seconds")
        print("=" * 60)
        
        # Display results for all users
        print(f"\n📋 ALL USERS ({len(all_users)} records):")
        print("-" * 40)
        if all_users:
            for user in all_users:
                print(f"ID: {user[0][:8]}... | Name: {user[1]} {user[2]} | Age: {user[7]} | Role: {user[6]}")
        else:
            print("No users found.")
        
        # Display results for older users
        print(f"\n👴 USERS OLDER THAN 40 ({len(older_users)} records):")
        print("-" * 40)
        if older_users:
            for user in older_users:
                print(f"ID: {user[0][:8]}... | Name: {user[1]} {user[2]} | Age: {user[7]} | Role: {user[6]}")
        else:
            print("No users older than 40 found.")
            
    except Exception as e:
        print(f"❌ Error during concurrent execution: {e}")


# Main execution using asyncio.run()
if __name__ == "__main__":
    print("🎯 Starting Concurrent Database Query Demo")
    print("=" * 60)
    
    # Run the concurrent fetch using asyncio.run()
    asyncio.run(fetch_concurrently())
    
    print("\n🎉 Demo completed!")