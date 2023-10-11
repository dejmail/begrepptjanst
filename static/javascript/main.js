const userInput = $("#user-input");
const searchIcon = $('#search-icon');
const SearchResultDiv = $('#search-row-middle-column');
const term_details = $('#mitten-span-modal');


function endpoint_check() {

    if (location.hostname == "127.0.0.1") { 
		const endpoint = '/';
		return endpoint
    } else {
		const endpoint = document.URL;
		return endpoint
	} 

}

const endpoint = endpoint_check();


const delayMilliseconds = 750
let scheduledFunction = true

function toggle_element(element_id) {
	var div = document.getElementById(element_id);
	while(div.firstChild) {
		div.removeChild(div.firstChild);
	}
}

function ajaxCall(endpoint, request_parameters, url, csrfToken) {
	$("#term_förklaring_tabell").remove();
	SearchResultDiv.empty();
	// #$("#search-row-middle-column").r();
	$("#search-row-right-column").empty();

	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() {
		if (this.readyState == 4 && this.status == 200) {
		   // Typical action to be performed when the document is ready:
		    console.log("document.URL", document.URL)
		    console.log("endpoint", endpoint);
			changeBrowserURL(xhttp.responseText, url);
			// fade out the search result, then:
			SearchResultDiv.fadeTo('fast', 0).promise().then(() => {
    		// replace the HTML contents & display the filter bar
			
			document.getElementById("search-row-middle-column").outerHTML = JSON.parse(xhttp.responseText);
				
			//document.getElementById("sidebar").style.display = "block";

			// fade-in the div with new contents
			SearchResultDiv.fadeTo('fast', 1);
			// stop animating search icon
			searchIcon.removeClass('blink');
			popStateHandler();
			})
		};
	}
	xhttp.open("GET", url, true);
	xhttp.setRequestHeader("x-requested-with", "XMLHttpRequest");
	xhttp.send();
	popStateHandler();
	}


userInput.keyup(function () {
	$("#search-row-middle-column").empty();
	//toggle_element("replaceable-content-middle-column");
	

	// start animating the search icon with the CSS class
	searchIcon.addClass('blink')

	// rehide the colour panel
	$("#färg_panel").addClass('d-none');
	$("#about-card").addClass('d-none');
	$("#about-card").removeClass('d-inline-block');

	// if scheduled_function is NOT false, cancel the execution of the function


});

  function processCheckboxes(checkboxes) {
	var results = [];
  
	for (var i = 0; i < checkboxes.length; i++) {
	  var checkbox = checkboxes[i];
	  var isChecked = checkbox.checked;
	  if (isChecked) {
		results.push(checkbox.name);
	  }
	}
  
	return results;
  }

  function buildURL(searchString, selectedFilters) {
	if (typeof selectedFilters === 'undefined') {

		return (endpoint + 
			'?term=' + 
			searchString + 
			'&dictionaries='
			);
	} else {
	
		return (endpoint + 
			'?term=' + 
			searchString + 
			'&dictionaries=' + 
			selectedFilters.join(',')
			);
	}

  }


//   function docReady() {

// 	// Intercept form submission
// 	const input = document.querySelector("#filter-form");
// 	input.addEventListener("input", updateFilter);
// 	function updateFilter(event) {
	  

// 		event.preventDefault();
		
// 		const selectedFilters = document.querySelectorAll("#itemList").forEach(box => 
		
// 		box.addEventListener("click", (event) => {
// 			let selectedItems = [];
// 			const selectedItem = event.target;
// 			// Check if the clicked element is a list item
// 			if (selectedItem.classList.contains('list-group-item')) {
// 				// Toggle the "active" class to select/deselect the item
				
// 				console.log(selectedItem.innerText + " clicked");
// 				selectedItem.classList.toggle('active');

// 				// If item is selected, add it to the selectedItems array; if deselected, remove it
// 				if (selectedItem.classList.contains('active')) {
// 					selectedItems.push(selectedItem.innerText);
// 				} else {
// 					const index = selectedItems.indexOf(selectedItem.innerText);
// 					if (index !== -1) {
// 						selectedItems.splice(index, 1);
// 					}
// 				}
// 			}

// 			if (typeof selectedItems === 'undefined') {
// 				return ''
// 			} else {
// 				return selectedItems
// 			}
// 		})
		
// 		);
// 		debugger;
// 		// Access the current search string from the input field
// 		const searchInput = document.getElementById("user-input");
// 		const searchString = searchInput.value;
// 		// Send the selected items and search string to a function or process
// 		sendSelectedItemsAndSearchString(selectedFilters, searchString);
// 	}


function docReady() {
    const userInput = document.getElementById("user-input");
    const filterButtons = document.querySelectorAll(".filter-button");
    const selectedFilters = [];

    userInput.addEventListener("input", function () {
        handleInputChange();
    });

    filterButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            handleFilterButtonClick(button);
        });
    });

    function handleInputChange() {
        const searchString = userInput.value;
        sendSelectedItemsAndSearchString(selectedFilters, searchString);
    }

    function handleFilterButtonClick(button) {
        // Handle filter button click
        const selectedFilter = button.getAttribute("data-item-id"); // Get the filter's value
        if (selectedFilters.includes(selectedFilter)) {
            // If the filter is already selected, remove it
            selectedFilters.splice(selectedFilters.indexOf(selectedFilter), 1);
        } else {
            // If the filter is not selected, add it
            selectedFilters.push(selectedFilter);
        }
        const searchString = userInput.value;
        sendSelectedItemsAndSearchString(selectedFilters, searchString);
    }

    // Rest of your code...
}
// Function to send the selected items and search string
function sendSelectedItemsAndSearchString(selectedItems, searchString) {
    // Here, you can perform actions with the selected items and search string
    console.log("Selected Items: ", selectedItems);
    console.log("Search String: ", searchString);
	var csrfToken = document.getElementsByName("csrfmiddlewaretoken");
	var postURL = buildURL(searchString, selectedItems);
	
	// Send checkbox status to the backend, and update page
	if ((searchString.length > 1) || (selectedItems.length > 0)) {

	  if (scheduledFunction) {
		  clearTimeout(scheduledFunction)
		  }

  	// setTimeout returns the ID of the function to be executed
	  scheduledFunction = setTimeout(ajaxCall, delayMilliseconds, endpoint, searchString, postURL, csrfToken)

  	}

	};



docReady();


document.body.addEventListener("click", function(e) {
	// e.target was the clicked element
	if(e.target && e.target.nodeName == "A") {
    // Stop the browser redirecting to  the HREF value.
    e.preventDefault();    
    console.log("sending", e.target.id, "ID to URL", e.target.href);
    // Attach event listeners for browser history and hash changes.
    
    //changeBrowserURL(null, e.target.href);            
	// Get page and replace current content.
	debugger;
	getPage(e.target.href, SearchResultDiv);
	popStateHandler();
	}
});

function getPage(link_url, div) {
	
	console.log('entering ajax getPage function');
	$.ajax({
		type: "GET",
		url: link_url,
	}).done(function(data, textStatus, jqXHR) {
		$('#replaceable-content-middle-column').empty();
		$("#search-row-middle-column").empty();
		div.html(data);
		changeBrowserURL(data, this.url);
	}).fail(function(data,textStatus,jqXHR) {
		  $('#search-row-middle-column').html("Fel - Hoppsan! Jag får ingen definition från servern...finns ett problem..prova trycka Ctrl-Shift-R");
		});
	  };

/*
* Function to modify URL within browser address bar.
*/

function changeBrowserURL(data, href) {
	// Change URL with browser address bar using the HTML5 History API.
	if (history.pushState) {
	  console.log('in changeBrowserURL function, changing URL to', href)
	  // Parameters: data, page title, URL
	  history.pushState(data, null, href);
	}
	
   };

/*
 * Function to detect when back and forward buttons clicked.
 *
 * This function will allow us to load content on the fly, as
 * the browser cannot re-render the AJAX content between state changes.
 */
function popStateHandler() {
	// FF, Chrome, Safari, IE9.
	if (history.pushState) {
	  // Event listener to capture when user pressing the back and forward buttons within the browser.
	  console.log('popStateHandler  - history.pushState variable exists');
	  window.addEventListener("popstate", function(e) {
		// Get the URL from the address bar and fetch the page.
		console.log('popstateHandler eventlistener fired, next stop getPage function')
		//debugger;
		$('#search-row-middle-column').html(history.state);
		//getPage(document.URL);
	  });
}
};