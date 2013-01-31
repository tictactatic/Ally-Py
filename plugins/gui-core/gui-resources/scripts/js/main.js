requirejs.config
({
	baseUrl: config.content_url,
//	urlArgs: "bust=" +  (new Date).getTime(),
	waitSeconds: 15,
    templatePaths:
	{
	    'default': config.core('')+'templates/',
		'plugin': config.gui('{plugin}/templates/')
	},
	paths: 
	{
		'jquery': config.cjs('jquery'),
		'jqueryui': config.cjs('jquery/ui'),
		'bootstrap': config.cjs('jquery/bootstrap'),
		'dust': config.cjs('dust'),
		'history': config.cjs('history'),
		'utils': config.cjs('utils'),
		'gettext': config.cjs('gettext'),
        'order': config.cjs('require/order'),
		'tmpl': config.cjs('require/tmpl'),
		'model': config.cjs('require/model'),
		'i18n': config.cjs('require/i18n'),
		'gizmo': config.cjs('gizmo'),
		'concat': config.cjs('concat'),		
		'newgizmo': config.cjs('newgizmo')		
	}
});
require(['concat'], function(){
	require
	([
	  config.cjs('views/menu.js'), 
	  config.cjs('views/auth.js'), 
	  'jquery', 'jquery/superdesk', 'jquery/i18n', 'jqueryui/ext'
	], 
	function(MenuView, authView, $, superdesk)
	{
        // initialize menu before auth because we have some events bound to auth there
        new MenuView({ el: $('#navbar-top') });
	    // initialize navigation authentication display
        $.superdesk.navigation.init(function(){ authView.render() });
	    // apply layout
	    $(superdesk.layoutPlaceholder).html(authView.el);
	});
});