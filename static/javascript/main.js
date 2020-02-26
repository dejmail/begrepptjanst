const user_input = $("#user-input")
const search_icon = $('#search-icon')
const begrepp_div = $('#replaceable-content')
const endpoint = ''
const delay_by_in_ms = 750
let scheduled_function = true


user_input.keyup(function () {

	const request_parameters = {
		
		q: $(this).val() // value of user_input: the HTML element with ID user-input
	}
	
	var ajax_call = function (endpoint, request_parameters) {
		$("#term_förklaring_tabell").remove();
		$.getJSON(endpoint, request_parameters)
			.done(response => {
				// fade out the begrepp_div, then:
				begrepp_div.fadeTo('fast', 0).promise().then(() => {
					// replace the HTML contents
					begrepp_div.html(response['html_from_view'])
					// fade-in the div with new contents
					begrepp_div.fadeTo('fast', 1)
					// stop animating search icon
					search_icon.removeClass('blink')
				})
			})
	}


	// start animating the search icon with the CSS class
	search_icon.addClass('blink')

	// if scheduled_function is NOT false, cancel the execution of the function
	if (scheduled_function) {
		clearTimeout(scheduled_function)
	}

	// setTimeout returns the ID of the function to be executed
	scheduled_function = setTimeout(ajax_call, delay_by_in_ms, endpoint, request_parameters)

})
