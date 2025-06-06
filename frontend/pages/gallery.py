import streamlit as st
from api.client import get_user_photos, get_current_user, get_signed_url, get_photo_details, upload_photo, delete_photo, get_base_url
#import pydeck as pdk
import folium
from streamlit_folium import st_folium
from utils.session_state import get_session_state
from components.navbar import show_navbar, show_sidebar

def show_upload_form(token, state):
    st.subheader("Upload a new photo")
    uploaded_file = st.file_uploader("Choose a photo to upload", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        if st.button("Upload", key="upload_btn"):
            result = upload_photo(
                file_obj=uploaded_file,
                filename=uploaded_file.name,
                content_type=uploaded_file.type,
                token=token
            )
            if result.get("success"):
                st.success("Photo uploaded successfully!")
                state["show_upload_form"] = False
                st.rerun()
            else:
                st.error(f"Failed to upload: {result.get('status_code', '')} {result.get('error', '')}")

    if st.button("Cancel", key="cancel_upload"):
        state["show_upload_form"] = False
        st.rerun()

state=get_session_state()
st.set_page_config(page_title="My Gallery", layout="wide")
show_sidebar(state)
show_navbar(state)
st.title("🖼️ My Gallery")
if "auth_token" not in state:
    st.warning("You must be logged in to view your gallery.")
    st.stop()

token = state["auth_token"]
user_info = get_current_user(token)

if not user_info or "pk" not in user_info:
    st.warning("Invalid session. Please log in again.")
    st.stop()

user_id = user_info["pk"]

### Flag of form for uploading photo ###
if "show_upload_form" not in state:
    state["show_upload_form"] = False


# if st.button("📤 Upload New Photo"):
#     state["show_upload_form"] = True
col_upload, col_share, _ = st.columns([1, 1, 2])

with col_upload:
    if st.button("📤 Upload New Photo"):
        state["show_upload_form"] = True

### Failed to add sharing  ###
# with col_share:
#     public_url = f"https://landmark-app-streamlit-jcj4dqmava-lm.a.run.app/public_gallery?user_id={user_id*923+2}"
#     if st.button("🌐 Share My Gallery"):
#         st.success("Gallery shared!")
#         st.markdown(f"[🔗 Click here to view]( {public_url} )")
if state["show_upload_form"]:
    show_upload_form(token, state)
### Getting info about user photos ###
photos = get_user_photos(user_id, token)
if "error" in photos:
    st.error(f"Error loading photos: {photos['error']}")
    st.stop()

coordinates = []
photos_with_coords = []

for photo in photos:
    photo_id = photo.get("photo_id") or photo.get("id")
    filename = photo.get("original_filename")
    signed_url = get_signed_url(photo_id, token)
    
    details = get_photo_details(photo_id, token)
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

### Creating map with visited coordinates ###
if coordinates:
    st.subheader("🗺️ Visited Locations Map")

    col1, col2 = st.columns([3, 1])

    with col1:
        m = folium.Map(location=[coordinates[0]['lat'], coordinates[0]['lon']], zoom_start=1.5)
        for coord in coordinates:
            folium.Marker(
                location=[coord['lat'], coord['lon']],
                #popup=coord['name'],
                tooltip=coord['name'],
                icon=folium.Icon(color="red", icon="camera", prefix="fa")
            ).add_to(m)

        map_data = st_folium(m, width=700, height=500)

    with col2:
        clicked = map_data.get("last_object_clicked", None)

        if clicked:
            lat_clicked = clicked.get("lat")
            lon_clicked = clicked.get("lng")

            matched_photo = next(
                (c for c in coordinates if c['lat'] == lat_clicked and c['lon'] == lon_clicked),
                None
            )
            if matched_photo:
                photo_id_clicked = matched_photo['photo_id']
                photo_obj = next(
                    (p for p in photos_with_coords if p["photo_id"] == photo_id_clicked),
                    None
                )
                if photo_obj:
                    st.write(f"Photo of: {matched_photo['name']}")
                    st.image(photo_obj['signed_url'], use_container_width=True)

                if st.button("ℹ️ View Details"):
                    st.query_params = {"photo_id": [photo_id_clicked]}
                    st.switch_page("pages/photo_details.py")
else:
    st.info("No geolocation data available for your photos yet.")
st.subheader("📷 My Photos")

for photo in photos_with_coords:
    cols = st.columns([3, 2]) 

    with cols[0]:
        if photo["signed_url"]:
            st.image(photo["signed_url"], use_container_width=True)
        else:
            st.write(f"❌ No image for {photo['filename']}")

    with cols[1]:
        if photo["landmark"]:
            st.markdown(f"🏛️ **Landmark:** {photo['landmark'].get('detected_landmark_name', 'N/A')}")
            st.markdown(f"📍 {photo['landmark'].get('formatted_address', 'N/A')}")
        else:
            st.markdown("No landmark data available")

        if st.button(f"ℹ️ View Details", key=f"details_{photo['photo_id']}"):
            st.query_params = {"photo_id": [photo['photo_id']]}
            st.switch_page("pages/photo_details.py")

        if st.button(f"🗑️ Delete Photo", key=f"delete_{photo['photo_id']}"):
            result = delete_photo(photo['photo_id'], token)
            if result.get("success"):
                st.success("Photo deleted successfully.")
                #st.query_params = {}
                st.rerun()
            else:
                st.error(f"Failed to delete photo: {result.get('error', 'Unknown error')}")
