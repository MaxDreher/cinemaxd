$(document).ready(function() {
    var table = $('#watchlist').DataTable( {
        "autoWidth": false,
        paging: false,
        order: [[5, 'desc'], [1, 'asc']],
        dom: '<"dtsp-dataTable"Pfrtip>',
        searchPanes: {
            order: ['Providers', 'Runtime', 'Reason', 'Cast', 'Director', 'Production Companies', 'Genres', 'Year', 'Decade'], 
            layout: 'columns-1',
            // cascadePanes: true,
        },
        columnDefs: [
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
                            label: 'Under 90',
                            value: function(rowData, rowIdx) {
                                return rowData[6] < 90;
                            }
                        },
                        {
                            label: '91 to 120',
                            value: function(rowData, rowIdx) {
                                return rowData[6] <= 120 && rowData[6] >=91;
                            }
                        },
                        {
                            label: '121 to 150',
                            value: function(rowData, rowIdx) {
                                return rowData[6] <= 150 && rowData[6] >=121;
                            }
                        },
                        {
                            label: '151 to 180',
                            value: function(rowData, rowIdx) {
                                return rowData[6] <= 180 && rowData[6] >=151;
                            }
                        },
                        {
                            label: 'Over 180',
                            value: function(rowData, rowIdx) {
                                return rowData[6] > 180;
                            }
                        }
                    ]
                },
                targets: [6]
            },
        ],
        initComplete: function(settings, json) {
            $('#superDiv').show();
            $('#watchlist').DataTable().columns.adjust();
        },
    });
 
    table.searchPanes()
    $("div.dtsp-verticalPanes").append(table.searchPanes.container());
});