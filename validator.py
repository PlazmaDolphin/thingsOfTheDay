import requests
from PIL import Image, UnidentifiedImageError
from io import BytesIO
from urllib.parse import urlparse, parse_qs

def is_volatile_image_host(url: str) -> tuple[bool, str]:
    """
    Checks if the image URL is hosted on a service known for volatile/expiring links.
    Returns (True, reason) if it's volatile, (False, "OK") if not.
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    query = parse_qs(parsed.query)

    # List of known volatile hosts
    volatile_domains = [
        "cdn.discordapp.com", "media.discordapp.net",
        "media.tenor.com", "tenor.com",
        "googleusercontent.com",
        "fbcdn.net", "facebook.com",
        "dropboxusercontent.com",
        "pbs.twimg.com", "twimg.com", "twitter.com"
    ]

    if any(domain in host for domain in volatile_domains):
        return True, f"Volatile CDN: {host}"

    # Check for query strings that indicate tokenized access
    token_indicators = ['token', 'signature', 'Expires', 'X-Amz-Expires', 'e']
    if any(key in query for key in token_indicators):
        return True, "URL contains expiration token"

    return False, "OK"

def is_valid_image(url: str, timeout: float = 5.0) -> tuple[bool, str]:
    """
    Check whether `url` resolves to a live image (status-200, image/* MIME,
    and decodable by Pillow).

    Returns
    -------
    (ok: bool, reason: str)

    Examples
    --------
    >>> ok, reason = is_valid_image("https://i.imgur.com/abcd123.jpg")
    >>> if ok:
    ...     print("Looks good!")
    ... else:
    ...     print("Bad link:", reason)
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (image-validator/1.1)"
    }
    try:
        # Full GET (HEAD can be unreliable)
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"
        
        ct = response.headers.get("Content-Type", "")
        if not ct.startswith("image/"):
            return False, f"Unexpected MIME type: {ct}"

        # Try decoding with Pillow
        img_data = BytesIO(response.content)
        try:
            img = Image.open(img_data)
            img.load()  # Fully decode the image (more reliable than verify)
            return True, "OK"
        except UnidentifiedImageError:
            return False, "Cannot identify image file"
        except Exception as e:
            return False, f"Decode error: {e}"

    except requests.RequestException as e:
        return False, f"Request failed: {e}"


# quick demo
if __name__ == "__main__":
    test_urls = [
        "https://i.imgur.com/fDJSMOg_d.webp?maxwidth=1520&fidelity=grand",            # valid
        "https://i.imgur.com/I7Y9Zdt_d.webp?maxwidth=1520&fidelity=grand",
        "https://cdn.discordapp.com/attachments/1347039719858638970/1369506170833997844/images.png?ex=68878dc3&is=68863c43&hm=9315f2be01e8ef538a4a07123637445eae039419b5c8e166a721c0c524ae1086&",
        "https://cdn.discordapp.com/attachments/1347039719858638970/1372237722781220957/496923587_29875851002000190_2821266901531979039_n.png?ex=688648f8&is=6884f778&hm=bc7da98a1799963eb6532c98ad9b99c58214af240a6fa1b2cf619dff9668bc5c&"  # likely expired
    ]
    for url in test_urls:
        ok, reason = is_valid_image(url)
        volitile, reason2 = is_volatile_image_host(url)
        print(f"{url:70}\n ->  {'Link Alive' if ok else 'Link Dead'}, {reason}, {'Temporary' if volitile else 'Permanent'}, {reason2}\n")