# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MIDeL (Medical Image Deep Learning) is an educational static website that helps healthcare professionals and medical imaging scientists learn deep learning methods for medical images. The site combines comprehensive text content with practical Jupyter notebook examples focusing on the MONAI framework, Python, and PyTorch.

## Development Environment

This is a **static website** with no build process or package managers. All dependencies are loaded via CDN.

### Key Dependencies
- **Frontend**: HTML5, CSS3, JavaScript (jQuery 3.3.1)
- **UI Framework**: Bootstrap 5.2.0-beta1
- **Content Management**: JSON-based system

### Testing/Development
- **Local Testing**: Use a simple HTTP server to serve files locally
- **Common command**: `python -m http.server 8000` or `npx http-server`
- **Chrome Note**: The comment in `main.js:1` indicates Chrome needs `--allow-file-access-from-files` flag for local file testing

## Architecture

### Content Management System
- **Dynamic Content**: Driven by JSON files in `/assets/html/`
- **chapters.json**: Contains all educational content structure with 18 main topics
- **Content Levels**: Three difficulty tiers (beginner/intermediate/advanced)
- **External Integration**: GitHub notebooks automatically convert to Google Colab links

### File Structure
```
/assets/
  /css/           - Page-specific stylesheets
  /html/          - JSON data files and HTML components (menu.html, footer.html)
  /js/custom/     - JavaScript modules (main.js, chapters.js, etc.)
  /icons/         - UI icons and graphics
  /imgs/          - Images and team photos

/chapters/        - 25+ Jupyter notebooks (.ipynb files)
```

### Key JavaScript Modules
- **main.js**: Handles menu/footer loading and SVG processing
- **chapters.js**: Dynamically generates chapter content from JSON
- **chapters.json**: Central content configuration with notebook links that auto-redirect to Colab

### Content Updates
When adding new educational content:
1. Add Jupyter notebook to `/chapters/` directory
2. Update `/assets/html/chapters.json` with new entry
3. Include proper difficulty level and GitHub notebook link
4. Links automatically convert from GitHub to Google Colab via JavaScript

### Styling System
- **Bootstrap-based**: Responsive design with custom overrides
- **Page-specific CSS**: Each HTML page has corresponding CSS file
- **Theme Colors**: Primary color #68ACC6 (teal), secondary #71A9B1

## Publication Management System

The site includes an enhanced publication management system with GitHub organization access control:

### Key Features
- **GitHub Issues-based submissions**: Publications submitted via standardized GitHub issues
- **Access Control**: Only Mayo-Radiology-Informatics-Lab organization members can submit
- **Automated Validation**: GitHub Actions workflow validates JSON structure and prevents duplicates
- **Web Interface**: Enhanced papers.html with search, filtering, and submission capabilities

### Files and Workflow
- **Issue Template**: `.github/ISSUE_TEMPLATE/publication_submission.md`
- **Validation Workflow**: `.github/workflows/publication_management.yml`
- **Data Store**: `assets/html/publications.json` (JSON-based publication database)
- **Frontend**: `assets/js/custom/publications.js` with GitHub auth integration
- **Documentation**: `PUBLICATION_MANAGEMENT.md`

### Submission Process
1. Organization members authenticate via GitHub (simplified demo implementation)
2. Submit publication details through web interface
3. System creates pre-filled GitHub issue
4. Maintainers review and add to JSON file via PR
5. GitHub Actions validate changes before merge

## Deployment

- **Platform**: GitHub Pages
- **URL**: mayo-radiology-informatics-lab.github.io/MIDeL/
- **Process**: Direct push to main branch (no build step required)
- **Analytics**: Google Analytics integrated (tracking ID: G-QD6MB5R106)

## Educational Content Structure

The curriculum spans 18 main topics from ML fundamentals to advanced concepts like LLMs and active learning. Each topic has up to 3 difficulty levels with corresponding Jupyter notebooks that execute in Google Colab for hands-on learning.