import requests
from requests import RequestException


def fetch_book_metadata_google(isbn):
    meta = {}
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                metadata = data["items"][0]["volumeInfo"]
                if metadata:
                    meta["TITLE"] = metadata.get("title", "None")
                    meta["SUBTITLE"] = metadata.get("subtitle", "None")
                    # meta["DESCRIPTION"] = text_block(metadata.get("description", "None"))
                    meta["AUTHORS"] = metadata.get("authors", [])
                    meta["DATE"] = metadata.get("publishedDate", "None")[:4]
                    publisher = metadata.get("publisher", "None")
                    meta["ISBN"] = isbn

    except RequestException:
        print("An error occurred whilst getting book metadata")
    return meta


meta = fetch_book_metadata_google('9781804613986')

print(meta)
