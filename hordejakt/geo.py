"""Spherical helpers. Angles in degrees, distances in km unless stated."""
import numpy as np

R_EARTH = 6371.0088


def haversine(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = p2 - p1
    dl = np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R_EARTH * np.arcsin(np.minimum(1.0, np.sqrt(a)))


def bearing(lat1, lon1, lat2, lon2):
    """Initial great-circle bearing from point 1 to point 2, 0..360."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dl = np.radians(np.asarray(lon2) - np.asarray(lon1))
    y = np.sin(dl) * np.cos(p2)
    x = np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl)
    return (np.degrees(np.arctan2(y, x)) + 360.0) % 360.0


def destination(lat, lon, brg, km):
    d = np.asarray(km) / R_EARTH
    t = np.radians(brg)
    p1, l1 = np.radians(lat), np.radians(lon)
    p2 = np.arcsin(np.sin(p1) * np.cos(d) + np.cos(p1) * np.sin(d) * np.cos(t))
    l2 = l1 + np.arctan2(np.sin(t) * np.sin(d) * np.cos(p1), np.cos(d) - np.sin(p1) * np.sin(p2))
    return np.degrees(p2), np.degrees(l2)


def angdiff(a, b):
    """Smallest absolute difference between two bearings, 0..180."""
    return np.abs((np.asarray(a) - np.asarray(b) + 180.0) % 360.0 - 180.0)


def elevation_angle(ground_km, height_m_above_observer):
    """Elevation angle (deg) of a target at horizontal distance ground_km and
    height above the observer, with a simple 4/3-earth refraction correction."""
    h = np.asarray(height_m_above_observer) / 1000.0
    g = np.maximum(np.asarray(ground_km), 1e-6)
    drop = g ** 2 / (2 * R_EARTH * 4 / 3)
    return np.degrees(np.arctan2(h - drop, g))


def slant_km(ground_km, height_m_above_observer):
    return np.hypot(np.asarray(ground_km), np.asarray(height_m_above_observer) / 1000.0)


FT = 0.3048
