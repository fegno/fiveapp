// https://codepen.io/ARiyou2000/pen/YzyxMOQ

$(document).ready(function () {
  if (!sessionStorage.getItem('isPreloder')) {
    $(document).ready(preloderFunction());
    sessionStorage.setItem('isPreloder', true);
    $('#preloader').removeClass('d-none');
  }
  else {
    $('#preloader-section').remove();
    $('#preloader').addClass('d-none');
    $('body').removeClass('no-scroll-y');
  }
}); 

function preloderFunction() {
  
    setTimeout(function() {
        
        // Force Main page to show from the Start(Top) even if user scroll down on preloader - Primary (Before showing content)
       
        // Model 1 - Fast            
        document.getElementById("body").scrollIntoView();
        
        // Model 2 - Smooth             
        // document.getElementById("body").scrollIntoView({behavior: 'smooth'});

        // Removing Preloader:
        
        $('#ctn-preloader').addClass('loaded');  
        // Once the preloader has finished, the scroll appears 
        $('body').removeClass('no-scroll-y');

        if ($('#ctn-preloader').hasClass('loaded')) {
            // It is so that once the preloader is gone, the entire preloader section will removed
            $('#preloader').delay(1000).queue(function() {
                $('#preloader-section').remove();
                
                // If you want to do something after removing preloader:
                afterLoad();
                
            });
        }
    }, 2200);
}

function afterLoad() {
    // After Load function body!
}