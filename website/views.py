# coding: utf-8

from django.shortcuts import render_to_response, get_object_or_404
from rdflib import Namespace
from django.utils.encoding import smart_str
from django.template import RequestContext
from datetime import datetime
from django.http import Http404, HttpResponse
from sets import Set

from utils import *

import os
import json

GEONAMES_CODES = {
    'A': 'country, state, region, ...',
    'H': 'stream, lake, ...',
    'L': 'parks, area, ...',
    'P': 'city, village, ...',
    'R': 'road, railroad',
    'S': 'spot, building, farm',
    'T': 'mountain, hill, rock, ...',
    'U': 'undersea',
    'V': 'forest, heath, ...'
}

JSON_PATH = os.path.abspath(os.path.join(os.getcwd(), 'municipality_geonames.json'))
MUNICIPALITY_DICT = json.load(open(JSON_PATH))

def index(request):
    details={}

    kg_waste_person_mun_year, details['kg_waste_person_mun_year_query'] = get_total_waste_per_person_year_all_municipalities()
    details['kg_waste_person_mun_year'] = json.dumps(kg_waste_person_mun_year)

    details['municipality_points'] = MUNICIPALITY_LATLNG_DICT

    return render_to_response('index.html', details, context_instance=RequestContext(request))

def doc(request):
    return render_to_response('doc.html', context_instance=RequestContext(request))

def municipality_search(request):
    details={}

    municipality_official_names = Set()

    for key, val in MUNICIPALITY_DICT.items():
        if val[1]:
            municipality_official_names.add(key)

    details['all_municipality_names'] = sorted(list(municipality_official_names))

    return render_to_response('municipality_search.html', details, context_instance=RequestContext(request))

def municipality(request, municipality_name):
    details={}

    try:
        geonames_uri = MUNICIPALITY_DICT[municipality_name][0]
    except KeyError:
        raise Http404

    kg_person_year, details['kg_person_year_query'] = get_kg_per_person_year_municipality(geonames_uri)
    details['kg_person_year'] = json.dumps(kg_person_year)
    
    kg_wastetype_year, details['kg_wastetype_year_query'] = get_wastekg_by_wastetype_municipality_year(geonames_uri)
    details['kg_wastetype_year'] = json.dumps(kg_wastetype_year)

    avg_kg_person_year, details['avg_kg_person_year_query'] = get_avg_kg_per_person_year_biscay()
    details['avg_kg_person_year'] = json.dumps(avg_kg_person_year)

    details['municipality_info'], details['extra_info_queries'] = get_extra_info_about_municipality(geonames_uri)
    if not details['municipality_info']['name']:
        details['municipality_info']['name'] = municipality_name
        details['municipality_info']['lat'] = MUNICIPALITY_LATLNG_DICT[geonames_uri]["lat"]
        details['municipality_info']['long'] = MUNICIPALITY_LATLNG_DICT[geonames_uri]["long"]


    details['population_year'], details['population_year_query'] = get_population_year_municipality(geonames_uri)

    return render_to_response('municipality.html', details, context_instance=RequestContext(request))

def population(request):
    details = {}

    details['population'], details['population_query'] = get_population_whole_biscay()

    return render_to_response('population.html', details, context_instance=RequestContext(request))