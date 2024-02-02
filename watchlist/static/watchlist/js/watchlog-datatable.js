$(document).ready(function() {
    var table = $('#log').DataTable( {
        "autoWidth": true,
        paging: true,
        lengthMenu: [
            [50, 100, 250, -1],
            [50, 100, 250, 'All']
        ],    
        order: [[5, 'desc'], [1, 'asc']],
        dom: '<"card-header d-flex justify-content-between"lf><"card-body py-0 "t><"card-footer d-flex justify-content-between"ip>',
        // buttons:['colvis'],
        searchPanes: {
            order: ['Cast', 'Director', 'Rating', 'Year', 'Decade', 'Date Seen', 'Production Companies', 'Genres', 'Service', 'Theaters',], 
            layout: 'columns-2',
            orderable: false,
            // cascadePanes: true,
        },
        columnDefs: [
            {
                targets: [0],
                sortable: false
            },
            {
                targets: [16,17,18,19,20,21],
                visible: false,
                searchable: true
            },
            {
                searchPanes: {
                    dtOpts: {
                        searching: false,
                        order: [[0, 'desc']]
                    }
                },
                targets: [2, 3, 4, 7]
            },
            {
                searchPanes: {
                    show: true,
                    orthogonal:'sp',
                    dtOpts: {
                        order: [[1, "desc"]]
                    }
                },
                targets: [16,17,18,19,20],
                render: function (data, type, row) {
                    if (type === 'sp') {
                        return data.split(', ')
                    }
                    return data;
                }
            },
            {
                searchPanes: {
                    header: 'Year Seen',
                    show: true,
                    orthogonal:'sp',
                    dtOpts: {
                        order: [[0, "desc"]]
                    }
                },
                targets: [5],
                render: function (data, type, row) {
                    if (type === 'sp') {
                        return data.split('-')[0]
                    }
                    return data;
                }
            },
            {
                searchPanes: {
                    options: [
                        {
                            label: 'Seen in Theaters',
                            value: function(rowData, rowIdx) {
                                return rowData[21] == "True";
                            }
                        },
                        {
                            label: 'Not Seen in Theaters',
                            value: function(rowData, rowIdx) {
                                return rowData[21] != "True";
                            }
                        },
                    ]
                },
                targets: [21]
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
