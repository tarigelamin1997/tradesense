#!/bin/bash

# Frontend Build Optimization Script for TradeSense
# This script optimizes the production build

echo "🚀 Starting TradeSense Frontend Build Optimization..."
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: Not in frontend directory. Run this script from the frontend folder.${NC}"
    exit 1
fi

# Step 1: Install optimization dependencies
echo -e "\n${YELLOW}1. Installing optimization dependencies...${NC}"
npm install --save-dev \
    vite-plugin-compression \
    rollup-plugin-visualizer \
    terser \
    @rollup/plugin-terser \
    vite-plugin-pwa \
    workbox-window

# Step 2: Clean previous builds
echo -e "\n${YELLOW}2. Cleaning previous builds...${NC}"
rm -rf dist .svelte-kit/output

# Step 3: Run production build with optimized config
echo -e "\n${YELLOW}3. Building with optimizations...${NC}"
# Use optimized config if it exists
if [ -f "vite.config.optimized.ts" ]; then
    echo "Using optimized Vite config..."
    mv vite.config.ts vite.config.backup.ts
    cp vite.config.optimized.ts vite.config.ts
fi

# Build with production environment
NODE_ENV=production npm run build

# Restore original config
if [ -f "vite.config.backup.ts" ]; then
    mv vite.config.backup.ts vite.config.ts
fi

# Step 4: Analyze build size
echo -e "\n${YELLOW}4. Analyzing build size...${NC}"
if [ -d "dist" ]; then
    echo "Build output size:"
    du -sh dist
    echo ""
    echo "Largest files:"
    find dist -type f -exec du -h {} + | sort -rh | head -10
fi

# Step 5: Check for large chunks
echo -e "\n${YELLOW}5. Checking for large chunks...${NC}"
LARGE_FILES=$(find dist -name "*.js" -size +500k 2>/dev/null)
if [ -n "$LARGE_FILES" ]; then
    echo -e "${RED}Warning: Found large JavaScript files (>500KB):${NC}"
    echo "$LARGE_FILES" | while read file; do
        size=$(du -h "$file" | cut -f1)
        echo "  - $file ($size)"
    done
else
    echo -e "${GREEN}✓ No large JavaScript chunks found${NC}"
fi

# Step 6: Generate bundle analysis report
echo -e "\n${YELLOW}6. Generating bundle analysis...${NC}"
if command -v npx &> /dev/null; then
    ANALYZE=true npm run build > /dev/null 2>&1
    if [ -f "dist/stats.html" ]; then
        echo -e "${GREEN}✓ Bundle analysis report generated: dist/stats.html${NC}"
    fi
fi

# Step 7: Optimize images (if imagemin is available)
echo -e "\n${YELLOW}7. Optimizing images...${NC}"
if command -v npx &> /dev/null && [ -d "dist/assets/images" ]; then
    npx imagemin dist/assets/images/* --out-dir=dist/assets/images 2>/dev/null || echo "Skipping image optimization (imagemin not available)"
fi

# Step 8: Generate build report
echo -e "\n${YELLOW}8. Generating build report...${NC}"
cat > dist/build-report.txt << EOF
TradeSense Frontend Build Report
================================
Build Date: $(date)
Node Version: $(node -v)
NPM Version: $(npm -v)

Build Size Summary:
$(du -sh dist)

File Count:
- JavaScript files: $(find dist -name "*.js" | wc -l)
- CSS files: $(find dist -name "*.css" | wc -l)
- HTML files: $(find dist -name "*.html" | wc -l)
- Total files: $(find dist -type f | wc -l)

Compression:
- Gzip files: $(find dist -name "*.gz" 2>/dev/null | wc -l)
- Brotli files: $(find dist -name "*.br" 2>/dev/null | wc -l)

Largest Assets:
$(find dist -type f -exec du -h {} + | sort -rh | head -5)
EOF

echo -e "${GREEN}✓ Build report saved to: dist/build-report.txt${NC}"

# Step 9: Performance recommendations
echo -e "\n${YELLOW}9. Performance Recommendations:${NC}"
echo "1. Enable gzip/brotli compression on your web server"
echo "2. Set up CDN for static assets"
echo "3. Configure proper cache headers:"
echo "   - Static assets: Cache-Control: max-age=31536000"
echo "   - HTML files: Cache-Control: no-cache"
echo "4. Enable HTTP/2 on your server"
echo "5. Consider lazy loading for large components"

echo -e "\n${GREEN}✅ Build optimization complete!${NC}"
echo "=================================================="

# Show final build size
echo -e "\nFinal build size: $(du -sh dist | cut -f1)"