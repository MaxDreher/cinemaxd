console.log("script loaded");
$(function () {
    $("#sortable").sortable({
        update: function (event, ui) {
            console.log("Sortable updated");

            // Collect movie IDs from the sorted list
            var movieIds = [];
            $("#sortable li").each(function () {
                movieIds.push($(this).data("movie-id"));
            });
            // Make AJAX request to update the movie order on the backend
            $.ajax({
                url: updateOrderUrl,
                method: "POST",
                data: {
                    movie_ids: movieIds,
                    list_id: 1,
                },
                success: function (response) {
                    console.log("Order updated successfully:", response);
                },
                error: function (error) {
                    console.error("Error updating order:", error);
                }
            });
        },
    });
});
