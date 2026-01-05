#!/usr/bin/env python3
"""
Test Google Ads API Connection
"""

from google.ads.googleads.client import GoogleAdsClient

def main():
    print("\n" + "="*60)
    print("TESTING GOOGLE ADS API CONNECTION")
    print("="*60 + "\n")

    try:
        # Load credentials from local yaml file
        client = GoogleAdsClient.load_from_storage("google-ads.yaml")

        # Test by listing accessible customers
        customer_service = client.get_service("CustomerService")

        accessible_customers = customer_service.list_accessible_customers()

        print("✅ API Connection Successful!\n")
        print("Accessible Customer IDs:")
        print("-" * 40)

        for resource_name in accessible_customers.resource_names:
            customer_id = resource_name.split("/")[-1]
            print(f"  • {customer_id}")

        print("\n" + "="*60)
        print("CONNECTION TEST PASSED")
        print("="*60 + "\n")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n" + "="*60)
        print("CONNECTION TEST FAILED")
        print("="*60 + "\n")
        return False

if __name__ == "__main__":
    main()
