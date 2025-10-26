// document.getElementById('dictionary-select').addEventListener('change', function () {
//     const selectedValue = this.value;
//     console.log('Getting new about text for card');
//     console.log(`${baseUrl}get-dictionary-content/${selectedValue}`);
//     // Make an AJAX call to the Django view
//     const encodedName = encodeURIComponent(selectedValue);
//     console.log(`Encoded dictionary name = ${encodedName}`);
//     fetch(`${baseUrl}get-dictionary-content/${encodedName}`)
//       .then(response => response.json())
//       .then(html => {
//         document.getElementById('about-card-text').innerHTML = html.dictionary_context;
//       })
//       .catch(error => console.error('Error fetching content:', error));
//   });

  function updateDictionaryContent() {
    const selectElement = document.getElementById('dictionary-select');
    const selectedValue = selectElement.value;

    console.log('Getting new about text for card');
    console.log(`${baseUrl}get-dictionary-content/${selectedValue}`);

    // Make an AJAX call to the Django view
    const encodedName = encodeURIComponent(selectedValue);
    console.log(`Encoded dictionary name = ${encodedName}`);

    fetch(`${baseUrl}get-dictionary-content/${encodedName}`)
      .then(response => response.json())
      .then(html => {
        document.getElementById('about-card-text').innerHTML = html.dictionary_context;
      })
      .catch(error => console.error('Error fetching content:', error));
}

// Run function on page load
document.addEventListener('DOMContentLoaded', updateDictionaryContent);

// Run function when selection changes
document.getElementById('dictionary-select').addEventListener('change', updateDictionaryContent);
