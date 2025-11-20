"""
HTTP Session utilities for data downloads.
Provides session management with rotating User-Agents to avoid rate limiting.
"""

import random
import requests
from typing import Optional


# 다양한 User-Agent 리스트 (실제 브라우저들)
USER_AGENTS = [
    # Chrome on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    
    # Chrome on Mac
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    
    # Firefox on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    
    # Firefox on Mac
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
    
    # Safari on Mac
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    
    # Edge on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
]


def get_random_user_agent() -> str:
    """
    랜덤한 User-Agent를 반환합니다.
    매번 다른 브라우저로 위장하여 차단을 피합니다.
    
    Returns:
        str: Random User-Agent string
    """
    return random.choice(USER_AGENTS)


def create_session(
    user_agent: Optional[str] = None,
    timeout: int = 30,
    max_retries: int = 3
) -> requests.Session:
    """
    HTTP 요청용 Session을 생성합니다.
    User-Agent를 설정하여 403 Forbidden 에러를 방지합니다.
    
    Args:
        user_agent: Custom User-Agent (None이면 랜덤 선택)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
    
    Returns:
        requests.Session: Configured session
    
    Example:
        >>> session = create_session()
        >>> response = session.get('https://example.com')
    """
    session = requests.Session()
    
    # User-Agent 설정
    if user_agent is None:
        user_agent = get_random_user_agent()
    
    session.headers.update({
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',  # Do Not Track
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    # Retry 설정
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=1,  # 1초, 2초, 4초 대기
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


def get_wikipedia_session() -> requests.Session:
    """
    Wikipedia 전용 세션을 생성합니다.
    
    Returns:
        requests.Session: Wikipedia optimized session
    """
    return create_session()


if __name__ == "__main__":
    # 테스트
    print("Available User-Agents:")
    for i in range(3):
        print(f"{i+1}. {get_random_user_agent()}")
    
    print("\nCreating session...")
    session = create_session()
    print(f"User-Agent: {session.headers['User-Agent']}")
    
    # Wikipedia 테스트
    print("\nTesting Wikipedia access...")
    try:
        response = session.get('https://en.wikipedia.org/wiki/S%26P_500')
        print(f"✅ Success! Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed: {e}")
