# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Firestore-backed function tools for FloraCare Plant Care Assistant."""

from typing import Any
from google.cloud import firestore
from google.adk.tools import ToolContext

# Hardcode project ID and GCS bucket explicitly as required.
# Never derive from GOOGLE_CLOUD_PROJECT or google.auth.default() as those return project number.
GCP_PROJECT_ID = "qwiklabs-gcp-02-e42345eb957f"
COLLECTION_NAME = "plants"
GCS_BUCKET_NAME = "floracare-assets-qwiklabs-gcp-02-e42345eb957f"

db = firestore.Client(project=GCP_PROJECT_ID)


def search_plant_catalog(query: str = "") -> list[dict[str, Any]]:
    """Search or list plants in the FloraCare plant catalog.

    Args:
        query: Optional search keyword to filter plants by name or care level.
               Leave empty to return all catalog plants.

    Returns:
        A list of plant dictionary records matching the query.
    """
    plants_ref = db.collection(COLLECTION_NAME)
    docs = plants_ref.stream()

    results = []
    q_clean = query.strip().lower()

    for doc in docs:
        plant_data = doc.to_dict()
        plant_data["id"] = doc.id

        if not q_clean:
            results.append(plant_data)
        else:
            # Check query against name, scientific name, or care level
            name = str(plant_data.get("name", "")).lower()
            scientific = str(plant_data.get("scientific_name", "")).lower()
            care_level = str(plant_data.get("care_level", "")).lower()

            if q_clean in name or q_clean in scientific or q_clean in care_level:
                results.append(plant_data)

    return results


def lookup_plant_care(plant_name: str) -> dict[str, Any]:
    """Retrieve detailed care requirements for a specific house plant from the catalog.

    Args:
        plant_name: The name or ID of the plant (e.g., 'Monstera Deliciosa', 'snake-plant').

    Returns:
        A dictionary containing plant care details or an error message if not found.
    """
    clean_name = plant_name.strip().lower()
    doc_id = clean_name.replace(" ", "-")

    # Direct document lookup
    doc = db.collection(COLLECTION_NAME).document(doc_id).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data

    # Search by name match
    all_plants = search_plant_catalog(clean_name)
    if all_plants:
        return all_plants[0]

    return {
        "error": f"Plant '{plant_name}' was not found in the catalog.",
        "suggestion": "Try searching the catalog using search_plant_catalog() to see available plants."
    }


def check_watering_schedule(plant_name: str, days_since_last_watered: int) -> str:
    """Check whether a plant needs watering based on its care requirements and days since last watered.

    Args:
        plant_name: The name of the plant (e.g., 'Monstera Deliciosa', 'Peace Lily').
        days_since_last_watered: Number of days since the plant was last watered.

    Returns:
        A human-readable recommendation on whether to water the plant now or wait.
    """
    care_info = lookup_plant_care(plant_name)
    if "error" in care_info:
        return f"Could not determine watering schedule: {care_info['error']}"

    interval = care_info.get("watering_interval_days", 7)
    name = care_info.get("name", plant_name)
    light = care_info.get("light_requirement", "Medium indirect light")

    if days_since_last_watered >= interval:
        overdue_by = days_since_last_watered - interval
        if overdue_by == 0:
            return f"It is time to water your {name}! Recommended watering interval is every {interval} days."
        return f"Your {name} is overdue for watering by {overdue_by} day(s) (last watered {days_since_last_watered} days ago, ideal interval is {interval} days under {light})."
    
    days_remaining = interval - days_since_last_watered
    return f"Your {name} does not need water yet. Wait approximately {days_remaining} more day(s) before watering again (recommended interval: every {interval} days)."


def add_plant_to_catalog(
    plant_id: str,
    name: str,
    scientific_name: str,
    care_level: str,
    light_requirement: str,
    watering_interval_days: int,
    description: str,
) -> str:
    """Add a new plant to the FloraCare catalog or update an existing plant entry in Firestore.

    Args:
        plant_id: Unique slug identifier for the plant (e.g., 'pothos-golden').
        name: Common name of the plant.
        scientific_name: Botanical / scientific name.
        care_level: Care difficulty level ('Easy', 'Moderate', 'Hard').
        light_requirement: Ideal lighting conditions.
        watering_interval_days: Standard days between watering.
        description: Brief care notes or description.

    Returns:
        A confirmation message indicating successful store/update.
    """
    clean_id = plant_id.strip().lower().replace(" ", "-")
    doc_ref = db.collection(COLLECTION_NAME).document(clean_id)

    plant_data = {
        "name": name.strip(),
        "scientific_name": scientific_name.strip(),
        "care_level": care_level.strip(),
        "light_requirement": light_requirement.strip(),
        "watering_interval_days": watering_interval_days,
        "description": description.strip(),
    }

    doc_ref.set(plant_data, merge=True)
    return f"Successfully saved plant '{name}' ({clean_id}) to the FloraCare Firestore catalog."


def calculate_soil_and_fertilizer(
    pot_diameter_inches: float,
    pot_height_inches: float,
    fertilizer_strength: str = "standard",
) -> dict[str, Any]:
    """Calculate required soil volume for a round pot and recommended fertilizer dilution ratio.

    Args:
        pot_diameter_inches: Top diameter of the round pot in inches.
        pot_height_inches: Height of the pot in inches.
        fertilizer_strength: Dilution strength target ('mild', 'standard', 'strong').

    Returns:
        A dictionary with soil volume calculations (liters, dry quarts) and fertilizer guidance.
    """
    import math

    radius = pot_diameter_inches / 2.0
    volume_cu_in = math.pi * (radius**2) * pot_height_inches
    volume_liters = round(volume_cu_in * 0.0163871, 2)
    volume_quarts = round(volume_cu_in * 0.017316, 2)

    strength_map = {
        "mild": 1.0,
        "standard": 2.5,
        "strong": 5.0,
    }
    ml_per_liter = strength_map.get(fertilizer_strength.lower(), 2.5)

    return {
        "pot_dimensions": f"{pot_diameter_inches}\" diameter x {pot_height_inches}\" height",
        "estimated_soil_volume_liters": volume_liters,
        "estimated_soil_volume_quarts": volume_quarts,
        "fertilizer_strength_target": fertilizer_strength,
        "fertilizer_dilution_recommendation": f"{ml_per_liter} mL of liquid fertilizer per 1 Liter (approx. {round(ml_per_liter * 3.785, 1)} mL per gallon) of water.",
        "note": "Mix fertilizer into water before applying. Water thoroughly until runoff escapes drainage holes.",
    }


def get_local_plant_environment(location: str) -> dict[str, Any]:
    """Fetch real-time ambient weather and humidity data for a city using Open-Meteo public API.
    Used to assess environmental conditions (temperature, humidity) for indoor/outdoor house plants.

    Args:
        location: City or location name (e.g. 'San Francisco', 'Miami', 'Tokyo').

    Returns:
        A dictionary containing live weather, relative humidity, temperature, and plant care humidity advice.
    """
    import json
    import os
    import urllib.parse
    import urllib.request

    # Optional API key support from environment variable if configured
    api_key = os.environ.get("WEATHER_API_KEY")

    try:
        encoded_loc = urllib.parse.quote(location)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_loc}&count=1"
        req = urllib.request.Request(
            geo_url, headers={"User-Agent": "FloraCare/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            geo_data = json.loads(response.read().decode("utf-8"))

        if not geo_data.get("results"):
            return {
                "error": f"Could not find coordinates for location '{location}'."
            }

        place = geo_data["results"][0]
        lat, lon = place["latitude"], place["longitude"]
        city_name = place.get("name", location)
        country = place.get("country", "")

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,rain"
        )
        req_w = urllib.request.Request(
            weather_url, headers={"User-Agent": "FloraCare/1.0"}
        )
        with urllib.request.urlopen(req_w, timeout=5) as resp_w:
            w_data = json.loads(resp_w.read().decode("utf-8"))

        current = w_data.get("current", {})
        temp_c = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        temp_f = round(temp_c * 9 / 5 + 32, 1) if temp_c is not None else None

        humidity_advice = "Optimal for most tropical house plants (50-70%)."
        if humidity is not None:
            if humidity < 40:
                humidity_advice = "Low humidity alert! Consider misting tropical plants or using a pebble tray/humidifier."
            elif humidity > 75:
                humidity_advice = "High humidity! Great for ferns and tropicals, but ensure good airflow to prevent fungal spots."

        return {
            "location": f"{city_name}, {country}".strip(", "),
            "temperature_celsius": temp_c,
            "temperature_fahrenheit": temp_f,
            "relative_humidity_percent": humidity,
            "humidity_care_advice": humidity_advice,
            "api_provider": "Open-Meteo Public Weather API (Free)",
        }
    except Exception as e:
        return {
            "error": f"Failed to fetch environmental data for '{location}': {str(e)}"
        }


def geocode_address(address: str) -> dict[str, Any]:
    """Turn a street address or location name into geographic coordinates using Google Maps Geocoding API.

    Args:
        address: Freeform address or location string (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        A dictionary containing formatted address, latitude, and longitude.
    """
    import json
    import os
    import urllib.parse
    import urllib.request
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY is not configured in .env."}

    encoded_addr = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_addr}&key={api_key}"

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "FloraCare/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("status") != "OK" or not data.get("results"):
            return {
                "error": f"Geocoding failed for '{address}': {data.get('status', 'NO_RESULTS')}"
            }

        first = data["results"][0]
        loc = first["geometry"]["location"]
        return {
            "name": address,
            "address": first.get("formatted_address"),
            "location": {
                "latitude": loc["lat"],
                "longitude": loc["lng"],
            },
        }
    except Exception as e:
        return {"error": f"Failed to geocode address '{address}': {str(e)}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "garden_center",
    radius_meters: float = 5000.0,
) -> dict[str, Any]:
    """Find nearby places of a given type (e.g., 'garden_center', 'florist', 'park') near coordinates using Google Maps Places API (New).

    Args:
        latitude: Center latitude coordinate.
        longitude: Center longitude coordinate.
        place_type: Google Maps place type (e.g., 'garden_center', 'florist', 'store', 'park').
        radius_meters: Search radius in meters (default 5000.0).

    Returns:
        A list of nearby places with name, address, and location coordinates.
    """
    import json
    import os
    import urllib.request
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY is not configured in .env."}

    url = "https://places.googleapis.com/v1/places:searchNearby"
    payload = {
        "includedTypes": [place_type],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": latitude, "longitude": longitude},
                "radius": radius_meters,
            }
        },
    }

    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }

    try:
        req = urllib.request.Request(
            url, data=body, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        raw_places = data.get("places", [])
        results = []
        for p in raw_places:
            results.append(
                {
                    "name": p.get("displayName", {}).get("text", "Unknown"),
                    "address": p.get("formattedAddress", "N/A"),
                    "location": p.get("location", {"latitude": latitude, "longitude": longitude}),
                }
            )

        return {
            "place_type": place_type,
            "center": {"latitude": latitude, "longitude": longitude},
            "count": len(results),
            "places": results,
        }
    except Exception as e:
        return {"error": f"Failed to search nearby places: {str(e)}"}


def generate_plant_image(
    prompt: str,
    tool_context: ToolContext = None,
) -> dict[str, Any]:
    """Generate a realistic image for a plant variety or house plant room arrangement using gemini-3.1-flash-lite-image in global region.
    Saves the image artifact to the ADK session and uploads it directly to the public GCS bucket.

    Args:
        prompt: Detailed description of the plant or arrangement to visualize (e.g. 'A mature Monstera Deliciosa in a terracotta pot').
        tool_context: ADK ToolContext injected by the agent framework.

    Returns:
        A dictionary containing the public GCS URL of the generated image and status.
    """
    import uuid
    import google.genai as genai
    from google.genai import types
    from google.cloud import storage

    client = genai.Client(
        vertexai=True,
        location="global",
        project=GCP_PROJECT_ID,
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )

        img_bytes = None
        mime_type = "image/jpeg"

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    img_bytes = part.inline_data.data
                    if part.inline_data.mime_type:
                        mime_type = part.inline_data.mime_type
                    break

        if not img_bytes:
            return {"error": f"Failed to generate image for prompt: '{prompt}'."}

        filename = f"plant_{uuid.uuid4().hex[:8]}.jpg"

        # 1. Save artifact using tool_context if present (shows in Playground Artifacts panel)
        if tool_context is not None:
            artifact_part = types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload image bytes directly to public Cloud Storage bucket
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(img_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "prompt": prompt,
            "filename": filename,
            "public_url": public_url,
        }
    except Exception as e:
        return {"error": f"Image generation failed: {str(e)}"}


def generate_plant_video(
    prompt: str,
    tool_context: ToolContext = None,
) -> dict[str, Any]:
    """Generate a short video for a house plant, greenhouse scene, or plant care technique using gemini-omni-flash-preview in global region.
    Saves the video artifact to the ADK session and uploads it directly to the public GCS bucket.

    Args:
        prompt: Detailed description of the plant or care scene to visualize as a video (e.g. 'A short video of a Monstera Deliciosa unfolding a new leaf').
        tool_context: ADK ToolContext injected by the agent framework.

    Returns:
        A dictionary containing the public GCS URL of the generated video and status.
    """
    import base64
    import uuid
    import google.genai as genai
    from google.genai import types
    from google.cloud import storage

    client = genai.Client(
        vertexai=True,
        location="global",
        project=GCP_PROJECT_ID,
    )

    try:
        response = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
            generation_config={"response_modalities": ["VIDEO"]},
        )

        video_bytes = None
        mime_type = "video/mp4"

        video_obj = getattr(response, "output_video", None)
        if video_obj and hasattr(video_obj, "data") and video_obj.data:
            raw_data = video_obj.data
            if getattr(video_obj, "mime_type", None):
                mime_type = video_obj.mime_type
            if isinstance(raw_data, str):
                video_bytes = base64.b64decode(raw_data)
            else:
                video_bytes = raw_data

        if not video_bytes and hasattr(response, "outputs") and response.outputs:
            for out in response.outputs:
                if getattr(out, "type", None) == "video" or "video" in str(getattr(out, "mime_type", "")):
                    raw_data = getattr(out, "data", None) or getattr(out, "bytes", None)
                    if raw_data:
                        if getattr(out, "mime_type", None):
                            mime_type = out.mime_type
                        if isinstance(raw_data, str):
                            video_bytes = base64.b64decode(raw_data)
                        else:
                            video_bytes = raw_data
                        break

        if not video_bytes:
            return {"error": f"Failed to generate video for prompt: '{prompt}'."}

        filename = f"plant_video_{uuid.uuid4().hex[:8]}.mp4"

        # 1. Save artifact using tool_context if present (shows in Playground Artifacts panel)
        if tool_context is not None:
            artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
            tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload video bytes directly to public Cloud Storage bucket
        storage_client = storage.Client(project=GCP_PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

        return {
            "status": "success",
            "prompt": prompt,
            "filename": filename,
            "public_url": public_url,
        }
    except Exception as e:
        return {"error": f"Video generation failed: {str(e)}"}





