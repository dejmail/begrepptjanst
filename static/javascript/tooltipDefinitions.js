
    $('[data-toggle="tooltip"]').tooltip();
      $("#färg_panel").removeClass('d-none');
      $("#färg_förklaring").click(function(){
          $("#färg_panel").toggle();
          });
  
  
    console.log('DOM fully loaded and parsed');

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
        // debugger;
        if (!existingDefinition) {
            // Add the copied definition to the right column if no duplicate exists
            rightColumn.appendChild(copiedDefinition);
            copiedDefinition.hidden = false;
        }
      }
  
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