# ruff: noqa
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

import json
from pathlib import Path
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.load_memory_tool import load_memory_tool
from google.adk.tools.preload_memory_tool import preload_memory_tool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.tools import (
    add_plant_to_catalog,
    calculate_soil_and_fertilizer,
    check_watering_schedule,
    find_nearby_places,
    generate_plant_image,
    generate_plant_video,
    geocode_address,
    get_local_plant_environment,
    lookup_plant_care,
    search_plant_catalog,
)


# Hardcoded GCP Project ID and Agent Engine Memory Bank ID
GCP_PROJECT_ID = "qwiklabs-gcp-02-e42345eb957f"
GCP_REGION = "us-east1"
MEMORY_BANK_ID = "1736425728397803520"

# Configure Memory Bank service for future redeployments
memory_service = VertexAiMemoryBankService(
    project=GCP_PROJECT_ID,
    location=GCP_REGION,
    agent_engine_id=MEMORY_BANK_ID,
)

# Configure Agent Platform sandbox code execution using deployment_metadata.json
code_executor = None
metadata_file = Path("deployment_metadata.json")
if metadata_file.exists():
    try:
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
            sandbox_resource = metadata.get("sandbox_resource_name")
            agent_engine_resource = metadata.get("remote_agent_runtime_id")
            if sandbox_resource:
                code_executor = AgentEngineSandboxCodeExecutor(
                    sandbox_resource_name=sandbox_resource
                )
            elif agent_engine_resource:
                code_executor = AgentEngineSandboxCodeExecutor(
                    agent_engine_resource_name=agent_engine_resource
                )
    except Exception as e:
        print(f"Warning: Failed to initialize AgentEngineSandboxCodeExecutor: {e}")

# Build A2UI system prompt (v0.8) with Basic Catalog
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are FloraCare, an expert plant care and greenhouse assistant. "
        "You assist users in managing house plants, checking watering schedules, searching the plant catalog, "
        "calculating soil volume & fertilizer requirements, fetching live local weather/humidity data, "
        "geocoding addresses, finding nearby plant nurseries/garden centers, and generating plant visuals."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects. "
        "IMPORTANT MEMORY INSTRUCTIONS: Always remember and load user plant allergies, skin/pollen sensitivities, "
        "and household pet safety constraints across sessions. Whenever recommending, searching for, or advising on house plants, "
        "check the user's remembered allergies and explicitly exclude or warn about plants that cause allergic reactions or toxicity."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        search_plant_catalog,
        lookup_plant_care,
        check_watering_schedule,
        add_plant_to_catalog,
        calculate_soil_and_fertilizer,
        get_local_plant_environment,
        geocode_address,
        find_nearby_places,
        generate_plant_image,
        generate_plant_video,
        load_memory_tool,
        preload_memory_tool,
    ],
    code_executor=code_executor,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

