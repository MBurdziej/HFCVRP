from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import googlemaps

# Google Maps API
gmaps = googlemaps.Client(key="Google Maps API") #uzupełnić swoim Google Maps API

# Dane wejściowe
clients = [
    {"location": "Kraków, Polska", "demand": 40},
    {"location": "Warszawa, Polska", "demand": 20},
    {"location": "Wrocław, Polska", "demand": 50},
    {"location": "Szczecin, Polska", "demand": 50},
    {"location": "Gdańsk, Polska", "demand": 20},
    {"location": "Łódź, Polska", "demand": 30},
    {"location": "Białystok, Polska", "demand": 50},
    {"location": "Zakopane, Polska", "demand": 20},
    {"location": "Karpacz, Polska", "demand": 20},
]
depot = "Katowice, Polska"  # Magazyn
vehicle_data = [
    {"capacity": 50, "fuel_consumption": 0.12, "fuel_cost_per_liter": 6.5, "hourly_wage": 30, "time_limit": 18},
    {"capacity": 100, "fuel_consumption": 0.2, "fuel_cost_per_liter": 6.5, "hourly_wage": 40, "time_limit": 10},
    {"capacity": 50, "fuel_consumption": 0.13, "fuel_cost_per_liter": 6.5, "hourly_wage": 30, "time_limit": 18},
    {"capacity": 100, "fuel_consumption": 0.3, "fuel_cost_per_liter": 6.5, "hourly_wage": 40, "time_limit": 10},
    {"capacity": 50, "fuel_consumption": 0.12, "fuel_cost_per_liter": 6.5, "hourly_wage": 30, "time_limit": 18},
    {"capacity": 100, "fuel_consumption": 0.2, "fuel_cost_per_liter": 6.5, "hourly_wage": 40, "time_limit": 10},
    {"capacity": 50, "fuel_consumption": 0.13, "fuel_cost_per_liter": 6.5, "hourly_wage": 30, "time_limit": 18},
    {"capacity": 100, "fuel_consumption": 0.3, "fuel_cost_per_liter": 6.5, "hourly_wage": 40, "time_limit": 10},
]

# Pobieranie macierzy odległości i czasów przejazdu z Google API
locations = [depot] + [client["location"] for client in clients]
distance_matrix = gmaps.distance_matrix(locations, locations, mode="driving", units="metric")

# Konwersja macierzy odległości (kilometry) i czasu przejazdu (sekundy)
distance_matrix_km = [
    [row["elements"][col]["distance"]["value"] / 1000 for col in range(len(locations))]
    for row in distance_matrix["rows"]
]
time_matrix_seconds = [
    [row["elements"][col]["duration"]["value"] for col in range(len(locations))]
    for row in distance_matrix["rows"]
]


# Tworzenie danych dla OR-Tools
def create_data_model():
    data = {}
    data["distance_matrix"] = distance_matrix_km
    data["time_matrix"] = time_matrix_seconds
    data["demands"] = [0] + [client["demand"] for client in clients]
    data["vehicle_capacities"] = [v["capacity"] for v in vehicle_data]
    data["num_vehicles"] = len(vehicle_data)
    data["depot"] = 0
    return data

# Tworzenie funkcji kosztów dla każdego pojazdu
def create_vehicle_cost_callbacks():
    cost_callbacks = []
    for vehicle_id, vehicle in enumerate(vehicle_data):
        def vehicle_cost_callback(from_index, to_index, v_id=vehicle_id, v=vehicle):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            distance = data["distance_matrix"][from_node][to_node]
            travel_time = data["time_matrix"][from_node][to_node] / 3600  # W godzinach

            # Obliczanie kosztów
            fuel_cost = distance * v["fuel_consumption"] * v["fuel_cost_per_liter"]
            labor_cost = travel_time * v["hourly_wage"]

            return int((fuel_cost + labor_cost) * 1000)  # Koszt w groszach

        cost_callbacks.append(vehicle_cost_callback)
    return cost_callbacks


def solve_vrp():
    global data
    data = create_data_model()
    global manager
    manager = pywrapcp.RoutingIndexManager(len(data["distance_matrix"]), len(vehicle_data), data["depot"])
    global routing
    routing = pywrapcp.RoutingModel(manager)

    # Tworzenie funkcji kosztów dla każdego pojazdu
    cost_callbacks = create_vehicle_cost_callbacks()
    for vehicle_id, callback in enumerate(cost_callbacks):
        transit_callback_index = routing.RegisterTransitCallback(callback)
        routing.SetArcCostEvaluatorOfVehicle(transit_callback_index, vehicle_id)

    # Dodanie wymiaru pojemności
    def demand_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return data["demands"][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,
        data["vehicle_capacities"],
        True,
        "Capacity",
    )

    # Dodanie wymiaru czasu (Time)
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(data["time_matrix"][from_node][to_node])  # Czas w sekundach

    time_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(
        time_callback_index,
        0,
        max(vehicle["time_limit"] * 3600 for vehicle in vehicle_data),  # Limit czasu w sekundach
        True,
        "Time",
    )

    # Ustawienie limitów czasu dla każdego pojazdu
    time_dimension = routing.GetDimensionOrDie("Time")
    for vehicle_id, vehicle in enumerate(vehicle_data):
        time_limit_seconds = vehicle["time_limit"] * 3600
        time_dimension.CumulVar(routing.End(vehicle_id)).SetMax(time_limit_seconds)

        # Powrót do magazynu
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(routing.End(vehicle_id)))

    # Parametry wyszukiwania
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        print_solution(data, manager, routing, solution)
    else:
        print("Nie znaleziono rozwiązania.")



def print_solution(data, manager, routing, solution):
    total_cost = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = f"Trasa dla pojazdu {vehicle_id}: "
        route_cost = 0
        total_travel_time = 0
        total_fuel_cost = 0
        total_labor_cost = 0
        total_fuel_consumed = 0
        total_distance = 0
        total_demand = 0

        while not routing.IsEnd(index):
            from_node = manager.IndexToNode(index)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            to_node = manager.IndexToNode(index)

            if not routing.IsEnd(index):
                arc_cost = routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
                route_cost += arc_cost

                distance = data["distance_matrix"][from_node][to_node]
                travel_time = data["time_matrix"][from_node][to_node] / 3600  # W godzinach
                fuel_consumed = distance * vehicle_data[vehicle_id]["fuel_consumption"]
                fuel_cost = fuel_consumed * vehicle_data[vehicle_id]["fuel_cost_per_liter"]
                labor_cost = travel_time * vehicle_data[vehicle_id]["hourly_wage"]

                total_travel_time += travel_time
                total_fuel_cost += fuel_cost
                total_labor_cost += labor_cost
                total_fuel_consumed += fuel_consumed
                total_distance += distance

                total_demand += data["demands"][to_node]

            plan_output += f"{clients[from_node - 1]['location'] if from_node > 0 else depot} -> "

        # Uwzględnienie powrotu do magazynu
        if from_node != 0:
            distance = data["distance_matrix"][from_node][0]
            travel_time = data["time_matrix"][from_node][0] / 3600  # W godzinach
            fuel_consumed = distance * vehicle_data[vehicle_id]["fuel_consumption"]
            fuel_cost = fuel_consumed * vehicle_data[vehicle_id]["fuel_cost_per_liter"]
            labor_cost = travel_time * vehicle_data[vehicle_id]["hourly_wage"]

            # Aktualizacja kosztów powrotu
            total_travel_time += travel_time
            total_fuel_cost += fuel_cost
            total_labor_cost += labor_cost
            total_fuel_consumed += fuel_consumed
            total_distance += distance

            route_cost += int((fuel_cost + labor_cost) * 1000)  # Koszt powrotu w groszach
            plan_output += f"{depot}"

        plan_output += f"\nKoszt trasy: {route_cost / 1000:.2f} zł\n"
        plan_output += f"Przejechana odległość: {total_distance:.2f} km\n"
        hours = int(total_travel_time)
        minutes = int((total_travel_time - hours) * 60)
        plan_output += f"Czas w trasie: {hours} godz {minutes} min\n"
        plan_output += f"Paliwo zużyte: {total_fuel_consumed:.2f} l\n"
        plan_output += f"Koszt paliwa: {total_fuel_cost:.2f} zł\n"
        plan_output += f"Koszt kierowcy: {total_labor_cost:.2f} zł\n"
        # plan_output += f"Zabrane paczki: {total_demand}\n"
        print(plan_output)

        total_cost += route_cost

    print(f"Całkowity koszt (zł): {total_cost / 1000:.2f} zł")



# Uruchomienie
solve_vrp()