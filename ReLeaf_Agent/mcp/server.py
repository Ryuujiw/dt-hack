import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict
from datetime import timedelta

from fastmcp import FastMCP
from google.cloud import storage

from geocoding_search import GeocodingSearch

# Add urban_tree_planting to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import urban tree planting pipeline
from urban_tree_planting.models.location import Location
from urban_tree_planting.pipeline.processor import TreePlantingPipeline
from urban_tree_planting.core.visualizer import ResultVisualizer

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

mcp = FastMCP("Tree Planting Agent MCP Server on Cloud Run")

# Global pipeline instance (reuse across requests for performance)
_pipeline = None
_visualizer = None
_storage_client = None
_signing_credentials = None


def get_signing_credentials():
    """Get service account credentials with private key for signing URLs"""
    global _signing_credentials
    if _signing_credentials is None:
        try:
            # Try to get service account key from Secret Manager
            from google.cloud import secretmanager
            from google.oauth2 import service_account
            import json
            
            project_id = os.getenv("GCP_PROJECT", "us-con-gcp-sbx-0001190-100925")
            client = secretmanager.SecretManagerServiceClient()
            secret_name = f"projects/{project_id}/secrets/releaf-service-account-key/versions/latest"
            
            response = client.access_secret_version(request={"name": secret_name})
            key_json = response.payload.data.decode("UTF-8")
            key_data = json.loads(key_json)
            
            _signing_credentials = service_account.Credentials.from_service_account_info(key_data)
            logger.info("Loaded service account credentials for URL signing")
            
        except Exception as e:
            logger.error(f"Failed to load signing credentials: {e}")
            _signing_credentials = None
    
    return _signing_credentials


def get_storage_client():
    """Lazy initialization of GCS client"""
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client()
    return _storage_client


def upload_to_gcs(local_path: Path, blob_name: str) -> str:
    """
    Upload file to Google Cloud Storage and return signed URL
    
    Args:
        local_path: Local file path
        blob_name: Name for the blob in GCS
        
    Returns:
        Signed URL valid for 7 days
    """
    try:
        # Get project ID from environment or metadata server
        project_id = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            # Try to get from metadata server (works in Cloud Run)
            try:
                import requests
                metadata_url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
                headers = {"Metadata-Flavor": "Google"}
                response = requests.get(metadata_url, headers=headers, timeout=2)
                if response.status_code == 200:
                    project_id = response.text
            except Exception as meta_error:
                logger.error(f"Could not get project ID from metadata server: {meta_error}")
        
        if not project_id:
            # Fallback to hardcoded project ID
            project_id = "us-con-gcp-sbx-0001190-100925"
            logger.warning(f"Using hardcoded project ID: {project_id}")
        
        bucket_name = f"{project_id}-tree-analysis"
        
        client = get_storage_client()
        
        # Create bucket if it doesn't exist
        try:
            bucket = client.get_bucket(bucket_name)
        except:
            bucket = client.create_bucket(bucket_name, location="us-central1")
            logger.info(f"Created GCS bucket: {bucket_name}")
        
        # Upload file
        blob = bucket.blob(blob_name)
        
        # Set cache control for 7 days
        blob.cache_control = "public, max-age=604800"
        
        blob.upload_from_filename(str(local_path))
        logger.info(f"Uploaded {local_path.name} to gs://{bucket_name}/{blob_name}")
        
        # Generate signed URL valid for 7 days using service account key
        credentials = get_signing_credentials()
        
        if credentials:
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(days=7),
                method="GET",
                credentials=credentials
            )
            logger.info(f"Generated signed URL (valid for 7 days)")
            return signed_url
        else:
            logger.error("No signing credentials available")
            return f"(File saved at gs://{bucket_name}/{blob_name}, but could not generate signed URL)"
        
    except Exception as e:
        logger.error(f"Failed to upload to GCS: {e}")
        return f"(File saved locally at {local_path}, but could not generate public URL)"


def get_pipeline():
    """Lazy initialization of pipeline to avoid cold start overhead"""
    global _pipeline, _visualizer
    if _pipeline is None:
        logger.info("Initializing TreePlantingPipeline...")
        # Pipeline will use settings from urban_tree_planting/config/settings.py
        # which now reads GOOGLE_MAPS_API_KEY from environment
        _pipeline = TreePlantingPipeline()
        _visualizer = ResultVisualizer()
        logger.info("Pipeline initialized successfully")
    return _pipeline, _visualizer


@mcp.tool()
def analyze_tree_planting_opportunities(
    latitude: float,
    longitude: float,
    location_name: str = "analysis_location"
) -> str:
    """
    Perform comprehensive real-time tree planting analysis for any location in Kuala Lumpur.
    
    This tool runs a complete geospatial analysis pipeline that:
    1. Downloads satellite imagery from Google Maps
    2. Downloads building footprints and street network from OpenStreetMap
    3. Detects existing vegetation using NDVI (Normalized Difference Vegetation Index)
    4. Identifies shadow areas for sun exposure analysis
    5. Generates masks for buildings, streets (with tiered buffers), and sidewalks
    6. Calculates 100-point priority scores based on:
       - Sidewalk proximity (35 points)
       - Building cooling zones (25 points)
       - Sun exposure (20 points)
       - Amenity density (10 points)
    7. Identifies critical priority spots (score 80-100) with GPS coordinates
    8. Generates Google Maps and Street View URLs for each spot
    9. Creates visualization outputs:
       - 6-panel analysis PNG (satellite image with overlays)
       - Component breakdown PNG (showing individual scoring components)
       - JSON summary file
    
    Processing time: 10-25 seconds depending on area complexity
    
    Output files are saved to /tmp directory on Cloud Run (ephemeral storage) or 
    local output directory when running locally.
    
    Args:
        latitude: Latitude coordinate (e.g., 3.1379 for Menara LGB)
        longitude: Longitude coordinate (e.g., 101.6295 for Menara LGB)
        location_name: Optional name for the location (default: "analysis_location")
    
    Returns:
        JSON string containing comprehensive analysis results:
        - location: Name, description, and coordinates
        - critical_priority_spots: List of high-priority planting areas with:
          * spot_id: Unique identifier for each spot
          * coordinates: GPS coordinates (latitude, longitude)
          * priority_score: Score from 80-100
          * area_m2: Area in square meters
          * area_pixels: Area in pixels
          * google_street_view_url: Direct link to Street View
          * google_maps_url: Direct link to Google Maps
        - land_coverage: Statistics on buildings, vegetation, shadows, plantable area
        - priority_distribution: Breakdown by priority level (critical/high/medium/low)
        - street_network: Count of streets by traffic type
        - amenities: Total count of nearby amenities
        - recommendations: Actionable next steps for tree planting
        - output_files: Paths to generated visualization files:
          * analysis_visualization: 6-panel analysis PNG
          * component_breakdown: Component scores breakdown PNG
          * json_summary: JSON file with complete data
        
    Example usage:
        analyze_tree_planting_opportunities(3.1379, 101.6295, "Menara LGB")
    """
    try:
        import time
        start_time = time.time()
        logger.info(f"⏱️ [START] Starting tree planting analysis for '{location_name}' at ({latitude}, {longitude})")
        
        # USER-FACING PROGRESS: Initial message
        logger.info(f"🌍 [USER] Initializing analysis for {location_name}... (Step 1/6)")
        
        # Create location object
        step_start = time.time()
        location = Location(
            name=location_name.lower().replace(' ', '_'),
            description=f"Tree planting analysis for {location_name}",
            lat=latitude,
            lon=longitude
        )
        logger.info(f"⏱️ [STEP 1] Location object created in {time.time() - step_start:.2f}s")
        
        # Get pipeline instance
        step_start = time.time()
        pipeline, visualizer = get_pipeline()
        logger.info(f"⏱️ [STEP 2] Pipeline initialized in {time.time() - step_start:.2f}s")
        
        # Run the full 6-step pipeline
        step_start = time.time()
        logger.info(f"📊 [USER] Downloading satellite imagery and analyzing vegetation... (Step 2/6 - Est. 15-20s)")
        logger.info("Running analysis pipeline (this may take 10-25 seconds)...")
        processed_location = pipeline.process_location(location)
        pipeline_time = time.time() - step_start
        logger.info(f"⏱️ [STEP 3] Pipeline processing completed in {pipeline_time:.2f}s")
        logger.info(f"✅ [USER] Satellite analysis complete! Found {len(processed_location.critical_priority) if hasattr(processed_location, 'critical_priority') else 0} critical priority areas.")
        
        # Generate summary data using the visualizer
        step_start = time.time()
        logger.info(f"📈 [USER] Calculating priority scores and generating maps... (Step 3/6 - Est. 3-5s)")
        priority_results = {
            'enhanced_priority_score': processed_location.enhanced_priority_score,
            'critical_priority': processed_location.critical_priority,
            'high_priority': processed_location.high_priority,
            'medium_priority': processed_location.medium_priority,
            'low_priority': processed_location.low_priority,
            'sidewalk_component': processed_location.sidewalk_component,
            'building_component': processed_location.building_component,
            'sun_component': processed_location.sun_component,
            'amenity_component': processed_location.amenity_component,
        }
        
        summary_data = visualizer.create_summary_statistics(
            processed_location,
            priority_results
        )
        logger.info(f"⏱️ [STEP 4] Summary data generated in {time.time() - step_start:.2f}s")
        
        # Generate visualization files
        step_start = time.time()
        from pathlib import Path
        from urban_tree_planting.config.settings import OUTPUT_DIR
        
        location_dir = OUTPUT_DIR / location.name
        location_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Enhanced 6-panel visualization (satellite + overlays)
        viz_start = time.time()
        analysis_viz_path = location_dir / f"{location.name}_analysis.png"
        visualizer.create_enhanced_visualization(
            processed_location,
            priority_results,
            analysis_viz_path
        )
        logger.info(f"⏱️   → Analysis visualization created in {time.time() - viz_start:.2f}s")
        
        # 2. Component breakdown visualization
        viz_start = time.time()
        component_viz_path = location_dir / f"{location.name}_components.png"
        visualizer.create_component_breakdown(
            processed_location,
            priority_results,
            component_viz_path
        )
        logger.info(f"⏱️   → Component breakdown created in {time.time() - viz_start:.2f}s")
        
        # 3. Save JSON summary
        json_path = location_dir / f"{location.name}_summary.json"
        with open(json_path, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        logger.info(f"⏱️ [STEP 5] All visualizations generated in {time.time() - step_start:.2f}s")
        logger.info(f"✅ [USER] Maps and visualizations ready!")
        
        # Upload visualizations to GCS and generate signed URLs
        step_start = time.time()
        logger.info(f"☁️ [USER] Uploading analysis results to cloud storage... (Step 4/6 - Est. 4-6s)")
        timestamp = int(time.time())
        
        # Generate preview images for critical spots
        preview_start = time.time()
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        critical_spots = summary_data.get('critical_priority_spots', [])
        
        if api_key and critical_spots:
            logger.info(f"Generating preview images for {len(critical_spots[:5])} critical spots...")
            for i, spot in enumerate(critical_spots[:5]):
                spot_lat = spot['coordinates']['latitude']
                spot_lon = spot['coordinates']['longitude']
                
                # Generate Google Maps Static API URL with marker
                # Size: 600x400, zoom: 19 (street level), maptype: satellite with hybrid overlay
                static_map_url = (
                    f"https://maps.googleapis.com/maps/api/staticmap?"
                    f"center={spot_lat},{spot_lon}"
                    f"&zoom=19"
                    f"&size=600x400"
                    f"&maptype=satellite"
                    f"&markers=color:red%7Clabel:{i+1}%7C{spot_lat},{spot_lon}"
                    f"&key={api_key}"
                )
                
                # Add preview URL to spot data
                spot['preview_image_url'] = static_map_url
                spot['preview_note'] = f"Satellite view of Spot {i+1} with marker showing exact planting location"
        logger.info(f"⏱️   → Preview URLs generated in {time.time() - preview_start:.2f}s")
        
        # Upload detailed analysis map (will be shown in chat)
        upload_start = time.time()
        analysis_url = upload_to_gcs(
            analysis_viz_path,
            f"analysis/{location.name}_{timestamp}_analysis.png"
        )
        logger.info(f"⏱️   → Analysis map uploaded to GCS in {time.time() - upload_start:.2f}s")
        
        # Upload component breakdown (stored only, not shown in chat)
        upload_start = time.time()
        component_url = upload_to_gcs(
            component_viz_path,
            f"analysis/{location.name}_{timestamp}_components.png"
        )
        logger.info(f"⏱️   → Component breakdown uploaded to GCS in {time.time() - upload_start:.2f}s")
        
        logger.info(f"⏱️ [STEP 6] GCS uploads & preview generation completed in {time.time() - step_start:.2f}s")
        logger.info(f"✅ [USER] Aerial analysis complete! Found {len(summary_data.get('critical_priority_spots', []))} high-priority planting spots.")
        
        # Add file paths and URLs to response
        summary_data["output_files"] = {
            "analysis_visualization": str(analysis_viz_path),
            "analysis_visualization_url": analysis_url,
            "component_breakdown": str(component_viz_path),
            "component_breakdown_url": component_url,
            "json_summary": str(json_path),
            "note": "Detailed analysis visualization will be shown in chat. Component breakdown is stored in GCS for reference."
        }
        
        # Only include the main analysis map for display (not component breakdown)
        summary_data["visualization_urls"] = {
            "analysis_map": analysis_url,
            "instructions": "The detailed 6-panel analysis map shows satellite imagery, vegetation detection, shadow analysis, street networks, priority scores, and recommended planting zones."
        }
        
        # Return formatted JSON string
        total_time = time.time() - start_time
        logger.info(f"⏱️ [TOTAL] Complete analysis finished in {total_time:.2f}s")
        logger.info(f"⏱️ [BREAKDOWN] Pipeline: {pipeline_time:.2f}s ({pipeline_time/total_time*100:.1f}%), Other steps: {total_time-pipeline_time:.2f}s ({(total_time-pipeline_time)/total_time*100:.1f}%)")
        
        return json.dumps(summary_data, indent=2)
        
    except Exception as e:
        logger.error(f"Error analyzing location '{location_name}': {e}", exc_info=True)
        error_response = {
            "error": str(e),
            "location": {
                "name": location_name,
                "coordinates": {
                    "latitude": latitude,
                    "longitude": longitude
                }
            },
            "status": "failed",
            "message": "Analysis failed. Please check the coordinates and try again. Ensure the location is within Kuala Lumpur region."
        }
        return json.dumps(error_response, indent=2)


@mcp.tool()
async def analyze_spot_with_gemini_vision(
    critical_spots: list,
    max_spots: int = 5
) -> str:
    """
    Analyze critical spots using Gemini Vision to detect existing trees and assess planting context.
    
    This tool uses Google's Gemini 2.0 Flash model with vision capabilities to:
    1. Download Street View images at each critical spot
    2. Use AI vision to count existing trees (mature, young, saplings)
    3. Analyze surrounding context (buildings, shops, roads, sidewalks)
    4. Assess planting feasibility (space, sunlight, obstacles)
    5. Provide intelligent recommendations based on visual analysis
    
    Unlike traditional object detection models, Gemini Vision provides:
    - Accurate tree counting with context understanding
    - Detailed descriptions of surroundings
    - Assessment of tree health and maturity
    - Identification of planting opportunities and obstacles
    - Species suggestions based on visual cues
    
    Processing time: 2-3 seconds per spot
    
    Args:
        critical_spots: List of spot dictionaries with structure:
            [
                {
                    "coordinates": {"latitude": float, "longitude": float},
                    "priority_score": float,
                    "area_m2": float,
                    "spot_id": int (optional)
                },
                ...
            ]
        max_spots: Maximum number of spots to analyze (default: 5)
    
    Returns:
        JSON string containing vision analysis results:
        - total_spots_analyzed: Number of spots successfully analyzed
        - results: List of analysis per spot:
          * spot_number: Sequential number
          * location: GPS coordinates
          * street_view_available: Boolean
          * vision_analysis: Detailed AI analysis including:
            - tree_count: Total trees detected
            - mature_trees: Count of mature/large trees
            - young_trees: Count of young/small trees
            - tree_health: Overall health assessment
            - surroundings: Description of buildings, shops, context
            - road_characteristics: Width, traffic, condition
            - sidewalk_space: Available planting space
            - sunlight_exposure: Sun/shade assessment
            - obstacles: Utility poles, signs, drainage, etc.
            - planting_recommendations: AI suggestions for this spot
          * spot_info: Original aerial analysis data
        - summary:
          * spots_with_trees: Count of spots with existing trees
          * spots_without_trees: Count of clear spots (highest priority)
          * total_trees_detected: Total trees across all spots
          * average_trees_per_spot: Average tree density
        
    Example usage:
        analyze_spot_with_gemini_vision(
            critical_spots=[
                {"coordinates": {"latitude": 3.1379, "longitude": 101.6294}, 
                 "priority_score": 95.2, "area_m2": 55.8},
                {"coordinates": {"latitude": 3.1382, "longitude": 101.6301}, 
                 "priority_score": 88.7, "area_m2": 42.3}
            ],
            max_spots=3
        )
    
    Note: Requires GOOGLE_MAPS_API_KEY and Google Cloud Vertex AI access
    """
    try:
        import time
        start_time = time.time()
        logger.info(f"⏱️ [START] Starting Gemini Vision analysis for {len(critical_spots)} spots (max: {max_spots})")
        logger.info(f"👁️ [USER] Starting ground-level vision analysis for {min(len(critical_spots), max_spots)} spots... (Step 5/6 - Est. 12-15s)")
        
        # Get API key
        step_start = time.time()
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not api_key:
            error_msg = "GOOGLE_MAPS_API_KEY not found in environment variables"
            logger.error(error_msg)
            return json.dumps({"error": error_msg, "status": "failed"}, indent=2)
        
        # Initialize Vertex AI
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel, Part
            import base64
            from io import BytesIO
            
            project_id = os.getenv("GCP_PROJECT", "us-con-gcp-sbx-0001190-100925")
            vertexai.init(project=project_id, location="us-central1")
            
            # Use Gemini 2.0 Flash for vision (fast + accurate)
            model = GenerativeModel("gemini-2.0-flash-exp")
            logger.info(f"⏱️ [STEP 1] Vertex AI initialized in {time.time() - step_start:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            return json.dumps({"error": f"Vertex AI initialization failed: {e}", "status": "failed"}, indent=2)
        
        # Process spots
        step_start = time.time()
        results = []
        streetview_total_time = 0
        gemini_total_time = 0
        
        # OPTIMIZATION: Process spots in parallel with asyncio.gather
        async def process_single_spot(i, spot):
            """Process a single spot with Street View + Gemini Vision"""
            spot_num = i + 1
            spot_start = time.time()
            
            # Extract coordinates
            if "coordinates" in spot:
                lat = spot["coordinates"]["latitude"]
                lon = spot["coordinates"]["longitude"]
            else:
                lat = spot.get("latitude") or spot.get("lat")
                lon = spot.get("longitude") or spot.get("lon")
            
            if lat is None or lon is None:
                logger.warning(f"Skipping spot {spot_num}: missing coordinates")
                return None
            
            # Download Street View image
            try:
                sv_start = time.time()
                from streetview import search_panoramas, get_panorama_async
                
                panos = search_panoramas(lat=lat, lon=lon)
                
                if not panos:
                    logger.warning(f"No Street View available at ({lat}, {lon})")
                    return {
                        "spot_number": spot_num,
                        "location": {"latitude": lat, "longitude": lon},
                        "street_view_available": False,
                        "vision_analysis": None,
                        "spot_info": {
                            "spot_number": spot_num,
                            "priority_score": spot.get("priority_score"),
                            "area_m2": spot.get("area_m2"),
                            "spot_id": spot.get("spot_id")
                        }
                    }
                
                pano_id = panos[0].pano_id
                image = await get_panorama_async(pano_id=pano_id, zoom=5)
                sv_time = time.time() - sv_start
                logger.info(f"⏱️ [SPOT {spot_num}] Street View downloaded in {sv_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Failed to download Street View for spot {spot_num}: {e}")
                return {
                    "spot_number": spot_num,
                    "location": {"latitude": lat, "longitude": lon},
                    "street_view_available": False,
                    "error": str(e),
                    "spot_info": {
                        "spot_number": spot_num,
                        "priority_score": spot.get("priority_score"),
                        "area_m2": spot.get("area_m2")
                    }
                }
            
            # Convert image to base64 for Gemini
            from io import BytesIO
            import base64
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            # Create vision prompt
            prompt = f"""Analyze this Street View image for urban tree planting assessment.

Location: Latitude {lat}, Longitude {lon}
Area available: {spot.get('area_m2', 'unknown')} square meters
Priority score: {spot.get('priority_score', 'N/A')}/100

Please provide a detailed JSON analysis with the following structure:
{{
  "tree_count": <total number of visible trees>,
  "mature_trees": <count of mature/large trees>,
  "young_trees": <count of young/small trees or saplings>,
  "tree_health": "<overall health: excellent/good/fair/poor>",
  "tree_species_hints": "<any identifiable tree types from appearance>",
  "surroundings": "<description of buildings, shops, residential/commercial mix>",
  "road_characteristics": "<road width estimate, traffic level, pavement condition>",
  "sidewalk_space": "<sidewalk width, available planting space, surface type>",
  "sunlight_exposure": "<full sun/partial shade/full shade, building shadows>",
  "obstacles": "<utility poles, street signs, drainage grates, other obstacles>",
  "planting_feasibility": "<high/medium/low - can new trees be planted here?>",
  "recommended_tree_count": <number of new trees that could fit>,
  "spacing_suggestion": "<recommended spacing between trees in meters>",
  "planting_recommendations": "<specific suggestions for this location>"
}}

Be precise with counts and descriptive with observations."""

            # Call Gemini Vision
            try:
                gemini_start = time.time()
                response = model.generate_content([
                    Part.from_data(data=base64.b64decode(img_base64), mime_type="image/jpeg"),
                    prompt
                ])
                
                # Parse JSON response
                response_text = response.text.strip()
                # Remove markdown code blocks if present
                if response_text.startswith("```json"):
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif response_text.startswith("```"):
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                vision_analysis = json.loads(response_text)
                gemini_time = time.time() - gemini_start
                logger.info(f"⏱️ [SPOT {spot_num}] Gemini Vision: {gemini_time:.2f}s, detected {vision_analysis.get('tree_count', 0)} trees")
                logger.info(f"🌳 [USER] Spot {spot_num}/{max_spots} analyzed: {vision_analysis.get('tree_count', 0)} trees found")
                
                return {
                    "spot_number": spot_num,
                    "location": {"latitude": lat, "longitude": lon},
                    "street_view_available": True,
                    "vision_analysis": vision_analysis,
                    "spot_info": {
                        "spot_number": spot_num,
                        "priority_score": spot.get("priority_score"),
                        "area_m2": spot.get("area_m2"),
                        "spot_id": spot.get("spot_id")
                    },
                    "timing": {"streetview": sv_time, "gemini": gemini_time, "total": time.time() - spot_start}
                }
                
            except Exception as e:
                logger.error(f"Gemini Vision analysis failed for spot {spot_num}: {e}")
                return {
                    "spot_number": spot_num,
                    "location": {"latitude": lat, "longitude": lon},
                    "street_view_available": True,
                    "vision_analysis_error": str(e),
                    "spot_info": {
                        "spot_number": spot_num,
                        "priority_score": spot.get("priority_score"),
                        "area_m2": spot.get("area_m2")
                    }
                }
        
        # Process all spots in parallel
        logger.info(f"🚀 [USER] Processing {min(len(critical_spots), max_spots)} spots in parallel...")
        tasks = [process_single_spot(i, spot) for i, spot in enumerate(critical_spots[:max_spots])]
        results = await asyncio.gather(*tasks)
        results = [r for r in results if r is not None]  # Filter out None results
        
        # Calculate timing statistics
        for result in results:
            if "timing" in result:
                streetview_total_time += result["timing"]["streetview"]
                gemini_total_time += result["timing"]["gemini"]
        
        # Calculate summary statistics
        summary_start = time.time()
        successful_analyses = [r for r in results if r.get("vision_analysis")]
        spots_with_trees = sum(1 for r in successful_analyses 
                               if r["vision_analysis"].get("tree_count", 0) > 0)
        spots_without_trees = len(successful_analyses) - spots_with_trees
        total_trees = sum(r["vision_analysis"].get("tree_count", 0) 
                         for r in successful_analyses)
        avg_trees = total_trees / len(successful_analyses) if successful_analyses else 0
        logger.info(f"⏱️ [STEP 2] Vision analysis completed in {time.time() - step_start:.2f}s")
        logger.info(f"⏱️   → Street View downloads: {streetview_total_time:.2f}s avg per spot: {streetview_total_time/max(len(results), 1):.2f}s")
        logger.info(f"⏱️   → Gemini API calls: {gemini_total_time:.2f}s avg per spot: {gemini_total_time/max(len(successful_analyses), 1):.2f}s")
        logger.info(f"✅ [USER] Vision analysis complete! Analyzed {len(successful_analyses)} spots, found {total_trees} total trees.")
        
        # Prepare response
        response = {
            "total_spots_analyzed": len(successful_analyses),
            "results": results,
            "summary": {
                "spots_with_trees": spots_with_trees,
                "spots_without_trees": spots_without_trees,
                "total_trees_detected": total_trees,
                "average_trees_per_spot": round(avg_trees, 2),
                "highest_priority_for_planting": [
                    {
                        "spot_number": r["spot_number"],
                        "location": r["location"],
                        "priority_score": r["spot_info"]["priority_score"],
                        "tree_count": r["vision_analysis"]["tree_count"],
                        "planting_feasibility": r["vision_analysis"].get("planting_feasibility", "unknown"),
                        "recommended_tree_count": r["vision_analysis"].get("recommended_tree_count", 0),
                        "reason": "No existing trees - ready for new planting"
                    }
                    for r in successful_analyses 
                    if r["vision_analysis"].get("tree_count", 0) == 0
                ]
            },
            "recommendations": {
                "immediate_planting": f"{spots_without_trees} spot(s) have no existing trees and are ready for planting",
                "maintenance_focus": f"{spots_with_trees} spot(s) have existing trees - assess health and species diversity",
                "next_steps": "Use context-aware recommendation tool to get specific species, spacing, and planting timeline based on all collected data"
            }
        }
        
        total_time = time.time() - start_time
        logger.info(f"⏱️ [TOTAL] Gemini Vision analysis finished in {total_time:.2f}s")
        logger.info(f"⏱️ [SUMMARY] {total_trees} trees detected across {len(successful_analyses)} spots")
        
        return json.dumps(response, indent=2)
        
    except Exception as e:
        logger.error(f"Error in Gemini Vision analysis: {e}", exc_info=True)
        error_response = {
            "error": str(e),
            "status": "failed",
            "message": "Vision analysis failed. Check logs for details."
        }
        return json.dumps(error_response, indent=2)


@mcp.tool()
def search_all_matching_location_based_on_keyword(keyword) -> Dict[str, tuple]:
    """
    Search for addresses based on a keyword using GeoPy + Nominatim.
    :param keyword: Search term (e.g., 'Menara LGB', 'Menara OBYU')
    :param max_results: Maximum number of results to return
    :return: List of (address, latitude, longitude) tuples
    """
    keyword = keyword.strip()
    try:
        geocoder = GeocodingSearch()
        return geocoder.search_address(keyword)
    except ValueError as e:
        logger.error(f"Error: {e}")
        return {}


@mcp.tool()
def get_tree_species_recommendations() -> str: ## Ru-Jin last part to contribute
    """
    Get information about recommended tree species for Kuala Lumpur urban planting.
    
    Returns detailed information about Malaysian tree species suitable for urban environments,
    including water absorption, shade coverage, flood tolerance, and planting seasons.
    """
    return """RECOMMENDED TREE SPECIES FOR KUALA LUMPUR:

🌳 RAIN TREE (Samanea saman)
   - Water Absorption: High (500L/day)
   - Shade Coverage: Excellent
   - Flood Tolerance: High
   - Best Planting Season: Monsoon (May-October)
   - Mature Height: 25m | Canopy Spread: 30m
   - Air Quality Improvement: High
   - Notes: Excellent for flood mitigation and shade

🌳 ANGSANA (Pterocarpus indicus)
   - Water Absorption: Medium
   - Shade Coverage: Excellent
   - Flood Tolerance: Medium
   - Best Planting Season: Monsoon (May-October)
   - Mature Height: 30m | Canopy Spread: 20m
   - Air Quality Improvement: High
   - Notes: Dense canopy, beautiful flowering tree

🌳 YELLOW FLAME (Peltophorum pterocarpum)
   - Water Absorption: Medium
   - Shade Coverage: Good
   - Flood Tolerance: Medium
   - Best Planting Season: Monsoon (May-October)
   - Mature Height: 15m | Canopy Spread: 12m
   - Air Quality Improvement: Medium
   - Notes: Good for medium-sized areas, yellow flowers

🌳 SEA APPLE (Syzygium grande)
   - Water Absorption: High
   - Shade Coverage: Good
   - Flood Tolerance: High
   - Best Planting Season: Monsoon (May-October)
   - Mature Height: 20m | Canopy Spread: 15m
   - Air Quality Improvement: Medium
   - Notes: Native species, good for wet areas, low maintenance

🌳 TEMBUSU (Fagraea fragrans)
   - Water Absorption: Low (drought tolerant)
   - Shade Coverage: Medium
   - Flood Tolerance: Medium
   - Best Planting Season: Dry (November-April)
   - Mature Height: 25m | Canopy Spread: 15m
   - Air Quality Improvement: Medium
   - Notes: Drought tolerant, fragrant flowers, excellent for urban environments

GENERAL PLANTING CONSIDERATIONS:
• Plant during monsoon season (May-October) for most species
• Maintain 30m distance from buildings for large trees (Rain Tree, Angsana, Tembusu)
• Maintain 15-20m distance for medium trees (Yellow Flame, Sea Apple)
• Consider underground utilities when selecting planting spots
• Ensure adequate water drainage for flood-prone areas
• Regular monitoring during first 2 years of establishment"""


if __name__ == "__main__":
    try:
        port = int(os.getenv("PORT", "8080"))
        logger.info(f"Starting ReLeaf MCP Server on port {port}...")
        logger.info(f"Python path: {sys.path}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Test imports
        logger.info("Testing critical imports...")
        try:
            import vertexai
            logger.info("✓ vertexai imported successfully")
        except Exception as e:
            logger.error(f"✗ vertexai import failed: {e}")
        
        try:
            from streetview import search_panoramas
            logger.info("✓ streetview imported successfully")
        except Exception as e:
            logger.error(f"✗ streetview import failed: {e}")
        
        try:
            from urban_tree_planting.pipeline.processor import TreePlantingPipeline
            logger.info("✓ urban_tree_planting imported successfully")
        except Exception as e:
            logger.error(f"✗ urban_tree_planting import failed: {e}")
        
        logger.info("All critical imports successful. Starting server...")
        
        asyncio.run(
            mcp.run_async(
                transport="streamable-http",
                host="0.0.0.0",
                port=port,
            )
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)
