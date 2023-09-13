$(document).ready(function () {
  // pre-loader script 
    $(".pre_loader").fadeOut("slow");
  
  // active link 
    for (var i = 0; i < document.links.length; i++) {
     if (document.links[i].href == document.URL) {
   $(document.links[i]).addClass('active');
   }}
 
 });

// mobile_device
$(document).ready(function () {
  if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
    $('body').addClass("mobile_device");
  }
});