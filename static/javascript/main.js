const user_input = $("#user-input");
const search_icon = $('#search-icon');
const begrepp_div = $('#display-middle-column');
$("#colour-panel").addClass('d-none');
const rootUrl =  window.location.href;


console.log('loading the main.js');
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

const delay_by_in_ms = 1000
let scheduled_function = false

function toggle_element(element_id) {
	var div = document.getElementById(element_id);
	while(div.firstChild) {
		div.removeChild(div.firstChild);
	}
}

/**
 * @param {URL} endpoint - The URL to make the AJAX call to
 * @param {object} requestParameters - URL parameters to be included
 */

const ajax_call = function (endpoint, requestParameters) {

    console.log('inside ajax_call function');
    console.log('requestParameters:', requestParameters);   
    console.log('endpoint.href', endpoint.href);
    
    let customHeaders = new Headers({
        "X-CUSTOM-REQUESTED-WITH": "XMLHttpRequest",
    });
    fetch(endpoint, {
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
        changeBrowserURL(responseData, endpoint);
        toggle_element("replaceable-content-middle-column");
        toggle_element("display-middle-column");
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
    $("#display-middle-column").empty();
    toggle_element("replaceable-content-middle-column");

    const requestParameters = {
        category: $('[name="category"]').val(),
        q: $(this).val() 
    }
    
    const url = new URL(rootUrl);
    const params = new URLSearchParams(requestParameters);
    url.search = params.toString();
        
    if (requestParameters.q.length > 1) {
        // Start animating the search icon with the CSS class
        search_icon.addClass('blink');

        // Rehide the color panel
        $("#colour-panel").addClass('d-none');

        // If scheduled_function is NOT false, cancel the execution of the function
        if (scheduled_function) {
            clearTimeout(scheduled_function);
        }

        // setTimeout returns the ID of the function to be executed
        scheduled_function = setTimeout(() => {
            console.log('executing ajax_call');
            ajax_call(url, requestParameters);
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
    
    const url = new URL(e.target.href);
    const requestParameters = {
        category: url.searchParams.get('category'), 
        q: url.searchParams.get('q') 
    }
    //changeBrowserURL(null, e.target.href);            
	// Get page and replace current content.
	ajax_call(url, requestParameters);
	popStateHandler();
	}
});

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
		$('#display-middle-column').html(history.state);
		//getPage(document.URL);
	  });
}
};