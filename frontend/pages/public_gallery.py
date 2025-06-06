# pages/public_gallery.py
import streamlit as st
from api.client import get_user_photos, get_signed_url, get_photo_details
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Public Gallery", layout="wide")
st.title("🌍 Public Photo Gallery")

user_id = st.query_params["user_id"]
user_id=int((int(user_id) - 2) / 923)
if not user_id:
    st.error("No user ID provided.")
    st.stop()

photos = get_user_photos(user_id, None)
if "error" in photos:
    st.error(f"Error loading photos: {photos['error']}")
    st.stop()

coordinates = []
photos_with_coords = []

for photo in photos:
    photo_id = photo.get("photo_id") or photo.get("id")
    filename = photo.get("original_filename")
    signed_url = get_signed_url(photo_id, None)
    
    details = get_photo_details(photo_id, None)
    landmark = details.get("landmark_data") if details else None

    if landmark:
        lat = landmark.get("latitude")
        lon = landmark.get("longitude")
        if lat and lon:
            coordinates.append({
                "lat": float(lat),
                "lon": float(lon),
                "photo_id": photo_id,
                "name": landmark.get("detected_landmark_name")
            })

    photos_with_coords.append({
        "photo_id": photo_id,
        "filename": filename,
        "signed_url": signed_url,
        "landmark": landmark,
        "details": details
    })

if coordinates:
    st.subheader("🗺️ Visited Locations Map")
    m = folium.Map(location=[coordinates[0]['lat'], coordinates[0]['lon']], zoom_start=1.5)
    for coord in coordinates:
        folium.Marker(
            location=[coord['lat'], coord['lon']],
            tooltip=coord['name'],
            icon=folium.Icon(color="blue", icon="camera", prefix="fa")
        ).add_to(m)
    map_data = st_folium(m, width=700, height=500)
else:
    st.info("No geolocation data available.")

# Photo grid (read-only)
st.subheader("📷 Photos")
for photo in photos_with_coords:
    cols = st.columns([3, 2])
    with cols[0]:
        st.image(photo["signed_url"], use_container_width=True)
    with cols[1]:
        if photo["landmark"]:
            st.markdown(f"🏛️ **Landmark:** {photo['landmark'].get('detected_landmark_name', 'N/A')}")
            st.markdown(f"📍 {photo['landmark'].get('formatted_address', 'N/A')}")
        else:
            st.markdown("No landmark data.")