from flask import Flask, render_template, request, jsonify
import os
import shutil
import route

app = Flask(__name__, static_folder='static')

API_KEY_OC = "4a5c67bb5b164ce8bcdd5603bd4bc348"
API_KEY_ORS = "5b3ce3597851110001cf624883442da13b3f48ddb6c425cdcf81eeec"
TOLLGURU_API_KEY = os.environ.get("TOLLGURU_API_KEY")

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