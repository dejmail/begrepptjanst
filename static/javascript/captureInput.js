const baseUrl = home_url;
console.log(`baseUrl: ${baseUrl}`);

const dictionarySelect = document.querySelector('select[name="dictionary"]');
console.log(`dictionarySelect: ${dictionarySelect}`);

const links = document.querySelectorAll('a[data-letter]');
console.log(`links: ${links}`);

dictionarySelect.addEventListener('change', function() {
    const dictionary = this.value;
    console.log(`dictionary: ${dictionary}`);
    links.forEach(function(link) {
        const letter = link.getAttribute('data-letter');
        console.log(`letter: ${letter}`);
        link.href = `${baseUrl}?dictionary=${dictionary}&q=${letter}`;
        console.log(`link.href: ${link.href}`);
    });

});
