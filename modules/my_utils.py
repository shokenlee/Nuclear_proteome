import requests
import sys
import modules.my_config as my_config
from time import sleep

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
            
    
def get_source_pmid(entry, loc_of_interest):
    """
    Obtain PMIDs for subcellular loc information of a given Uniprot ID.
    
    Parameters:
    - entry (str): Uniprot ID of interest.
    - loc_of_interest (str): Subcellular location name for which PMID may exist.
    
    Returns:
    - pmid_list (list).
    """
    
    pmid_list = []
    
    # Query the gene name to get the Uniprot ID and the Uniprot-registered gene name
    params = {
    "query": f'accession:{entry}',
    "fields": "cc_subcellular_location",
    "format": "json"
    }

    r = get_url(my_config.WEBSITE_API, params=params)
    result = r.json()['results'][0]
    
    sleep(1)
        
    if 'comments' in result:
        for comment in result['comments']: # Each comment contains information for each isoform, if any
            if comment['commentType'] == 'SUBCELLULAR LOCATION':
                locs = comment.get('subcellularLocations', [])

                for loc in locs:
                    if 'location' in loc:
                        value = loc['location'].get('value', '')

                        # If this is the location of interest
                        # then dig into pmid info
                        if value == loc_of_interest:
                            evidences = loc['location'].get('evidences', '')
                            for evidence in evidences:
                                pmid = evidence.get('id', '')
                                pmid_list.append(pmid)

    return pmid_list
    

