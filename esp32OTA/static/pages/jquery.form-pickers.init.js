/**
 * Theme: Zircos Admin Template
 * Author: Coderthemes
 * Form Pickers
 */

    $('#reportrange').daterangepicker({
        format: 'DD/MM/YYYY',
        startDate: moment().subtract(29, 'days'),
        endDate: moment(),
        minDate: '01/01/2021',
        maxDate: '12/31/2030',
        dateLimit: {
            days: 600
        },
        showDropdowns: true,
        showWeekNumbers: false,
        timePicker: false,
        timePickerIncrement: 1,
        timePicker12Hour: true,
        ranges: {
            'Today': [moment(), moment()],
            'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
            'Last 7 Days': [moment().subtract(6, 'days'), moment()],
            'Last 30 Days': [moment().subtract(29, 'days'), moment()],
            'This Month': [moment().startOf('month'), moment().endOf('month')],
            'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        },
        opens: 'left',
        drops: 'down',
        buttonClasses: ['btn', 'btn-sm'],
        applyClass: 'btn-success',
        cancelClass: 'btn-default',
        separator: ' to ',
        locale: {
            applyLabel: 'Submit',
            cancelLabel: 'Cancel',
            fromLabel: 'From',
            toLabel: 'To',
            customRangeLabel: 'Custom',
            daysOfWeek: ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'],
            monthNames: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
            firstDay: 1
        }
    }, function (start, end, label) {
        console.log(start.format('DD MM YYYY').toString(), end.format('DD MM YYYY').toString(), label);
        $('#reportrange span').html(start.format('DD-MM-YYYY') + ' to ' + end.format('DD-MM-YYYY'));
        $('#start').val(start.format('DD MM YYYY').toString());
        $('#end').val(end.format('DD MM YYYY').toString());
        // $('#reportrange').append('<input id="start" type="hidden" name="date_start" value="' + start.toISOString() + '" >');
        // $('#reportrange').append('<input id="end" type="hidden" name="date_end" value="' + end.toISOString() + '" >');
    });