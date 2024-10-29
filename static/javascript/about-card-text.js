document.getElementById('dictionary-select').addEventListener('change', function () {
    const selectedValue = this.value;
    console.log('Getting new about text for card');
    console.log(`${baseUrl}get-dictionary-content/${selectedValue}`);
    // Make an AJAX call to the Django view
    const encodedName = encodeURIComponent(selectedValue);
    console.log(`Encoded dictionary name = ${encodedName}`);
    fetch(`${baseUrl}get-dictionary-content/${encodedName}`)
      .then(response => response.json())
      .then(html => {
        let decodedContent = decodeURIComponent(html);
        document.getElementById('about-card-text').innerHTML = decodedContent.dictionary_context;
      })
      .catch(error => console.error('Error fetching content:', error));
  });

