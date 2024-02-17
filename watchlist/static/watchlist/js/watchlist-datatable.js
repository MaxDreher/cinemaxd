$(document).ready(function() {
    var table = $('#watchlist').DataTable( {
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
            order: ['Streaming', 'Runtime', 'Decade', 'Tags', 'Cast', 'Director', 'Production Companies', 'Genres', 'Year', 'Providers'], 
            layout: 'columns-2',
            orderable: false,
            panes: [
                {
                    header: 'Streaming',
                    options: [
                        {
                            label: 'Streaming',
                            value: function(rowData, rowIdx) {
                                return rowData[23] != '';
                            },
                            className: 'streaming'
                        },
                        {
                            label: 'Not Streaming',
                            value: function(rowData, rowIdx) {
                                return rowData[23] === '';
                            },
                            className: 'not_streaming'
                        }
                    ],
                    dtOpts: {
                        searching: false,
                        order: [[1, 'desc']]
                    }
                }
            ]
        },
        columnDefs: [
            // make poster, service icon unsortable
            { targets: [0, 3], sortable: false },

            // hide csv rows that are used for filter data
            { targets: [19,20,21,22,23], visible: false, searchable: true },

            {
                searchPanes: {
                    show: true,
                    orthogonal:'sp',
                    dtOpts: {
                        order: [[1, "desc"]]
                    }
                },
                targets: [5,19,20,21,22,23],
                render: function (data, type, row) {
                    if (type === 'sp') {
                        return data.split(', ')
                    }
                    return data;
                }
            },
            {
                searchPanes: {
                    options: [
                        {
                            label: 'Under 1hr30',
                            value: function (rowData, rowIdx, columnIndex) {
                                return parseRuntime(rowData[6]) < 90 && rowData[6] !== '';
                            }
                        },
                        {
                            label: 'Under 2hr00',
                            value: function (rowData, rowIdx, columnIndex) {
                                return parseRuntime(rowData[6]) < 120 && rowData[6] !== '';
                            }
                        },
                        {
                            label: 'Under 2hr30',
                            value: function (rowData, rowIdx, columnIndex) {
                                return parseRuntime(rowData[6]) < 150 && rowData[6] !== '';
                            }
                        },
                        {
                            label: 'Under 3hr00',
                            value: function (rowData, rowIdx, columnIndex) {
                                return parseRuntime(rowData[6]) < 180 && rowData[6] !== '';
                            }
                        },
                        {
                            label: 'Unlimited Time',
                            value: function (rowData, rowIdx, columnIndex) {
                                return parseRuntime(rowData[6]) > 0 && rowData[6] !== '';
                            }
                        }
                    ]
                },
                targets: [6]
            },
            {
                searchPanes: {
                    dtOpts: {
                        order: [[0, 'desc']]
                    }
                },
                targets: [2, 9]
            },
            {
                targets: [6, 18],
                type: 'natural'
            }
        ],
        initComplete: function(settings, json) {
            $('#container').show();
            $('#watchlist').DataTable().columns.adjust();
        },
    });
 
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

// Custom function to parse runtime string into minutes
function parseRuntime(runtimeString) {
    if (runtimeString) {
        var parts = runtimeString.split(' ');
        if (parts.length === 14) {
            var hours = parseInt(parts[12].replace('hr', ''), 10) || 0;
            var minutes = parseInt(parts[13].replace('min\n</p>', ''), 10) || 0;
            return hours * 60 + minutes;
        }
    }
    return 0;  // Return 0 if the format is unexpected or runtimeString is undefined
}
