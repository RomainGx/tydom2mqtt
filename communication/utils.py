from http.client import HTTPResponse

import urllib3

from communication.BytesIOSocket import BytesIOSocket


def response_from_bytes(data):
    sock = BytesIOSocket(data)
    response = HTTPResponse(sock)
    response.begin()
    return urllib3.HTTPResponse.from_httplib(response)
