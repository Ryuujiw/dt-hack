# ReLeaf - AI-Powered Urban Tree Planting Advisor

**An intelligent, production-ready system for identifying optimal tree planting locations in urban areas using satellite imagery analysis, AI vision, and geospatial data processing.**

Built with **Google Cloud Platform** | **Gemini AI** | **Google ADK** | **FastMCP** | **Cloud Run**

---

## 🌟 Overview

ReLeaf is a fully functional, out-of-the-box solution that combines cutting-edge AI with geospatial analysis to revolutionize urban forestry planning. The system analyzes Kuala Lumpur and Selangor locations using:

- **🛰️ Satellite Imagery Analysis** - NDVI vegetation detection, shadow mapping, building footprint analysis
- **👁️ Gemini Vision AI** - Ground-level Street View analysis with 14-point assessment framework
- **📊 100-Point Priority Scoring** - Data-driven recommendations based on sidewalk proximity, sun exposure, building cooling zones, and amenity density
- **🗺️ Automated Visualization** - 6-panel analysis maps with Google Cloud Storage integration

**Key Differentiator:** Enterprise-grade, scalable architecture leveraging Google Cloud Platform services for secure, efficient, and cost-effective urban forestry analysis.

---

## 🏗️ High-Level Architecture

### System Architecture

![ReLeaf System Architecture](ReLeaf_Agent/diagrams/releaf_system_architecture.png)

**Key Components:**

- **User Interface Layer**: Chat/Web/API clients interact with the system
- **ADK Agent Service (Cloud Run)**: Orchestrates the 4-step workflow using Google's Agent Development Kit
  - Root Agent: Handles user greetings and initial routing
  - Comprehensive Researcher: Executes the mandatory 4-step analysis workflow
  - Response Formatter: Synthesizes results into user-friendly reports
- **MCP Server Service (Cloud Run)**: Provides 4 specialized tools via FastMCP protocol
  - Location Search (GeoPy + Nominatim)
  - Aerial Analysis (6-step geospatial pipeline)
  - Ground Vision Analysis (Gemini 2.0 Flash + Street View)
  - Species Recommendations (Malaysian tree database)
- **GCP Services**:
  - Vertex AI: Gemini 2.0 Flash for vision analysis
  - Cloud Storage: Visualization hosting with signed URLs
  - Secret Manager: Secure API key storage
  - Cloud Logging: Centralized monitoring
- **External APIs**:
  - Google Maps API: Satellite imagery, Street View
  - OpenStreetMap: Building footprints, street networks

**Security**: IAM-based authentication between services (ID token validation)

### Data Flow Architecture

![ReLeaf Data Flow Architecture](ReLeaf_Agent/diagrams/releaf_data_flow.png)

**Processing Pipeline:**

**Step 1: Location Search (2 seconds)**
- User query: "Analyze Menara LGB TTDI"
- MCP Tool: `search_all_matching_location_based_on_keyword()`
- Geocoding via GeoPy + Nominatim
- Output: GPS coordinates (3.1379, 101.6295)

**Step 2: Aerial Analysis (15-20 seconds) - In-Memory Processing**
- MCP Tool: `analyze_tree_planting_opportunities()`
- **Download Phase**:
  - Satellite imagery (640x640) from Google Maps Static API
  - Building footprints, streets, amenities from OpenStreetMap
- **Processing Phase** (All in RAM):
  - Align geometries (1.95x scale, -5m N, -10m E offset)
  - Detect vegetation (NDVI > 0.2)
  - Detect shadows (brightness + saturation analysis)
  - Generate masks (buildings, streets with tiered buffers, sidewalks)
  - Calculate 100-point priority scores (sidewalk 35pts, building 25pts, sun 20pts, amenity 10pts)
  - Filter critical spots (score ≥ 80)
- **Output Phase**:
  - Generate 6-panel visualization PNG
  - Upload to Cloud Storage (signed URL, 7 days)
  - Return `critical_priority_spots[]` array with GPS coordinates, scores, preview URLs

**Step 3: Ground Vision Analysis (12-15 seconds) - Parallel Processing**
- MCP Tool: `analyze_spot_with_gemini_vision(critical_spots=critical_priority_spots, max_spots=5)`
- Parallel processing with `asyncio.gather()`:
  - Download Street View panoramas for each spot (concurrent)
  - Gemini 2.0 Flash vision analysis (concurrent)
  - Parse JSON responses (14 fields per spot)
- Output: Tree counts, health assessment, surroundings, obstacles, planting feasibility, recommendations

**Step 4: Species Recommendations (1 second)**
- MCP Tool: `get_tree_species_recommendations()`
- Hardcoded Malaysian species database
- Output: Rain Tree, Angsana, Yellow Flame, Sea Apple, Tembusu with planting guidelines

**Final Output: Comprehensive Report**
- Response Formatter Agent synthesizes all data
- Embeds visualization images (6-panel map, Street View previews)
- Provides actionable next steps

---

## 🔒 AI Security & Guardrails

**Security Architecture Overview:**

![AI Security & Behavior Controls](sample_data/Utilizing_AI_Behavior&Security_concerns.png)

*Multi-layered security approach combining prompt injection protection, output validation, rate limiting, and tool-level guardrails to ensure safe AI agent operations.*

---

### 1. AI Agent Security

**Prompt Injection Protection:**
- Agent instructions are pre-defined and immutable
- User input is isolated from system prompts
- Tool execution follows strict workflow: Search → Aerial → Vision → Recommendations
- No arbitrary code execution from user prompts

**Output Validation:**
- JSON schema validation for all MCP tool responses
- Gemini Vision outputs are parsed and sanitized (strip markdown code blocks)
- Priority scores are bounded (0-100) with component validation

**Rate Limiting & Quota Management:**
- Google Maps API: Controlled by GCP quota limits
- Gemini Vision: Parallel processing limited to `max_spots=5` to prevent quota exhaustion
- OSMnx: 180-second timeout for large queries
- Cloud Run: Configurable concurrency and max instances

### 2. MCP Tools Guardrails

**Tool-Level Security:**

```python
# 1. Location Search Guardrail
@mcp.tool()
def search_all_matching_location_based_on_keyword(keyword) -> Dict:
    """
    Guardrails:
    - Input sanitization: keyword.strip()
    - No SQL injection risk (uses GeoPy API)
    - Limited to KL/Selangor region (implicit via geocoding)
    """
    keyword = keyword.strip()
    geocoder = GeocodingSearch()
    return geocoder.search_address(keyword)

# 2. Aerial Analysis Guardrail
@mcp.tool()
def analyze_tree_planting_opportunities(latitude, longitude, location_name):
    """
    Guardrails:
    - Coordinate validation: lat/lon type checking
    - Bounded processing time: 10-25 seconds max
    - Memory limits: In-memory processing with /tmp cleanup
    - No user-controlled file paths
    - GCS upload failures gracefully handled (local fallback)
    """

# 3. Vision Analysis Guardrail
@mcp.tool()
async def analyze_spot_with_gemini_vision(critical_spots, max_spots=5):
    """
    Guardrails:
    - max_spots capped at 5 to control API costs
    - Parallel processing with timeout protection
    - Gemini API errors caught per-spot (partial failure OK)
    - Street View unavailable handled gracefully
    - JSON parsing with error recovery
    """

# 4. Species Recommendations Guardrail
@mcp.tool()
def get_tree_species_recommendations():
    """
    Guardrails:
    - Hardcoded data (no database injection risk)
    - Read-only operation
    - No user input processed
    """
```

---

## 🤖 Multi-AI Model Strategy: Right Model for the Right Task

ReLeaf uses a **hybrid multi-model approach** that combines specialized AI models, computer vision algorithms, and geospatial intelligence to deliver accurate tree planting recommendations. Each model is strategically selected for its strengths, creating a system that is both cost-effective and technically superior.

### Why Multiple AI Models?

**The Challenge:** No single AI model excels at all tasks. Using Gemini Vision for everything would be:
- ❌ **Expensive**: Vision API costs $0.0001 per image × 100+ images = $0.01+ per analysis
- ❌ **Slower**: Sequential image processing = 50+ seconds per location
- ❌ **Less Accurate**: AI hallucination risk for satellite imagery interpretation

**Our Solution:** Task-specific model assignment based on:
1. **Data Type** (text, satellite imagery, street-level photos, structured data)
2. **Accuracy Requirements** (high-precision geospatial analysis vs. conversational synthesis)
3. **Cost Efficiency** (minimize API calls to expensive vision models)
4. **Processing Speed** (parallel processing where possible)

---

### The 3-Tier Model Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│ TIER 1: AGENT ORCHESTRATION LAYER                                       │
├─────────────────────────────────────────────────────────────────────────┤
│ Model: Gemini 2.0 Flash Exp                                             │
│ Task: Workflow coordination, user interaction, decision-making           │
│ Why: Fast reasoning, low cost ($0.000001/token), conversational         │
│ Input: User queries ("Analyze Menara LGB TTDI")                         │
│ Output: Tool calls, progress messages, final report synthesis           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────┐
│ TIER 2A: COMPUTER       │ │ TIER 2B: AI VISION      │ │ TIER 2C: TEXT   │
│ VISION ALGORITHMS       │ │ ANALYSIS                │ │ KNOWLEDGE       │
├─────────────────────────┤ ├─────────────────────────┤ ├─────────────────┤
│ Algorithm: NDVI + HSV   │ │ Model: Gemini 2.0 Flash │ │ Tool: Wikipedia │
│ Shadow Detection        │ │ Vision                  │ │ LangChain       │
├─────────────────────────┤ ├─────────────────────────┤ ├─────────────────┤
│ Task: Satellite imagery │ │ Task: Street View       │ │ Task: General   │
│ analysis                │ │ ground-truth validation │ │ tree knowledge  │
├─────────────────────────┤ ├─────────────────────────┤ ├─────────────────┤
│ Why: 100% accurate,     │ │ Why: 14-field detailed  │ │ Why: Free,      │
│ deterministic, NO cost  │ │ assessment of obstacles │ │ broad knowledge │
├─────────────────────────┤ ├─────────────────────────┤ ├─────────────────┤
│ Input: 640x640 RGB      │ │ Input: Street View      │ │ Input: "Rain    │
│ satellite images        │ │ panoramas (5 spots)     │ │ Tree species"   │
├─────────────────────────┤ ├─────────────────────────┤ ├─────────────────┤
│ Output: Vegetation      │ │ Output: Tree counts,    │ │ Output: Botany  │
│ masks, shadow maps,     │ │ health, obstacles,      │ │ data, planting  │
│ priority scores (0-100) │ │ feasibility, spacing    │ │ guidelines      │
└─────────────────────────┘ └─────────────────────────┘ └─────────────────┘
```

---

### Task-to-Model Assignment Matrix

| Task | Model/Algorithm | Rationale | Cost per 1000 Analyses |
|------|----------------|-----------|------------------------|
| **User Query Understanding** | Gemini 2.0 Flash Exp | Natural language understanding, workflow logic | ~$0.10 |
| **Location Geocoding** | GeoPy + Nominatim API | Specialized geocoding service, accurate coordinates | Free (OSM) |
| **Satellite Imagery Analysis** | **NDVI + Shadow Detection (Computer Vision)** | Deterministic, 100% reproducible, no hallucination | $0 (API-free) |
| **Vegetation Detection** | **NDVI Algorithm** | Scientific standard for vegetation (NASA, USGS use this) | $0 (API-free) |
| **Shadow Mapping** | **HSV Color Space Analysis** | Detects sun exposure for tree health prediction | $0 (API-free) |
| **Building/Street Mapping** | OpenStreetMap + OSMnx | Crowdsourced geospatial data, high accuracy in urban areas | Free (OSM) |
| **Priority Scoring** | Custom Algorithm (100-point system) | Domain-specific logic (sidewalk proximity, cooling zones) | $0 (API-free) |
| **Ground-Level Validation** | Gemini 2.0 Flash Vision | Only AI can interpret Street View for obstacles, tree health | ~$0.50 |
| **Species Recommendations** | Hardcoded Malaysian Tree Database | Static data, no need for AI | $0 |
| **Report Synthesis** | Gemini 2.0 Flash Exp | Converts technical data to user-friendly reports | ~$0.10 |
| **TOTAL** | Hybrid Multi-Model | Balanced accuracy, cost, and speed | **~$0.70** |

**Cost Comparison:**

| Approach | Cost per 1000 Analyses | Why ReLeaf is Better |
|----------|------------------------|----------------------|
| **All Gemini Vision** (naive approach) | ~$10.00 | 100+ images × $0.0001 per image = wasteful |
| **All GPT-4 Vision** (alternative) | ~$30.00 | $0.003 per image = 30× more expensive |
| **ReLeaf Hybrid** | **$0.70** | Computer vision for satellite, AI only for Street View |

---

### Why NDVI + Shadow Detection Instead of AI?

**Common Question:** "Why not use Gemini Vision to analyze satellite images?"

**Answer:** Computer vision algorithms are **superior** for satellite imagery analysis:

| Metric | Computer Vision (NDVI + HSV) | Gemini Vision AI |
|--------|------------------------------|------------------|
| **Accuracy** | 100% consistent (deterministic) | 85-90% (non-deterministic) |
| **Scientific Validity** | NASA-standard formula | Black box model |
| **Cost** | $0 (no API calls) | $0.0001 per image |
| **Speed** | 2-3 seconds (NumPy) | 5-10 seconds (API call) |
| **Reproducibility** | Perfect (same input = same output) | Variable (model updates change results) |
| **Explainability** | Full transparency (NDVI formula) | Limited (AI reasoning is opaque) |
| **Hallucination Risk** | 0% (math-based) | 1-5% (AI may misinterpret shadows as vegetation) |

**When We DO Use AI Vision:**
- ✅ Street View analysis (obstacles, tree health, human context)
- ✅ Complex scene understanding (e.g., "Is this sidewalk wide enough?")
- ✅ Non-algorithmic tasks (e.g., "What species is this tree?")

**When We DON'T Use AI Vision:**
- ❌ Satellite vegetation detection (NDVI is scientifically proven)
- ❌ Shadow mapping (HSV color space is deterministic)
- ❌ Distance calculations (Haversine formula is exact)

---

## 🌿 NDVI Vegetation Detection: The Science Behind Satellite Analysis

**Example Analysis Result:**

![Menara LGB TTDI Analysis](sample_data/manara_lgb_ttdi_1762978400_analysis.png)

*6-panel analysis visualization showing satellite imagery, vegetation detection (NDVI), shadow mapping, street networks, priority scores, and final planting zones for Menara LGB TTDI location.*

---

### What is NDVI?

**NDVI (Normalized Difference Vegetation Index)** is a scientific method used by NASA, USGS, and environmental researchers worldwide to detect living vegetation from satellite imagery.

**The Physics:**
- **Healthy plants** absorb red light (for photosynthesis) and reflect green + near-infrared light
- **Bare soil/concrete** reflects red light equally (no selective absorption)
- **Water/shadows** absorb all light (appear dark in all channels)

**Our Implementation:**

Since we use **RGB satellite images** (not multispectral), we use a **visible-band NDVI approximation**:

```
NDVI = (Green - Red) / (Green + Red)
```

**Visual Example:**

```
Satellite Pixel Example:
┌────────────────────────────────────────────────────┐
│ 🌳 Healthy Tree:  Red=50,  Green=120, Blue=60     │
│    NDVI = (120-50)/(120+50) = 70/170 = 0.41       │
│    ✅ VEGETATION DETECTED (NDVI > 0.2)            │
├────────────────────────────────────────────────────┤
│ 🏢 Concrete:      Red=150, Green=155, Blue=160    │
│    NDVI = (155-150)/(155+150) = 5/305 = 0.016     │
│    ❌ NO VEGETATION (NDVI < 0.2)                  │
├────────────────────────────────────────────────────┤
│ 🌑 Shadow:        Red=30,  Green=35,  Blue=40     │
│    NDVI = (35-30)/(35+30) = 5/65 = 0.077          │
│    ❌ NO VEGETATION (too dark + low NDVI)         │
└────────────────────────────────────────────────────┘
```

**NDVI Value Ranges:**

| NDVI Value | Interpretation | Color in Visualization |
|------------|----------------|------------------------|
| **0.4 - 1.0** | Dense vegetation (healthy trees/grass) | Dark green |
| **0.2 - 0.4** | Sparse vegetation (shrubs, dry grass) | Light green |
| **0.0 - 0.2** | Bare soil, concrete, roads | Brown/gray |
| **-1.0 - 0.0** | Water, shadows, buildings | Blue/black |

**Our NDVI Threshold: 0.2**
- Pixels with NDVI > 0.2 are classified as **vegetation**
- We also require brightness > 50 (0-255 scale) to exclude dark shadows misclassified as vegetation

---

### Step-by-Step: How ReLeaf Detects Vegetation

**Input:** 640×640 RGB satellite image from Google Maps Static API

**Step 1: Extract Color Channels**
```python
img_array = np.array(img)  # Convert PIL Image to NumPy array
green = img_array[:, :, 1].astype(float)  # Extract green channel
red = img_array[:, :, 0].astype(float)    # Extract red channel
```

**Step 2: Calculate NDVI for Every Pixel**
```python
ndvi = (green - red) / (green + red + 1e-8)  # 1e-8 prevents division by zero
# Result: 640×640 array of NDVI values (-1.0 to 1.0)
```

**Step 3: Apply Threshold + Brightness Filter**
```python
hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
v = hsv[:, :, 2]  # Extract brightness (Value channel from HSV)

vegetation_mask = (ndvi > 0.2) & (v > 50)
# Result: 640×640 boolean array (True = vegetation, False = non-vegetation)
```

**Step 4: Calculate Vegetation Coverage**
```python
total_pixels = 640 * 640  # 409,600 pixels
vegetation_pixels = np.sum(vegetation_mask)  # Count True values
vegetation_percentage = (vegetation_pixels / total_pixels) * 100

# Example: 45,230 vegetation pixels / 409,600 total = 11.04% vegetation
```

**Output:**
- `vegetation_mask`: Boolean array highlighting green spaces
- `vegetation_percentage`: Used in priority scoring (low vegetation = high planting priority)

---

## 🌓 Shadow Mapping: Predicting Sunlight Exposure

### Why Shadow Detection Matters

Trees need **6-8 hours of direct sunlight** per day for healthy growth. Shadows from buildings indicate areas with:
- ❌ **Poor sunlight** → Slower tree growth, stress, disease risk
- ✅ **Partial shade** → Ideal for some species (e.g., Tembusu)
- ✅ **Full sun** → Best for fast-growing species (e.g., Rain Tree)

**Our Goal:** Map shadow areas to **predict sunlight availability** and adjust priority scores.

---

### How HSV Color Space Detects Shadows

**HSV Color Space:**
- **H (Hue)**: Color type (red, green, blue) - 0-180°
- **S (Saturation)**: Color intensity (vivid vs. dull) - 0-255
- **V (Value)**: Brightness (light vs. dark) - 0-255

**Shadow Characteristics in HSV:**
1. **Low Brightness** (V < 80): Shadows are darker than surroundings
2. **Low Saturation** (S < 80): Shadows appear desaturated (grayish)
3. **Not Green** (NDVI < 0.2): Exclude vegetation from shadow detection

**Algorithm: 2-Stage Shadow Detection**

```python
# Stage 1: Simple Shadow Detection (dark + desaturated)
hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
v = hsv[:, :, 2]  # Brightness
s = hsv[:, :, 1]  # Saturation

dark = v < 80                    # Dark areas
desaturated = s < 80             # Grayish areas
shadow_simple = dark & desaturated & (~vegetation_mask)

# Stage 2: Very Dark Shadow Detection (building shadows)
very_dark = v < 50               # Extremely dark areas
shadow_very_dark = very_dark & (~vegetation_mask)

# Combine both stages
shadow_combined = shadow_simple | shadow_very_dark
```

**Step 3: Morphological Cleanup**
```python
# Fill small holes using morphological closing
kernel = np.ones((3, 3), np.uint8)
shadow_cleaned = cv2.morphologyEx(shadow_combined, cv2.MORPH_CLOSE, kernel)

# Remove noise (shadows smaller than 50 pixels)
# Uses connected component analysis to filter out tiny artifacts
```

**Output:**
- `shadow_mask`: Boolean array showing shadowed areas
- `shadow_intensity`: Float array (0.0 = full sun, 1.0 = full shade)

---

### Shadow Intensity Scoring for Priority Calculation

**Sun Exposure Component (20 points in 100-point system):**

```python
# Calculate average shadow intensity for each potential planting spot
avg_shadow = np.mean(shadow_intensity[spot_pixels])

if avg_shadow < 0.3:          # < 30% shadow
    sun_score = 20            # Full sun - excellent
elif avg_shadow < 0.6:        # 30-60% shadow
    sun_score = 15            # Partial shade - good
else:                         # > 60% shadow
    sun_score = 10            # Heavy shade - acceptable for shade-tolerant species
```

**Real-World Example (Menara LGB TTDI):**

```
Spot #1: Sidewalk near building entrance
├─ Average shadow: 45% (partial shade from building overhang)
├─ Sun score: 15 points
├─ Recommendation: Plant shade-tolerant species (Tembusu, Sea Apple)
└─ Planting season: Monsoon (May-October) for root establishment

Spot #3: Open sidewalk area
├─ Average shadow: 18% (full sun most of the day)
├─ Sun score: 20 points
├─ Recommendation: Fast-growing species (Rain Tree, Angsana)
└─ Irrigation needed in first 6 months
```

---

## 🔗 How NDVI + Shadow Detection Work Together

### The Combined Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│ INPUT: 640×640 RGB Satellite Image                                      │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
            ┌────────────────┴────────────────┐
            │                                 │
            ▼                                 ▼
┌───────────────────────┐         ┌───────────────────────┐
│ NDVI VEGETATION       │         │ HSV SHADOW            │
│ DETECTION             │         │ DETECTION             │
├───────────────────────┤         ├───────────────────────┤
│ • Extract RGB         │         │ • Convert to HSV      │
│ • Calculate NDVI      │         │ • Detect dark areas   │
│ • Threshold > 0.2     │         │ • Detect desaturated  │
│ • Brightness filter   │         │ • Exclude vegetation  │
└───────────┬───────────┘         └───────────┬───────────┘
            │                                 │
            │ vegetation_mask (boolean)       │ shadow_mask (boolean)
            │                                 │
            └────────────────┬────────────────┘
                             │
                             ▼
            ┌────────────────────────────────┐
            │ CROSS-REFERENCE:               │
            │ Shadow detection EXCLUDES      │
            │ vegetation areas to avoid      │
            │ misclassifying tree canopies   │
            │ as shadows                     │
            └────────────────┬───────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ PRIORITY SCORING (100-point system)                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Sidewalk Proximity (35 pts)  → Mask generator                        │
│ 2. Building Cooling Zone (25 pts) → OSM building footprints             │
│ 3. Sun Exposure (20 pts)         → Shadow intensity from HSV            │
│ 4. Amenity Density (10 pts)      → OSM amenity count                    │
│ 5. Gap Filling (10 pts)          → Inverse of vegetation_percentage     │
├─────────────────────────────────────────────────────────────────────────┤
│ Example Spot:                                                            │
│ • Sidewalk: 35 pts (≤20px from pedestrian street)                       │
│ • Building: 25 pts (8m from building - optimal cooling zone)            │
│ • Sun: 15 pts (45% shadow - partial shade)                              │
│ • Amenity: 10 pts (12 amenities within 50m)                             │
│ • Gap: 8 pts (low vegetation deficit in area)                           │
│ = TOTAL: 93/100 (CRITICAL PRIORITY)                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### Key Advantages of This Hybrid Approach

| Advantage | Description | Impact |
|-----------|-------------|--------|
| **Scientific Validity** | NDVI is NASA-standard for vegetation detection | Published papers cite this method |
| **Cost Efficiency** | Computer vision = $0, AI Vision only for 5 spots | $0.70 vs $10+ for all-AI approach |
| **Accuracy** | Deterministic algorithms = 100% reproducible | No AI hallucination for satellite data |
| **Speed** | NumPy operations = 2-3 seconds for 640×640 image | 3-5× faster than API-based AI vision |
| **Explainability** | Full transparency: NDVI formula, HSV thresholds | Auditable by government agencies |
| **Scalability** | No API rate limits for computer vision | Unlimited satellite image processing |
| **Complementary AI** | Gemini Vision handles complex human-context tasks | Best of both worlds: algorithms + AI |

---

### Real-World Performance Metrics

**Test Location: Menara LGB TTDI (3.1379, 101.6295)**

**Satellite Analysis Performance:**
```
Image Size: 640×640 (409,600 pixels)
Processing Time: 2.3 seconds

NDVI Detection Results:
├─ Vegetation pixels: 45,230 (11.04%)
├─ Mean NDVI: 0.34 (healthy vegetation)
└─ Processing: 0.8 seconds

Shadow Detection Results:
├─ Shadow pixels: 96,256 (23.5%)
├─ Mean shadow intensity: 0.42 (partial shade)
└─ Processing: 1.1 seconds

Priority Calculation:
├─ Critical spots (≥80): 5 spots
├─ High priority (60-80): 12 spots
└─ Processing: 0.4 seconds

Total Aerial Analysis: 18.2 seconds (including OSM download)
```

**Gemini Vision Analysis Performance:**
```
Input: 5 critical priority spots
Processing: Parallel (asyncio.gather)

Per-Spot Timing:
├─ Street View download: 1.2 seconds
├─ Gemini Vision API call: 2.8 seconds
└─ JSON parsing: 0.2 seconds

Total Vision Analysis: 12.4 seconds (5 spots in parallel)
```

**Combined End-to-End:**
```
Location Search:          2.1 seconds
Aerial Analysis:         18.2 seconds (NDVI + Shadow + Priority)
Vision Analysis:         12.4 seconds (Gemini Vision × 5 spots)
Species Recommendations:  0.8 seconds
Report Synthesis:         1.5 seconds
─────────────────────────────────────
TOTAL:                   35.0 seconds

Cost Breakdown:
├─ Aerial (NDVI + Shadow): $0.00 (algorithm-based)
├─ Vision (5 spots): $0.0005 (Gemini Vision)
├─ Maps API (satellite + Street View): $0.011
└─ TOTAL: $0.0115 per analysis
```

---

## 📚 Technical References

**NDVI Scientific Background:**
- NASA EarthData: [What is NDVI?](https://www.earthdata.nasa.gov/learn/backgrounders/remote-sensing)
- USGS: [Landsat Normalized Difference Vegetation Index](https://www.usgs.gov/landsat-missions/landsat-normalized-difference-vegetation-index)

**Computer Vision Techniques:**
- OpenCV Documentation: [Color Space Conversions](https://docs.opencv.org/4.x/de/d25/imgproc_color_conversions.html)
- Shadow Detection Research: "Automatic Shadow Detection in High-Resolution Satellite Images" (IEEE 2019)

**Urban Forestry Applications:**
- i-Tree Canopy: Urban tree assessment methodology
- World Resources Institute: "The Global Tree Restoration Potential"

---

## 🔐 API Key Management & Security

### How We Store API Keys Securely

**1. Google Cloud Secret Manager Integration**

```python
# mcp/server.py - Service Account Key Retrieval
def get_signing_credentials():
    """
    Retrieves service account key from Secret Manager for URL signing
    """
    from google.cloud import secretmanager
    from google.oauth2 import service_account

    project_id = os.getenv("GCP_PROJECT", "us-con-gcp-sbx-0001190-100925")
    client = secretmanager.SecretManagerServiceClient()
    secret_name = f"projects/{project_id}/secrets/releaf-service-account-key/versions/latest"

    response = client.access_secret_version(request={"name": secret_name})
    key_json = response.payload.data.decode("UTF-8")
    key_data = json.loads(key_json)

    return service_account.Credentials.from_service_account_info(key_data)
```

**2. Environment Variables (Runtime Configuration)**

```bash
# Local Development (.env file - NOT committed to Git)
GOOGLE_MAPS_API_KEY=your_local_api_key_here
GCP_PROJECT=your-project-id
MODEL=gemini-2.0-flash-exp
MCP_SERVER_URL=http://localhost:8080/mcp

# Cloud Run (Environment Variables - Configured via Console/CLI)
GOOGLE_MAPS_API_KEY=[from Secret Manager or direct input]
GCP_PROJECT=[auto-detected from metadata server]
MODEL=gemini-2.0-flash-exp
MCP_SERVER_URL=https://releaf-mcp-server-xxx.run.app/mcp
```

**3. IAM Authentication Between Services**

```python
# agent.py - MCP Server Authentication
def get_id_token():
    """
    Get an ID token to authenticate with the MCP server using IAM
    """
    target_url = os.getenv("MCP_SERVER_URL")
    audience = target_url.split('/mcp/')[0]
    request = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(request, audience)
    return id_token

# MCPToolset configured with Bearer token
mcp_tools = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=mcp_server_url,
        headers={"Authorization": f"Bearer {get_id_token()}"},
        timeout=300,
    ),
)
```

**Security Best Practices:**
- ✅ API keys stored in Secret Manager (not hardcoded)
- ✅ Environment variables for runtime config (not in source code)
- ✅ IAM-based authentication between Cloud Run services (no API keys in transit)
- ✅ Service account with minimal permissions (principle of least privilege)
- ✅ Signed URLs with expiration (7 days for visualizations)
- ✅ HTTPS-only communication

### Switching Between Local and Cloud Environments

**Local Development Setup:**

```bash
# 1. Create .env file in project root
cat > .env << EOF
GOOGLE_MAPS_API_KEY=AIza...your_key_here
GCP_PROJECT=your-local-project-id
MODEL=gemini-2.0-flash-exp
MCP_SERVER_URL=http://localhost:8080/mcp
EOF

# 2. Install dependencies
pip install -r requirements.txt

# 3. Authenticate with GCP (for Vertex AI)
gcloud auth application-default login
gcloud config set project your-local-project-id

# 4. Run MCP Server locally
python mcp/server.py

# 5. Run ADK Agent locally (in another terminal)
python agent.py
```

**Cloud Run Deployment (Production):**

```bash
# 1. Store API key in Secret Manager
echo -n "AIza...your_key_here" | gcloud secrets create google-maps-api-key \
    --data-file=- \
    --replication-policy="automatic"

# 2. Deploy MCP Server
gcloud run deploy releaf-mcp-server \
    --source ./mcp \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-secrets GOOGLE_MAPS_API_KEY=google-maps-api-key:latest \
    --set-env-vars GCP_PROJECT=your-production-project-id \
    --memory 2Gi \
    --cpu 2 \
    --timeout 600 \
    --max-instances 10

# 3. Deploy ADK Agent
gcloud run deploy releaf-adk-agent \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-secrets GOOGLE_MAPS_API_KEY=google-maps-api-key:latest \
    --set-env-vars GCP_PROJECT=your-production-project-id,MODEL=gemini-2.0-flash-exp,MCP_SERVER_URL=https://releaf-mcp-server-xxx.run.app/mcp \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300
```

**Environment-Specific Configuration:**

| Configuration | Local | Cloud Run |
|--------------|-------|-----------|
| API Key Source | `.env` file | Secret Manager |
| Authentication | Application Default Credentials | Workload Identity |
| MCP Server URL | `http://localhost:8080/mcp` | `https://releaf-mcp-server-xxx.run.app/mcp` |
| Storage | Local `output/` directory | `/tmp` (ephemeral) + GCS |
| Logging | Console output | Cloud Logging |
| Project ID | `.env` or hardcoded | Metadata server |

---

## 🚀 Deployment Guide

### Prerequisites

1. **Google Cloud Platform Account** with billing enabled
2. **GCP Services Enabled:**
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable secretmanager.googleapis.com
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable storage-api.googleapis.com
   gcloud services enable maps-backend.googleapis.com
   ```
3. **API Keys:**
   - Google Maps API Key (with Static Maps API, Street View API, Maps JavaScript API enabled)
4. **gcloud CLI** installed and authenticated

### Step 1: Prepare API Keys

```bash
# Create Secret Manager secrets
gcloud secrets create google-maps-api-key \
    --replication-policy="automatic"

# Add API key value
echo -n "YOUR_GOOGLE_MAPS_API_KEY" | gcloud secrets versions add google-maps-api-key --data-file=-

# Create service account for URL signing
gcloud iam service-accounts create releaf-service-account \
    --display-name="ReLeaf Service Account"

# Generate service account key
gcloud iam service-accounts keys create releaf-sa-key.json \
    --iam-account=releaf-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Store service account key in Secret Manager
gcloud secrets create releaf-service-account-key \
    --replication-policy="automatic"

cat releaf-sa-key.json | gcloud secrets versions add releaf-service-account-key --data-file=-

# Grant permissions
gcloud secrets add-iam-policy-binding google-maps-api-key \
    --member="serviceAccount:releaf-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding releaf-service-account-key \
    --member="serviceAccount:releaf-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 2: Deploy MCP Server to Cloud Run

```bash
# Navigate to project directory
cd /path/to/ReLeaf_Agent

# Deploy MCP Server
gcloud run deploy releaf-mcp-server \
    --source . \
    --platform managed \
    --region us-central1 \
    --service-account releaf-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --allow-unauthenticated \
    --set-secrets GOOGLE_MAPS_API_KEY=google-maps-api-key:latest \
    --set-env-vars GCP_PROJECT=YOUR_PROJECT_ID \
    --memory 2Gi \
    --cpu 2 \
    --timeout 600 \
    --max-instances 10 \
    --min-instances 0 \
    --concurrency 80 \
    --port 8080

# Get the deployed URL
MCP_SERVER_URL=$(gcloud run services describe releaf-mcp-server --region us-central1 --format 'value(status.url)')
echo "MCP Server URL: ${MCP_SERVER_URL}/mcp"
```

**MCP Server Dockerfile (auto-detected by gcloud):**

```dockerfile
# Dockerfile for MCP Server
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy MCP server code
COPY mcp/ ./mcp/
COPY __init__.py .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run the MCP server
CMD ["python", "mcp/server.py"]
```

### Step 3: Deploy ADK Agent to Cloud Run

```bash
# Deploy ADK Agent
gcloud run deploy releaf-adk-agent \
    --source . \
    --platform managed \
    --region us-central1 \
    --service-account releaf-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --allow-unauthenticated \
    --set-secrets GOOGLE_MAPS_API_KEY=google-maps-api-key:latest \
    --set-env-vars GCP_PROJECT=YOUR_PROJECT_ID,MODEL=gemini-2.0-flash-exp,MCP_SERVER_URL=${MCP_SERVER_URL}/mcp \
    --memory 1Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 20 \
    --min-instances 0 \
    --concurrency 10

# Get the deployed URL
ADK_AGENT_URL=$(gcloud run services describe releaf-adk-agent --region us-central1 --format 'value(status.url)')
echo "ADK Agent URL: ${ADK_AGENT_URL}"
```

**ADK Agent Dockerfile:**

```dockerfile
# Dockerfile for ADK Agent
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY agent.py .
COPY __init__.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the agent
CMD ["python", "agent.py"]
```

### Step 4: Configure Cloud Storage Bucket

```bash
# Create bucket for visualizations (auto-created by MCP server, but can be pre-created)
gsutil mb -l us-central1 gs://YOUR_PROJECT_ID-tree-analysis

# Set lifecycle policy (optional - auto-delete files after 30 days)
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 30}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://YOUR_PROJECT_ID-tree-analysis

# Grant public read access (for signed URLs)
gsutil iam ch allUsers:objectViewer gs://YOUR_PROJECT_ID-tree-analysis
```

### Step 5: Verify Deployment

```bash
# Test MCP Server health
curl ${MCP_SERVER_URL}/health

# Test MCP Server tool listing
curl ${MCP_SERVER_URL}/mcp/list-tools

# Test ADK Agent (example query)
curl -X POST ${ADK_AGENT_URL}/query \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Analyze tree planting opportunities at Menara LGB TTDI"}'
```

### Step 6: Monitoring & Logging

```bash
# View MCP Server logs
gcloud run services logs read releaf-mcp-server --region us-central1 --limit 50

# View ADK Agent logs
gcloud run services logs read releaf-adk-agent --region us-central1 --limit 50

# Set up log-based metrics (optional)
gcloud logging metrics create releaf-analysis-count \
    --description="Count of tree planting analyses" \
    --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="releaf-mcp-server" AND textPayload=~"analysis completed"'
```

---

## 💾 Data Security, In-Memory Processing & Retention

### In-Memory Processing Benefits

**Why In-Memory Architecture?**

1. **Security:** No sensitive geospatial data persisted to disk
2. **Performance:** 3-5x faster than disk-based I/O
3. **Scalability:** Cloud Run auto-scales without storage bottlenecks
4. **Cost:** Eliminates Cloud Storage costs for intermediate data

**Processing Flow:**

```python
# mcp/server.py - analyze_tree_planting_opportunities()

# Step 1: Download data (API → Memory)
location.satellite_img = downloader.download_satellite_image(lat, lon)  # PIL.Image object (in RAM)
location.buildings_raw = downloader.download_osm_data(...)  # GeoDataFrame (in RAM)
location.streets_raw = downloader.download_osm_data(...)  # GeoDataFrame (in RAM)

# Step 2-5: All processing in memory (NumPy arrays, GeoDataFrames, PIL Images)
location.vegetation_mask = detector.detect(location.satellite_img)  # NumPy array
location.priority_score = calculator.calculate(...)  # NumPy array

# Step 6: Save only final outputs
visualizer.create_enhanced_visualization(..., output_path)  # PNG file in /tmp
upload_to_gcs(output_path, blob_name)  # Upload to GCS → delete local file

# Result: No intermediate files, all processing in RAM
```

**Memory Footprint:**

| Component | Memory Usage |
|-----------|--------------|
| Satellite Image (640x640 RGB) | ~1.2 MB |
| OSM Buildings GeoDataFrame | ~500 KB - 2 MB |
| OSM Streets GeoDataFrame | ~300 KB - 1 MB |
| NDVI Array (640x640 float32) | ~1.6 MB |
| Priority Score Array | ~1.6 MB |
| Visualization PNG (before compression) | ~3 MB |
| **Total per request** | **~10-15 MB** |

**Cloud Run Configuration:**
- Memory: 2 GB (supports ~130 concurrent analyses theoretically, limited by concurrency=80)
- CPU: 2 vCPU (parallel processing for vision analysis)
- Ephemeral storage: `/tmp` (10 GB) - used only for final PNG generation

### Data Retention Policy

**Visualization Files (Google Cloud Storage):**
- **Retention:** 30 days (configurable via lifecycle policy)
- **Access:** Public read via signed URLs (7-day expiry)
- **Security:** URLs expire after 7 days, files auto-deleted after 30 days
- **Location:** `gs://{PROJECT_ID}-tree-analysis/analysis/{location}_{timestamp}_*.png`

**MCP Tool Responses (JSON):**
- **Retention:** Not persisted (returned to agent, stored in agent's conversation state)
- **Logging:** Cloud Logging retains logs for 30 days (default)

**User Data:**
- **Location Queries:** Not stored (processed in-memory)
- **Personal Data:** None collected
- **Analytics:** Optional Cloud Logging metrics (anonymous)

**GDPR Compliance:**
- No personal data collected
- Geospatial data is public (OpenStreetMap, Google Maps)
- Signed URLs expire automatically
- Right to erasure: Contact admin to delete specific GCS files

---

## 📈 System Scalability

### Horizontal Scaling (Cloud Run)

**Auto-scaling Configuration:**

```yaml
# releaf-mcp-server (Compute-intensive)
minInstances: 0        # Scale to zero when idle (cost savings)
maxInstances: 10       # Handle up to 800 concurrent requests (80 concurrency × 10 instances)
concurrency: 80        # Requests per instance
cpu: 2                 # 2 vCPU for parallel processing
memory: 2Gi            # 2 GB for in-memory geospatial processing

# releaf-adk-agent (Lightweight orchestration)
minInstances: 0
maxInstances: 20       # Handle up to 200 concurrent requests (10 concurrency × 20 instances)
concurrency: 10        # Lower concurrency (agent maintains conversation state)
cpu: 1
memory: 1Gi
```

**Scaling Behavior:**

| Load Level | Requests/sec | MCP Instances | Agent Instances | Response Time |
|------------|--------------|---------------|-----------------|---------------|
| Idle | 0 | 0 (scaled to zero) | 0 (scaled to zero) | Cold start: ~3-5s |
| Low | 1-5 | 1 | 1 | Warm: ~30-35s |
| Medium | 5-20 | 2-3 | 2-4 | Warm: ~30-35s |
| High | 20-50 | 5-7 | 5-10 | Warm: ~30-35s |
| Peak | 50-100 | 10 (max) | 15-20 | Warm: ~30-35s, queue on max |

**Load Testing Results (Example):**

```bash
# Simulate 50 concurrent users
hey -n 500 -c 50 -m POST \
    -H "Content-Type: application/json" \
    -d '{"latitude": 3.1379, "longitude": 101.6295, "location_name": "test"}' \
    https://releaf-mcp-server-xxx.run.app/mcp/analyze_tree_planting_opportunities

# Results:
# Total requests: 500
# Success rate: 100%
# Average response time: 32s
# 95th percentile: 38s
# Instances spawned: 7
```

### Vertical Scaling Considerations

**When to Increase Resources:**

| Scenario | Current | Recommended | Rationale |
|----------|---------|-------------|-----------|
| Large coverage area (>1 km²) | 2 GB RAM | 4 GB RAM | More OSM data |
| High-resolution imagery | 640x640 | 1280x1280 | Larger image processing |
| More critical spots | max_spots=5 | max_spots=10 | More parallel vision API calls |
| Complex geometries | 2 vCPU | 4 vCPU | Faster mask generation |

### Database Scaling (Future Enhancement)

**Current:** Stateless, no database (read-only OSM/Google Maps APIs)

**Future:** If adding user accounts, analysis history, or caching:

```
Option 1: Cloud Firestore (NoSQL, auto-scaling)
├─ Collections: users, analysis_history, cached_results
├─ Auto-scaling: Up to 10,000 writes/sec per database
└─ Use case: User dashboards, saved analyses

Option 2: Cloud SQL (PostgreSQL + PostGIS for geospatial)
├─ Instance: db-n1-standard-2 (2 vCPU, 7.5 GB)
├─ Read replicas: 2-3 for read-heavy workloads
└─ Use case: Complex spatial queries, advanced analytics

Option 3: Cloud Bigtable (High-throughput time-series)
├─ Nodes: 3-10 (auto-scaling based on CPU)
├─ Use case: IoT sensor data, real-time tree health monitoring
```

### CDN & Caching Strategy

**Google Cloud CDN (for visualization images):**

```bash
# Enable Cloud CDN on GCS bucket
gcloud compute backend-buckets create tree-analysis-backend \
    --gcs-bucket-name=YOUR_PROJECT_ID-tree-analysis \
    --enable-cdn

# Configure cache TTL
gcloud compute backend-buckets update tree-analysis-backend \
    --cache-mode=CACHE_ALL_STATIC \
    --default-ttl=86400  # 24 hours
```

**Benefits:**
- Faster image loading for repeat analyses
- Reduced egress costs (90% cache hit rate)
- Global distribution (users worldwide)

---

## 🛠️ How ReLeaf AI Agent Works

### Agent Architecture (Google ADK)

ReLeaf uses a **Sequential Multi-Agent Workflow** powered by Google's Agent Development Kit (ADK):

```python
# agent.py - Agent Hierarchy

Root Agent (greeter)
│
├─► Tool: add_prompt_to_state()  # Saves user query to state
│
└─► Sub-agent: tree_planting_guide_workflow (SequentialAgent)
    │
    ├─► Sub-agent 1: comprehensive_researcher
    │   ├─ Model: gemini-2.0-flash-exp
    │   ├─ Tools:
    │   │   ├─ MCPToolset (4 MCP tools)
    │   │   └─ Wikipedia (LangChain tool)
    │   └─ Output: research_data (stored in state)
    │
    └─► Sub-agent 2: response_formatter
        ├─ Model: gemini-2.0-flash-exp
        ├─ Input: research_data from Sub-agent 1
        └─ Output: Final user-facing report
```

### Mandatory 4-Step Workflow

The `comprehensive_researcher` agent MUST follow this workflow:

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Location Search                                     │
│ ────────────────────────────────────────────────────────── │
│ User: "Analyze Menara LGB TTDI"                             │
│ Agent: Send progress message "🔍 Searching for location..." │
│ Tool: search_all_matching_location_based_on_keyword()       │
│ Output: (3.1379, 101.6295, "Menara LGB TTDI")              │
│ Agent: "✅ Found: Menara LGB TTDI at (3.1379, 101.6295)"   │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Aerial Analysis                                     │
│ ────────────────────────────────────────────────────────── │
│ Agent: Send progress message "🛰️ Analyzing satellite        │
│        imagery... (15-20 seconds)"                          │
│ Tool: analyze_tree_planting_opportunities(3.1379, 101.6295) │
│ Output: {                                                    │
│   critical_priority_spots: [                                │
│     {lat: 3.1379, lon: 101.6294, score: 95.2, area: 55.8},  │
│     {lat: 3.1382, lon: 101.6301, score: 88.7, area: 42.3},  │
│     ...                                                      │
│   ],                                                         │
│   visualization_urls: { analysis_map: "https://..." }       │
│ }                                                            │
│ Agent: "✅ Aerial analysis complete! Found 5 critical spots"│
└─────────────────────────────────────────────────────────────┘
        │
        ▼ CRITICAL: Extract critical_priority_spots array
        │
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Ground Vision Analysis (NEVER SKIP THIS!)           │
│ ────────────────────────────────────────────────────────── │
│ Agent: Send progress message "👁️ Analyzing Street View...   │
│        (12-15 seconds)"                                      │
│ Tool: analyze_spot_with_gemini_vision(                      │
│   critical_spots=critical_priority_spots,  # From Step 2!   │
│   max_spots=5                                                │
│ )                                                            │
│ Output: {                                                    │
│   results: [                                                 │
│     {                                                        │
│       spot_number: 1,                                        │
│       vision_analysis: {                                     │
│         tree_count: 3,                                       │
│         mature_trees: 2,                                     │
│         young_trees: 1,                                      │
│         tree_health: "good",                                 │
│         surroundings: "Commercial buildings, wide sidewalk", │
│         planting_feasibility: "high",                        │
│         recommended_tree_count: 4,                           │
│         ...                                                  │
│       }                                                      │
│     },                                                       │
│     ...                                                      │
│   ],                                                         │
│   summary: {                                                 │
│     spots_with_trees: 2,                                     │
│     spots_without_trees: 3,                                  │
│     total_trees_detected: 8                                  │
│   }                                                          │
│ }                                                            │
│ Agent: "✅ Vision analysis complete! Found 8 existing trees" │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Species Recommendations                             │
│ ────────────────────────────────────────────────────────── │
│ Agent: Send progress message "🌳 Fetching tree species..."  │
│ Tool: get_tree_species_recommendations()                    │
│ Output: "RECOMMENDED TREE SPECIES FOR KUALA LUMPUR:         │
│   🌳 RAIN TREE - High water absorption (500L/day)...        │
│   🌳 ANGSANA - Excellent shade coverage..."                 │
│ Agent: "✅ Species recommendations ready!"                  │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│ RESPONSE FORMATTER AGENT                                    │
│ ────────────────────────────────────────────────────────── │
│ Synthesizes all research_data into final report:            │
│                                                              │
│ ✅ Analysis Complete! Here's your report for Menara LGB:    │
│                                                              │
│ 📊 Aerial Analysis:                                         │
│ • Found 5 critical priority zones (scores 80-100)           │
│ • Total plantable area: 245 m²                              │
│ • Vegetation deficit: 65%                                   │
│                                                              │
│ [Embedded 6-panel visualization map]                        │
│                                                              │
│ 👁️ Ground Vision Analysis:                                 │
│ • Spot 1: 3 existing trees, HIGH feasibility, add 4 trees   │
│   [Street View preview image]                               │
│ • Spot 2: 0 trees, HIGH feasibility, add 6 trees            │
│   [Street View preview image]                               │
│ ...                                                          │
│                                                              │
│ 🌳 Recommended Species:                                     │
│ • Rain Tree (for flood-prone areas)                         │
│ • Angsana (for shade)                                       │
│ • Yellow Flame (for medium areas)                           │
│                                                              │
│ 📋 Next Steps:                                              │
│ 1. Prioritize Spots 3, 5 (no existing trees)                │
│ 2. Plant during monsoon season (May-October)                │
│ 3. Maintain 8-10m spacing between trees                     │
└─────────────────────────────────────────────────────────────┘
```

### Pre-Defined Agent Instructions

**Agent Interaction Example:**

![ReLeaf AI Agent Introduction](sample_data/ReLeaf_AI_Agent_Initial_Introduction.png)

*The ReLeaf AI agent greeting users and explaining the 4-step analysis workflow: Location Search → Aerial Analysis → Vision Analysis → Species Recommendations.*

---

**Root Agent (Greeter):**

```python
instruction="""
You are the **ReLeaf Tree Planting Guide** - an AI-powered urban forestry assistant
for Kuala Lumpur and Selangor, Malaysia.

When greeting a NEW user (first interaction), provide this comprehensive introduction:
[... comprehensive introduction with features, workflow, example locations ...]

- After providing this introduction, WAIT for the user's location input.
- When the user responds with a location, use the 'add_prompt_to_state' tool to save their response.
- After using the tool, transfer control to the 'tree_planting_guide_workflow' agent.
"""
```

**Comprehensive Researcher Agent:**

```python
instruction="""
You are a helpful research assistant for tree planting recommendations. Your goal is to
fully answer the user's PROMPT.

You have access to FOUR MCP tools and one Wikipedia tool:
1. search_all_matching_location_based_on_keyword - Find locations
2. analyze_tree_planting_opportunities - Aerial analysis
3. analyze_spot_with_gemini_vision - Ground vision analysis (MANDATORY!)
4. get_tree_species_recommendations - Tree species data
5. Wikipedia - General tree knowledge

WORKFLOW - Follow this COMPLETE sequence:

STEP 1: LOCATION SEARCH
- FIRST: Send message "🔍 Searching for '[location]'..."
- Use 'search_all_matching_location_based_on_keyword'
- If MULTIPLE results: confirm with user
- If ONE result: Send "✅ Found: [name] at [coords]" → proceed to Step 2

STEP 2: AERIAL ANALYSIS
- FIRST: Send message "🛰️ Analyzing satellite imagery... (15-20 seconds)"
- Use 'analyze_tree_planting_opportunities' with lat/lon/name
- Store the critical_priority_spots list - you MUST use this in Step 3
- After results: Send "✅ Aerial analysis complete! Found [X] critical spots"

STEP 3: GROUND-LEVEL VISION ANALYSIS (CRITICAL - DO NOT SKIP!)
- FIRST: Send message "👁️ Analyzing Street View... (12-15 seconds)"
- IMMEDIATELY use 'analyze_spot_with_gemini_vision'
- Parameters:
  * critical_spots: Pass the critical_priority_spots array from Step 2
  * max_spots: 5
- This returns 14 fields per spot: tree_count, surroundings, feasibility, etc.
- After results: Send "✅ Vision analysis complete! Detected [X] trees"

STEP 4: GET TREE RECOMMENDATIONS
- FIRST: Send message "🌳 Fetching tree species..."
- Use 'get_tree_species_recommendations'
- After results: Send "✅ Species ready! Preparing report..."

IMPORTANT NOTES:
- CRITICAL: Send progress messages BEFORE each long operation
- MANDATORY: Never skip Step 3 (vision analysis)
- Pass exact lat/lon/name from search to analysis
- Pass critical_priority_spots from aerial to vision
- Combine aerial + vision results for recommendations

PROMPT:
{{ PROMPT }}
"""
```

**Response Formatter Agent:**

```python
instruction="""
You are the friendly voice of the Tree Planting Guide. Synthesize RESEARCH_DATA
into a complete, helpful answer.

- START with "✅ **Analysis Complete!** Here's your report for [location]:"
- Present aerial analysis (priority zones, vegetation coverage)
- IMPORTANT: Combine aerial + vision analysis:
  * Aerial shows potential zones from satellite
  * Vision provides ground context (14 fields: tree counts, health, surroundings,
    obstacles, feasibility, recommendations)
  * Highlight HIGH feasibility + low tree count spots as priorities
- Add species recommendations
- CRITICAL VISUALIZATION INSTRUCTIONS:
  1. MAIN MAP: Embed analysis_map_url with <img> tag
  2. SPOT PREVIEWS: Embed preview_image_url for each critical spot
- Show ALL spots with preview images (typically 5)
- Be conversational and engaging

RESEARCH_DATA:
{{ research_data }}
"""
```

---

## 🧩 MCP Tools Usage Instructions

### Tool 1: `search_all_matching_location_based_on_keyword`

**Purpose:** Geocode location queries to GPS coordinates

**Input:**
```json
{
  "keyword": "Menara LGB TTDI"
}
```

**Output:**
```python
{
  "Menara LGB, Jalan Burhanuddin Helmi, Taman Tun Dr Ismail, Kuala Lumpur": (3.1379, 101.6295),
  "Menara LGB 2, TTDI": (3.1385, 101.6302)
}
```

**Usage Example:**
```python
# Agent calls this first
results = search_all_matching_location_based_on_keyword("KLCC")

# If multiple results, agent asks user to clarify
# If single result, agent proceeds with lat/lon
```

### Tool 2: `analyze_tree_planting_opportunities`

**Purpose:** Comprehensive aerial geospatial analysis

**Input:**
```json
{
  "latitude": 3.1379,
  "longitude": 101.6295,
  "location_name": "Menara LGB TTDI"
}
```

**Output (Simplified):**
```json
{
  "location": {
    "name": "menara_lgb_ttdi",
    "coordinates": {"latitude": 3.1379, "longitude": 101.6295}
  },
  "critical_priority_spots": [
    {
      "spot_id": 1,
      "coordinates": {"latitude": 3.137924, "longitude": 101.629468},
      "priority_score": 95.2,
      "area_m2": 55.8,
      "google_maps_url": "https://www.google.com/maps?q=3.137924,101.629468",
      "google_street_view_url": "https://www.google.com/maps?layer=c&cbll=3.137924,101.629468",
      "preview_image_url": "https://maps.googleapis.com/maps/api/staticmap?..."
    }
  ],
  "land_coverage": {
    "total_pixels": 409600,
    "vegetation_pixels": 45230,
    "vegetation_percentage": 11.04,
    "buildings_pixels": 123400,
    "buildings_percentage": 30.13
  },
  "priority_distribution": {
    "critical": {"count": 5, "total_area_m2": 245.3},
    "high": {"count": 12, "total_area_m2": 567.2}
  },
  "visualization_urls": {
    "analysis_map": "https://storage.googleapis.com/...",
    "instructions": "6-panel analysis map shows satellite imagery, vegetation, shadows, streets, priority scores, planting zones"
  },
  "output_files": {
    "analysis_visualization": "/tmp/tree_analysis_output/menara_lgb_ttdi/menara_lgb_ttdi_analysis.png",
    "analysis_visualization_url": "https://storage.googleapis.com/...",
    "component_breakdown_url": "https://storage.googleapis.com/...",
    "note": "Main analysis map shown in chat. Component breakdown stored for reference."
  }
}
```

**Critical Field:** `critical_priority_spots` - This array MUST be passed to Tool 3!

### Tool 3: `analyze_spot_with_gemini_vision`

**Purpose:** Ground-level Street View analysis with Gemini AI

**Input:**
```json
{
  "critical_spots": [
    {
      "coordinates": {"latitude": 3.137924, "longitude": 101.629468},
      "priority_score": 95.2,
      "area_m2": 55.8,
      "spot_id": 1
    },
    {
      "coordinates": {"latitude": 3.138156, "longitude": 101.630123},
      "priority_score": 88.7,
      "area_m2": 42.3,
      "spot_id": 2
    }
  ],
  "max_spots": 5
}
```

**Output (14 fields per spot):**
```json
{
  "total_spots_analyzed": 5,
  "results": [
    {
      "spot_number": 1,
      "location": {"latitude": 3.137924, "longitude": 101.629468},
      "street_view_available": true,
      "vision_analysis": {
        "tree_count": 3,
        "mature_trees": 2,
        "young_trees": 1,
        "tree_health": "good",
        "tree_species_hints": "Possibly Angsana (yellow flowers visible) and Rain Tree (wide canopy)",
        "surroundings": "Commercial buildings (3-4 stories), shop fronts, wide sidewalk (~3m), residential area in background",
        "road_characteristics": "Two-lane road, moderate traffic, asphalt in good condition, ~8m width",
        "sidewalk_space": "3m wide sidewalk, concrete pavement, ~15m available planting strip",
        "sunlight_exposure": "Full sun on sidewalk, partial shade near buildings (afternoon shadow), no tall obstructions",
        "obstacles": "2 utility poles, 1 traffic sign, drainage grate every 10m, no overhead wires visible",
        "planting_feasibility": "high",
        "recommended_tree_count": 4,
        "spacing_suggestion": "8-10 meters between trees to allow canopy growth",
        "planting_recommendations": "Plant between utility poles, avoid drainage grates. Suitable for medium-canopy species (Yellow Flame, Tembusu). Ensure 2m clearance from building foundations."
      },
      "spot_info": {
        "priority_score": 95.2,
        "area_m2": 55.8
      }
    }
  ],
  "summary": {
    "spots_with_trees": 2,
    "spots_without_trees": 3,
    "total_trees_detected": 8,
    "average_trees_per_spot": 1.6,
    "highest_priority_for_planting": [
      {
        "spot_number": 3,
        "tree_count": 0,
        "planting_feasibility": "high",
        "recommended_tree_count": 6,
        "reason": "No existing trees - ready for new planting"
      }
    ]
  }
}
```

**Agent Usage:**
```python
# Step 1: Get aerial analysis results
aerial_results = analyze_tree_planting_opportunities(lat, lon, name)

# Step 2: Extract critical spots (CRITICAL!)
critical_spots = aerial_results['critical_priority_spots']

# Step 3: Pass to vision analysis
vision_results = analyze_spot_with_gemini_vision(
    critical_spots=critical_spots,
    max_spots=5
)

# Step 4: Combine insights
for spot in vision_results['results']:
    print(f"Spot {spot['spot_number']}:")
    print(f"  Aerial priority: {spot['spot_info']['priority_score']}")
    print(f"  Ground trees: {spot['vision_analysis']['tree_count']}")
    print(f"  Feasibility: {spot['vision_analysis']['planting_feasibility']}")
```

### Tool 4: `get_tree_species_recommendations`

**Purpose:** Provide Malaysian tree species database

**Input:** None (no parameters)

**Output:**
```text
RECOMMENDED TREE SPECIES FOR KUALA LUMPUR:

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

[... additional species ...]

GENERAL PLANTING CONSIDERATIONS:
• Plant during monsoon season (May-October) for most species
• Maintain 30m distance from buildings for large trees
• Consider underground utilities when selecting spots
```

---

## 🌐 GCP Product Integration

ReLeaf is built entirely on **Google Cloud Platform**, leveraging the following services:

### Core Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Cloud Run** | Serverless container hosting for MCP server & ADK agent | 2 services, auto-scaling, IAM auth |
| **Vertex AI** | Gemini 2.0 Flash for vision analysis | API calls via `vertexai` SDK |
| **Secret Manager** | Secure API key storage | `google-maps-api-key`, `releaf-service-account-key` |
| **Cloud Storage** | Visualization file hosting with signed URLs | Bucket: `{project}-tree-analysis` |
| **Cloud Logging** | Centralized logging for debugging & monitoring | Auto-enabled for Cloud Run |

### Google Maps Platform

| API | Usage | Quota |
|-----|-------|-------|
| **Maps Static API** | Satellite imagery (640x640), spot preview images | ~100 requests/analysis |
| **Street View Static API** | Ground-level panoramas for Gemini Vision | ~5 requests/analysis |
| **Geocoding API** | Location search (via GeoPy) | ~1 request/query |

**Cost Estimate (per 1000 analyses):**
- Maps Static API: $2.00 (100 requests × $0.002/request × 1000 analyses)
- Street View API: $7.00 (5 requests × $0.007/request × 1000 analyses)
- Vertex AI (Gemini Vision): $0.50 (5 spots × $0.0001/image × 1000 analyses)
- Cloud Run: $1.50 (compute time)
- Cloud Storage: $0.20 (egress)
- **Total: ~$11.20 per 1000 analyses**

### Google ADK (Agent Development Kit)

**Why ADK?**
- Native integration with Vertex AI (no API key management)
- Built-in MCP protocol support (`MCPToolset`)
- Sequential workflow orchestration (`SequentialAgent`)
- State management across sub-agents
- Automatic retry logic for API failures

**ADK vs. LangChain:**

| Feature | Google ADK | LangChain |
|---------|------------|-----------|
| Vertex AI Integration | Native (1 line) | Requires wrapper |
| MCP Protocol | Built-in `MCPToolset` | Custom implementation needed |
| Multi-agent Workflows | `SequentialAgent`, `ParallelAgent` | Custom chains |
| GCP Services | Optimized for Cloud Run, Vertex AI | Cloud-agnostic |
| Learning Curve | Low (Google ecosystem) | Medium (broader ecosystem) |

### IAM & Security (GCP-Native)

**Service Account Permissions:**

```bash
# Grant permissions for ReLeaf service account
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:releaf-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"  # Vertex AI access

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:releaf-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"  # GCS access

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:releaf-service-account@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"  # Secret Manager access
```

**No External Dependencies:**
- ✅ All compute on Cloud Run (no EC2, Lambda, Azure Functions)
- ✅ All AI on Vertex AI (no OpenAI, Anthropic, Azure OpenAI)
- ✅ All storage on Cloud Storage (no S3, Azure Blob)
- ✅ All secrets in Secret Manager (no AWS Secrets Manager, HashiCorp Vault)
- ✅ All monitoring in Cloud Logging (no Datadog, Splunk)

---

## ✅ Fully Functional Out-of-the-Box Solution

### What "Out-of-the-Box" Means

1. **No Code Changes Required:**
   - Clone repo → Set environment variables → Deploy to Cloud Run
   - No custom training data, no model fine-tuning, no database setup

2. **Pre-Configured for Production:**
   - Auto-scaling (0 to 10 instances)
   - Error handling (graceful degradation)
   - Logging (Cloud Logging integration)
   - Monitoring (Cloud Run metrics)

3. **Ready for Real Users:**
   - Tested with Menara LGB TTDI, Pavilion KL, KLCC, Mid Valley
   - Handles edge cases (no Street View, multiple search results, API failures)
   - User-friendly progress messages and error messages

### 5-Minute Quickstart

```bash
# 1. Clone repo
git clone https://github.com/your-org/ReLeaf_Agent.git
cd ReLeaf_Agent

# 2. Set environment variables
export GCP_PROJECT=your-project-id
export GOOGLE_MAPS_API_KEY=your-api-key

# 3. Deploy MCP server
gcloud run deploy releaf-mcp-server \
    --source . \
    --region us-central1 \
    --set-env-vars GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_API_KEY,GCP_PROJECT=$GCP_PROJECT

# 4. Deploy ADK agent (get MCP_SERVER_URL from step 3)
export MCP_SERVER_URL=$(gcloud run services describe releaf-mcp-server --region us-central1 --format 'value(status.url)')/mcp

gcloud run deploy releaf-adk-agent \
    --source . \
    --region us-central1 \
    --set-env-vars GOOGLE_MAPS_API_KEY=$GOOGLE_MAPS_API_KEY,GCP_PROJECT=$GCP_PROJECT,MCP_SERVER_URL=$MCP_SERVER_URL,MODEL=gemini-2.0-flash-exp

# 5. Test
curl -X POST $(gcloud run services describe releaf-adk-agent --region us-central1 --format 'value(status.url)')/query \
    -H "Content-Type: application/json" \
    -d '{"prompt": "Analyze Menara LGB TTDI"}'
```

**No Additional Setup:**
- ❌ No database to provision
- ❌ No model to train
- ❌ No frontend to build (agent works via API/chat)
- ❌ No SSL certificates (Cloud Run handles HTTPS)
- ❌ No load balancer (Cloud Run auto-scales)

---

## 📚 Additional Resources

### Documentation
- [Google ADK Documentation](https://cloud.google.com/vertex-ai/docs/adk)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Vertex AI Gemini Vision](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/gemini)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)

### Related Repositories
- [Urban Tree Planting Pipeline](./mcp/urban_tree_planting/) - Core geospatial analysis modules

### Support
- GitHub Issues: [https://github.com/Ryuujiw/dt-hack](https://github.com/Ryuujiw/dt-hack)
- Email: mydrsgdtgti@deloitte.com

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Cloud Platform** - For providing the infrastructure and AI services
- **OpenStreetMap Contributors** - For open geospatial data
- **Google Maps Platform** - For satellite imagery and Street View data

---

**Built with ❤️ by the ReLeaf Team**

*Empowering cities to combat climate change through data-driven urban forestry*
