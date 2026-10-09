import numpy as np

def haversine_distance_km(lat1, lon1, lat2, lon2):
    """
    Computes great-circle distance between two points on Earth in kilometers.
    Handles numpy arrays or scalar floats.
    """
    R = 6371.0 # Earth radius in km

    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = np.sin(dlat / 2.0)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2.0)**2
    c = 2.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))

    return R * c

def calculate_distance_from_home_km(tx_lat, tx_lon, home_lat, home_lon):
    """Calculates physical distance from customer home address."""
    return haversine_distance_km(tx_lat, tx_lon, home_lat, home_lon)

def calculate_geo_distance_ip_gps_km(ip_lat, ip_lon, gps_lat, gps_lon):
    """Calculates discrepancy between IP-derived location and GPS coordinates."""
    return haversine_distance_km(ip_lat, ip_lon, gps_lat, gps_lon)
