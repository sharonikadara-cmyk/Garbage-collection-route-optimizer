import streamlit as st
import networkx as nx
import folium
from streamlit_folium import st_folium

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Garbage Collection Route Optimizer",
    page_icon="🚛",
    layout="wide"
)

# ---------------------------------------------------------
# LOCATION DATA
# Prototype coordinates and road distances
# ---------------------------------------------------------
LOCATIONS = {
    "Depot": (17.3850, 78.4867),
    "Madhapur": (17.4483, 78.3915),
    "Kukatpally": (17.4849, 78.4138),
    "Ameerpet": (17.4375, 78.4483),
    "Banjara Hills": (17.4156, 78.4347),
    "Hitech City": (17.4435, 78.3772),
    "Mehdipatnam": (17.3950, 78.4400),
}

# Weighted road network
EDGES = [
    ("Depot", "Mehdipatnam", 6),
    ("Depot", "Banjara Hills", 7),
    ("Depot", "Ameerpet", 8),

    ("Mehdipatnam", "Banjara Hills", 5),
    ("Mehdipatnam", "Ameerpet", 6),

    ("Banjara Hills", "Ameerpet", 4),
    ("Banjara Hills", "Madhapur", 9),

    ("Ameerpet", "Madhapur", 7),
    ("Ameerpet", "Kukatpally", 9),

    ("Madhapur", "Hitech City", 4),
    ("Madhapur", "Kukatpally", 8),

    ("Kukatpally", "Hitech City", 7),
]


# ---------------------------------------------------------
# CREATE GRAPH
# ---------------------------------------------------------
def build_graph():
    graph = nx.Graph()

    graph.add_nodes_from(LOCATIONS.keys())

    graph.add_weighted_edges_from(EDGES)

    return graph


# ---------------------------------------------------------
# ROUTE OPTIMIZATION
# Dijkstra + Greedy approach
# ---------------------------------------------------------
def optimize_route(targets):

    graph = build_graph()

    remaining = set(targets)

    current = "Depot"

    route = [current]

    decisions = []

    total_distance = 0.0

    while remaining:

        # Dijkstra shortest paths from current location
        distances, paths = nx.single_source_dijkstra(
            graph,
            current,
            weight="weight"
        )

        # Greedy selection:
        # choose nearest unvisited collection point
        next_stop = min(
            remaining,
            key=lambda node: distances[node]
        )

        distance = distances[next_stop]

        # Add path to route
        route.extend(paths[next_stop][1:])

        decisions.append(
            (current, next_stop, distance)
        )

        total_distance += distance

        current = next_stop

        remaining.remove(next_stop)

    # Return to depot
    if current != "Depot":

        distance, path = nx.single_source_dijkstra(
            graph,
            current,
            "Depot",
            weight="weight"
        )

        route.extend(path[1:])

        decisions.append(
            (current, "Depot", distance)
        )

        total_distance += distance

    return route, decisions, total_distance


# ---------------------------------------------------------
# USER INTERFACE
# ---------------------------------------------------------

st.title("🚛 Garbage Collection Route Optimizer")

st.subheader(
    "Smart Waste Collection and Route Optimization System"
)

st.write(
    "This application uses a weighted road network, "
    "Dijkstra's shortest-path algorithm and a greedy "
    "selection strategy to generate an efficient "
    "garbage collection route."
)

# ---------------------------------------------------------
# INPUT SECTION
# ---------------------------------------------------------

col1, col2 = st.columns(2)

with col1:

    area = st.text_input(
        "Area / Location",
        "Hyderabad"
    )

with col2:

    waste = st.number_input(
        "Waste Amount (kg)",
        min_value=1.0,
        value=50.0,
        step=5.0
    )


collection_points = [
    location
    for location in LOCATIONS
    if location != "Depot"
]


targets = st.multiselect(
    "Select Garbage Collection Points",
    collection_points,
    default=[
        "Madhapur",
        "Kukatpally",
        "Ameerpet",
        "Banjara Hills",
        "Mehdipatnam"
    ]
)


# ---------------------------------------------------------
# OPTIMIZATION BUTTON
# ---------------------------------------------------------

# ---------------------------------------------------------
# OPTIMIZATION BUTTON + PERSISTENT RESULTS
# ---------------------------------------------------------

if "route_results" not in st.session_state:
    st.session_state.route_results = None

if st.button("🚀 Optimize Route", type="primary"):

    if not targets:
        st.error("Please select at least one collection point.")
    else:
        route, decisions, total_distance = optimize_route(targets)

        # Save results so they survive Streamlit reruns
        st.session_state.route_results = {
            "route": route,
            "decisions": decisions,
            "total_distance": total_distance,
            "area": area,
            "waste": waste,
            "targets": list(targets),
        }

# Display saved results whenever the app reruns
results = st.session_state.route_results

if results is not None:

    route = results["route"]
    decisions = results["decisions"]
    total_distance = results["total_distance"]
    selected_targets = results["targets"]

    st.success(
        f"Route optimized successfully for {results['area']}!"
    )

    st.subheader("Recommended Route")
    st.write(" → ".join(route))

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Distance", f"{total_distance:.1f} km")
    col2.metric(
        "Collection Points",
        f"{len(selected_targets)}/{len(selected_targets)}"
    )
    col3.metric("Waste Input", f"{results['waste']:.1f} kg")

    # -----------------------------------------------------
    # MAP
    # -----------------------------------------------------
    st.subheader("🗺️ Optimized Route Map")

    map_object = folium.Map(
        location=LOCATIONS["Depot"],
        zoom_start=12
    )

    for name, coordinates in LOCATIONS.items():

        if name == "Depot":
            icon = folium.Icon(color="red", icon="home")

        elif name in selected_targets:
            icon = folium.Icon(color="green", icon="trash")

        else:
            continue

        folium.Marker(
            coordinates,
            tooltip=name,
            icon=icon
        ).add_to(map_object)

    route_coordinates = [
        LOCATIONS[node] for node in route
    ]

    folium.PolyLine(
        route_coordinates,
        color="blue",
        weight=5,
        tooltip="Optimized collection route"
    ).add_to(map_object)

    st_folium(
        map_object,
        width=None,
        height=500,
        key="optimized_route_map"
    )

    # -----------------------------------------------------
    # DECISION LOG
    # -----------------------------------------------------
    st.subheader("🧠 Algorithm Decision Log")

    for index, (source, destination, distance) in enumerate(
        decisions, 1
    ):
        st.write(
            f"**Step {index}:** {source} → {destination} "
            f"| Distance: {distance:.1f} km"
        )

    st.caption(
        "Dijkstra calculates shortest paths, and Greedy selects "
        "the nearest unvisited collection point. Road distances "
        "are illustrative prototype data."
    )

else:
    st.info(
        "Enter the collection details, select collection points, "
        "and click 'Optimize Route'."
    )