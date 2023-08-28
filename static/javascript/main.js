const user_input = $("#user-input");
const search_icon = $('#search-icon');
const search_result_div = $('#search-row-middle-column');
const term_details = $('#mitten-span-modal');


function endpoint_check() {

    if (document.domain == "127.0.0.1") { 
		const endpoint = '/';
		return endpoint
    } else {
		const endpoint = document.URL;
		return endpoint
	} 

}

const endpoint = endpoint_check();


const delay_by_in_ms = 750
let scheduled_function = true

function toggle_element(element_id) {
	var div = document.getElementById(element_id);
	while(div.firstChild) {
		div.removeChild(div.firstChild);
	}
}

function ajaxCall(endpoint, request_parameters, url, csrf_token) {
	$("#term_förklaring_tabell").remove();
	search_result_div.empty();
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
			search_result_div.fadeTo('fast', 0).promise().then(() => {
    		// replace the HTML contents & display the filter bar
			
			document.getElementById("search-row-middle-column").outerHTML = JSON.parse(xhttp.responseText);
				
			//document.getElementById("sidebar").style.display = "block";

			// fade-in the div with new contents
			search_result_div.fadeTo('fast', 1);
			// stop animating search icon
			search_icon.removeClass('blink');
			popStateHandler();
			})
		};
	}
	xhttp.open("GET", url, true);
	xhttp.setRequestHeader("x-requested-with", "XMLHttpRequest");
	xhttp.send();
	popStateHandler();
	}
	// $.getJSON(url, request_parameters)
	// 	.done(response => {
			
			// console.log("document.URL", document.URL)
			// console.log("endpoint", endpoint);
			// changeBrowserURL(response, url);
			// // fade out the search result, then:
			// search_result_div.fadeTo('fast', 0).promise().then(() => {
			// 	// replace the HTML contents & display the filter bar
				
			// 	search_result_div.html(response);
				
			// 	//document.getElementById("sidebar").style.display = "block";

			// 	// fade-in the div with new contents
			// 	search_result_div.fadeTo('fast', 1);
			// 	// stop animating search icon
			// 	search_icon.removeClass('blink');
			// 	popStateHandler();
		// 	})
		// });
	// popStateHandler();
// }

user_input.keyup(function () {
	$("#search-row-middle-column").empty();
	//toggle_element("replaceable-content-middle-column");
	

	// start animating the search icon with the CSS class
	search_icon.addClass('blink')

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

  function buildURL(search_term, dictionary_checkboxes, relation_checkboxes) {
	
	return (endpoint + 
			'?term=' + 
			search_term + 
			'&dictionaries=' + 
			dictionary_checkboxes.join(',') + 
			'&relationships=' + 
			relation_checkboxes.join(','));
  }


  function docReady() {

	// Intercept form submission
	const input = document.querySelector("#filter-form");
	input.addEventListener("input", updateFilter);
	function updateFilter(event) {
	  // Prevent the form from submitting traditionally

	  event.preventDefault();
	  const search_term = document.getElementById("user-input").value
	  const dictionary_checkboxes = document.querySelectorAll('input[id^="dictionary-filter-checkbox-"]')
	  const relation_checkboxes = document.querySelectorAll('input[id^="relationship-filter-checkbox-"]')

	  var dictionary_checked = processCheckboxes(dictionary_checkboxes);
	  var relationship_checked = processCheckboxes(relation_checkboxes);
	  var csrf_token = document.getElementsByName("csrfmiddlewaretoken");
	  var post_url = buildURL(search_term, dictionary_checked, relationship_checked);
	  
	  // Send checkbox status to the backend, and update page
	  if ((search_term.length > 1) || (dictionary_checkboxes.length > 0)) {

		if (scheduled_function) {
			clearTimeout(scheduled_function)
			}

	// setTimeout returns the ID of the function to be executed
		scheduled_function = setTimeout(ajaxCall, delay_by_in_ms, endpoint, search_term, post_url, csrf_token)

		// ajaxCall(endpoint, search_term, post_url, csrf_token)
	}

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
	//debugger;
	getPage(e.target.href, begrepp_div);
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