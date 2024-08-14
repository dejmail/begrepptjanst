
    $('[data-toggle="tooltip"]').tooltip();
      $("#färg_panel").removeClass('d-none');
      $("#färg_förklaring").click(function(){
          $("#färg_panel").toggle();
          });
  
  
    if (typeof currentTerm === 'undefined') {
        var currentTerm = null;
    }

    function sanitizeId(id) {
        return id.replace(/\s+/g, '-').replace(/[^a-zA-Z0-9-]/g, '');
    }

      document.body.addEventListener('click', (e) => {
  
        console.log('Click event triggered', e.target);
  
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
  
    //   function showDefinition(term, definitionElement) {
      
    //     const definitionId = sanitizeId(definitionElement.id);

    //     // New code to copy definition to right panel
    //     const rightColumn = document.getElementById('display-right-column');
        
    //     // Create a new element for the copied definition
    //     const copiedDefinition = document.createElement('div');
    //     copiedDefinition.className = 'copied-definition';
    //     copiedDefinition.id = `copied-${definitionId}`;
        
    //     // Copy the content of the definition
    //     copiedDefinition.innerHTML = `
    //         <h5>${term.textContent}</h5>
    //         <p>${definitionElement.textContent}</p>
    //     `;       

    //     // Add a close button
    //     const closeButton = document.createElement('button');
    //     closeButton.textContent = 'X';
    //     closeButton.className = 'close-definition';
    //     closeButton.onclick = function() {
    //         rightColumn.removeChild(copiedDefinition);
    //     };
    //     copiedDefinition.prepend(closeButton);

    //     // Check if an element with the same ID already exists
    //     const existingDefinition = rightColumn.querySelector(`#copied-${definitionId}`);
    //     // debugger;
    //     if (!existingDefinition) {
    //         // Add the copied definition to the right column if no duplicate exists
    //         rightColumn.appendChild(copiedDefinition);
    //         copiedDefinition.hidden = false;
    //     }
    //   }
  
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
            event.preventDefault(); // Prevent default action
            
            // Simulate a click event
            term.click();
        }
    });
    
    // Optional: If you want to handle the click event separately
    term.addEventListener('click', function() {
        const definitionId = term.getAttribute('aria-describedby');
        const definitionElement = document.getElementById(definitionId);
        
        // Toggle the display of the definition (for example)
        definitionElement.hidden = !definitionElement.hidden;
    });
});


// Adjust the position of the tooltips carrying term definitions to the viewport of the user
function updateDefinitionsPosition() {
    const definitions = document.querySelectorAll('.copied-definition');
    const margin = 20; // Minimum margin between definitions
    let topOffset = margin; // Initial top offset

    definitions.forEach((definition) => {
        definition.style.position = 'fixed'; // Fix position relative to viewport
        definition.style.top = `${topOffset}px`;

        // Update the top offset for the next definition
        topOffset += definition.offsetHeight + margin;

        // Ensure width is responsive
        definition.style.width = `calc(100% - ${2 * margin}px)`; // Adjust width to fit within the viewport minus margin
    });
}

// Call this function initially and on window resize and scroll
updateDefinitionsPosition();
window.addEventListener('scroll', updateDefinitionsPosition);
window.addEventListener('resize', updateDefinitionsPosition);

function showDefinition(term, definitionElement) {
    const definitionId = sanitizeId(definitionElement.id);

    // New code to copy definition to right panel
    const rightColumn = document.getElementById('display-right-column');
    
    // Create a new element for the copied definition
    const copiedDefinition = document.createElement('div');
    copiedDefinition.className = 'copied-definition';
    copiedDefinition.id = `copied-${definitionId}`;
    
    // Copy the content of the definition
    copiedDefinition.innerHTML = `
        <h5>${term.textContent}</h5>
        <p>${definitionElement.textContent}</p>
    `;

    // Add a close button
    const closeButton = document.createElement('button');
    closeButton.textContent = 'X';
    closeButton.className = 'close-definition';
    closeButton.onclick = function() {
        rightColumn.removeChild(copiedDefinition);
    };
    copiedDefinition.prepend(closeButton);

    // Check if an element with the same ID already exists
    const existingDefinition = rightColumn.querySelector(`#copied-${definitionId}`);
    if (!existingDefinition) {
        // Add the copied definition to the right column if no duplicate exists
        rightColumn.appendChild(copiedDefinition);
        updateDefinitionsPosition(); // Ensure the position is updated
    }
}

