function toggleDetails(itemId) {
    var elem = document.getElementById('details-' + itemId);
    if (elem.style.display === 'none' || elem.style.display === '') {
        elem.style.display = 'block';
    } else {
        elem.style.display = 'none';
    }
}