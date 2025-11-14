---
theme: default
background: https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=1920
class: text-center
highlighter: shiki
lineNumbers: false
info: |
  ## ReLeaf - Agentic AI for Urban Tree Planting
  Transforming Corporate Carbon Footprints into Climate Action
drawings:
  persist: false
transition: slide-left
title: ReLeaf - Agentic AI
mdc: true
colorSchema: dark
exportFilename: ReLeaf-Presentation
export:
  format: pdf
  timeout: 30000
  dark: true
  withClicks: false
---

# ReLeaf 🌿

## Agentic AI for Urban Tree Planting

Transforming Carbon Footprints into Climate Action

<div class="pt-12">
  <span class="text-sm opacity-75">Team - ReLeaf the Earth</span>
</div>

 
---
layout: center
class: text-center
---

# The Vision 🌍

<div class="text-xl pt-6 pb-8 leading-relaxed max-w-3xl mx-auto">
  ReLeaf transforms Deloitte into a living, breathing example of corporate climate leadership —
  <span class="font-bold text-green-400">powered by cutting-edge  agentic AI</span>.
</div>

<div class="pt-8 text-lg opacity-75">
  This isn't just sustainability — it's <span class="font-bold">accountability</span>.
</div>

---
layout: default
---

# Benefits of Trees 🌳
 
<div class="grid grid-cols-2 gap-6 pt-8">
 
<div class="space-y-4">
 
### Known Ecological Benefits
 
<div class="space-y-3 text-lg">
  <div class="flex items-center gap-3">
    <div class="text-2xl">💨</div>
    <div>
      <div class="font-bold">Air Pollution Removal</div>
      <div class="text-sm opacity-75">Cleaner urban air</div>
    </div>
  </div>
 
  <div class="flex items-center gap-3">
    <div class="text-2xl">💧</div>
    <div>
      <div class="font-bold">Stormwater Interception</div>
      <div class="text-sm opacity-75">Reduces flooding</div>
    </div>
  </div>
 
  <div class="flex items-center gap-3">
    <div class="text-2xl">⚡</div>
    <div>
      <div class="font-bold">Energy Conservation</div>
      <div class="text-sm opacity-75">Natural cooling</div>
    </div>
  </div>
 
  <div class="flex items-center gap-3">
    <div class="text-2xl">🌍</div>
    <div>
      <div class="font-bold">Carbon Dioxide Storage</div>
      <div class="text-sm opacity-75">Climate action</div>
    </div>
  </div>
</div>
 
</div>
 
<div>
 
### Why This Matters
 
<div class="space-y-3 text-sm bg-green-500 bg-opacity-10 rounded-lg p-6 border-2 border-green-400">
  <div class="flex items-start gap-2">
    <div class="text-xl">🏥</div>
    <div>
      <div class="font-bold">Health Benefits</div>
      <div class="opacity-75">Looking at trees reduces stress significantly</div>
    </div>
  </div>
 
  <div class="flex items-start gap-2">
    <div class="text-xl">🧘</div>
    <div>
      <div class="font-bold">Forest Bathing Trend</div>
      <div class="opacity-75">Rising popularity worldwide</div>
    </div>
  </div>
 
  <div class="flex items-start gap-2">
    <div class="text-xl">❄️</div>
    <div>
      <div class="font-bold">Urban Cooling</div>
      <div class="opacity-75">Lowers energy consumption</div>
    </div>
  </div>
 
  <div class="flex items-start gap-2">
    <div class="text-xl">🌊</div>
    <div>
      <div class="font-bold">Flood Alleviation</div>
      <div class="opacity-75">Critical for Malaysia's climate</div>
    </div>
  </div>
</div>
 
</div>
 
</div>

---
layout: default
---

# Why This Analysis is Important 🎯
 
<div class="grid grid-cols-2 gap-8 pt-8">
 
<div class="space-y-3">
 
### Urban Planning Benefits
 
<div class="p-4 bg-blue-500 bg-opacity-10 rounded-lg border-l-4 border-blue-400">
  <div class="font-bold text-lg pb-2">💧 Flood Alleviation</div>
  <div class="text-sm opacity-90">Strategic tree placement to intercept stormwater and reduce flooding risks</div>
</div>
 
<div class="p-4 bg-green-500 bg-opacity-10 rounded-lg border-l-4 border-green-400">
  <div class="font-bold text-lg pb-2">🚶 Walkable Cities</div>
  <div class="text-sm opacity-90">Shade and greenery encourage pedestrian activity and safer streets</div>
</div>
 
<div class="p-4 bg-purple-500 bg-opacity-10 rounded-lg border-l-4 border-purple-400">
  <div class="font-bold text-lg pb-2">🌍 Air Quality</div>
  <div class="text-sm opacity-90">Data-backed decisions to improve urban air quality</div>
</div>
 
</div>
 
<div class="space-y-3">
 
### Critical Needs
 
<div class="p-4 bg-yellow-500 bg-opacity-10 rounded-lg border-l-4 border-yellow-400">
  <div class="font-bold text-lg pb-2">🌳 Road Disaster Prevention</div>
  <div class="text-sm opacity-90">Proactive measures to prevent tree-related accidents during storms</div>
</div>
 
<div class="p-4 bg-red-500 bg-opacity-10 rounded-lg border-l-4 border-red-400">
  <div class="font-bold text-lg pb-2">⚠️ Pedestrian Safety</div>
  <div class="text-sm opacity-90">Trees provide shelter and reduce urban hazards</div>
</div>
 
<div class="p-4 bg-pink-500 bg-opacity-10 rounded-lg border-l-4 border-pink-400">
  <div class="font-bold text-lg pb-2">🌱 Greener Cities</div>
  <div class="text-sm opacity-90">Nature in the city improves wellbeing and lowers stress</div>
</div>
 
</div>
 
</div>
 
---
layout: default
---

# Architecture

```mermaid
graph TB
    subgraph "User Interface"
        USER[👤 User Query]
    end
   
    subgraph "Google Agent Development Kit"
        AGENT[🤖 ReLeaf Agent<br/>Sequential Agent]
        RESEARCHER[🔍 Researcher Agent<br/>Data Collection]
        FORMATTER[📝 Formatter Agent<br/>Response Generation]
    end
   
    subgraph "MCP Tools Layer"
        MCP[MCP Toolset<br/>HTTP Connection]
        WIKI[Wikipedia Tool<br/>External Knowledge]
    end
   
    subgraph "MCP Server - Cloud Run"
        SEARCH[🔍 Geocoding Search<br/>Location Resolution]
        AERIAL[🛰️ Aerial Analysis<br/>Satellite + OSM]
        VISION[👁️ Vision Analysis<br/>Street View + Gemini]
        SPECIES[🌳 Species Recommendations<br/>Malaysian Climate]
    end
   
    subgraph "Analysis Pipeline"
        DOWNLOAD[Image Downloader<br/>Google Maps API]
        DETECT[Vegetation Detector<br/>NDVI Analysis]
        MASK[Mask Generator<br/>OSM Geometries]
        PRIORITY[Priority Calculator<br/>Scoring System]
        VIZ[Visualizer<br/>6-Panel Output]
        GROUND[Ground Detector<br/>YOLO + Street View]
    end
   
    subgraph "External APIs"
        GMAPS[Google Maps API<br/>Satellite Imagery]
        OSM[OpenStreetMap<br/>Geospatial Data]
        STREETVIEW[Street View API<br/>Ground Images]
        GEMINI[Gemini Vision API<br/>AI Image Analysis]
    end
   
    subgraph "Storage"
        GCS[☁️ Google Cloud Storage<br/>Visualization Files]
        OUTPUT[📁 Output Files<br/>PNG + JSON]
    end
   
    USER --> AGENT
    AGENT --> RESEARCHER
    RESEARCHER --> MCP
    RESEARCHER --> WIKI
    MCP --> SEARCH
    MCP --> AERIAL
    MCP --> VISION
    MCP --> SPECIES
   
    SEARCH --> GMAPS
    AERIAL --> DOWNLOAD
    DOWNLOAD --> GMAPS
    DOWNLOAD --> OSM
    AERIAL --> DETECT
    AERIAL --> MASK
    AERIAL --> PRIORITY
    AERIAL --> VIZ
    VIZ --> GCS
   
    VISION --> GROUND
    GROUND --> STREETVIEW
    GROUND --> GEMINI
   
    RESEARCHER --> FORMATTER
    FORMATTER --> USER
   
    GCS --> OUTPUT
```

---
layout: center
class: text-center
---

# Let's See It In Action 🚀

<div class="pt-8">
  <div class="p-6 bg-gray-800 rounded-lg inline-block text-left font-mono text-sm">
    <div class="text-green-400 pb-2">🤖 Agent URL:</div>
    <div class="text-blue-400">https://releaf-agent-254863210019.us-central1.run.app</div>
    <div class="text-green-400 pt-4 pb-2">💬 Try asking:</div>
    <div class="text-blue-400">"Analyze tree planting opportunities near Menara LGB"</div>
  </div>
</div>

---
layout: default
---

# Business Value for Deloitte 💼

<div class="grid grid-cols-2 gap-6 pt-6">

<div class="p-5 bg-green-500 bg-opacity-10 rounded-lg border-2 border-green-400">
  <div class="text-3xl pb-3">🌱</div>
  <div class="font-bold text-xl pb-2">Environmental Leadership</div>
  <div class="text-sm space-y-2">
    <div>✓ Turn carbon footprint into measurable action</div>
    <div>✓ Lead by example in sustainability</div>
  </div>
</div>

<div class="p-5 bg-blue-500 bg-opacity-10 rounded-lg border-2 border-blue-400">
  <div class="text-3xl pb-3">💼</div>
  <div class="font-bold text-xl pb-2">Client Solutions</div>
  <div class="text-sm space-y-2">
    <div>✓ Offer as consulting service</div>
    <div>✓ New revenue stream opportunity</div>
  </div>
</div>

<div class="p-5 bg-purple-500 bg-opacity-10 rounded-lg border-2 border-purple-400">
  <div class="text-3xl pb-3">🏙️</div>
  <div class="font-bold text-xl pb-2">Urban Planning</div>
  <div class="text-sm space-y-2">
    <div>✓ Collaborate with city governments</div>
    <div>✓ Support KL sustainability plans</div>
  </div>
</div>

<div class="p-5 bg-yellow-500 bg-opacity-10 rounded-lg border-2 border-yellow-400">
  <div class="text-3xl pb-3">📣</div>
  <div class="font-bold text-xl pb-2">Brand Differentiation</div>
  <div class="text-sm space-y-2">
    <div>✓ Showcase AI innovation in climate tech</div>
    <div>✓ Sustainability thought leadership</div>
  </div>
</div>

</div>

---
layout: end
class: text-center
---

# 🌿 ReLeaf

📊 City Councils Can Now Make Data-Backed Decisions<br>
Moving from intuition to evidence-based urban planning

Turn guilt into measurable action.<br>
Together, we make Deloitte a living example of corporate climate leadership!