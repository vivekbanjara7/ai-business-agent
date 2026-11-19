
import os
import json
import requests


# --------------------------------------------------
# Configuration
# --------------------------------------------------

API_URL = "https://api.search.tinyfish.ai"
QUERY = "latest Android Studio version"
TIMEOUT = 20


# --------------------------------------------------
# Check API key
# --------------------------------------------------

api_key = os.environ.get("TINYFISH_API_KEY")

if not api_key:
    print("ERROR: TINYFISH_API_KEY is not set.")
    print("Set the environment variable and try again.")
    raise SystemExit(1)


# --------------------------------------------------
# Send search request
# --------------------------------------------------

print("=" * 60)
print("TINYFISH SEARCH TEST")
print("=" * 60)
print("Query:", QUERY)
print("\nSending request...")


try:
    response = requests.get(
        API_URL,
        params={"query": QUERY},
        headers={"X-API-Key": api_key},
        timeout=TIMEOUT
    )

    print("\nHTTP Status:", response.status_code)

    # Stop with a useful message if the request failed.
    response.raise_for_status()

    # Parse the JSON response.
    try:
        data = response.json()
    except ValueError:
        print("\nERROR: The server did not return valid JSON.")
        print("Response preview:")
        print(response.text[:2000])
        raise SystemExit(1)

    print("\n" + "=" * 60)
    print("STRUCTURED JSON RESPONSE")
    print("=" * 60)

    print(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        )
    )

    # Show the top-level structure without assuming
    # a particular response schema.
    print("\n" + "=" * 60)
    print("RESPONSE STRUCTURE")
    print("=" * 60)

    if isinstance(data, dict):
        print("Top-level type: dictionary")
        print("Top-level keys:", list(data.keys()))

        for key, value in data.items():
            print(f"\nField: {key}")
            print("Value type:", type(value).__name__)

            if isinstance(value, list):
                print("Number of items:", len(value))

                if value:
                    print(
                        "First item:",
                        json.dumps(
                            value[0],
                            indent=2,
                            ensure_ascii=False
                        )[:1500]
                    )

            elif isinstance(value, dict):
                print("Nested keys:", list(value.keys()))

            elif isinstance(value, str):
                print("Text preview:", value[:300])

    elif isinstance(data, list):
        print("Top-level type: list")
        print("Number of items:", len(data))

        if data:
            print(
                "First item:",
                json.dumps(
                    data[0],
                    indent=2,
                    ensure_ascii=False
                )[:1500]
            )

    else:
        print("Top-level type:", type(data).__name__)

except requests.exceptions.Timeout:
    print("\nERROR: The request timed out.")
    print("Try again later.")

except requests.exceptions.HTTPError as exc:
    print("\nERROR: TinyFish returned an HTTP error.")
    print("Details:", exc)
    print("Response preview:", response.text[:1000])

except requests.exceptions.RequestException as exc:
    print("\nERROR: The network request failed.")
    print("Details:", exc)

print("\nTest finished.")
