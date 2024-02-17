$(document).ready(function() {
    var table = $('#log').DataTable( {
        "autoWidth": true,
        paging: true,
        lengthMenu: [
            [50, 100, 250, -1],
            [50, 100, 250, 'All']
        ],    
        order: [[7, 'desc'], [1, 'asc']],
        dom: '<"card-header d-flex justify-content-between"lf><"card-body py-0 "t><"card-footer d-flex justify-content-between"ip>',
        // buttons:['colvis'],
        searchPanes: { 
            order: ['Cast', 'Director', 'Rating', 'Year', 'Decade', 'Date Seen', 'Production Companies', 'Genres', 'Service', 'Theaters'], 
            layout: 'columns-2',
            orderable: false,
        },
        columnDefs: [
            // make poster, service icon unsortable
            { targets: [0, 3], sortable: false },

            // hide csv rows that are used for filter data
            { targets: [20,21,22,23,24,25], visible: false, searchable: true },
            
            {
                // order Year, Rating, Runtime, Decade SearchPanes by Desc order.
                searchPanes: { dtOpts: { order: [[0, 'desc']] } },
                targets: [2, 5, 6, 9]
            },

            {
                // enable searchpanes for hidden columns for actor, director, companies, service, genre
                searchPanes: { show: true, orthogonal:'sp', dtOpts: { order: [[1, "desc"]] }},
                targets: [20,21,22,23,24],
                render: function (data, type, row) {
                    if (type === 'sp') {
                        return data.split(', ')
                    }
                    return data;
                }
            },
            {
                // create "year seen" searchpane from date seen values
                searchPanes: { header: 'Year Seen', show: true, orthogonal:'sp', dtOpts: { order: [[0, "desc"]] } },
                targets: [7],
                render: function (data, type, row) {
                    if (type === 'sp') {
                        return data.split('-')[0]
                    }
                    return data;
                }
            },
            {   
                // create seen in theaters pane w/ t/f options
                searchPanes: {
                    options: [
                        { label: 'Seen in Theaters', value: function(rowData, rowIdx) {return rowData[25] == "True";}},
                        { label: 'Not Seen in Theaters', value: function(rowData, rowIdx) {return rowData[25] != "True";}},
                    ]
                },
                targets: [25]
            },
            {
                targets: [6, 18],
                type: 'natural'
            }
        ],

        initComplete: function( settings, json ) {
            $('#container').show();
            $('#log').DataTable().columns.adjust();
        },
    } );
    table.searchPanes();

    // Append title row
    $("div.dtsp-verticalPanes").append(table.searchPanes.container());
    var divToMove = document.querySelector('.dtsp-titleRow');
    var newContainer = document.getElementById('sidebar-header');
    newContainer.appendChild(divToMove);
    var titleRow = document.querySelector('.dtsp-titleRow');
    var buttons = titleRow.querySelectorAll('.btn');
    var buttonContainer = document.createElement('div');
    buttonContainer.classList.add('d-flex', 'me-0');
    buttons.forEach(function(button) {
        buttonContainer.appendChild(button);
    });
    titleRow.appendChild(buttonContainer);
    
});
