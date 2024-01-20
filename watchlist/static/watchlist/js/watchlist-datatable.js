$(document).ready(function() {
    var table = $('#watchlist').DataTable( {
        "autoWidth": true,
        paging: true,
        lengthMenu: [
            [50, 100, 250, -1],
            [50, 100, 250, 'All']
        ],    
        order: [[6, 'desc'], [1, 'asc']],
        dom: '<"card-header d-flex justify-content-between"lf><"card-body py-0 "t><"card-footer d-flex justify-content-between"ip>',
        // buttons:['colvis'],
        searchPanes: {
            order: ['Streaming', 'Runtime', 'Decade', 'Reason', 'Cast', 'Director', 'Production Companies', 'Genres', 'Year', 'Providers'], 
            layout: 'columns-2',
            orderable: false,
            panes: [
                {
                    header: 'Streaming',
                    options: [
                        {
                            label: 'Streaming',
                            value: function(rowData, rowIdx) {
                                return rowData[21] != '';
                            },
                            className: 'streaming'
                        },
                        {
                            label: 'Not Streaming',
                            value: function(rowData, rowIdx) {
                                return rowData[21] === '';
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
            {
                targets: [0],
                sortable: false
            },
            {
                targets: [17,18,19,20,21],
                visible: false,
                searchable: true
            },
            {
                searchPanes: {
                    show: true,
                    orthogonal:'sp',
                    dtOpts: {
                        order: [[1, "desc"]]
                    }
                },
                targets: [4,17,18,19,20,21],
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
                            value: function(rowData, rowIdx) {
                                return rowData[5] < 90 && rowData[5] != '';
                            }
                        },
                        {
                            label: 'Under 2hr00',
                            value: function(rowData, rowIdx) {
                                return rowData[5] < 120 && rowData[5] != '';
                            }
                        },
                        {
                            label: 'Under 2hr30',
                            value: function(rowData, rowIdx) {
                                return rowData[5] < 150 && rowData[5] != '';
                            }
                        },
                        {
                            label: 'Under 3hr00',
                            value: function(rowData, rowIdx) {
                                return rowData[5] < 180 && rowData[5] != '';
                            }
                        },
                        {
                            label: 'Unlimited Time',
                            value: function(rowData, rowIdx) {
                                return rowData[5] > 0 && rowData[5] != '';
                            }
                        }
                    ]
                },
                targets: [5]
            },
            {
                searchPanes: {
                    dtOpts: {
                        searching: false,
                        order: [[0, 'desc']]
                    }
                },
                targets: [2, 8]
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