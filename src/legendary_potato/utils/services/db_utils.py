import os

def get_database_url() -> str | None:
    url = os.environ.get("DATABASE_URL")
    password = os.environ.get("DATABASE_PASSWORD")
    
    if not url:
        return None
        
    if password and "[YOUR-PASSWORD]" in url:
        return url.replace("[YOUR-PASSWORD]", password)
        
    return url
