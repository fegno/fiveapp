// nav-bar
$('.toggle-btn, .menu li a:not(.dropdown-toggle)').on('click', function () {
  $('header nav').toggleClass('menu_open');
  $('.toggle-btn').toggleClass('toggle_btn_on');
});
$('.menu-area').on('click', function () {
  $('header nav').removeClass('menu_open');
  $('.toggle-btn').removeClass('toggle_btn_on');
});


//
$('.equal_heights').each(function () {
  var $columns = $('.equal_height', this);
  var maxHeight = Math.max.apply(Math, $columns.map(function () {
    return $(this).height();
  }).get());
  $columns.height(maxHeight);
});

// specific_scroll
$(window).scroll(function () {
  if ($(this).scrollTop() > 300) {
    $('body').addClass("specific_scroll");
  }
  else {
    $('body').removeClass("specific_scroll");
  }
});

// up down scroll
$(window).ready(function () {
  var previousScroll = 0;
  $(window).scroll(function () {
    var currentScroll = $(this).scrollTop();
    if (currentScroll > previousScroll) {
      $('body').removeClass("up_scroll");
    }
    else {
      $('body').addClass("up_scroll");
    }
    previousScroll = currentScroll;
  });
}());


// sidebar
$('.toggle_sidebar').on('click', function () {
  $('body').toggleClass('sidebar_open');
});


// modal_show_file
$("body").on("click", ".show_file_btn", function (event) {
  $('#file_src').attr('src', $(this).data('file-src'));
  $('#modal_show_file').find('#file_src');
  $('#modal_show_file').modal('show');
});
$(".remove_src").click(function () {
  $('#file_src').replaceWith($('#file_src').clone().attr('src', ''));
});

// WOW
$(document).ready(function(){
  new WOW().init();     
}); 
function addWowDelay() { 
  $('.wow_item').each(function(i) { d = i * 0.25 ; $(this).attr('data-wow-delay', d + "s");
   }); 
} addWowDelay();