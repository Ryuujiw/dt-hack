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


def download_street_view_for_spots(downloader, critical_spots, location_dir, location_name):
    """
    Download Google Street View images for critical priority spots
    
    Args:
        downloader: DataDownloader instance
        critical_spots: List of critical spot dictionaries with coordinates
        location_dir: Directory to save street view images
        location_name: Name of the location (for logging)
    
    Returns:
        dict: Mapping of spot_id to street view image path
    """
    streetview_dir = location_dir / "streetview"
    streetview_dir.mkdir(parents=True, exist_ok=True)
    
    street_view_results = {}
    
    for i, spot in enumerate(critical_spots, 1):
        try:
            spot_id = spot.get("spot_id", i)
            lat = spot["coordinates"]["latitude"]
            lon = spot["coordinates"]["longitude"]
            
            logger.info(f"  Downloading street view for spot {spot_id} ({lat:.6f}, {lon:.6f})")
            
            # Download street view image
            image_path = downloader.download_street_view(lat, lon, output_dir=streetview_dir)
            
            if image_path:
                street_view_results[spot_id] = {
                    "path": image_path,
                    "coordinates": spot["coordinates"],
                    "priority_score": spot["priority_score"]
                }
                logger.info(f"    ✓ Saved street view for spot {spot_id}")
            else:
                logger.warning(f"    ⚠ Could not download street view for spot {spot_id}")
                
        except Exception as e:
            logger.warning(f"  Failed to download street view for spot {spot_id}: {e}")
            continue
    
    logger.info(f"Street view download complete: {len(street_view_results)}/{len(critical_spots)} spots")
    return street_view_results


def upload_street_view_images(street_view_results, location_name):
    """
    Upload street view images to GCS and generate signed URLs
    
    Args:
        street_view_results: Dictionary mapping spot_id to {path, coordinates, priority_score}
        location_name: Name of the location
    
    Returns:
        dict: Mapping of spot_id to GCS signed URL
    """
    import time
    timestamp = int(time.time())
    street_view_urls = {}
    
    for spot_id, data in street_view_results.items():
        try:
            image_path = Path(data["path"])
            
            if not image_path.exists():
                logger.warning(f"Street view image not found: {image_path}")
                continue
            
            # Upload to GCS
            blob_name = f"streetview/{location_name}_spot_{spot_id}_{timestamp}.jpeg"
            signed_url = upload_to_gcs(image_path, blob_name)
            
            street_view_urls[spot_id] = {
                "url": signed_url,
                "coordinates": data["coordinates"],
                "priority_score": data["priority_score"]
            }
            logger.info(f"  ✓ Uploaded street view for spot {spot_id} to GCS")
            
        except Exception as e:
            logger.warning(f"  Failed to upload street view for spot {spot_id}: {e}")
            continue
    
    return street_view_urls


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
    8. Downloads Google Street View images for each critical priority spot
    9. Generates Google Maps and Street View URLs for each spot
    10. Creates visualization outputs:
       - 6-panel analysis PNG (satellite image with overlays)
       - Component breakdown PNG (showing individual scoring components)
       - JSON summary file
       - Street View images uploaded to GCS with signed URLs
    
    Processing time: 15-30 seconds depending on area complexity (includes street view downloads)
    
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
          * street_view_image_url: Signed URL to downloaded Street View image (if available)
          * street_view_available: Boolean indicating if street view image was successfully downloaded
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
        logger.info(f"Starting tree planting analysis for '{location_name}' at ({latitude}, {longitude})")
        
        # Create location object
        location = Location(
            name=location_name.lower().replace(' ', '_'),
            description=f"Tree planting analysis for {location_name}",
            lat=latitude,
            lon=longitude
        )
        
        # Get pipeline instance
        pipeline, visualizer = get_pipeline()
        
        # Run the full 6-step pipeline
        logger.info("Running analysis pipeline (this may take 10-25 seconds)...")
        processed_location = pipeline.process_location(location)
        
        # Generate summary data using the visualizer
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
        
        # Generate visualization files
        from pathlib import Path
        from urban_tree_planting.config.settings import OUTPUT_DIR
        
        location_dir = OUTPUT_DIR / location.name
        location_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Enhanced 6-panel visualization (satellite + overlays)
        analysis_viz_path = location_dir / f"{location.name}_analysis.png"
        visualizer.create_enhanced_visualization(
            processed_location,
            priority_results,
            analysis_viz_path
        )
        
        # 2. Component breakdown visualization
        component_viz_path = location_dir / f"{location.name}_components.png"
        visualizer.create_component_breakdown(
            processed_location,
            priority_results,
            component_viz_path
        )
        
        # 3. Save JSON summary
        json_path = location_dir / f"{location.name}_summary.json"
        with open(json_path, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        logger.info(f"Analysis complete for '{location_name}'. Found {len(summary_data.get('critical_priority_spots', []))} critical priority spots.")
        logger.info(f"Visualizations saved to: {location_dir}")
        
        # Download Google Street View images for critical priority spots
        logger.info("\nDownloading Google Street View images for critical priority spots...")
        critical_spots = summary_data.get('critical_priority_spots', [])
        
        if critical_spots:
            # Download street view images
            street_view_results = download_street_view_for_spots(
                pipeline.downloader,
                critical_spots,
                location_dir,
                location.name
            )
            
            # Upload street view images to GCS
            if street_view_results:
                logger.info("Uploading street view images to Google Cloud Storage...")
                street_view_urls = upload_street_view_images(street_view_results, location.name)
                
                # Add street view URLs to each critical spot in the response
                for i, spot in enumerate(summary_data['critical_priority_spots']):
                    spot_id = spot.get('spot_id')
                    if spot_id in street_view_urls:
                        spot['street_view_image_url'] = street_view_urls[spot_id]['url']
                        spot['street_view_available'] = True
                    else:
                        spot['street_view_available'] = False
                
                logger.info(f"Street view images uploaded: {len(street_view_urls)} of {len(critical_spots)} spots")
        else:
            logger.info("No critical priority spots found for street view download")
        
        # Upload visualizations to GCS and generate signed URLs
        import time
        timestamp = int(time.time())
        
        # Upload detailed analysis map (will be shown in chat)
        analysis_url = upload_to_gcs(
            analysis_viz_path,
            f"analysis/{location.name}_{timestamp}_analysis.png"
        )
        
        # Upload component breakdown (stored only, not shown in chat)
        component_url = upload_to_gcs(
            component_viz_path,
            f"analysis/{location.name}_{timestamp}_components.png"
        )
        
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
def get_tree_species_recommendations() -> str:
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
    asyncio.run(
        mcp.run_async(
            transport="streamable-http",
            host="0.0.0.0",
            port=os.getenv("PORT", 8080),
        )
    )
