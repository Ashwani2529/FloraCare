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

"""Seed script to populate Firestore 'plants' collection for FloraCare."""

from google.cloud import firestore

# Hardcode project ID explicitly
GCP_PROJECT_ID = "qwiklabs-gcp-02-e42345eb957f"
COLLECTION_NAME = "plants"

INITIAL_PLANTS = [
    {
        "id": "monstera-deliciosa",
        "name": "Monstera Deliciosa",
        "scientific_name": "Monstera deliciosa",
        "care_level": "Easy to Moderate",
        "light_requirement": "Medium to bright indirect light",
        "watering_interval_days": 7,
        "description": "Popular tropical houseplant with iconic fenestrated (split) leaves. Thrives in warm, humid indoor spaces.",
    },
    {
        "id": "snake-plant",
        "name": "Snake Plant",
        "scientific_name": "Sansevieria trifasciata",
        "care_level": "Easy",
        "light_requirement": "Low to bright indirect light",
        "watering_interval_days": 14,
        "description": "Extremely resilient succulent with upright sword-like leaves. Excellent for low-light rooms and beginner plant parents.",
    },
    {
        "id": "peace-lily",
        "name": "Peace Lily",
        "scientific_name": "Spathiphyllum wallisii",
        "care_level": "Moderate",
        "light_requirement": "Medium indirect light",
        "watering_interval_days": 7,
        "description": "Lush foliage plant with elegant white blooms. Visually flags when thirsty by gently drooping its leaves.",
    },
    {
        "id": "pothos-golden",
        "name": "Golden Pothos",
        "scientific_name": "Epipremnum aureum",
        "care_level": "Easy",
        "light_requirement": "Low to bright indirect light",
        "watering_interval_days": 10,
        "description": "Fast-growing vine with heart-shaped variegated leaves. Great for hanging baskets or trailing shelf displays.",
    },
    {
        "id": "fiddle-leaf-fig",
        "name": "Fiddle Leaf Fig",
        "scientific_name": "Ficus lyrata",
        "care_level": "Hard",
        "light_requirement": "Bright indirect light",
        "watering_interval_days": 7,
        "description": "Dramatic indoor tree with large violin-shaped leaves. Prefers consistent bright light and steady watering habits.",
    },
]


def seed_database():
    """Seeds initial plant records into Firestore."""
    print(f"Connecting to Firestore for project '{GCP_PROJECT_ID}'...")
    db = firestore.Client(project=GCP_PROJECT_ID)
    collection_ref = db.collection(COLLECTION_NAME)

    print(f"Seeding '{COLLECTION_NAME}' collection...")
    for plant in INITIAL_PLANTS:
        plant_id = plant["id"]
        doc_data = {k: v for k, v in plant.items() if k != "id"}
        doc_ref = collection_ref.document(plant_id)
        doc_ref.set(doc_data, merge=True)
        print(f"  ✓ Seeded plant: {plant['name']} ({plant_id})")

    print(f"\nSuccessfully seeded {len(INITIAL_PLANTS)} plants into Firestore 'plants' collection!")


if __name__ == "__main__":
    seed_database()
