import httpx

def get_bin_details(bin_number):
    """
    Get BIN (Bank Identification Number) details
    Returns dict with bin info or None on failure
    """
    try:
        # Use binlist.net API (free, no auth required)
        url = f"https://lookup.binlist.net/{bin_number[:6]}"
        headers = {"Accept-Version": "3"}
        
        response = httpx.get(url, headers=headers, timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            
            country_data = data.get("country", {})
            bank_data = data.get("bank", {})
            
            return {
                "bin": bin_number[:6],
                "country": country_data.get("name", "Unknown"),
                "flag": country_data.get("emoji", "🏳️"),
                "vendor": data.get("scheme", "Unknown").upper(),
                "type": data.get("type", "Unknown").upper(),
                "level": data.get("brand", "Unknown").upper(),
                "bank": bank_data.get("name", "Unknown")
            }
        
        return None
        
    except Exception as e:
        print(f"[getbin error] {e}")
        return {
            "bin": bin_number[:6],
            "country": "Unknown",
            "flag": "🏳️",
            "vendor": "Unknown",
            "type": "Unknown",
            "level": "Unknown",
            "bank": "Unknown"
        }


async def get_bin_details_async(bin_number):
    """
    Async version of get_bin_details
    """
    try:
        url = f"https://lookup.binlist.net/{bin_number[:6]}"
        headers = {"Accept-Version": "3"}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                country_data = data.get("country", {})
                bank_data = data.get("bank", {})
                
                return {
                    "bin": bin_number[:6],
                    "country": country_data.get("name", "Unknown"),
                    "flag": country_data.get("emoji", "🏳️"),
                    "vendor": data.get("scheme", "Unknown").upper(),
                    "type": data.get("type", "Unknown").upper(),
                    "level": data.get("brand", "Unknown").upper(),
                    "bank": bank_data.get("name", "Unknown")
                }
        
        return None
        
    except Exception as e:
        print(f"[getbin async error] {e}")
        return {
            "bin": bin_number[:6],
            "country": "Unknown",
            "flag": "🏳️",
            "vendor": "Unknown",
            "type": "Unknown",
            "level": "Unknown",
            "bank": "Unknown"
        }
