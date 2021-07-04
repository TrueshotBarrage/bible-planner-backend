from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

import json
import utils.generator as gen


@csrf_exempt
def index(request):
    config = request.POST.get("config", "")
    if config != "":
        meta = gen.run_from_server(config)
    else:
        meta = {}
    return JsonResponse(meta)
