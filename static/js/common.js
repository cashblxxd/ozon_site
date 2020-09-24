$(document).ready(function() {
  
  var fActive = '';
 
  function filterGoods(goods){
   if(fActive != goods){
   $('.wrap_tab_content_filter tbody tr').filter('.'+goods).fadeIn();
   $('.wrap_tab_content_filter tbody tr').filter(':not(.'+goods+')').hide();
   fActive = goods;
   }
  }

  function buttonShow(filt) {
    if( filt == 'expect') $('.wrap_button_order').empty().append("<a class='btn' href='#'>Собрать выделенные</a><a class='btn' href='#'>Собрать все</a>").show();
    else if( filt == 'cargo') $('.wrap_button_order').empty().append("<a class='btn' href='#'>Заказать курьера</a><a class='btn' href='#'>Печать маркировок</a><a class='btn' href='#'>Печать акта и ттн</a>").show();
          else $('.wrap_button_order').empty().hide();
  }

  //Tabs  
  $(".wrapper_tab .list_tabs .tab").click(function() {     
    $(this).addClass("active"); 
    $(this).siblings('.active').removeClass('active');   
    
    var num = $(this).attr('data-tab');

    $(".wrapper_tab_content .wrap_tab").removeClass("active");
    $(".wrapper_tab_content .wrap_tab").hide();
    $(".wrapper_tab_content .tab_item"+num).fadeIn();

    var filt = $(".wrapper_tab_content .tab_item"+num).find(".wrapper_tab_filter .list_tabs .tab.active").attr('data-filtr');

    filterGoods(filt);

    if(filt == 'all') {
      $('.wrap_tab_content_filter tr').fadeIn();
    }
    fActive='';
    
    buttonShow(filt);
  });  

  $(".wrapper_tab_filter .list_tabs .tab").click(function() {     
    $(this).addClass("active"); 
    $(this).siblings('.active').removeClass('active');   
    
    var goods = $(this).attr('data-filtr');

    filterGoods(goods);

    buttonShow(goods);

    if(goods == 'all') {
      $('.wrap_tab_content_filter tr').fadeIn();
    }

  });

  //Left menu
  $(".accordeon .accordeon-head").click(function() {
    var ah = $(this);
      
      $(".accordeon .accordeon-body").not(ah.next()).slideUp("slow"); 
      setTimeout(function(){
         $('.accordeon .accordeon-head').closest('li').not(ah.closest('li')).removeClass('active');
        }, 500);     
      
      ah.next().slideToggle("slow");
      
      if(ah.closest('li').hasClass('active'))
        setTimeout(function(){
         ah.closest('li').removeClass('active');
        }, 500);
      else ah.closest('li').addClass('active');
      
  });

  //Slider month
  $('.wrap_slider .next').click(function() {
    var w_p = $(this).closest('.wrap_slider').width(),
        w_s = $(this).siblings('.slide_items').width(),
        x_pos = $(this).siblings('.slide_items').position().left,
        l = w_s - w_p + x_pos;

    

    $('.wrap_slider .slide_items').animate({left: -l}, 500);
    $(this).hide();
    $('.wrap_slider .prev').show();
  })

  $('.wrap_slider .prev').click(function() {
    
    $('.wrap_slider .slide_items').animate({left: '18px'}, 500);
    $(this).hide();
    $('.wrap_slider .next').show();
  })

  //Tolltip
  $('.tooltip').mouseenter(function() {
    var h = $(this).find('span').height(),
        w = $(this).find('span').width(),
        hr = $(this).height(),
        wr = $(this).width(),
        top = hr + 5,
        left = wr/2 - w/2;
        
        $(this).find('span').addClass('visible')
                     .css({ 
                         "top" : top,
                        "left" : left
                     })

    }).mouseleave(function() {

        $(this).find('span').removeClass('visible');
    });

    //user menu
    $('.spec').click(function() {
      var h = $(this).find('.span').height(),
        w = $(this).find('.span').width(),
        hr = $(this).height(),
        wr = $(this).width(),
        top = hr + 5,
        left = wr/2 - w/2;

      if($(this).attr('id') == 'user')              
        $(this).find('.span').addClass('visible').css({"top" : '0', "left" : '27px'});        
      else        
          $(this).find('.span').addClass('visible').css({"top" : top, "left" : left});

      $(this).addClass('active');
        
    })

    //close user menu
    $('.spec .span .esc, .spec .span .btn').click(function(e) {
      e.stopImmediatePropagation();
      $(this).closest('.span').removeClass('visible');
      document.location.href=$(this).attr('href');
      $(this).closest('.spec').removeClass('active');
    })

    //message form box 
    $('body').on('submit', '.form', function(evt) {
      evt.preventDefault();

      $('.overlay').fadeIn(297, function(){
        $('.wrap_mess') 
        .css('display', 'inline-block')
        .animate({opacity: 1}, 198);
      });

    });

    //close message box
    $('.wrap_mess .close, .overlay').click( function(){
      $('.wrap_mess').animate({opacity: 0}, 198, function(){
        $(this).css('display', 'none');
        $('.overlay').fadeOut(297);
      });
    });

    //add account
    $('#add_acc').click(function(e) {
      e.preventDefault();
      $('.wrap_acc').append('<div class="wrap_input_acc"><div class="wrap_acc_name input_group"><div class="wrap_input"><input type="text" name="acc_name" placeholder="Название"></div></div><div class="wrap_id input_group"><div class="wrap_input"><input type="text" name="id" placeholder="Client ID"></div></div><div class="wrap_api input_group"><div class="wrap_input"><input type="text" name="key" placeholder="API key"></div></div></div>');
    });
    
});

//close user menu
$(document).mouseup(function (e){
    var div = $('.spec.active .span');
    if (!div.is(e.target)
        && div.has(e.target).length === 0) { 
      div.removeClass('visible');
      div.closest('.spec').removeClass('active');
    }
});