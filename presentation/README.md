## 🚀 Quick Start

### Option 1: Run with Node.js (Recommended)

1. **Install dependencies:**
   ```powershell
   cd presentation
   npm install
   ```

2. **Start the presentation:**
   ```powershell
   npm run dev
   ```

3. **Open in browser:**
   - Navigate to: http://localhost:3030
   - Slides will auto-reload on changes

### Option 2: Export to PDF (For Download)

1. **Install dependencies** (if not done):
   ```powershell
   npm install
   ```

2. **Install Playwright** (required for PDF export):
   ```powershell
   npx playwright install chromium
   ```

3. **Export to PDF:**
   ```powershell
   npm run export-pdf
   ```

4. **Find your PDF:**
   - Output: `ReLeaf-Presentation.pdf`
   - Professional quality, print-ready

## 🎨 Customization

### Change Theme:

Edit the `theme` property in `slides.md`:
```yaml
---
theme: default  # Try: seriph, apple-basic, shibainu, etc.
---
```

### Change Background:

Replace the `background` URL in slide frontmatter:
```yaml
---
background: https://your-image-url.jpg
---
```

## 🔧 Troubleshooting

### Slides won't start?

```powershell
# Clear cache and reinstall
rm -r node_modules
rm package-lock.json
npm install
npm run dev
```

### PDF export fails?

```powershell
# Install Playwright browsers
npx playwright install --with-deps chromium
npm run export-pdf
```

### Port 3030 already in use?

```powershell
# Use different port
npx slidev slides.md --port 3031
```
