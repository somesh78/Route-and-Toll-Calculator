import folium
import openrouteservice
from opencage.geocoder import OpenCageGeocode
from openrouteservice.exceptions import ApiError
import requests
from datetime import datetime, timezone
import os

API_KEY_OC = "API_KEY_OPENCAGE"
TOLLGURU_API_KEY = "API_KEY_TOLLGURU"
TOLLGURU_API_URL = "https://apis.tollguru.com/toll/v2"
POLYLINE_ENDPOINT = "complete-polyline-from-mapping-service"

def get_coordinates(api_key, address):
    geocoder = OpenCageGeocode(api_key)
    result = geocoder.geocode(address)
    if result and len(result) > 0:
        return result[0]['geometry']['lat'], result[0]['geometry']['lng']
    else:
        return None, None

def get_shortest_route(api_key_ors, api_key_oc, origin_address, destination_address):
    try:
        origin_lat, origin_lng = get_coordinates(api_key_oc, origin_address)
        destination_lat, destination_lng = get_coordinates(api_key_oc, destination_address)

        if origin_lat is None or origin_lng is None or destination_lat is None or destination_lng is None:
            return None

        client = openrouteservice.Client(key=api_key_ors)

        coords = [[origin_lng, origin_lat], [destination_lng, destination_lat]]
        routes = client.directions(coordinates=coords, profile='driving-car', format='geojson')

        if 'features' not in routes or len(routes['features']) == 0:
            return None

        route_geometry = routes['features'][0]['geometry']['coordinates']

        m = folium.Map(location=[(origin_lat + destination_lat) / 2, 
                                 (origin_lng + destination_lng) / 2], zoom_start=5)

        folium.Marker([origin_lat, origin_lng], tooltip="Origin", popup=origin_address, icon=folium.Icon(color="green")).add_to(m)
        folium.Marker([destination_lat, destination_lng], tooltip="Destination", popup=destination_address, icon=folium.Icon(color="red")).add_to(m)

        route_coords = [[point[1], point[0]] for point in route_geometry]

        folium.PolyLine(locations=route_coords, color='blue', weight=5, opacity=0.7).add_to(m)

        map_filename = f"route_map.html"
        m.save(map_filename)

        return map_filename

    except Exception as e:
        return None

    except ApiError as e:
        return None

def get_rates_from_tollguru(polyline):
    request_parameters = {
        "vehicle": {
            "type": "2AxlesAuto",
        },
        "departure_time": datetime.now(timezone.utc).isoformat() + 'Z',
    }

    headers = {"Content-type": "application/json", "x-api-key": TOLLGURU_API_KEY}
    params = {
        **request_parameters,
        "source": "osrm",
        "polyline": polyline,
    }

    response_tollguru = requests.post(
        f"{TOLLGURU_API_URL}/{POLYLINE_ENDPOINT}",
        json=params,
        headers=headers,
        timeout=200,
    ).json()

    if "message" in response_tollguru:
        raise Exception(response_tollguru["message"])
    elif "route" in response_tollguru and "costs" in response_tollguru["route"]:
        return response_tollguru["route"]["costs"]
    else:
        raise Exception("Unexpected response format from TollGuru API")

def polyline_generator(origin_address, destination_address):
    origin_lat, origin_lng = get_coordinates(API_KEY_OC, origin_address)
    destination_lat, destination_lng = get_coordinates(API_KEY_OC, destination_address)

    if origin_lat is None or origin_lng is None or destination_lat is None or destination_lng is None:
        print("Could not find one or both of the addresses.")
        return None

    osrm_url = 'http://router.project-osrm.org/route/v1/driving/'

    url = f"{osrm_url}{origin_lng},{origin_lat};{destination_lng},{destination_lat}?overview=full"

    response = requests.get(url)

    if response.status_code == 200:
        route = response.json()
        if 'routes' in route and len(route['routes']) > 0:
            polyline = route['routes'][0]['geometry']
            return polyline
        else:
            print("No route found")
    else:
        print(f"Request failed with status code {response.status_code}")
