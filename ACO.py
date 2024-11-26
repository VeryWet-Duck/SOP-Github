# Importing necessary libraries
import folium  # For creating interactive maps
from geopy.geocoders import Nominatim  # For geocoding (converting addresses to latitude and longitude)
from geopy.exc import GeocoderTimedOut  # For handling geocoding timeout errors
import time  # For measuring execution time
import webbrowser  # To open the generated map in a web browser
from geopy.distance import geodesic  # For calculating distances between geographical coordinates
import random  # For probabilistic decisions in Ant Colony Optimization
import numpy as np  # For efficient numerical computations and matrix operations

# Initialize geocoder
geolocator = Nominatim(user_agent="tsp_solver")  # Nominatim geocoder initialization

# Function to geocode an address into latitude, longitude, and formatted address
def geocode_address(address):
    try:
        location = geolocator.geocode(address)  # Try to geocode the address
        if location:
            # Log the result and return latitude, longitude, and formatted address
            print(f"Geocoded: {address} -> ({location.latitude}, {location.longitude})")
            return location.latitude, location.longitude, location.address
        else:
            # Log if the geocoding fails
            print(f"Could not geocode address: {address}")
            return None
    except GeocoderTimedOut:
        # Log if the geocoding request times out
        print(f"Geocoding timed out for address: {address}")
        return None

# Function to solve the Traveling Salesman Problem using Ant Colony Optimization
def solve_aco(locations, start_index, n_ants=50, n_iterations=1000, alpha=1, beta=2, rho=0.5, q0=0.9):
    """
    Solves the Traveling Salesman Problem (TSP) using the Ant Colony Optimization (ACO) algorithm
    Parameters:
        locations: List of tuples containing latitude, longitude, and address
        start_index: Index of the starting location
        n_ants: Number of ants to simulate
        n_iterations: Number of iterations for the algorithm (reason for not using (n-1)!: 
        The factorial growth would be too rapid, which means that exploring every possible route for large datasets would not be feasable)
        alpha: Influence of pheromone trails
        beta: Influence of distance (visibility)
        rho: Pheromone evaporation rate
        q0: Probability threshold for exploitation, this is in correlation to a greedy heuristic. 
        it's just used to add som "randomness" to the algorithm, so everyant doesn't necesarily choose the same path
    Returns:
        Best route as a list
    """
    num_locations = len(locations)

    # Create a distance matrix for pairwise distances between all locations
    distance_matrix = np.array([[geodesic(locations[i][:2], locations[j][:2]).kilometers for j in range(num_locations)] for i in range(num_locations)])

    # Initialize pheromone levels (start with uniform pheromone across all paths)
    pheromone_matrix = np.ones((num_locations, num_locations))

    # Initialize variables to track the best solution
    best_route = None
    best_distance = float('inf')

    # Main loop for ACO iterations
    for iteration in range(n_iterations):
        all_routes = []  # To store routes generated by all ants in this iteration
        all_distances = []  # To store distances of the routes

        # Simulate each ant's route
        for _ in range(n_ants):
            route = [start_index]  # Start from the user-selected starting location
            visited = set(route)  # Set of visited locations
            total_distance = 0  # Total distance of the route

            # Build the route until all locations are visited
            while len(visited) < num_locations:
                current = route[-1]
                # Calculate probabilities for moving to unvisited locations
                probabilities = []
                for next_location in range(num_locations):
                    if next_location not in visited:
                        # Compute pheromone and distance contributions
                        pheromone = pheromone_matrix[current, next_location] ** alpha
                        distance = distance_matrix[current, next_location] ** (-beta)
                        probabilities.append(pheromone * distance)
                    else:
                        probabilities.append(0)
                # Normalize probabilities
                total_prob = sum(probabilities)
                probabilities = [p / total_prob for p in probabilities]

                # Choose the next location based on q0 threshold (exploitation vs. exploration)
                if random.random() < q0:
                    next_location = probabilities.index(max(probabilities))  # Exploitation
                else:
                    next_location = random.choices(range(num_locations), weights=probabilities)[0]  # Exploration

                # Add the selected location to the route
                route.append(next_location)
                visited.add(next_location)
                total_distance += distance_matrix[current, next_location]

            # Complete the route by returning to the starting point
            total_distance += distance_matrix[route[-1], route[0]]
            route.append(route[0])  # Ensure the route forms a loop
            all_routes.append(route)
            all_distances.append(total_distance)

            # Update the best solution if this route is shorter
            if total_distance < best_distance:
                best_distance = total_distance
                best_route = route

        # Update pheromone levels based on the ants' performance
        pheromone_matrix *= (1 - rho)  # Evaporation
        for i, route in enumerate(all_routes):
            for j in range(len(route) - 1):
                pheromone_matrix[route[j], route[j + 1]] += 1 / all_distances[i]  # Deposit pheromone

        # Print progress for debugging
        print(f"Iteration {iteration + 1}/{n_iterations}, Best Distance: {best_distance:.2f} km")

    return best_route

# Function to plot the TSP solution route on an interactive map
def plot_route(locations, route):
    """
    Plots the optimal route on a map using folium and displays distances.
    """
    print("Plotting the optimal route on the map...")

    # Create a map centered at the first location
    m = folium.Map(location=locations[0][:2], zoom_start=12)

    # Add markers for each location
    for idx, (lat, lon, address) in enumerate(locations):
        folium.Marker(
            (lat, lon),
            popup=folium.Popup(address, max_width=400),
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    # Add the route lines and display distances
    total_distance = 0
    for i in range(len(route) - 1):
        start = locations[route[i]]
        end = locations[route[i + 1]]
        distance = geodesic(start[:2], end[:2]).kilometers
        total_distance += distance
        folium.PolyLine([start[:2], end[:2]], color="blue", weight=2, opacity=0.6).add_to(m)

    # Display the total distance on the map
    total_distance_label = f"Total Distance: {total_distance:.2f} km"
    total_distance_html = f'<div style="position: fixed; top: 10px; right: 
    10px; font-size: 16pt; color: black; background-color: white; padding: 
    10px 20px; border-radius: 5px; font-weight: bold; z-index: 9999;">{total_distance_label}</div>'
    m.get_root().html.add_child(folium.Element(total_distance_html))

    print(f"Total route distance: {total_distance:.2f} km")

    return m
# Input addresses
addresses = [
    "Nystedvej 33, 7400 Herning, Denmark",
    "Merkurvej 1, 7400 Herning, Denmark",
    "Sunds Hovedgade 77, 7451 Sunds, Denmark",
    "Ilskovvej 4, 7451 Sunds, Denmark",
    "Hammerum Hovedgade 53, 7400 Herning, Denmark",
    "Rådhusstrædet 2, 7430 Ikast, Denmark",
    "Laust Kristensens Plads 1, 7400 Herning, Denmark",
    "Industrivej 12, 7480 Vildbjerg, Denmark",
    "Passagerterminalen 3, 7190 Billund, Denmark",
    "Hildesheimer Str. 25, 38114 Braunschweig, Germany"
]
start_time = time.time()
locations = [geocode_address(address) for address in addresses if geocode_address(address)]
if len(locations) < 2:
    print("Not enough valid locations to plot.")
    exit()
print("Please select the starting location by entering the corresponding number:")
for idx, (lat, lon, address) in enumerate(locations):
    print(f"{idx+1}. {address}")
start_location = int(input("Enter the number of the starting location: ")) - 1
if start_location < 0 or start_location >= len(locations):
    print("Invalid location number. Exiting...")
    exit()
route = solve_aco(locations, start_location)
route_map = plot_route(locations, route)
route_map.save("optimal_route_map_aco.html")
elapsed_time = time.time() - start_time
print(f"Calculation completed in {elapsed_time:.2f} seconds.")
webbrowser.open("optimal_route_map_aco.html")

# Explanation of Libraries Used
"""
1. folium: For creating interactive maps and visualizing the route.
2. geopy: For geocoding addresses and calculating geographical distances.
3. time: To measure the execution time of the script.
4. webbrowser: To automatically open the generated map in a web browser.
5. random: To introduce probabilistic decisions in the Ant Colony Optimization algorithm.
6. numpy: For efficient numerical computations, such as working with matrices.
"""