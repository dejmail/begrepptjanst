function endpoint_check() {
    if (location.hostname == "127.0.0.1" || location.hostname == "localhost") { 
        return '/';
    } else {
        // Construct the base URL using location.origin
        return location.origin + '/';
    } 
}



const endpoint = endpoint_check();

const delayMilliseconds = 750
let scheduledFunction = true

// userInput.keyup(function () {
	
// 	//toggle_element("replaceable-content-middle-column");
	

// 	// start animating the search icon with the CSS class
// 	// searchIcon.addClass('blink')

// 	// rehide the colour panel
// 	$("#färg_panel").addClass('d-none');
// 	$("#about-card").addClass('d-none');
// 	$("#about-card").removeClass('d-inline-block');

// 	// if scheduled_function is NOT false, cancel the execution of the function


// });