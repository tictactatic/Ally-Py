define([ 'jquery', 'ui/multiSplit', 'format/format-plugin' ],
function ($, MultiSplit, Format) 
{
	'use strict';
	
	var origInit = MultiSplit.prototype.init;
	MultiSplit.prototype.init = function()
	{
	    var ret = origInit.apply(this, arguments);

	    // make list item from each button
	    for( var btn in this.buttons)
	    {
	        var newEl = $('<li />').append($(this.buttons[btn].element).clone(true, true)),
            modelEl = $("[data-format='"+btn+"']", Aloha.settings.plugins.toolbar.element);
            modelEl.length 
                && $(modelEl.prop('attributes')).each(function(){ newEl.attr(this.name, this.value); })
                && $(this.buttons[btn].element).replaceWith(newEl);
	    };
	    
	    // make the container ul
	    var newContent = $('[data-format-content]', Aloha.settings.plugins.toolbar.element).clone(true, true);
	    newContent.append(this.contentElement.contents());
	    this.contentElement.replaceWith(newContent);
	    
	    return ret;
	};
	
	MultiSplit.prototype.open = function() 
	{
        this.element.addClass('open');
        this._isOpen = true;
    };

    MultiSplit.prototype.close = function() 
    {
        this.element.removeClass('open');
        this._isOpen = false;
    };
    
    MultiSplit.prototype.toggle = function () 
    {
        this.element.toggleClass('open');
        this._isOpen = !this._isOpen;
    };
	
	return MultiSplit
});
