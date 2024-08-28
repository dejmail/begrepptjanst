$('[data-toggle="tooltip"]').tooltip({
    placement: function(context, source) {
        const position = $(source).offset();
        if (position.top < 200) {
            return "bottom";
        } else if ($(window).width() - position.left < 200) {
            return "left";
        }
        return "top";
    }
});

$('[data-toggle="tooltip"]').on('shown.bs.tooltip', function () {
    const tooltipId = $(this).attr('aria-describedby');
    const tooltipElement = $('#' + tooltipId);
    const currentTop = parseInt(tooltipElement.css('top'), 10);
    const newTop = currentTop + 250; // Example: Move it 50px down
    tooltipElement.css('top', newTop + 'px');
});

$("#colour-panel").removeClass('d-none');
$("#colour-explanation").click(function(){
    $("#colour-panel").toggle();
    });

  
if (typeof currentTerm === 'undefined') {
    var currentTerm = null;
}

function sanitizeId(id) {
    return id.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '');
}

document.body.addEventListener('click', (e) => {
    if (e.target.classList.contains('term')) {
        console.log('Term clicked:', e.target);
        e.preventDefault();
        
        const term = e.target;
        const definitionId = term.getAttribute('aria-describedby');
        const definitionElement = document.getElementById(definitionId);        
        if (currentTerm === term) {
            // If clicking the same term, hide the definition
            console.log('Hiding definition');
            hideDefinition(definitionElement);
        } else {
            // Show definition for the new term
            console.log('Showing definition');
            showDefinition(term, definitionElement);
        }
    } else {
        // Hide definition when clicking outside
        console.log('Clicked outside term');

        hideAllDefinitions();
    }
});
  
document.body.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        hideAllDefinitions();
    }
});
  
function hideDefinition(definitionElement) {
    if (definitionElement) {
        definitionElement.hidden = true;
    }
    currentTerm = null;
}
  
function hideAllDefinitions() {
    document.querySelectorAll('.definition').forEach(def => def.hidden = true);
    currentTerm = null;
}

// To make the span elements selectable with the Enter key
const termElements = document.querySelectorAll('.term');

termElements.forEach(term => {
    term.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            term.click();
        }
    });
    
    // Optional: If you want to handle the click event separately
    term.addEventListener('click', function() {
        const definitionId = term.getAttribute('aria-describedby');
        const definitionElement = document.getElementById(definitionId);
    });
});


function updateDefinitionsPosition() {

    const definitions = document.querySelectorAll('.copied-definition');
    const margin = 10; // Minimum margin between definitions
    const maxDefinitions = 5; // Limit to 5 definitions
    let topOffset = window.scrollY + margin; // Start with the top offset adjusted by scroll position
    // let topOffset = margin;

    const sortedDefinitions = Array.from(definitions).sort((a, b) => {
        const aTime = parseInt(a.dataset.timestamp, 10);
        const bTime = parseInt(b.dataset.timestamp, 10);
        return bTime - aTime; // Sort descending by activation time
    });

    // Show and position the top `maxDefinitions` elements
    sortedDefinitions.slice(0, maxDefinitions).forEach((definition, index) => {
        definition.style.position = 'absolute'; // Absolute positioning relative to container
        definition.style.top = `${topOffset}px`;
        definition.style.zIndex = 100; // Ensure tooltips stay on top
        definition.style.display = 'block'; // Ensure it's visible
        definition.style.width = `calc(100% - ${2 * margin}px)`; // Adjust width to fit within the viewport minus margin

        topOffset += definition.offsetHeight + margin; // Use the current tooltip's height

    });

    // Remove definitions beyond the limit
    sortedDefinitions.slice(maxDefinitions).forEach(definition => {
        definition.remove();
    });

    // updateTooltips();
}

// Show and hide the "Close All Tooltips" button
function updateTooltips() {
    const definitions = document.querySelectorAll('.copied-definition');
    const closeAllButton = document.getElementById('close-all-tooltips');
    debugger;
    if (definitions.length > 1) {
        closeAllButton.style.display = 'block'; // Show button if more than one tooltip
    } else {
        closeAllButton.style.display = 'none'; // Hide button if one or no tooltips
    }
}

function showDefinition(term, definitionElement) {
    const definitionId = sanitizeId(definitionElement.id);

    // New code to copy definition to right panel
    const rightColumn = document.getElementById('display-right-column');
    
    // Create a new element for the copied definition
    const copiedDefinition = document.createElement('div');
    copiedDefinition.dataset.timestamp = Date.now();
    copiedDefinition.className = 'copied-definition';
    copiedDefinition.id = `copied-${definitionId}`;
    
    const headerContainer = document.createElement('div');
    headerContainer.className = 'header-container';

    const heading = document.createElement('h5');
    heading.textContent = `${term.textContent}`;
    
    const closeButton = document.createElement('button');
    closeButton.textContent = 'X';
    closeButton.className = 'close-definition';

    headerContainer.appendChild(heading);
    headerContainer.appendChild(closeButton);

    copiedDefinition.appendChild(headerContainer);
    const content = document.createElement('p');
    content.textContent = definitionElement.textContent;
    copiedDefinition.appendChild(content);

    
    closeButton.onclick = function() {
        rightColumn.removeChild(copiedDefinition);
        // updateTooltips(); // Update visbility after closing a tooltip
    };

    copiedDefinition.prepend(closeButton);

    // Check if an element with the same ID already exists
    const existingDefinition = rightColumn.querySelector(`#copied-${definitionId}`);
    if (!existingDefinition) {
        // Add the copied definition to the right column if no duplicate exists
        rightColumn.prepend(copiedDefinition);
    } else {
        // Toggle visibility of the existing copied definition
        // existingDefinition.style.display = existingDefinition.style.display === 'none' ? 'block' : 'none';
        existingDefinition.remove();
        }
        updateDefinitionsPosition();
}

function closeAllTooltips() {
    const rightColumn = document.getElementById('display-right-column');
    rightColumn.innerHTML = ''; // Remove all tooltips
    updateTooltips(); // Update button visibility
}

// Event listener for the "Close All Tooltips" button
document.getElementById('close-all-tooltips').addEventListener('click', closeAllTooltips);

// Call this function initially and on window resize and scroll
updateDefinitionsPosition();
window.addEventListener('scroll', updateDefinitionsPosition);
window.addEventListener('resize', updateDefinitionsPosition);
