# Publication Management System

This document describes the enhanced publication management system for the MIDeL website, which allows Mayo-Radiology-Informatics-Lab organization members to easily submit publications while maintaining quality control and access restrictions.

## Overview

The publication management system consists of:

1. **GitHub Issues-based submission workflow**
2. **Automated validation and access control**
3. **Web-based submission interface**
4. **JSON-based publication storage**

## Features

### ✅ **Access Control**
- Only Mayo-Radiology-Informatics-Lab organization members can submit publications
- GitHub organization membership is verified automatically
- Submissions are validated through GitHub Actions

### ✅ **Easy Submission Process**
- Web-based submission form integrated into the publications page
- Pre-filled GitHub issue templates
- Automatic validation of submission format

### ✅ **Quality Control**
- JSON schema validation
- Duplicate publication detection
- URL format validation
- Maintainer review process through GitHub PRs

### ✅ **Enhanced User Experience**
- Search and filter functionality
- Export to BibTeX format
- Publication statistics
- Responsive design

## How to Submit a Publication

### For Organization Members

1. **Visit the Publications Page**
   - Go to `papers.html` on the MIDeL website
   - The submission section will be visible at the top

2. **Authenticate with GitHub**
   - Click "Connect with GitHub"
   - Enter your GitHub username (in demo mode)
   - System verifies your organization membership

3. **Submit Publication**
   - Click "Submit Publication" (appears after authentication)
   - Fill in basic publication details
   - System opens a pre-filled GitHub issue

4. **Complete the GitHub Issue**
   - Review and complete all required fields
   - Submit the GitHub issue
   - Maintainers will review and process

### For Maintainers

1. **Review Submissions**
   - Check GitHub issues with `publication` label
   - Verify publication details and relevance
   - Ensure no duplicates exist

2. **Add to JSON**
   - Edit `assets/html/publications.json`
   - Add publication entry following the schema
   - Create pull request with changes

3. **Validation**
   - GitHub Actions automatically validates the JSON
   - Checks for duplicates and required fields
   - Validates URL formats

4. **Merge and Deploy**
   - Once validated, merge the PR
   - Changes are automatically deployed via GitHub Pages

## File Structure

### Core Files

```
/.github/
  /ISSUE_TEMPLATE/
    publication_submission.md     # GitHub issue template
  /workflows/
    publication_management.yml    # Automated validation workflow

/assets/
  /html/
    publications.json            # Publication data store
  /js/custom/
    publications.js              # Frontend logic with auth
    
papers.html                      # Enhanced publications page
PUBLICATION_MANAGEMENT.md        # This documentation
```

### Publication JSON Schema

```json
[
  {
    "year": 2024,
    "publications": [
      {
        "id": "2024_unique_identifier",
        "title": "Publication Title",
        "url": "https://doi.org/...",
        "type": "journal",
        "status": "published"
      }
    ]
  }
]
```

#### Field Descriptions

- **year**: Publication year (number) or "older" for pre-2022
- **id**: Unique identifier (format: `YYYY_brief_title`)
- **title**: Full publication title
- **url**: DOI, PubMed, or journal URL
- **type**: `journal`, `conference`, `preprint`, `book_chapter`, `other`
- **status**: `published`, `in_process`, `accepted`

## GitHub Actions Workflow

### Triggers

- **Issue Events**: `opened`, `edited` with `publication` label
- **Pull Request Events**: Changes to `publications.json`

### Validation Steps

1. **Organization Membership Check**
   - Verifies user is active member of Mayo-Radiology-Informatics-Lab
   - Closes issue if not authorized
   - Adds validation labels

2. **JSON Structure Validation**
   - Validates JSON syntax
   - Checks required fields presence
   - Validates URL formats

3. **Duplicate Detection**
   - Checks for duplicate publication IDs
   - Prevents duplicate entries

4. **Quality Assurance**
   - Posts validation results
   - Provides statistics
   - Guides maintainers through review

## Web Interface Features

### Authentication System

The web interface includes a simplified authentication system for demonstration:

- **Mock Authentication**: Uses localStorage for demo purposes
- **Organization Check**: Simulates GitHub API membership verification
- **Progressive Enhancement**: Features appear only for authorized users

### Enhanced User Experience

- **Real-time Search**: Filter publications by title
- **Year Filtering**: Show publications by specific years
- **Status Filtering**: Filter by publication status
- **Export Functions**: Download BibTeX files
- **Link Validation**: Check for broken/placeholder URLs
- **Publication Statistics**: View counts by year

## Security Considerations

### Current Implementation (Demo)

- Uses simplified authentication for demonstration
- Mock organization membership checking
- Client-side token storage (localStorage)

### Production Recommendations

1. **OAuth Integration**
   - Implement proper GitHub OAuth flow
   - Secure token handling and storage
   - Server-side membership verification

2. **API Security**
   - Use GitHub Personal Access Tokens
   - Implement rate limiting
   - Add CSRF protection

3. **Data Validation**
   - Server-side validation
   - Sanitize user inputs
   - Prevent XSS attacks

## Troubleshooting

### Common Issues

**Issue**: "Access Denied" message
**Solution**: Ensure you are a member of the Mayo-Radiology-Informatics-Lab organization

**Issue**: GitHub issue not opening
**Solution**: Check popup blockers; try opening the link manually

**Issue**: JSON validation failing
**Solution**: Verify JSON syntax and required fields; check duplicate IDs

### For Developers

**Authentication Issues**
```javascript
// Clear stored authentication
localStorage.removeItem('github_token');
localStorage.removeItem('github_user');
location.reload();
```

**Mock Membership Testing**
```javascript
// Add test username to mock members list
const mockMembers = ['your-username', 'test-user'];
```

## Future Enhancements

### Planned Features

1. **Real GitHub OAuth Integration**
2. **Advanced Search with Filters**
3. **Author Management System**
4. **Citation Metrics Integration**
5. **Automated Publication Discovery**
6. **Enhanced Export Formats (EndNote, RIS)**
7. **Publication Categorization**
8. **Advanced Analytics Dashboard**

### API Endpoints (Future)

Consider implementing REST API endpoints:

```
GET /api/publications          # Get all publications
POST /api/publications         # Submit new publication
PUT /api/publications/:id      # Update publication
DELETE /api/publications/:id   # Remove publication
GET /api/stats                 # Get statistics
```

## Contributing

To contribute to the publication management system:

1. Fork the repository
2. Create a feature branch
3. Make changes and test thoroughly
4. Submit a pull request with detailed description
5. Ensure all GitHub Actions pass

## Support

For issues or questions:

1. Check this documentation first
2. Search existing GitHub issues
3. Create a new issue with detailed description
4. Tag relevant maintainers

---

**Last Updated**: 2024-06-19
**Version**: 1.0.0
**Maintainers**: Mayo-Radiology-Informatics-Lab team