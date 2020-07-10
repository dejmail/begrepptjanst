console.log("hello there, I'm on the admine page");


(function($){     

$(document).ready(function () {
  
function check_number_of_recent_comments()
{    
$.ajax({
	type: "GET",
	dataType: "html",
	url: "{% url 'unread_comments' %}",
	success: function(data) {
        var display_html = data.html_from_view;
        table_data = document.querySelector("#content-main > div.app-ordbok.module > table > tbody > tr.model-opponerabegreppdefinition");
        console.log(table_data);
		$('#mitten-span').html(data);
	},
	error: function() {
		$('#mitten-span').html("Loaded");
	},
	});
}

check_number_of_recent_comments();

});

})(django.jQuery);