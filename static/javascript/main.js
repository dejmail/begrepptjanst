const user_input = $("#user-input");
const search_icon = $('#search-icon');
const concept_div = $('#display-middle-column');
const rootUrl = window.location.href;

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
    while (div.firstChild) {
        div.removeChild(div.firstChild);
    }
}

function toggleHelp() {
    document.getElementById("helpInfo").classList.toggle("hidden");
}

function toggleVisibility(elementId, status = 'toggle') {
    const element = document.getElementById(elementId);
    if (element) {
        if (element.classList.contains('d-none') && status === 'off') {
            return
        } else if (element.classList.contains('d-none') && status === 'on') {
            element.classList.remove('d-none');
        } else if (!element.classList.contains('d-none') && status === 'off') {
            element.classList.add('d-none');
        } else if (status === 'toggle') {
            element.classList.toggle('d-none');
        }
        else {
            console.error(`Element with ID '${elementId}' not found.`);
        }
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
            clear_mittenspanrow();

            // fade out the concept_div, then:
            concept_div.fadeTo('fast', 0).promise().then(() => {
                // replace the HTML contents
                concept_div.html(responseData);
                // fade-in the div with new contents
                concept_div.fadeTo('fast', 1);
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
    toggleVisibility('colour-panel', 'off');
    closeAllTooltips();

    const requestParameters = {
        dictionary: $('[name="dictionary"]').val(),
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


//
document.getElementById('dictionary-select').addEventListener('change', function () {
    document.getElementById('display-middle-column').innerHTML = '';
    document.getElementById('display-right-column').innerHTML = '';
    toggleVisibility('colour-panel', 'off');
    document.getElementById('user-input').value = '';

});


document.body.addEventListener("click", function (e) {
    const link = e.target.closest('a'); // Handles clicks on nested elements like <span> inside <a>

    if (!link) return; // Not a link

    const linkUrl = new URL(link.href, window.location.origin);
    const isExternal = linkUrl.origin !== window.location.origin;

    if (isExternal || link.classList.contains('non-ajax-link')) {
        console.log('Following external or non-ajax link:', link.href);
        return; // Let the browser handle it
    }

    // Internal link: intercept and AJAX it
    e.preventDefault();

    console.log("Intercepting link:", link.href);

    const requestParameters = {
        dictionary: linkUrl.searchParams.get('dictionary'),
        q: linkUrl.searchParams.get('q'),
    };

    ajax_call(linkUrl, requestParameters);
    popStateHandler();
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
        window.addEventListener("popstate", function (e) {
            // Get the URL from the address bar and fetch the page.
            console.log('popstateHandler eventlistener fired, next stop getPage function')
            $('#display-middle-column').html(history.state);
            //getPage(document.URL);
        });
    }
};
