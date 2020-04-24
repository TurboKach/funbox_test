import json
import os
import re
import time

import redis
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from redis import RedisError
from rest_framework import status
from rest_framework.decorators import api_view

# TODO delete unused files (models etc)

# redis credentials
REDIS_HOST = os.getenv('REDIS_HOST', default='localhost')
REDIS_PORT = os.getenv('REDIS_PORT', default=6379)
if REDIS_HOST is None or REDIS_PORT is None:
    raise ConnectionError('Invalid Redis settings!')

# connect to Redis instance
redis_instance = redis.StrictRedis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0
)

# regex for finding hostname in url
regex = re.compile(r'^(?:https?:\/\/)?(?:[^@\/\n]+@)?(?:www\.)?([^:\/?\n]+)', re.IGNORECASE)


def parse_urls_to_domains(urls) -> list:
    """
    Get unique domains from urls list
    :param urls: url strings list
    :return: list of unique domain strings
    """
    domains = list(set([re.findall(regex, url)[0] for url in urls]))
    return domains


@csrf_exempt
@api_view(['POST'])
def visited_links(request):
    try:
        timestamp = time.time()
        data = json.loads(request.body)
        keys = list(data.keys())
        if keys != ['links']:
            response = {
                'status': 'error',
                'data': data
            }
            return JsonResponse(response, status=status.HTTP_400_BAD_REQUEST)
        urls = data['links']
        domains = parse_urls_to_domains(urls)

        # write domains to Redis in a single transaction
        if domains:
            pipe = redis_instance.pipeline()
            for domain in domains:
                pipe.zadd('links', {f'{domain}: {timestamp}': timestamp})
            pipe.execute()

        return JsonResponse({'status': 'ok'}, status=status.HTTP_201_CREATED)

    except RedisError as e:
        response = {
            'status': {
                'error': e.__class__.__name__,
                'args': e.args
            },
        }
        return JsonResponse(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        response = {
            'status': {
                'error': e.__class__.__name__,
                'args': e.args
            },
        }
        return JsonResponse(response, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['GET'])
def visited_domains(request):
    try:
        time_from = request.GET.get('from')
        time_to = request.GET.get('to')

        # get domains from Redis
        domains = redis_instance.zrangebyscore('links', time_from, time_to)
        # prepare data for output
        domains_unique = list(set([domain.decode('utf-8').split(":")[0] for domain in domains]))

        response = {
            'domains': domains_unique,
            'status': 'ok'
        }
        return JsonResponse(response, status=status.HTTP_200_OK)
    except Exception as e:
        response = {
            'status': {
                'error': e.__class__.__name__,
                'args': e.args
            },
        }
        return JsonResponse(response, status=status.HTTP_400_BAD_REQUEST)
