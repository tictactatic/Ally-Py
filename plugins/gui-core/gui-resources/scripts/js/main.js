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
	function(MenuView, AuthApp, $, superdesk)
	{
		var menuView = new MenuView, 
		makeMenu = function()
		{ 
		    menuView.getMenu(menuView.render);
		}, 
		authLock = function()
		{
			var args = arguments,
				self = this;
			AuthApp.success = makeMenu;
			AuthApp.require.apply(self, arguments); 
		},
		r = $.rest.prototype.doRequest;
		$.rest.prototype.doRequest = function()
		{
			var ajax = r.apply(this, arguments),
				self = this;
			ajax.fail(function(resp){ (resp.status == 404 || resp.status == 401) && authLock.apply(self, arguments); });
			return ajax;
		};

		$.rest.prototype.config.apiUrl = config.api_url;
		$.restAuth.prototype.config.apiUrl = config.api_url;

		function checkAndResetLocalStorage()
		{
		    var sl = 'superdesk.login.';
		    if( !localStorage.getItem(sl+'id') || !localStorage.getItem(sl+'selfHref') || !localStorage.getItem(sl+'name') )
		    {
		        localStorage.removeItem(sl+'id');
		        localStorage.removeItem(sl+'selfHref');
		        localStorage.removeItem(sl+'name');
		        return false;
		    }
		    return true;
		}
		// user already logged in
		// set authorization token, set some internal data, reset actions url
		if( checkAndResetLocalStorage() )
		{
			$.restAuth.prototype.requestOptions.headers.Authorization = localStorage.getItem('superdesk.login.session');
			superdesk.actionsUseAuth = true;
			superdesk.actionsUrl = localStorage.getItem('superdesk.login.selfHref')+'/Action';
			superdesk.login = {Id: localStorage.getItem('superdesk.login.id'), Name: localStorage.getItem('superdesk.login.name'), EMail: localStorage.getItem('superdesk.login.email')};
		}

		$.superdesk.navigation.init(makeMenu);
		
	});
});