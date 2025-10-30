from supabase import create_client
import os
from dotenv import load_dotenv
import random
from datetime import datetime, timedelta
import uuid
from decimal import Decimal

def generate_test_subscription_data():
    # Load environment variables
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("Error: Missing Supabase credentials in .env file")
        return
    
    try:
        # Initialize Supabase client
        supabase = create_client(url, key)
        
        # Create or get test user
        test_user_email = "test.user@pixelcraft.com"
        try:
            user_response = supabase.auth.admin.create_user({
                "email": test_user_email,
                "password": "TestUser123!",
                "email_confirm": True
            })
            test_user_id = user_response.user.id
            print("Test user created:", test_user_id)
        except Exception as e:
            # If user exists, get their ID
            print("User might already exist, attempting to get ID...")
            auth_response = supabase.rpc('get_user_id_by_email', {'email': test_user_email}).execute()
            test_user_id = auth_response.data[0]['id'] if auth_response.data else None
            if not test_user_id:
                print("Error: Could not create or retrieve test user")
                return
        
        # Fetch pricing packages
        packages = supabase.table('pricing_packages').select('*').eq('is_active', True).execute()
        if not packages.data:
            print("Error: No active pricing packages found")
            return
        
        package_list = packages.data
        
        # Fetch pricing campaigns (optional, for discount assignment)
        campaigns = supabase.table('pricing_campaigns').select('*').eq('is_active', True).execute()
        campaign_list = campaigns.data if campaigns.data else []
        
        # Generate 25 subscription records
        subscriptions = []
        now = datetime.now()
        
        for _ in range(25):
            # Choose random package
            package = random.choice(package_list)
            
            # Choose subscription type: monthly or yearly
            is_monthly = random.choice([True, False])
            
            # Calculate start_date: random over last 12 months
            start_date = now - timedelta(days=random.randint(0, 365))
            
            # Calculate end_date
            if is_monthly:
                end_date = start_date + timedelta(days=30)
                original_price = package['price_monthly']
            else:
                end_date = start_date + timedelta(days=365)
                original_price = package['price_yearly']
            
            # Apply discount randomly (0-30% for some subscriptions)
            discount_percentage = random.uniform(0, 0.3) if random.random() < 0.5 else 0
            discount_amount = Decimal(str(original_price)) * Decimal(str(discount_percentage))
            final_price = Decimal(str(original_price)) - discount_amount
            
            # Choose status with weights
            status = random.choices(['active', 'cancelled', 'expired'], weights=[70, 20, 10])[0]
            
            # Set updated_at for cancelled subscriptions
            updated_at = None
            if status == 'cancelled':
                # Set updated_at to a date after start_date, up to now
                days_since_start = (now - start_date).days
                if days_since_start > 0:
                    updated_at = start_date + timedelta(days=random.randint(1, days_since_start))
                else:
                    updated_at = now
            
            # Randomly assign campaign (optional)
            campaign_id = random.choice(campaign_list)['id'] if campaign_list and random.random() < 0.3 else None
            
            subscription = {
                "user_id": test_user_id,
                "package_id": package['id'],
                "campaign_id": campaign_id,
                "status": status,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "original_price": float(original_price),
                "discount_amount": float(discount_amount),
                "final_price": float(final_price),
                "updated_at": updated_at.isoformat() if updated_at else None
            }
            subscriptions.append(subscription)
        
        # Insert subscriptions
        print("Inserting subscription data...")
        supabase.table('user_subscriptions').insert(subscriptions).execute()
        
        # Verification
        print("\nVerification:")
        all_subs = supabase.table('user_subscriptions').select('*').eq('user_id', test_user_id).execute()
        total_subs = len(all_subs.data)
        active_count = sum(1 for s in all_subs.data if s['status'] == 'active')
        cancelled_count = sum(1 for s in all_subs.data if s['status'] == 'cancelled')
        expired_count = sum(1 for s in all_subs.data if s['status'] == 'expired')
        total_revenue = sum(float(s['final_price']) for s in all_subs.data)
        
        print(f"Total subscriptions: {total_subs}")
        print(f"Active: {active_count}")
        print(f"Cancelled: {cancelled_count}")
        print(f"Expired: {expired_count}")
        print(f"Total revenue: ${total_revenue:.2f}")
        
        # Print sample records
        print("\nSample subscription records:")
        for i, sub in enumerate(all_subs.data[:3]):
            print(f"Subscription {i+1}: Package {sub['package_id']}, Status {sub['status']}, Final Price ${sub['final_price']:.2f}")
        
        print("Test subscription data generation completed!")
        
    except Exception as e:
        print("Error generating test subscription data:", str(e))

if __name__ == "__main__":
    generate_test_subscription_data()