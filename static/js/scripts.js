$(document).ready(function() {
    // Initialize select2 for stock selection
    $("#stocks").select2({
        placeholder: "Recherchez et sélectionnez des stocks",
        minimumInputLength: 1,
        ajax: {
            url: "/stock_search", // Endpoint to search for stocks
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    q: params.term // search term
                };
            },
            processResults: function(data) {
                return {
                    results: data.items
                };
            },
            cache: true
        }
    });
});
