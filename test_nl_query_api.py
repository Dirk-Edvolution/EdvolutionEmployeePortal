#!/usr/bin/env python3
"""
Test the natural language audit query API endpoint
Note: This currently won't return real results because audit logging isn't integrated yet
"""
import requests
import json

# You'll need to get a real session cookie by logging in first
SESSION_COOKIE = ".eJydlO2PqjgUxv-VGz4PCL7iJDfZ6gyK74qgzmZDailQrS3SAjI393_fmntNNpv94Own0uR5nsP59Zz-0FCOI8wkgVRorz80RIk6hSTSXjW73e7YdrvbsTp9vVtYcRSh0rTadjvlPOrZzVT2YVdmZZ9YPQNmmTASzhOKC4FzxJlUSQbiF-3lESuwKidV9Gg59FZ7HZzoKS6Fc7h9sD2d6qwG2_PQ182OTJUrx3GORRpKfsZMuaxGw2yd2Kk7L8NTOHGGycEFGwBGYO4tKkef9d0cH9_DVbFOGBg1mbmSs7jV2ka90ylvr971-XrmdoSzujl2fESBOz6KT1ZO_IHv9tAu5cQDJlKVBeIZVkD-1NSXKRovWiplJl4bjaqqfrcJMyLu_TVgIdPGvWnCYm7gCyT0K4Ys5zGh-AkLjC6EGRHJMZI8r417xP-0GTmGEWe0fsKPIMUsgs-UekgNXKoLF084kjsuQ2ApCUuEcYSCoK_bRAoVzOQLRvbMpaIUSuOChYCJGoe_XrTHKNaw2TegCWAvGwJ9sfGzS3zZtIRvwZY53HqVd31Po4kzqMFnHfa2nzVctLq3-dhEyeAwBLFDp7zsm80gqO29B1Y9YZ8OfjDbXxaRRev9kkbjQF_hdnlbz7tn8LZLdpv3sspRgvR-0XbrS7RcWhswuLFrE976yUkP8k3f2iX7ClF7MM7l8hiuwtylUTkQBx56oEL-OTrTGd0FCZ_b5qCaL3z3hqDapCmAwFPb5Dnr8WjfnJOrGN3ccnG8RsXO3feacIKHQWI2za72m0NY5ESxeEDkd2TNf3P8Reyn2ikJJVZyc2Am42P5MTOP58EMT8TI6lCvF1njth9sVfZ9PMNfW_Sqqak9_4GjktNCEs4Mwh8KBi_3uDcl-AaY5IzwbxsurgWhFIqHKiNIFjn-x2_StPXf71QDNsAwsTma-gBm55m7YJv1mpnbz822axJCqpGYdmTsOLPpR_ft422_vXWCQ2txpd9Fv6sj7effIbDZ3A.aTgzVg.BK3mg9UOmwSstTsL9yCQ3f5KGG8"  # Replace with actual session cookie

BASE_URL = "http://localhost:8080"

def test_query(question):
    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print('='*60)

    response = requests.post(
        f"{BASE_URL}/api/audit/query",
        json={"question": question},
        cookies={"session": SESSION_COOKIE}
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"\nAnswer: {data['answer']}")
        print(f"Total matches: {data['total_matches']}")
        if data['logs']:
            print(f"\nTop logs:")
            for log in data['logs'][:3]:
                print(f"  - {log['user_email']} → {log['action']} at {log['timestamp']}")
    else:
        print(f"Error: {response.text}")

def main():
    print("TESTING NATURAL LANGUAGE AUDIT QUERY API")
    print("=" * 60)

    if SESSION_COOKIE == "YOUR_SESSION_COOKIE_HERE":
        print("\n⚠️  You need to set SESSION_COOKIE first!")
        print("\nHow to get session cookie:")
        print("1. Open http://localhost:3000 in browser")
        print("2. Log in to the app")
        print("3. Open DevTools (F12) → Application → Cookies")
        print("4. Copy the 'session' cookie value")
        print("5. Paste it in this script as SESSION_COOKIE")
        return

    # Test queries
    test_query("who approved mayra's vacation last week?")
    test_query("who modified roberto's manager?")
    test_query("what did dirk do yesterday?")

    print("\n" + "="*60)
    print("NOTE: Currently returns empty results because audit logging")
    print("      hasn't been integrated into the app yet.")
    print("="*60)

if __name__ == "__main__":
    main()
