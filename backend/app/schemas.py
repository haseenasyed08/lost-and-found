import os

def report_out(r, owner=False):
    if r is None:
        return None
    place_name = r.place.name if hasattr(r, 'place') and r.place else 'Campus'
    lat = r.place.latitude if hasattr(r, 'place') and r.place else 12.9
    lon = r.place.longitude if hasattr(r, 'place') and r.place else 77.5
    
    images = []
    if hasattr(r, 'images') and r.images:
        for img in r.images:
            images.append('/files/public/' + os.path.basename(img.public_path))
            
    d = {
        'id': r.id,
        'type': r.type,
        'category': r.category,
        'group': r.group,
        'brand': r.brand,
        'color': r.color,
        'description': r.description,
        'place': place_name,
        'place_id': r.place_id,
        'latitude': lat,
        'longitude': lon,
        'event_time': r.event_time.isoformat() if hasattr(r.event_time, 'isoformat') else str(r.event_time),
        'status': r.status,
        'images': images,
        'created_at': r.created_at.isoformat() if hasattr(r.created_at, 'isoformat') else str(r.created_at),
    }
    if owner:
        d['time_window_hours'] = r.time_window_hours
    return d
