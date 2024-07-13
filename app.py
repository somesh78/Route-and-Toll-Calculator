from flask import Flask, render_template, request, jsonify
import os
import shutil
import route

app = Flask(__name__, static_folder='static')

API_KEY_OC = "API_KEY_OPENCAGE"
API_KEY_ORS = "API_KEY_OPENROUTESERVICE"
TOLLGURU_API_KEY = "API_KEY_TOLLGURU"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    origin_address = request.form['origin']
    destination_address = request.form['destination']

    polyline = route.polyline_generator(origin_address, destination_address)

    if polyline:
        try:
            rates_from_tollguru = route.get_rates_from_tollguru(polyline)
            if rates_from_tollguru == {}:
                result = "The route doesn't have tolls"
            else:
                result = f"Toll rates are: {rates_from_tollguru['minimumTollCost']} \n"

            map_filename = route.get_shortest_route(API_KEY_ORS, API_KEY_OC, origin_address, destination_address)
            if map_filename:
                map_path = os.path.join(app.static_folder, map_filename)
                shutil.move(map_filename, map_path)
                
                return jsonify({'result': result, 'map_filename': map_filename})
            else:
                result = f"Could not generate route map for {origin_address} to {destination_address}."
        except Exception as e:
            result = f"Error fetching toll rates: {e}"
    else:
        result = f"Could not find a route from {origin_address} to {destination_address}."

    return jsonify({'result': result})

if __name__ == "__main__":
    app.run(debug=True)
