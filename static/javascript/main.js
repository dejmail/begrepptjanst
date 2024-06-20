const user_input = $("#user-input");
const search_icon = $('#search-icon');
const begrepp_div = $('#mitten-span-middle-column');


console.log('loading the main.js');
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

const delay_by_in_ms = 2000
let scheduled_function = false

function toggle_element(element_id) {
	var div = document.getElementById(element_id);
	while(div.firstChild) {
		div.removeChild(div.firstChild);
	}
}

const ajax_call = function (endpoint, request_parameters) {
    console.log('inside ajax_call function');
    console.log('request_parameters:', request_parameters);
    const url = new URL(document.location.protocol +"//"+ document.location.host + endpoint);
    console.log('after new URL');
    url.search = new URLSearchParams(request_parameters).toString();
    
    const complete_url = url + url.search;
    console.log('after URLSearchParams');
    
    let customHeaders = new Headers({
        "X-CUSTOM-REQUESTED-WITH": "XMLHttpRequest",
    });
    fetch(url, {
        method: 'GET',
        credentials: 'same-origin',
        headers: customHeaders
                },        
        )
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();  // Assuming the response is in JSON format
    })
    .then(responseData => {
        console.log("document.URL", document.URL);
        console.log("endpoint", endpoint);
        changeBrowserURL(responseData, complete_url);

        // fade out the begrepp_div, then:
        begrepp_div.fadeTo('fast', 0).promise().then(() => {
            // replace the HTML contents
            begrepp_div.html(responseData);
            // fade-in the div with new contents
            begrepp_div.fadeTo('fast', 1);
            // stop animating search icon
            search_icon.removeClass('blink');
            popStateHandler();
        });
    })
    .catch(error => {
        console.error('Error:', error);
    });

    popStateHandler();
};

$("#user-input").keyup(function (event) {
    event.preventDefault(); // Prevent the default form submission
    console.log('Form submission prevented');

    console.log('user entering search parameters');
    console.log('current value:', $(this).val());
    $("#mitten-span-middle-column").empty();
    toggle_element("replaceable-content-middle-column");

    const request_parameters = {
        category: $('[name="category"]').val(), // Get the selected value from dropdown
        q: $(this).val() // value of user_input: the HTML element with ID user-input
    }
    
    if (request_parameters.q.length > 1) {
        // Start animating the search icon with the CSS class
        search_icon.addClass('blink');

        // Rehide the color panel
        $("#färg_panel").addClass('d-none');

        // If scheduled_function is NOT false, cancel the execution of the function
        if (scheduled_function) {
            clearTimeout(scheduled_function);
        }

        // setTimeout returns the ID of the function to be executed
        scheduled_function = setTimeout(() => {
            console.log('executing ajax_call');
            ajax_call(endpoint, request_parameters);
        }, delay_by_in_ms);
    }
    
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
	getPage(e.target.href);
	popStateHandler();
	}
});

function getPage(link_url) {
	
	console.log('entering ajax getPage function');
	$.ajax({
		type: "GET",
		url: link_url,
	}).done(function(data, textStatus, jqXHR) {
		$('#replaceable-content-middle-column').empty();
		$("#mitten-span-middle-column").empty();
		begrepp_div.html(data);
		
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