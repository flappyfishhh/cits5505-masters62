$(function(){
    // Wait for the DOM to be fully loaded

    // Automatically hide flash messages after 3 seconds
    setTimeout(function(){
      $('.flashes').fadeOut(); // Smoothly fade out elements with class 'flashes'
    }, 3000); // 3000 milliseconds = 3 seconds
  });
  