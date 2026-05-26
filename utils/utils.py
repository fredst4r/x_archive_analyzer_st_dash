import random

# ------------------------------------------------------------------------------
# REQUESTS INFRASTRUCTURE
# ------------------------------------------------------------------------------

# Function to get a random user agent from a file
def get_random_user_agent():
    # Open the user agent file and read all lines
    with open('utils/user_agents.txt', 'r') as file:
        user_agents = file.readlines()
    # Strip whitespace and return a random user agent
    return random.choice([ua.strip() for ua in user_agents if ua.strip()])

# Headers to use for requests
headers = { 
	"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9", 
	"Accept-Encoding": "gzip, deflate, br", 
	"Accept-Language": "en-US,en;q=0.9", 
	"Host": "httpbin.org", 
	"Sec-Ch-Ua": "\"Chromium\";v=\"92\", \" Not A;Brand\";v=\"99\", \"Google Chrome\";v=\"92\"", 
	"Sec-Ch-Ua-Mobile": "?0", 
	"Sec-Fetch-Dest": "document", 
	"Sec-Fetch-Mode": "navigate", 
	"Sec-Fetch-Site": "none", 
	"Sec-Fetch-User": "?1", 
	"Upgrade-Insecure-Requests": "1", 
	"User-Agent": get_random_user_agent() 
}

def rotate_headers():
    """ Rotate the headers to reduce detection as a scraper"""
    headers["User-Agent"] = get_random_user_agent()
    headers["Accept-Language"] = random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.9"])
    headers["Accept"] = random.choice([
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ])
    headers["Accept-Encoding"] = random.choice(["gzip, deflate, br", "gzip, deflate"])
    return headers