function del(){
    if (confirm('Are you sure you want to delete this record? It cannot be recovered.')){
        let elem = $(this);
        let form = elem.closest('form');
        form.submit();
    }
}

$(function(){
    $('#delete').click(del);
});
