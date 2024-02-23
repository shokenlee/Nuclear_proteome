import requests

def get_url(url, **kwargs):
    """
    Obtain a response from a given URL, with graceful error handling.
    
    Parameters:
    - url (str): The URL to fetch.
    - kwargs: Additional keyword arguments to pass to requests.get().
    
    Returns:
    - requests.Response: The response object from the request, if successful.
    
    Exits:
    - The script exits gracefully if an unrecoverable error occurs, after logging the error.
    """
    try:
        response = requests.get(url, **kwargs)
        response.raise_for_status()  # Will raise HTTPError for 4xx/5xx responses
        return response
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error for URL {url}: {e.response.status_code} {e.response.reason}")
    except requests.exceptions.ConnectionError:
        print("Connection error. Please check your network connection.")
    except requests.exceptions.RequestException as e:
        print(f"An unexpected error occurred: {e}")

    # Exit the script
    sys.exit(1)
    

def find_duplicate(query_list):
    duplicates = []
    count = dict()
    for item in query_list:
        if item not in count.keys():
            count[item] = 1
        else:
            count[item] += 1
            duplicates.append(item)
    return duplicates
            
    

