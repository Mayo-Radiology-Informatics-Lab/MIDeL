$(document).ready(function(){
    // Check if user wants to enable submission features
    checkGitHubAuthStatus();
    
    // Set up real-time duplicate checking
    $(document).on('input', '#pubTitle', function() {
        // Debounce the duplicate check
        clearTimeout(this.duplicateCheckTimeout);
        this.duplicateCheckTimeout = setTimeout(checkForDuplicateTitle, 500);
    });
    
    // Set current year as default
    const currentYear = new Date().getFullYear();
    $(document).on('focus', '#pubYear', function() {
        if (!this.value) {
            this.value = currentYear;
        }
    });
    
    $.getJSON("./assets/html/publications.json", function(data){
        publications_html = ""
        
        // Group publications by year and sort in descending order
        data.sort((a, b) => {
            if (a.year === "older") return 1;
            if (b.year === "older") return -1;
            return b.year - a.year;
        });
        
        for (let i = 0; i < data.length; i++){
            year_group = data[i]
            year = year_group.year
            publications = year_group.publications
            
            // Create year section
            year_display = year === "older" ? "Older" : year
            publications_html += `<h2>${year_display}</h2><ul>`
            
            // Add each publication in the year group
            for (let j = 0; j < publications.length; j++){
                publication = publications[j]
                
                // Handle different publication statuses
                let link_class = ""
                let target = 'target="_blank"'
                
                if (publication.status === "in_process") {
                    link_class = 'class="text-muted"'
                    target = ""
                } else if (publication.url === "path" || publication.url === "NotAvailableYet") {
                    link_class = 'class="text-muted"'
                    target = ""
                }
                
                publications_html += `<li><a href="${publication.url}" ${target} ${link_class}>${publication.title}</a></li>`
            }
            
            publications_html += `</ul>`
        }
        
        $("#publications-content").html(publications_html)
    }).fail(function(){
        console.log("An error has occurred loading publications.");
        $("#publications-content").html("<p>Error loading publications. Please try again later.</p>");
    });
    
    // Add search functionality
    $("#publication-search").on("keyup", function() {
        var value = $(this).val().toLowerCase();
        $("#publications-content li").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });
    
    // Add filter functionality by year
    $("#year-filter").on("change", function() {
        var selectedYear = $(this).val();
        if (selectedYear === "all") {
            $("#publications-content h2, #publications-content ul").show();
        } else {
            $("#publications-content h2, #publications-content ul").hide();
            $("#publications-content h2").each(function() {
                if ($(this).text().toLowerCase() === selectedYear.toLowerCase()) {
                    $(this).show();
                    $(this).next("ul").show();
                }
            });
        }
    });
    
    // Add filter functionality by status
    $("#status-filter").on("change", function() {
        // This would require additional data attributes or restructuring
        // For now, we'll implement basic functionality
        var selectedStatus = $(this).val();
        if (selectedStatus === "all") {
            $("#publications-content li").show();
        } else if (selectedStatus === "published") {
            $("#publications-content li").show();
            $("#publications-content li a.text-muted").parent().hide();
        } else if (selectedStatus === "in_process") {
            $("#publications-content li").hide();
            $("#publications-content li a.text-muted").parent().show();
        }
    });
});

// Function to export publications to BibTeX format (basic implementation)
function exportToBibTeX() {
    $.getJSON("./assets/html/publications.json", function(data) {
        let bibtex = "";
        
        data.forEach(year_group => {
            year_group.publications.forEach(pub => {
                if (pub.status === "published" && pub.url !== "path" && pub.url !== "NotAvailableYet") {
                    bibtex += `@article{${pub.id},\n`;
                    bibtex += `  title={${pub.title}},\n`;
                    bibtex += `  year={${year_group.year === "older" ? "various" : year_group.year}},\n`;
                    bibtex += `  url={${pub.url}}\n`;
                    bibtex += `}\n\n`;
                }
            });
        });
        
        // Create and download file
        const element = document.createElement('a');
        const file = new Blob([bibtex], {type: 'text/plain'});
        element.href = URL.createObjectURL(file);
        element.download = 'ril_publications.bib';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    });
}

// Function to validate publication links (basic implementation)
function validateLinks() {
    $.getJSON("./assets/html/publications.json", function(data) {
        let broken_links = [];
        
        data.forEach(year_group => {
            year_group.publications.forEach(pub => {
                if (pub.url === "path" || pub.url === "NotAvailableYet" || pub.url === "#") {
                    broken_links.push({
                        title: pub.title,
                        year: year_group.year,
                        url: pub.url
                    });
                }
            });
        });
        
        if (broken_links.length > 0) {
            console.log("Publications with placeholder URLs:", broken_links);
            alert(`Found ${broken_links.length} publications with placeholder URLs. Check console for details.`);
        } else {
            alert("All publication URLs appear to be valid.");
        }
    });
}

// Function to get publication count by year
function getPublicationStats() {
    $.getJSON("./assets/html/publications.json", function(data) {
        let stats = {};
        let total = 0;
        
        data.forEach(year_group => {
            stats[year_group.year] = year_group.publications.length;
            total += year_group.publications.length;
        });
        
        console.log("Publication Statistics:", stats);
        console.log("Total Publications:", total);
        
        return {stats, total};
    });
}

// GitHub Authentication and Submission Functions
function checkGitHubAuthStatus() {
    // Show the GitHub auth section for users who want to submit
    $('#github-auth-section').show();
    
    // Check if there's a stored GitHub token (in a real implementation, this would be more secure)
    const githubToken = localStorage.getItem('github_token');
    const githubUser = localStorage.getItem('github_user');
    
    if (githubToken && githubUser) {
        showAuthenticatedState(githubUser);
        checkOrganizationMembership(githubToken, githubUser);
    }
}

function authenticateWithGitHub() {
    // In a production environment, this would use OAuth flow
    // For demonstration, we'll use a simplified approach
    
    const githubUsername = prompt("Enter your GitHub username (for demonstration):");
    
    if (githubUsername) {
        // Simulate checking organization membership
        // In production, this would use proper OAuth and GitHub API
        
        $('#auth-status').html(`
            <div class="alert alert-info">
                <i class="fas fa-spinner fa-spin"></i> Checking organization membership for ${githubUsername}...
            </div>
        `);
        
        // Simulate API call delay
        setTimeout(() => {
            // For demonstration, we'll assume certain usernames are members
            // In production, this would be a real API call
            const isMember = checkMockMembership(githubUsername);
            
            if (isMember) {
                localStorage.setItem('github_user', githubUsername);
                localStorage.setItem('github_token', 'mock_token'); // In production, use real token
                showAuthenticatedState(githubUsername);
                showSubmissionButton();
            } else {
                $('#auth-status').html(`
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle"></i> 
                        User ${githubUsername} is not a member of the Mayo-Radiology-Informatics-Lab organization.
                    </div>
                `);
            }
        }, 1500);
    }
}

function checkMockMembership(username) {
    // This is a mock function for demonstration
    // In production, this would call the GitHub API
    const mockMembers = ['slowvak', 'your-username', 'test-user', 'admin', 'researcher'];
    return mockMembers.includes(username.toLowerCase());
}

function showAuthenticatedState(username) {
    $('#github-auth-btn').hide();
    $('#auth-status').html(`
        <div class="alert alert-success">
            <i class="fas fa-check-circle"></i> 
            Authenticated as <strong>${username}</strong> 
            <button class="btn btn-sm btn-outline-secondary ms-2" onclick="logout()">Logout</button>
        </div>
    `);
}

function showSubmissionButton() {
    $('#submit-publication-btn').show();
    $('#auth-status').append(`
        <div class="alert alert-info mt-2">
            <i class="fas fa-info-circle"></i> 
            You can now submit publications for review.
        </div>
    `);
}

function checkOrganizationMembership(token, username) {
    // In production, this would make a real API call to GitHub
    // For demonstration, we'll use the mock function
    const isMember = checkMockMembership(username);
    
    if (isMember) {
        showSubmissionButton();
    }
}

// Global variable to store publications data for duplicate checking
let publicationsData = [];

function showSubmissionModal() {
    // Load publications data for duplicate checking if not already loaded
    if (publicationsData.length === 0) {
        loadPublicationsForDuplicateCheck();
    }
    
    // Reset form
    document.getElementById('publicationForm').reset();
    $('#titleDuplicateWarning').hide();
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('submissionModal'));
    modal.show();
}

function loadPublicationsForDuplicateCheck() {
    $.getJSON("./assets/html/publications.json", function(data) {
        publicationsData = data;
    }).fail(function() {
        console.warn("Could not load publications for duplicate checking");
    });
}

function checkForDuplicateTitle() {
    const title = document.getElementById('pubTitle').value.trim();
    const warningDiv = document.getElementById('titleDuplicateWarning');
    
    if (title.length < 3) {
        warningDiv.style.display = 'none';
        return false;
    }
    
    // Check for duplicates (case-insensitive)
    const titleLower = title.toLowerCase();
    let isDuplicate = false;
    
    for (let yearGroup of publicationsData) {
        for (let pub of yearGroup.publications) {
            if (pub.title && pub.title.toLowerCase() === titleLower) {
                isDuplicate = true;
                break;
            }
        }
        if (isDuplicate) break;
    }
    
    if (isDuplicate) {
        warningDiv.style.display = 'block';
        return true;
    } else {
        warningDiv.style.display = 'none';
        return false;
    }
}

function submitPublicationForm() {
    // Validate form
    const form = document.getElementById('publicationForm');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    
    // Check for duplicates one more time
    const isDuplicate = checkForDuplicateTitle();
    if (isDuplicate) {
        const confirmSubmit = confirm(
            "A publication with this title already exists. Are you sure you want to submit this as a new publication?\n\n" +
            "Click 'Cancel' to modify the title, or 'OK' to proceed with submission."
        );
        
        if (!confirmSubmit) {
            return; // User cancelled
        }
    }
    
    // Get form data
    const formData = {
        title: document.getElementById('pubTitle').value.trim(),
        authorLastname: document.getElementById('pubAuthorLastname').value.trim(),
        year: document.getElementById('pubYear').value,
        url: document.getElementById('pubURL').value.trim()
    };
    
    const githubUser = localStorage.getItem('github_user');
    
    // Create GitHub issue URL with pre-filled template
    const issueBody = encodeURIComponent(`**Title:** ${formData.title}

**First Author:** ${formData.authorLastname}

**Publication URL:** ${formData.url}

**Publication Year:** ${formData.year}

**Publication Type:** journal

**Journal/Conference:** [Please add journal/conference name]

**Status:** published

**Brief Description:** [Please add description of the publication's relevance to MIDeL]

## Checklist

- [x] I am a member of the Mayo-Radiology-Informatics-Lab GitHub organization
- [x] The publication is related to medical imaging or deep learning
- [x] The URL is accessible and correct
- [x] The publication information is accurate and complete
- [x] I have checked that this publication is not already listed on the website

## Additional Information

**Related Research Area:** [Please specify]

**Keywords:** [Optional keywords]

**Notes:** Submitted via website by ${githubUser}${isDuplicate ? ' (POTENTIAL DUPLICATE - user confirmed submission)' : ''}`);

    const issueTitle = encodeURIComponent(`[PUBLICATION] ${formData.title}`);
    const issueUrl = `https://github.com/Mayo-Radiology-Informatics-Lab/MIDeL/issues/new?title=${issueTitle}&body=${issueBody}&labels=publication,content`;
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('submissionModal'));
    modal.hide();
    
    // Open GitHub issue in new tab
    window.open(issueUrl, '_blank');
    
    // Show success message
    alert("Opening GitHub issue form. Please complete the submission there if any additional details are needed.");
}

function logout() {
    localStorage.removeItem('github_token');
    localStorage.removeItem('github_user');
    $('#github-auth-btn').show();
    $('#submit-publication-btn').hide();
    $('#auth-status').html('');
}