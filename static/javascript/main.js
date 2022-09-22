const user_input = $("#user-input");
const search_icon = $('#search-icon');
const begrepp_div = $('#mitten-span-middle-column');
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

user_input.keyup(function () {
	$("#mitten-span-middle-column").empty();
	toggle_element("replaceable-content-middle-column");
	
	const request_parameters = {
		
		q: $(this).val() // value of user_input: the HTML element with ID user-input
	}
	
	if (request_parameters.q.length > 1) {

	var ajax_call = function (endpoint, request_parameters) {
		$("#term_förklaring_tabell").remove();
		$("#mitten-span-middle-column").empty();
		var skapad_url = (endpoint + '?' + Object.keys(request_parameters) + '=' + Object.values(request_parameters));
		$.getJSON(endpoint, request_parameters)
			.done(response => {
				console.log("document.URL", document.URL)
		        console.log("endpoint", endpoint);
				changeBrowserURL(response, skapad_url);
				// fade out the begrepp_div, then:
				begrepp_div.fadeTo('fast', 0).promise().then(() => {
					// replace the HTML contents
					begrepp_div.html(response);
					
					// fade-in the div with new contents
					begrepp_div.fadeTo('fast', 1);
					// stop animating search icon
					search_icon.removeClass('blink');
					popStateHandler();
				})
			});
		popStateHandler();
	}
} 
	
	// start animating the search icon with the CSS class
	search_icon.addClass('blink')

	// rehide the colour panel
	$("#färg_panel").addClass('d-none');


	// if scheduled_function is NOT false, cancel the execution of the function
	if (scheduled_function) {
		clearTimeout(scheduled_function)
	}

	// setTimeout returns the ID of the function to be executed
	scheduled_function = setTimeout(ajax_call, delay_by_in_ms, endpoint, request_parameters)

});

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
		$("#mitten-span-middle-column").empty();
		div.html(data);
		
		
		changeBrowserURL(data, this.url);
	}).fail(function(data,textStatus,jqXHR) {
		  $('#mitten-span-middle-column').html("Fel - Hoppsan! Jag får ingen definition från servern...finns ett problem..prova trycka Ctrl-Shift-R");
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
		$('#mitten-span-middle-column').html(history.state);
		//getPage(document.URL);
	  });
}
};