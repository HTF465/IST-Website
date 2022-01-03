function onSubmit(token){
    let form = document.getElementById("form");
    $(':valid').parent('.formgroup').removeClass('has-error');
    $(':invalid').parent('.formgroup').addClass('has-error');
    if (form.checkValidity()){
        form.submit();
    }
    else {
        $('.g-recaptcha')
            .off('**')
            .click(function(){onSubmit(token);})
            .attr('name', 'g-recaptcha-response')
            .attr('value', token);
        $(form).find('.form-error').removeClass('hidden');
    }
}
