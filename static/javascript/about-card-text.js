const baseUrl = home_url;

document.getElementById('dictionary-select').addEventListener('change', function () {
    const selectedValue = this.value;
    
    // Make an AJAX call to the Django view
    fetch(`${baseUrl}/get-dictionary-content/${selectedValue}`)
      .then(response => response.json())
      .then(html => {
        document.getElementById('about-card-text').innerHTML = html.dictionary_context;
      })
      .catch(error => console.error('Error fetching content:', error));
  });

