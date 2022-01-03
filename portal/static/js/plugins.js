String.prototype.format = function(){
    let s = this;
    for (let i = 0; i < arguments.length; i++){
        s = s.replace(
            new RegExp("\\{" + i + "\\}", "gm"),
            arguments[i]
        );
    }
    return s;
}
