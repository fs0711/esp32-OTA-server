/**
 * Theme: Zircos Admin Template
 * Author: Coderthemes
 * Component: Datatable
 * 
 */
var handleDataTableButtons = function() {
        "use strict";
        // $('#datatable').DataTable();
        $("table").each(function(){
            $(this).DataTable();
            // 0 !== $(this).length && $(this).DataTable({
            //     dom: "Bfrtip",
            //     buttons: [{
            //         extend: "copy",
            //         className: "btn-sm"
            //     }, {
            //         extend: "excel",
            //         className: "btn-sm"
            //     }, {
            //         extend: "pdf",
            //         className: "btn-sm"
            //     }, {
            //         extend: "print",
            //         className: "btn-sm"
            //     }],
            //     responsive: !0
            // })
        })
    },
    TableManageButtons = function() {
        "use strict";
        return {
            init: function() {
                handleDataTableButtons()
            }
        }
    }();