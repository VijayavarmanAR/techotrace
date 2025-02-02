document.addEventListener('DOMContentLoaded', function() {
        // Get case data from localStorage (add this at the start)
        const caseData = localStorage.getItem('currentCase');
        if (!caseData) {
            window.location.href = '/new-case';
            return;
        }
        const currentCase = JSON.parse(caseData);
        
        // Update sidebar case information
        const caseElement = document.querySelector('.account-info');
        if (caseElement) {
            const caseNumberElement = caseElement.querySelector('p:last-child');
            if (caseNumberElement) {
                caseNumberElement.textContent = `Case: ${currentCase.caseNumber}`;
            }
        }
    
        // Store case number for API calls
        window.caseNumber = currentCase.caseNumber;
    // Initialize Lucide icons
    lucide.createIcons();

    // Get necessary elements
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const navButtons = document.querySelectorAll('.nav-button');
    const contentArea = document.getElementById('content-area');
    const reportsDropdown = document.getElementById('reportsDropdown');
    const dropdown = document.querySelector('.dropdown');

    // Analysis content for each section
    const analysisContent = {
        log: {
            title: 'Log Analysis',
            description: 'Analyze system logs, event logs, and application logs to identify suspicious activities and potential security incidents. Our advanced log analysis engine processes multiple log formats and correlates events across different sources.',
            buttonText: 'Analyze Logs',
            icon: 'search'
        },
        network: {
            title: 'Network Analysis',
            description: 'Examine network traffic patterns, connections, and protocols to detect anomalies and potential network-based attacks. Includes packet analysis, flow analysis, and protocol analysis capabilities.',
            buttonText: 'Analyze Network',
            icon: 'activity'
        },

        file: {
            title: 'File Analysis',
            description: 'Investigate files for their properties, metadata, and potential malicious content. Our file analysis tool helps identify suspicious files and analyzes their characteristics.',
            buttonText: 'Analyze Files',
            icon: 'folder'
        },

        registry: {
            title: 'Registry Analysis',
            description: 'Investigate Windows Registry for signs of system modifications, persistence mechanisms, and malware artifacts. Our registry analysis tool helps identify suspicious registry keys and values.',
            buttonText: 'Analyze Registry',
            icon: 'database'
        }
    };

    function updateNavTooltips() {
        const isCollapsed = sidebar.classList.contains('collapsed');
        navButtons.forEach(button => {
            if (isCollapsed) {
                const text = button.querySelector('span').textContent;
                button.setAttribute('title', text);
            } else {
                button.removeAttribute('title');
            }
        });
    }

    // Toggle sidebar
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('collapsed');
        lucide.createIcons();
    });

    // Dropdown handling
    if (dropdown && reportsDropdown) {
        reportsDropdown.addEventListener('mouseenter', function(e) {
            if (sidebar.classList.contains('collapsed')) {
                dropdown.classList.add('active');
            }
        });
    
        reportsDropdown.addEventListener('click', function(e) {
            if (!sidebar.classList.contains('collapsed')) {
                dropdown.classList.toggle('active');
            }
        });

        dropdown.addEventListener('mouseleave', function(e) {
            if (sidebar.classList.contains('collapsed')) {
                dropdown.classList.remove('active');
            }
        });

        // Handle dropdown item clicks
        const dropdownLinks = dropdown.querySelectorAll('.dropdown-content a');
        dropdownLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const fileName = this.getAttribute('data-file');
                simulateFileDownload(fileName);
                dropdown.classList.remove('active');
            });
        });
    }

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!dropdown.contains(e.target)&& !sidebar.classList.contains('collapsed')) {
            dropdown.classList.remove('active');
        }
    });

    // Update content area
    function updateContent(section) {
        if (analysisContent[section]) {
            const content = analysisContent[section];
            contentArea.innerHTML = `
                <div class="analysis-section active">
                    <h2>${content.title}</h2>
                    <p>${content.description}</p>
                    <button class="analyze-button" data-analysis="${section}">
                        <i data-lucide="${content.icon}"></i>
                        ${content.buttonText}
                    </button>
                </div>
            `;

            // Reinitialize Lucide icons for new content
            lucide.createIcons();

            // Add click event for the new analyze button
            const analyzeButton = contentArea.querySelector('.analyze-button');
            analyzeButton.addEventListener('click', function() {
                handleAnalysis(section);
            });
        }
    }

    // Handle analysis button clicks
    function handleAnalysis(type) {
        const button = document.querySelector(`[data-analysis="${type}"]`);
        const originalText = button.innerHTML;
        
        // Disable button and show loading state
        button.disabled = true;
        button.innerHTML = '<i data-lucide="loader-2" class="animate-spin"></i> Analyzing...';
        lucide.createIcons();
    
        if (type === 'log' || type === 'network' || type === 'file') {  // Added 'file' here
            // Get case data
            const caseData = localStorage.getItem('currentCase');
            if (!caseData) {
                console.error('No case data found');
                button.innerHTML = '<i data-lucide="x"></i> Error: No case data';
                lucide.createIcons();
                return;
            }
            const currentCase = JSON.parse(caseData);
    
            // Make API call to execute analysis
            fetch(`http://localhost:5000/api/analyze-${type}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    case_number: currentCase.caseNumber
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    button.innerHTML = '<i data-lucide="check"></i> Analysis Complete!';
                    console.log('Analysis output:', data.output);
                } else {
                    button.innerHTML = '<i data-lucide="x"></i> Analysis Failed';
                    console.error('Analysis error:', data.message);
                }
                lucide.createIcons();
                
                // Reset button after 2 seconds
                setTimeout(() => {
                    button.disabled = false;
                    button.innerHTML = originalText;
                    lucide.createIcons();
                }, 2000);
            })
            .catch(error => {
                console.error('Error:', error);
                button.innerHTML = '<i data-lucide="x"></i> Error';
                lucide.createIcons();
                
                setTimeout(() => {
                    button.disabled = false;
                    button.innerHTML = originalText;
                    lucide.createIcons();
                }, 2000);
            });
        } else {
            // Handle other analysis types
            setTimeout(() => {
                button.innerHTML = '<i data-lucide="check"></i> Analysis Complete!';
                lucide.createIcons();
                
                setTimeout(() => {
                    button.disabled = false;
                    button.innerHTML = originalText;
                    lucide.createIcons();
                }, 2000);
            }, 3000);
        }
    }
    
    // Add click events to navigation buttons
    navButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const section = this.getAttribute('data-section');
            
            // Skip if it's the reports button
            if (this.id === 'reportsDropdown') {
                return; // Handled by dropdown-specific event listener
            }

            // Remove active class from all buttons
            navButtons.forEach(btn => {
                btn.classList.remove('active');
                if (btn.id === 'reportsDropdown') {
                    btn.parentElement.classList.remove('active');
                }
            });

            // Add active class to clicked button
            this.classList.add('active');

            // Update content
            if (section) {
                updateContent(section);
            }
        });
    });
    // Import jsPDF
const { jsPDF } = window.jspdf;

// Add event listener for the Download PDF button
document.getElementById('downloadPdfButton').addEventListener('click', () => {
    // Get form values
    const caseNumber = document.getElementsByName('caseNumber')[0].value;
    const caseName = document.getElementsByName('caseName')[0].value;
    const priority = document.getElementsByName('priority')[0].value;
    const status = document.getElementsByName('status')[0].value;
    const dateReceived = document.getElementsByName('dateReceived')[0].value;
    const examiner = document.getElementsByName('examiner')[0].value;
    const requestingAgency = document.getElementsByName('requestingAgency')[0].value;
    const description = document.getElementsByName('description')[0].value;

    // Simple validation for required fields
    if (!caseNumber || !caseName || !dateReceived || !examiner || !requestingAgency || !description) {
        alert('Please fill out all required fields to download the PDF.');
        return;
    }

    // Create a new jsPDF instance
    const pdf = new jsPDF();

    // Add content to the PDF
    pdf.setFontSize(16);
    pdf.text('Case Details', 10, 10);

    pdf.setFontSize(12);
    pdf.text(`Case Number: ${caseNumber}`, 10, 20);
    pdf.text(`Case Name: ${caseName}`, 10, 30);
    pdf.text(`Priority: ${priority}`, 10, 40);
    pdf.text(`Status: ${status}`, 10, 50);
    pdf.text(`Date Received: ${dateReceived}`, 10, 60);
    pdf.text(`Lead Examiner: ${examiner}`, 10, 70);
    pdf.text(`Requesting Agency: ${requestingAgency}`, 10, 80);

    pdf.setFontSize(14);
    pdf.text('Description:', 10, 100);
    pdf.setFontSize(12);
    pdf.text(description, 10, 110, { maxWidth: 190 });

    // Save the PDF
    pdf.save(`Case_${caseNumber}.pdf`);
});


    // Function to simulate file download
    function simulateFileDownload(fileName) {
        alert(`Downloading ${fileName}...`);
        // In a real application, this would trigger an actual file download
    }
});

