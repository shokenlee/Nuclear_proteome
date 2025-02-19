# from https://www.uniprot.org/help/id_mapping

import re
import time
import json
import zlib
from xml.etree import ElementTree
from urllib.parse import urlparse, parse_qs, urlencode
import requests
from requests.adapters import HTTPAdapter, Retry


POLLING_INTERVAL = 3
API_URL = "https://rest.uniprot.org"


retries = Retry(total=5, backoff_factor=0.25, status_forcelist=[500, 502, 503, 504])
session = requests.Session()
session.mount("https://", HTTPAdapter(max_retries=retries))

# warn only when response has an error
def check_response(response):
    try:
        response.raise_for_status()
    except requests.HTTPError:
        print(response.json())
        raise


# submit the query and get the job id
def submit_id_mapping(from_db, to_db, ids):
    request = requests.post(
        f"{API_URL}/idmapping/run",
        data={"from": from_db, "to": to_db, "ids": ",".join(ids)},
    )
    check_response(request)
    return request.json()["jobId"]


# For batch request
# get the link for the next batch
# for a single batch request this returns nothing
def get_next_link(headers):
    re_next_link = re.compile(r'<(.+)>; rel="next"')
    if "Link" in headers:
        match = re_next_link.match(headers["Link"])
        if match:
            return match.group(1)


# get boolean if the result is ready
# judges if the reuslt json has 'job status' key
# if yes it is not ready
# if no the job is finished either with results or without it and with failed id
def check_id_mapping_results_ready(job_id):
    while True:
        request = session.get(f"{API_URL}/idmapping/status/{job_id}")
        check_response(request)
        j = request.json()
        if "jobStatus" in j:
            if j["jobStatus"] in ("NEW", "RUNNING"):
                print(f"Retrying in {POLLING_INTERVAL}s")
                time.sleep(POLLING_INTERVAL)
            else:
                raise Exception(j["jobStatus"])
        else:
            return bool(j["results"] or j["failedIds"])
        

# get the link to the result
# instead of constructing the url manually,
# get response from details api,
# get the authentic link from the rediretURL key
def get_id_mapping_results_link(job_id):
    url = f"{API_URL}/idmapping/details/{job_id}"
    request = session.get(url)
    check_response(request)
    return request.json()["redirectURL"]

# get the results by using the link that was gotten by get_id_mapping_results_link function
def get_id_mapping_results_search(url):
    # extract query from the url
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    
    # define file format from the query part if any - if not provided use json
    file_format = query["format"][0] if "format" in query else "json"
    
    # define size and compressed or not (boolean) if provided in the query part
    # if not use size 500 and compressed False
    if "size" in query:
        size = int(query["size"][0])
    else:
        size = 500
        query["size"] = size
    compressed = (
        query["compressed"][0].lower() == "true" if "compressed" in query else False
    )
    
    # re-encode the result url based on the updated query
    # if not compressed the url becomes like:
    # https://rest.uniprot.org/idmapping/results/f5b31f3eadab13d410f03217ba577ab3578bff09?size=500
    parsed = parsed._replace(query=urlencode(query, doseq=True))
    url = parsed.geturl()
    
    # get the result
    request = session.get(url)
    check_response(request)
    
    # decode the result
    # if file_format == json then just get request.json()
    results = decode_results(request, file_format, compressed)
    
    # get the total number of results
    # in the provided example this is only 1 because of the failed ID
    total = int(request.headers["x-total-results"])
    
    # print how many results of the total requst was fetched but don't understand
    print_progress_batches(0, size, total)
    
    # meaningful only when multiple batches
    # combine batches into a single results if multiple batches provided
    # loop over multiple batches if there are multiple batches
    # thus if the batch is single there is no loop because get_batch yields None
    for i, batch in enumerate(get_batch(request, file_format, compressed), 1): 
        # append the next batch to the results
        results = combine_batches(results, batch, file_format)
        print_progress_batches(i, size, total)
        
    # return results
    if file_format == "xml":
        return merge_xml_results(results)
    return results


# decode the result
# if file_format == json then just get request.json()
def decode_results(response, file_format, compressed):
    # if compressed, decompresse it and encode it such as json
    if compressed:
        decompressed = zlib.decompress(response.content, 16 + zlib.MAX_WBITS)
        if file_format == "json":
            j = json.loads(decompressed.decode("utf-8"))
            return j
        elif file_format == "tsv":
            return [line for line in decompressed.decode("utf-8").split("\n") if line]
        elif file_format == "xlsx":
            return [decompressed]
        elif file_format == "xml":
            return [decompressed.decode("utf-8")]
        else:
            return decompressed.decode("utf-8")
    
    # if the format is json simply get json
    elif file_format == "json":
        return response.json()
    elif file_format == "tsv":
        return [line for line in response.text.split("\n") if line]
    elif file_format == "xlsx":
        return [response.content]
    elif file_format == "xml":
        return [response.text]
    
    # if format is not determined just get the text
    return response.text

# if total number <= 500 this will be total / total
# honestly don't understand this purpose
def print_progress_batches(batch_index, size, total):
    n_fetched = min((batch_index + 1) * size, total)
    print(f"Fetched: {n_fetched} / {total}")

# meaningful only when response is with multiple batches
# For a single batch request None is yielded
def get_batch(batch_response, file_format, compressed):
    # returns a value when the reponse has "link" in its header
    # when the response is a single batch "Link" is absent in the header
    # thus the while loop is False and None is yielded
    batch_url = get_next_link(batch_response.headers)
    while batch_url:
        batch_response = session.get(batch_url)
        batch_response.raise_for_status()
        yield decode_results(batch_response, file_format, compressed)
        batch_url = get_next_link(batch_response.headers)


# append the batch to the main results
def combine_batches(all_results, batch_results, file_format):
    if file_format == "json":
        for key in ("results", "failedIds"):
            if key in batch_results and batch_results[key]:
                all_results[key] += batch_results[key]
    elif file_format == "tsv":
        return all_results + batch_results[1:]
    else:
        return all_results + batch_results
    return all_results



# handling xml
def get_xml_namespace(element):
    m = re.match(r"\{(.*)\}", element.tag)
    return m.groups()[0] if m else ""


def merge_xml_results(xml_results):
    merged_root = ElementTree.fromstring(xml_results[0])
    for result in xml_results[1:]:
        root = ElementTree.fromstring(result)
        for child in root.findall("{http://uniprot.org/uniprot}entry"):
            merged_root.insert(-1, child)
    ElementTree.register_namespace("", get_xml_namespace(merged_root[0]))
    return ElementTree.tostring(merged_root, encoding="utf-8", xml_declaration=True)
