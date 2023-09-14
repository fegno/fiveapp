// slick_slider_1
$('.slick_slider_1').slick({
  infinite: false,
  slidesToShow: 1,
  slidesToScroll: 1,
  dots: true,
  arrows: false,
});

// slick_slider_2
$('.slick_slider_2').slick({
  infinite: false,
  slidesToShow: 2,
  slidesToScroll: 1,
  dots: false,
  arrows: true,
  responsive: [
  {
    breakpoint: 767,
    settings: {
     slidesToShow: 1,
    },
  },
 ],
});

// slick_slider_3
$('.slick_slider_3').slick({
  infinite: false,
  slidesToShow: 3,
  slidesToScroll: 1,
  dots: false,
  arrows: false,
  autoplay: true,
  autoplaySpeed: 3000,
  pauseOnFocus: false,
  pauseOnHover: false,
  pauseOnDotsHover: false,
  responsive: [
  {
    breakpoint: 767,
    settings: {
     slidesToShow: 1,
    },
  },
 ],
});


// slick_slider_4
// $('.slick_slider_4').slick({
//   infinite: false,
//   slidesToShow: 4,
//   slidesToScroll: 1,
//   dots: false,
//   arrows: false,
//   autoplay: true,
//   autoplaySpeed: 3000,
//   pauseOnFocus: false,
//   pauseOnHover: false,
//   pauseOnDotsHover: false,
//   responsive: [
//   {
//     breakpoint: 767,
//     settings: {
//      slidesToShow: 1,
//     },
//   },
//  ],
// });

// slick_slider_3_sp
$('.slick_slider_3_sp').slick({
  infinite: false,
  slidesToShow: 3,
  slidesToScroll: 1,
  autoplay: false,
  autoplaySpeed: 2000,
  dots: false,
  arrows: true,
  responsive: [
   {
     breakpoint: 991,
     settings: {
      slidesToShow: 2,
     },
   },
  {
    breakpoint: 575,
    settings: {
     slidesToShow: 1,
    },
  },
 ],
});

// lick_for
$('.slick_for').slick({
  slidesToShow: 1,
  slidesToScroll: 1,
  fade: true,
  arrows: false,
  asNavFor: '.slick_nav',

  responsive: [
   {
     breakpoint: 991,
     settings: {
       dots: true,
       arrows: false,
     },
   },
 ],
});
$('.slick_nav').slick({
  slidesToShow: 4,
  slidesToScroll: 1,
  //variableWidth: true,
  asNavFor: '.slick_for',
  dots: true,
  arrows: true,
  autoplay: true,
  focusOnSelect: true,
  responsive: [
    {
      breakpoint: 991,
      settings: {
       slidesToShow: 2,
      },
    },
    {
     breakpoint: 768,
     settings: {
      slidesToShow: 2,
     },
   },
   {
     breakpoint: 575,
     settings: {
      slidesToShow: 2,
     },
   },
  ],
});