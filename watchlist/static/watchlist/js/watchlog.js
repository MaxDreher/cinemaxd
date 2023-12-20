$(document).ready(function() {
    var table = $('#log').DataTable( {
        "autoWidth": false,
        paging: false,
        order: [[4, 'desc'], [1, 'asc']],
        dom: '<"dtsp-dataTable"Pfrtip>',
        // buttons:['colvis'],
        searchPanes: {
            order: ['Cast', 'Director', 'Production Companies', 'Genres', 'Rating', 'Year', 'Decade', 'Date Seen', 'Service', 'Theaters'], 
            layout: 'columns-1',
            // cascadePanes: true,
        },
        columnDefs: [
            {
                targets: [16,17,18,19,20,21],
                visible: false,
                searchable: true
            },
            {
                targets: []
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
                targets: [4],
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
            $('#superDiv').show();
            $('#log').DataTable().columns.adjust();
        },
    } );
 
    table.searchPanes()
    $("div.dtsp-verticalPanes").append(table.searchPanes.container());
} );