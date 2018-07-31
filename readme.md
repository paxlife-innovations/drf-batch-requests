# DRF batch requests

[![PyPI version](https://badge.fury.io/py/drf-batch-requests.svg)](https://badge.fury.io/py/drf-batch-requests)
[![Travis CI](https://travis-ci.org/paxlife-innovations/drf-batch-requests.svg?branch=master)](https://travis-ci.org/roman-karpovich/drf-batch-requests)
[![Coverage Status](https://coveralls.io/repos/github/roman-karpovich/drf-batch-requests/badge.svg?branch=master)](https://coveralls.io/github/roman-karpovich/drf-batch-requests?branch=master)
[![Code Health](https://landscape.io/github/roman-karpovich/drf-batch-requests/master/landscape.svg?style=flat)](https://landscape.io/github/roman-karpovich/drf-batch-requests/master)
[![Python Versions](https://img.shields.io/pypi/pyversions/drf-batch-requests.svg?style=flat-square)](https://pypi.python.org/pypi/drf-batch-requests)
[![Implementation](https://img.shields.io/pypi/implementation/drf-batch-requests.svg?style=flat-square)](https://pypi.python.org/pypi/drf-batch-requests)


## Requirements

- Python 2.7 or 3.5, 3.6
- Django starting from 1.9
- Django rest framework (3.6 for 1.9 django)

## Quick Start

### Example 1

```shell
    curl -X POST \
      http://127.0.0.1:8000/batch/ \
      -H 'cache-control: no-cache' \
      -H 'content-type: application/json' \
      -d '{"batch": [
        {
            "headers": {
                "Content-ID": "1"
            }
            "method": "get",
            "relative_url": "/test/",
            "name": "yolo",
        },
        {
            "headers": {
                "Content-ID": "2"
            }
            "method": "post",
            "relative_url": "/test/?id={result=yolo:$.id}&ids={result=yolo:$.data.*.id}",
            "body": {
                "data": {
                    "id": "{result=yolo:$.id}",
                    "ids": "{result=yolo:$.data.*.id}"},
                    "test": "yolo"
                }
        },
        {
            "headers": {
                "Content-ID": "3"
            }
            "method": "post",
            "relative_url": "/test/",
            "body": "{\"data\": 42}",
            "omit_response_on_success": true,
        },
        {
            "headers": {
                "Content-ID": "4"
            }
            "method": "options",
            "relative_url": "/test/",
        }
    ]
    }'
```

### Example 2 (using file upload)

```shell
    curl -X POST \
      http://127.0.0.1:8000/batch/ \
      -H 'cache-control: no-cache' \
      -H 'content-type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW' \
      -F 'batch=[
        {
            "headers": {
                "Content-ID": "1"
            }
            "method": "get",
            "relative_url": "/test/",
            "name": "yolo",
        },
        {
            "headers": {
                "Content-ID": "2"
            }
            "method": "post",
            "relative_url": "/test/?id={result=yolo:$.id}&ids={result=yolo:$.data.*.id}",
            "body": {"data": "{result=yolo:$.data.*.id}", "test": "yolo"},
            "attached_files":{"file": "a.jpg"},
        },
        {
            "headers": {
                "Content-ID": "3"
            }
            "method": "post",
            "relative_url": "/test/",
            "body": "{\"data\": 42}",
            "omit_response_on_success": true,
            "attached_files":["a.jpg", "b.png"]
        },
        {
            "headers": {
                "Content-ID": "4"
            }
            "method": "options",
            "relative_url": "/test/"
        }
    ]' \
      -F b.png=@2476.png \
      -F a.jpg=@check_133.pdf
```

## Usage

Subrequests get all the HTTP request headers of the batch request. Additionally, each subrequest can define individual headers. These are overriding the global ones inherited. 

## Configuration

Settings for this package go into the namespace `DRF_BATCH_REQUESTS`. Thus, add a section like the following (displaying the default settings) to your Django settings file:

```Python
DRF_BATCH_REQUESTS = {
    'SUBREQ_CONSUMER_BACKEND': 'drf_batch_requests.backends.sync.SyncRequestsConsumeBackend',
    'SUBREQ_ID_REQUIRED': True,
    'SUBREQ_ID_HEADER': 'Content-ID',
    'SUBREQ_ID_RESPONSE_PREFIX': None
}
```

### `SUBREQ_CONSUMER_BACKEND`

The backend that is consuming the subrequests contained within the batch request. Change this if you want to use a custom backend.

### `SUBREQ_ID_REQUIRED`

If set to `True`, all subrequests are required to have an ID header, otherwise a `ValidationError` will be raised.

### `SUBREQ_ID_HEADER`

The name of the subrequest header that is containing the subrequest ID. 

### `SUBREQ_ID_RESPONSE_PREFIX`

Optional prefix that will be applied to each subrequest ID in order to generate the ID for the corresponding response. If you set this to `response-`, the response corresponding to the request ID `0815_42` will be assigned the ID `response-0815_42` .

## Future features:

- add support for requests pipelining. use responses as arguments to next requests (done)
- build graph based on requests dependencies & run simultaneously independent.
- ~~switchable atomic support. true - all fails if something wrong. else - fail only dependent (can be very hard to support on front-end side, but for now seems as good feature)~~ run all requests in single transaction. (done)
- ~~use native django. we don't use complicated things that require drf for work. all can be done with "naked" django.~~ (since we validate requests with drf serializers, it's better to leave as it is).
- support files uploading (done)