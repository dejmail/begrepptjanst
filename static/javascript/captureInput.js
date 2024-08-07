const baseUrl = '{% url "begrepp" %}';
console.log(`baseUrl: ${baseUrl}`);

const categorySelect = document.querySelector('select[name="category"]');
console.log(`categorySelect: ${categorySelect}`);

const links = document.querySelectorAll('a[data-letter]');
console.log(`links: ${links}`);

categorySelect.addEventListener('change', function() {
    const category = this.value;
    console.log(`category: ${category}`);
    links.forEach(function(link) {
        const letter = link.getAttribute('data-letter');
        console.log(`letter: ${letter}`);
        link.href = `${baseUrl}?category=${category}&q=${letter}`;
        console.log(`link.href: ${link.href}`);
    });

});

