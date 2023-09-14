// open-sidebar
$(document).ready(function () {
  $('.sub-menu-link').click(function () {
    $('body').addClass('open-sidebar');
  });
});
var div = localStorage['div'] || 0;
if (div == 1) {
  $('body').toggleClass("open-sidebar");
}
$('.sidebar_toggle').click(function () {
  $('body').toggleClass("open-sidebar");
  var current = localStorage['div'] || 0;
  if (current == 1) {
    localStorage['div'] = 0;
  }
  else {
    localStorage['div'] = 1;
  }
});

// hasClass active
$(document).ready(function () {
  if ($(".sidebar-menu .sub-menu li a").hasClass("active")) {
    localStorage['div'] = 0;
    var div = $(".sidebar-menu .sub-menu li a.active")
    div.parents('.sub-menu').parents('li').addClass("open");
  }
});

// sidebar_toggle_mob
$(document).ready(function () {
  $('.sidebar_toggle_mob').click(function () {
    $('body').toggleClass('open-sidebar-mob');
  });
});

// table_tr_listing
$(document).ready(function () {
  $('.btn_tr_listing').click(function () {
    $(this).parents('.table_tr_listing').toggleClass('listed');
  });
});

// text_uppercase
$('.text_uppercase').keyup(function () {
  $(this).val($(this).val().toUpperCase());
});

// range_datepicker
$(document).ready(function () {

  var start = moment();
  var end = moment();
  var from_date = window.from_date
  var to_date = window.to_date
  if (window.from_date != "None") {

    var start = moment(window.from_date)
    var end = moment(window.to_date)
  }
  function cb(start, end) {

    $('.range_datepicker span').html(start.format('DD/MM/YYYY') + ' - ' + end.format('DD/MM/YYYY'));
    $('#STARTDATE').val(start.format('YYYY-MM-DD'));
    $('#ENDDATE').val(end.format('YYYY-MM-DD'));
    $(document).trigger('myCustomEvent');
  }

  $('.range_datepicker').daterangepicker({

    startDate: start,
    endDate: end,
    ranges: {
      'Today': [moment(), moment()],
      'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
      'Last 7 Days': [moment().subtract(6, 'days'), moment()],
      'Last 30 Days': [moment().subtract(29, 'days'), moment()],
      'This Month': [moment().startOf('month'), moment().endOf('month')],
      'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
    },
    drops: 'auto',
  }, cb);
  cb(start, end);
});


// jquery_search_tr
$(document).ready(function () {
  $(".jquery_search_tr").on("keyup", function () {
    var value = $(this).val().toLowerCase();
    $(".jquery_search_item").filter(function () {
      $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
    });
  });
});


// jquery-file-upload-preview-remove-image
// https://stackoverflow.com/questions/40609463/jquery-file-upload-preview-remove-image
function readURL() {
  var $input = $(this);
  var $newinput = $(this).parent().find('.choose_file_view');
  if (this.files && this.files[0]) {
    var reader = new FileReader();
    reader.onload = function (e) {
      $newinput.attr('src', e.target.result).show();
    }
    reader.readAsDataURL(this.files[0]);
  }
}
$(".choose_file").change(readURL);


// upload_type_group
$(document).ready(function () {
  $(".upload_type_group input[name$='upload_type']").click(function () {
    var test = $(this).val();
    $(".upload_type_group .upload_type input").attr('required', false);
    $(".upload_type_group .upload_type input").attr('disabled', true);

    $(".upload_type_group #upload_type_" + test).find('input').attr('required', true)
    $(".upload_type_group #upload_type_" + test).find('input').attr('disabled', false)

    $(".upload_type_group .upload_type input").val('');
  });
});


// modal_show_image
function show_image(src) {
  $('.modal_show_image .show_image').attr('src', $(src).attr('src'));
  $('.modal_show_image').offcanvas('show');
}

function getId(url) {
  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
  const match = url.match(regExp);

  return (match && match[2].length === 11)
    ? match[2]
    : null;
}

// modal_show_file
$("body").on("click", ".show_file_btn", function (event) {
  $('#file_src').attr('src', $(this).data('file-src'));
  $('.modal_show_file').find('#video_file').attr('hidden', false);
  $('.modal_show_file').find('#i_file_src').attr('hidden', true);
  var url = $(this).data('url')
  if (url) {

    const videoId = getId(url);


    $('#i_file_src').attr('src', "//www.youtube.com/embed/" + videoId);
    $('.modal_show_file').find('#i_file_src').attr('hidden', false);
    $('.modal_show_file').find('#video_file').attr('hidden', true);
  }


  $('.modal_show_file').offcanvas('show');

});

$(".remove_src").click(function () {
  $('#file_src').replaceWith($('#file_src').clone().attr('src', ''));

  $('#i_file_src').replaceWith($('#i_file_src').clone().attr('src', ''));
});

// date_pick  
$(document).ready(function () {
  $(".date_pick").datepicker({
    // changeMonth: true,
    changeYear: true,
    yearRange: '1950:' + (new Date().getFullYear() + 2).toString()
  });
  $(".today_date").datepicker().datepicker("setDate", new Date());
});

// month_year_pick
$(function () {
  $('.month_year_pick').datepicker({
    changeMonth: true,
    changeYear: true,
    // showButtonPanel: true,
    dateFormat: 'MM yy',
    onClose: function (dateText, inst) {
      $(this).datepicker('setDate', new Date(inst.selectedYear, inst.selectedMonth, 1));
      $('#MONTH').val(inst.selectedMonth);
      $('#YEAR').val(inst.selectedYear);
      $('#FORMSUB').submit()
    },
    beforeShow: function (input, inst) {
      $(inst.dpDiv).addClass('ui_datepicker_month_year');
    }
  });
  $('.month_year_pick').datepicker('setDate', 'today');
});

// batch_start_date
var dateToday = '';
$('.batch_start_date').datepicker({
  onSelect: function (dateText, inst) {
    $('.date_time_pick').each(function () {
      $(this).daterangepicker({
        maxDate: dateText,
        singleDatePicker: true,
        autoUpdateInput: true,
        //defaultDate: '11/02/2022 23:59',
        timePicker: true,
        applyClass: 'btn-primary',
        cancelClass: 'btn-defult',
        drops: 'dwon',
        locale: {
          format: 'DD/MM/YYYY HH:mm'
        }
      }
      );
      $(".last_entry_date").val(moment('23:59', 'HH:mm').format('DD/MM/YYYY HH:mm'));
    });
    // dateToday=new Date(toString(dateText))
    //dateToday=moment(dateText).format('DD/MM/YYYY HH:mm')
  }
});

// date_time_pick
$('.date_time_pick').each(function () {
  $(this).daterangepicker({
    // minDate: dateToday,
    singleDatePicker: true,
    autoUpdateInput: true,
    timePicker: true,
    applyClass: 'btn-primary',
    cancelClass: 'btn-defult',
    drops: 'dwon',


    pickDate: false,
    pickSeconds: false,
    pick12HourFormat: false,

    locale: {
      format: 'DD/MM/YYYY HH:mm'
    }
  }
  );
});

// last_entry_date
$(".last_entry_date").val(moment('23:59', 'HH:mm').format('DD/MM/YYYY HH:mm'));


// submitAnyForm
function submitAnyForm(src) {
  var form = $(src).parents('form').first();
  if (!form[0].checkValidity())
    $('<input type="submit">').hide().appendTo(form).click().remove();
  else {
    $(src).removeAttr('onclick');
    $(src).prop("disabled", true)
    $(src).prop('onclick', null).off('click');
    $(src).text('Submitting...');
    form.submit();
  }
}


// Auto calculate table colspan if set to 0
var colCount = 0;
$("td[colspan='0'].colspan_auto").each(function () {
  colCount = 0;
  $(this).parents("table").find('tr').eq(0).children().each(function () {
    if ($(this).attr('colspan')) {
      colCount += +$(this).attr('colspan');
    } else {
      colCount++;
    }
  });
  $(this).attr("colspan", colCount);
});