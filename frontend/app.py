import streamlit as st
import requests
import os

st.set_page_config(layout="wide")

st.title("Photo Upload App - Database Status")

backend_url = os.environ.get("BACKEND_API_URL")
db_check_endpoint = "/api/db_check/"

if not backend_url:
    st.error("Error: BACKEND_API_URL environment variable is not set.")
    st.stop()

if not backend_url.startswith(("http://", "https://")):
    backend_url = f"https://{backend_url}"

### process photo

landmark_id = st.text_input("Enter the photo ID (e.g. landmark_photos/photo123.jpg)")

if st.button("Trigger Analysis"):
    if not landmark_id:
        st.warning("Please enter a photo ID.")
        st.stop()

    endpoint_url = f"{backend_url}/api/{landmark_id}/"

    st.write(f"Calling: `{endpoint_url}`")

    try:
        response = requests.get(endpoint_url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        st.error(f"HTTP Error: {errh}")
        st.stop()

    data = response.json()

    if data["status"] == "success":
        landmark = data["message"][0]
        description = landmark["description"]
        lat = landmark["locations"][0]["latitude"]
        lon = landmark["locations"][0]["longitude"]

        st.success(f"Landmark Detected: **{description}**")
        st.write(f"📍 Latitude: `{lat}`")
        st.write(f"📍 Longitude: `{lon}`")

        st.map(data={"lat": [lat], "lon": [lon]})
    else:
        st.error("Failed to detect landmark.")

###
### upload photo

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Selected Image", width=300)

    if st.button("Upload"):
        files = {"photo_id": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        response = requests.post(f"{backend_url}/api/upload_photo/", files=files)

        if response.status_code == 200:
            data = response.json()
            st.success(data["message"])
            st.image(f"{backend_url}{data['photo_url']}", caption="Uploaded Image", use_column_width=True)
        else:
            try:
                error_data = response.json()
                st.error(f"Upload failed: {error_data.get('errors') or error_data.get('message', 'Unknown error')}")
            except ValueError:
                st.error("Upload failed: Unable to parse error response.")
###
### get photo

landmark_id = st.number_input("Enter photo ID to view", min_value=1, step=1)

if landmark_id:
    # GET Request to fetch the photo
    if st.button("View Photo"):
        response = requests.get(f"{backend_url}/api/photo/{landmark_id}/")

        if response.status_code == 200:
            # Show image if successfully fetched
            st.image(response.content, caption="Fetched Photo", width=300)
        else:
            st.error(f"Error: {response.json().get('message', 'Unknown error')}")

###
### delete photo

if landmark_id:
    if st.button("Delete Photo"):
        # Get CSRF token from the session cookie
        csrf_token = os.environ.get('CSRF_TOKEN')  # Or get it dynamically from your session

        # Set the CSRF token header
        headers = {
            'X-CSRFToken': csrf_token
        }

        # DELETE Request to delete the photo with CSRF token
        response = requests.delete(f"{backend_url}/api/photo/{landmark_id}/")

        # Check if the response has JSON content
        try:
            response_data = response.json()
            if response.status_code == 200:
                # Show success message if deletion is successful
                st.success(f"Photo with ID {landmark_id} deleted successfully.")
            else:
                st.error(f"Error: {response_data.get('message', 'Unknown error')}")
        except ValueError:
            # If JSON decoding fails, handle it gracefully
            if response.status_code == 200:
                st.success(f"Photo with ID {landmark_id} deleted successfully. But sth wrong.")
            else:
                st.error(f"Error: {response.text}")  # Show raw text if no JSON returned

###

full_check_url = f"{backend_url.rstrip('/')}{db_check_endpoint}"

st.write(f"Checking backend database status at: `{full_check_url}`")

try:

    response = requests.get(full_check_url, timeout=15)
    response.raise_for_status()

    st.success("Successfully connected to the backend API.")

    try:
        data = response.json()
        st.subheader("Backend Response:")
        st.json(data)

        if data.get("status") == "ok":
            st.success(f"Database Status: OK - {data.get('message', '')}")
        else:
            st.error(f"Database Status: Error- {data.get('message', '')}")

    except requests.exceptions.JSONDecodeError:
        st.error("Backend response was not valid JSON.")
        st.text(response.text)

except requests.exceptions.ConnectionError as e:
    st.error(f"Connection Error: Could not connect to the backend API at {full_check_url}.")
    st.error(f"Details: {e}")
except requests.exceptions.Timeout:
    st.error(f"Timeout Error")
except requests.exceptions.RequestException as e:
    st.error(f"Request Error: An error occurred while contacting the backend API.")
    st.error(f"Details: {e}")
    if e.response is not None:
        st.error(f"Status Code: {e.response.status_code}")
        st.text(f"Response Text: {e.response.text}")

st.button("Re-check Status")
