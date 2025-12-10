#!/usr/bin/env python3
"""
Test natural language audit query service
"""
import sys
import os

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.services.audit_query_service import AuditQueryService

def main():
    print("=" * 60)
    print("TESTING NATURAL LANGUAGE AUDIT QUERY SERVICE")
    print("=" * 60)
    print()

    service = AuditQueryService()

    # Test queries
    test_questions = [
        "who approved mayra's vacation last week?",
        "who modified roberto's manager?",
        "what did dirk do yesterday?",
    ]

    for question in test_questions:
        print(f"Question: {question}")
        print("-" * 60)

        try:
            result = service.parse_natural_query(question)
            print("Parsed Query Parameters:")
            for key, value in result.items():
                print(f"  {key}: {value}")
            print()
        except Exception as e:
            print(f"ERROR: {e}")
            print()

    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
