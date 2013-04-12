# coding: utf-8

from SPARQLWrapper import SPARQLWrapper, JSON
from collections import namedtuple
from sets import Set
import os
import json

JSON_LATLONG_PATH = os.path.abspath(os.path.join(os.getcwd(), 'municipality_latlong.json'))
MUNICIPALITY_LATLNG_DICT = json.load(open(JSON_LATLONG_PATH))

GEONAMES_SPARQL = SPARQLWrapper("http://helheim.deusto.es/geonames/sparql")
LINKEDSTATS_SPARQL = SPARQLWrapper('http://helheim.deusto.es/linkedstats/sparql')
DBPEDIA_SPARQL = SPARQLWrapper('http://helheim.deusto.es/dbpedia/sparql')
SPARQL_PREFIXES =  '''PREFIX qb: <http://purl.org/linked-data/cube#>
PREFIX stats-dimension: <http://helheim.deusto.es/linkedstats/resource/dimension/>
PREFIX stats-measure: <http://helheim.deusto.es/linkedstats/resource/measure/>
PREFIX stats-dataset: <http://helheim.deusto.es/linkedstats/resource/dataset/>'''

INTERVAL_RESOURCE = 'http://reference.data.gov.uk/id/year/'
GEONAMES_ONT_PREFIX = 'http://www.geonames.org/ontology#'

def all_official_municipality_names():
    GEONAMES_SPARQL.setQuery("""
SELECT distinct(?name) WHERE {
    ?s <http://www.geonames.org/ontology#featureClass> <http://www.geonames.org/ontology#A> .
    ?s <http://www.geonames.org/ontology#parentADM2> <http://sws.geonames.org/3104469/> .
    ?s <http://www.geonames.org/ontology#name> ?name .
}
    """)

    GEONAMES_SPARQL.setReturnFormat(JSON)
    results = GEONAMES_SPARQL.query().convert()

    reslist = []
    for result in results["results"]["bindings"]:
        reslist.append(result["name"]["value"].encode('utf-8'))

    return reslist


def all_municipalities_to_json():
    GEONAMES_SPARQL.setQuery("""
SELECT ?s ?name ?alternatename WHERE {
    ?s <http://www.geonames.org/ontology#featureClass> <http://www.geonames.org/ontology#A> .
    ?s <http://www.geonames.org/ontology#parentADM2> <http://sws.geonames.org/3104469/> .
    ?s <http://www.geonames.org/ontology#name> ?name .
    OPTIONAL {?s <http://www.geonames.org/ontology#alternateName> ?alternatename .}
}
ORDER BY ?name
    """)

    # Not used by the moment, but it gets all alt.names by analyzing both administrative division URI (A) and *seat* 
    # of administrative division URI (P), and not only those given by A URI. Seat URI is gotten by string comparison
    # between A's name and its children's name, because most seats of administrative division aren't well defined 
    # -many of them don't include featureCode:P.PPLA2 relationship- and that's the only way to find the relationship
    # between an A and its PPLA2.
    completequery = """PREFIX geonames: <http://www.geonames.org/ontology#>

SELECT ?s ?name ?alternatename WHERE {
    ?s geonames:featureClass geonames:A .
    ?s geonames:parentADM2 <http://sws.geonames.org/3104469/> .
    {
        ?s geonames:name ?name .
        OPTIONAL {?s geonames:alternateName ?alternatename .}
    }
    UNION
    {
        ?s geonames:name ?name .
        ?child_uri geonames:parentADM3 ?s .
        OPTIONAL { ?child_uri geonames:name ?child_name } .
        OPTIONAL { ?child_uri geonames:alternateName ?alternatename } .
        FILTER (str(?name) = str(?child_name))
    }
}
ORDER BY ?name
    """

    GEONAMES_SPARQL.setReturnFormat(JSON)
    results = GEONAMES_SPARQL.query().convert()

    resdict = {}
    for result in results["results"]["bindings"]:
        resdict[result["name"]["value"].encode('utf-8')] = [result["s"]["value"], True]
        try:
            resdict[result["alternatename"]["value"].encode('utf-8')] = [result["s"]["value"], False]
        except:
            pass

    with open('municipality_geonames.json', 'w') as outfile:
        json.dump(resdict, outfile)

def all_municipalities_latlong_to_json():
    GEONAMES_SPARQL.setQuery("""PREFIX geonames: <http://www.geonames.org/ontology#>
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>

SELECT DISTINCT ?s ?name ?lat ?long WHERE {
    ?s geonames:featureClass geonames:A ;
      geonames:parentADM2 <http://sws.geonames.org/3104469/> ;
      geonames:name ?name ;
      geo:lat ?lat ;
      geo:long ?long .
}
    """)

    GEONAMES_SPARQL.setReturnFormat(JSON)
    results = GEONAMES_SPARQL.query().convert()

    resdict = {}
    for result in results["results"]["bindings"]:
        resdict[result["s"]["value"]] = {"lat": result["lat"]["value"], "long": result["long"]["value"], "name": result["name"]["value"]}

    with open('municipality_latlong.json', 'w') as outfile:
        json.dump(resdict, outfile)

def get_total_waste_per_person_year_all_municipalities():
    sparql_query = SPARQL_PREFIXES + '''
SELECT ?year ?municipality (SUM(?wastekg)/SUM(?population)/365 AS ?KG_per_person) WHERE {
        {
          ?dspopulation qb:dataSet stats-dataset:population ;
            stats-dimension:year ?year ;
            stats-dimension:municipality ?municipality ;
            stats-measure:population ?population .
        }
        UNION
        {
          ?dswaste qb:dataSet stats-dataset:waste ;
            stats-dimension:year ?year ;
            stats-dimension:municipality ?municipality ;
            stats-dimension:wasteType ?wasteType ;
            stats-measure:wasteKg ?wastekg .
        }
}
GROUP BY ?year ?municipality
ORDER BY ?year
    '''
    LINKEDSTATS_SPARQL.setQuery(sparql_query)
    LINKEDSTATS_SPARQL.setReturnFormat(JSON)
    kg_waste_person_mun_year = LINKEDSTATS_SPARQL.query().convert()

    datadict = {}
    for data in kg_waste_person_mun_year['results']['bindings']:
        year = data['year']['value'].replace(INTERVAL_RESOURCE,'')
        if year not in datadict:
            datadict[year] = []
        datadict[year].append({
            "lat": float(MUNICIPALITY_LATLNG_DICT[data['municipality']['value']]['lat']),
            "lng": float(MUNICIPALITY_LATLNG_DICT[data['municipality']['value']]['long']), 
            "count": float(data['KG_per_person']['value'])
        })
    return datadict, sparql_query


def get_all_data_about_municipality(geonamesuri):
    sparql_query = SPARQL_PREFIXES + '''
SELECT ?year ?ageRange ?population ?wasteType ?wastekg ?wastecont WHERE {
        {
          ?dspopulation qb:dataSet stats-dataset:population ;
            stats-dimension:year ?year ;
            stats-dimension:municipality <''' + geonamesuri + '''> ;
            stats-measure:population ?population ;
            stats-dimension:ageRange ?ageRange .
        }
        UNION
        {
          ?dswaste qb:dataSet stats-dataset:waste ;
            stats-dimension:year ?year ;
            stats-dimension:municipality <''' + geonamesuri + '''> ;
            stats-dimension:wasteType ?wasteType ;
            stats-measure:nContainers ?wastecont ;
            stats-measure:wasteKg ?wastekg .
        }
}
GROUP BY ?year
ORDER BY ?year ?ageRange
    '''
    LINKEDSTATS_SPARQL.setQuery(sparql_query)
    LINKEDSTATS_SPARQL.setReturnFormat(JSON)
    return LINKEDSTATS_SPARQL.query().convert(), sparql_query

def get_wastekg_by_wastetype_municipality_year(geonamesuri):
    sparql_query = SPARQL_PREFIXES + '''
SELECT ?year ?wastelabel ?wastekg WHERE {
    ?dswaste qb:dataSet stats-dataset:waste ;
        stats-dimension:year ?year ;
        stats-dimension:municipality <''' + geonamesuri + '''> ;
        stats-dimension:wasteType ?wastetype ;
        stats-measure:wasteKg ?wastekg .
    ?wastetype skos:prefLabel ?wastelabel .
    FILTER (str(?wastetype) != 'http://helheim.deusto.es/linkedstats/resource/code/wasteType/total')
}
ORDER BY ?year
    '''
    LINKEDSTATS_SPARQL.setQuery(sparql_query)
    LINKEDSTATS_SPARQL.setReturnFormat(JSON)

    kg_wastetype_year = LINKEDSTATS_SPARQL.query().convert()

    datadict = {}
    for data in kg_wastetype_year['results']['bindings']:
        wastelabel = data['wastelabel']['value']
        year = data['year']['value'].replace(INTERVAL_RESOURCE,'')
        if wastelabel not in datadict:
            datadict[wastelabel] = {}
        datadict[wastelabel][year] = data['wastekg']['value']

    return datadict, sparql_query

def get_kg_per_person_year_municipality(geonamesuri):
    sparql_query = SPARQL_PREFIXES + '''
SELECT ?year (SUM(?wastekg)/sum(?population)/365 AS ?KG_per_person) WHERE {
        {
          ?dspopulation qb:dataSet stats-dataset:population ;
            stats-dimension:year ?year ;
            stats-dimension:municipality <''' + geonamesuri + '''> ;
            stats-measure:population ?population ;
            stats-dimension:ageRange ?ageRange .
          FILTER (str(?ageRange) = 'http://helheim.deusto.es/linkedstats/resource/code/ageRange/total')
        }
        UNION
        {
          ?dswaste qb:dataSet stats-dataset:waste ;
            stats-dimension:year ?year ;
            stats-dimension:municipality <''' + geonamesuri + '''> ;
            stats-dimension:wasteType ?wasteType ;
            stats-measure:wasteKg ?wastekg .
          FILTER (str(?wasteType) = 'http://helheim.deusto.es/linkedstats/resource/code/wasteType/total')
        }
}
GROUP BY ?year
ORDER BY ?year
    '''
    LINKEDSTATS_SPARQL.setQuery(sparql_query)
    LINKEDSTATS_SPARQL.setReturnFormat(JSON)

    kg_person_year = LINKEDSTATS_SPARQL.query().convert()

    datadict = {}
    for data in kg_person_year['results']['bindings']:
        datadict[data['year']['value'].replace(INTERVAL_RESOURCE,'')] = data['KG_per_person']['value']

    return datadict, sparql_query

def get_population_year_municipality(geonamesuri):
    sparql_query = SPARQL_PREFIXES + '''
SELECT ?year ?population WHERE {
    ?dspopulation qb:dataSet stats-dataset:population ;
        stats-dimension:year ?year ;
        stats-dimension:municipality <''' + geonamesuri + '''> ;
        stats-measure:population ?population ;
        stats-dimension:ageRange <http://helheim.deusto.es/linkedstats/resource/code/ageRange/total> .
}
GROUP BY ?year
ORDER BY ?year
    '''
    LINKEDSTATS_SPARQL.setQuery(sparql_query)
    LINKEDSTATS_SPARQL.setReturnFormat(JSON)

    population_year = LINKEDSTATS_SPARQL.query().convert()

    datadict = {}
    for data in population_year['results']['bindings']:
        datadict[data['year']['value'].replace(INTERVAL_RESOURCE,'')] = data['population']['value']

    return datadict, sparql_query

def get_avg_kg_per_person_year_biscay():
    sparql_query = SPARQL_PREFIXES + '''
SELECT ?year (SUM(?wastekg)/sum(?population)/365 AS ?KG_per_person) WHERE {
        {
          ?dspopulation qb:dataSet stats-dataset:population ;
            stats-dimension:year ?year ;
            stats-measure:population ?population ;
            stats-dimension:ageRange ?ageRange .
          FILTER (str(?ageRange) = 'http://helheim.deusto.es/linkedstats/resource/code/ageRange/total')
        }
        UNION
        {
          ?dswaste qb:dataSet stats-dataset:waste ;
            stats-dimension:year ?year ;
            stats-dimension:wasteType ?wasteType ;
            stats-measure:wasteKg ?wastekg .
          FILTER (str(?wasteType) = 'http://helheim.deusto.es/linkedstats/resource/code/wasteType/total')
        }  
}
GROUP BY ?year
ORDER BY ?year
    '''
    LINKEDSTATS_SPARQL.setQuery(sparql_query)
    LINKEDSTATS_SPARQL.setReturnFormat(JSON)

    avg_kg_person_year = LINKEDSTATS_SPARQL.query().convert()

    datadict = {}
    for data in avg_kg_person_year['results']['bindings']:
        datadict[data['year']['value'].replace(INTERVAL_RESOURCE,'')] = data['KG_per_person']['value']

    return datadict, sparql_query

def get_population_whole_biscay():
    sparql_query = SPARQL_PREFIXES + '''
SELECT ?municipality ?year ?ageRangeLabel ?population WHERE {
          ?dspopulation qb:dataSet stats-dataset:population ;
            stats-dimension:municipality ?municipality ;
            stats-dimension:year ?year ;
            stats-measure:population ?population ;
            stats-dimension:ageRange ?ageRange .
          ?ageRange skos:notation ?ageRangeLabel
          FILTER (str(?ageRange) != 'http://helheim.deusto.es/linkedstats/resource/code/ageRange/total')
}
ORDER BY ?municipality ?year ?ageRangeLabel
    '''
    LINKEDSTATS_SPARQL.setQuery(sparql_query)
    LINKEDSTATS_SPARQL.setReturnFormat(JSON)

    avg_kg_person_year = LINKEDSTATS_SPARQL.query().convert()

    datadict = {}
    #munlist = ['Gatika', 'Bilbao', 'Abadiño', 'Elorrio', 'Lekeitio', 'Basauri']
    '''for data in avg_kg_person_year['results']['bindings']:
        year = data['year']['value'].replace(INTERVAL_RESOURCE,'')
        ageRange = data['ageRangeLabel']['value']
        municipality  = MUNICIPALITY_LATLNG_DICT[data['municipality']['value']]['name']
        if year not in datadict:
            datadict[year] = {}
        if ageRange not in datadict[year]:
            datadict[year][ageRange] = {}
        #if municipality in munlist:
        datadict[year][ageRange][municipality] = data['population']['value'] '''
    for data in avg_kg_person_year['results']['bindings']:
        year = data['year']['value'].replace(INTERVAL_RESOURCE,'')
        ageRange = data['ageRangeLabel']['value']
        municipality  = MUNICIPALITY_LATLNG_DICT[data['municipality']['value']]['name']
        if year not in datadict:
            datadict[year] = {}
        if municipality not in datadict[year]:
            datadict[year][municipality] = {}
        #if municipality in munlist:
        datadict[year][municipality][ageRange] = data['population']['value']

    return datadict, sparql_query

def get_extra_info_about_municipality(geonamesuri):
    sparql_query = '''PREFIX geonames: <http://www.geonames.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>
PREFIX geonamesuri: <''' + geonamesuri + '''>

SELECT ?main_name ?main_lat ?main_long ?main_alt_names ?dbpedia_uri ?child_name ?child_uri ?child_type ?child_dbpedia_uri WHERE {
    geonamesuri: geo:lat ?main_lat .
    geonamesuri: geo:long ?main_long .

    {
        OPTIONAL { geonamesuri: geonames:alternateName ?main_alt_names } .
        OPTIONAL { geonamesuri: rdfs:seeAlso ?dbpedia_uri } .

        geonamesuri: geonames:name ?main_name .
        ?child_uri geonames:parentADM3 geonamesuri: .
        ?child_uri geonames:featureClass ?child_type .
        OPTIONAL { ?child_uri geonames:name ?child_name } .
        OPTIONAL { ?child_uri rdfs:seeAlso ?child_dbpedia_uri } .
        FILTER (str(?main_name) != str(?child_name))
    }
    UNION
    {
        geonamesuri: geonames:name ?main_name .
        ?child_uri_comp geonames:parentADM3 geonamesuri: .
        OPTIONAL { ?child_uri_comp geonames:name ?child_name_comp } .
        OPTIONAL { ?child_uri_comp rdfs:seeAlso ?dbpedia_uri } .
        OPTIONAL { ?child_uri_comp geonames:alternateName ?main_alt_names } .
        FILTER (str(?main_name) = str(?child_name_comp))
    }
}
    '''

    GEONAMES_SPARQL.setQuery(sparql_query)
    GEONAMES_SPARQL.setReturnFormat(JSON)

    extra_info_geonames = GEONAMES_SPARQL.query().convert()

    datadict = {
        'name': None,
        'geonames': geonamesuri,
        'lat': None,
        'long': None,
        'alt_names': Set(),
        'dbpedia': None,
        'A': [],
        'H': [],
        'L': [],
        'P': [],
        'R': [],
        'S': [],
        'T': [],
        'U': [],
        'V': [],
        'description': None
    }
    ChildrenStruct = namedtuple("ChildrenStruct", "name uri dbpedia")

    for data in extra_info_geonames['results']['bindings']:
        if not datadict['name']:
            datadict['name'] = data['main_name']['value']
        if not datadict['lat']:
            datadict['lat'] = data['main_lat']['value']
        if not datadict['long']:
            datadict['long'] = data['main_long']['value']
        if 'main_alt_names' in data:
            datadict['alt_names'].add(data['main_alt_names']['value'])
        if 'dbpedia_uri' in data and not datadict['dbpedia']:
            datadict['dbpedia'] = data['dbpedia_uri']['value']
        if 'child_name' in data:
            child_dbpedia_uri = data['child_dbpedia_uri']['value'] if 'child_dbpedia_uri' in data else None
            child = ChildrenStruct(
                name=data['child_name']['value'], 
                uri=data['child_uri']['value'], 
                dbpedia=child_dbpedia_uri
            )
            classtype = data['child_type']['value'].replace(GEONAMES_ONT_PREFIX, '')
            datadict[classtype].append(dict(child._asdict()))

    dbpedia_sparql_query = None
    if datadict['dbpedia']:
        dbpedia_sparql_query = '''
SELECT ?description WHERE {
  <''' + datadict['dbpedia'] + '''> <http://dbpedia.org/ontology/abstract> ?description
  FILTER (lang(?description) = 'en')
}
        '''
        DBPEDIA_SPARQL.setQuery(dbpedia_sparql_query)
        DBPEDIA_SPARQL.setReturnFormat(JSON)
        
        try:
            datadict['description'] = DBPEDIA_SPARQL.query().convert()['results']['bindings'][0]['description']['value']
        except:
            pass

    return datadict, (sparql_query, dbpedia_sparql_query)