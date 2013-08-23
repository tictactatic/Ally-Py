/*
    Use:
        - $('#element').loadingblock();                 to make loading block over an element, without any msg
        - $('#element').loadingblock('Some msg here');  to make a loading block over an element, with text msg

        - $('#element').loadingblock('hide');           to hide loading block once it is initialize
        - $('#element').loadingblock('show');           to show loading block once it is initialize

        - $('#element').loadingblock('destroy');        to destroy oading block
        
    Calling .loadingblock() on already the element that already contained one, will result with showing new
    text and making it visible again. (so overriding the old one)

    It is not possible to use loadign block on elements that are not able to have child nodes (like <input>)
*/

(function ($) {
 
    $.fn.loadingblock = function(text) {
        var _block = this.find("> .async-loading");
        var _exist = _block.length > 0 ? true : false;
        switch (text) {
            case 'hide' : 
                        _exist == true && _block.hide();
                        break;
            case 'show' :  
                        _exist == true && _block.show();
                        break;
            case 'destroy' : 
                        _exist == true && _block.remove();
                        break;
            default : 
                        var msg = ( text === undefined ? '' : text);
                        if ( _exist == true) {
                            _block.find(".loading-msg").html(msg);
                            _block.show();
                        }
                        else {
                            var _pos = this.css('position');
                            (_pos !== 'absolute' && _pos !== 'relative' && _pos !== 'fixed') && this.css('position','relative');
                            var template = '<div class="async-loading"><div class="loading-msg">' + msg + '</div></div>';
                            this.append(template);
                        }
                        break;
        }
        return this;
    }; 
}( jQuery ));