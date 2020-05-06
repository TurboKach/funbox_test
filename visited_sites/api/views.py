import json
import re
import time

import redis
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from redis import RedisError
from rest_framework import status
from rest_framework.decorators import api_view

from visited_sites.visited_sites.settings import REDIS_HOST, REDIS_PORT

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
    return list(set([re.findall(regex, url)[0] for url in urls]))


@csrf_exempt
@api_view(['POST'])
def visited_links(request):
    try:
        timestamp = time.time()
        data = json.loads(request.body)
        keys = list(data.keys())
        if keys != ['links'] or len(data) == 0:
            response = {
                'status': 'error',
                'data': data
            }
            return JsonResponse(response, status=status.HTTP_400_BAD_REQUEST)
        urls = data['links']
        domains = parse_urls_to_domains(urls)
        if not domains:
            response = {
                'status': 'error',
                'data': data
            }
            return JsonResponse(response, status=status.HTTP_400_BAD_REQUEST)

        # write domains to Redis in a single transaction
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
        if time_from > time_to:
            response = {
                'status': {
                    'error': "from > to",
                    'args': f'{time_from} > {time_to}'
                },
            }
            return JsonResponse(response, status=status.HTTP_400_BAD_REQUEST)

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
