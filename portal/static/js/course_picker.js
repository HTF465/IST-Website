let options;
function get_sections(){
    let course = $('#course_id').val();
    let remove_selector = '#section_id optgroup:not([parent="{0}"])'.format(course);
    let remove = $(remove_selector);
    if ($('#section_id optgroup').length == remove.length){
        $('#section_id').val('');
        remove.remove();
        $('#section_id').append(
            options.filter('[parent="{0}"]'.format(course))
        );
    }
    else {
        remove.remove();
    }
}

$(function(){
    options = $('#section_id optgroup');
    $('#course_id').change(get_sections);
    get_sections();
});
