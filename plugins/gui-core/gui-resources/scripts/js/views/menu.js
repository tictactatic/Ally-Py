define
([
    'jquery','jquery/superdesk', 'gizmo/superdesk', 
    config.cjs('views/auth.js'),
    'dust/core','jquery/tmpl','jquery/rest', 'bootstrap',  
    'tmpl!layouts/dashboard',
    'tmpl!navbar'
], 
function($, superdesk, Gizmo, AuthApp)
{
    var MenuView = Gizmo.View.extend
    ({
        events: { "[data-logged-in]": { 'click' : 'loginHandler' } },
        
        getMenu: function(cb)
        {
            this.displayMenu = [];
            this.submenus = {};
            
            var dfd = new $.Deferred,
                self = this;
            dfd.done(cb); // attach callback to deferred
            
            if( localStorage.getItem('superdesk.login.selfHref') )
                superdesk.actionsUrl = localStorage.getItem('superdesk.login.selfHref')+'/Action';
            
            superdesk.getActions('menu.*')
            .done(function(menu)
            {
                self.displayMenu = [];
                $(menu).each(function()
                {
                    var Subs = null;
                    if(this.ChildrenCount > 0)
                    {
                        var Subs = 'data-submenu='+this.Path,
                            Subz = '[data-submenu="'+this.Path+'"]';
                        
                        self.submenus[this.Path] = this.Path + '.*';
                    }
                    self.displayMenu.push($.extend({}, this, 
                    { 
                        Path: this.Path.split('.'), 
                        Name: this.Path.replace('.', '-'),
                        Subs: Subs
                    }));
                });
                dfd.resolve(self);
            }).
            // we still resolve it so we can display something
            fail(function(){ dfd.resolve(self); });
            return this;
        },
        init: function()
        {
            var self = this;
            this.rnd = Math.random();
            this.setElement($('#navbar-top'));
            this.displayMenu = [];
            //this.getMenu(this.render, 'init');
            
            this.el.on('refresh-menu', function(){ self.getMenu(self.render, 'refresh'); });
            
            $(AuthApp)
            .off('authenticated.menu')
            .on('authenticated.menu', function()
            { 
                superdesk.clearActions();
                superdesk.actionsUseAuth = true;
                superdesk.actionsUrl = localStorage.getItem('superdesk.login.selfHref')+'/Action';
                self.getMenu(self.render, 'authenticated'); 
            });
            $(AuthApp).on('authlock', function()
            { 
                $('[data-username-display="true"]', self.el).text(_('Login'))
                    .on('click', function(evt)
                    {
                        $('#navbar-logout', self.el).trigger('click');
                        return false;
                    });
            });
            
            $.superdesk.applyLayout('layouts/dashboard', {}, function()
            {
                superdesk.getActions('modules.dashboard.*')
                .done(function(apps)
                {
                    $(apps).each(function()
                    {
                        require([config.api_url + this.ScriptPath], function(app)
                        { 
                            app && app.init && app.init( $($.superdesk.layoutPlaceholder) ); 
                        }); 
                    });
                });
            });
        },
        /*!
         * Deferred callback
         */
        render: function(view)
        {
            // make data for menu template
            var self = view,
                navData = {superdesk: {menu: self.displayMenu}};
            superdesk.login && $.extend(navData, {user: superdesk.login});

            self.el
            .html('')
            .tmpl('navbar', navData, function()
            {
                /*!
                 * for submenus, we get their corresponding build scripts
                 */
                self.el.find('[data-submenu]').each(function()
                {
                    var submenuElement = this;
                    superdesk.getActions( self.submenus[$(this).attr('data-submenu')] )
                    .done(function(subs)
                    {
                        $(subs).each(function()
                        { 
                            require([this.Script.href], function(submenuApp)
                            { 
                                submenuApp && submenuApp.init && submenuApp.init(submenuElement, self.el); 
                            }); 
                        });
                    });
                });
            })
            .off('click.superdesk')
            .on('click.superdesk', '.nav > li > a', function(event)
            {
                var self = this;
                if(!$(self).attr('href')) return;
                if(!$(self).attr('script-path')) { event.preventDefault(); return; }

                $(self).attr('data-loader') != 'false' && superdesk.showLoader();
                
                var callback = function()
                { 
                    require([$(self).attr('script-path')], function(x){ x && x.init && x.init(); });
                };
                  
                var href = $(self).attr('href').replace(/^\/+|\/+$/g, '');
                if( $.trim(href) != '' )
                    superdesk.navigation.bind( href, callback, $(self).text() || null );
                else
                    callback();
                
                event.preventDefault(); 
            });
            
            /*!
             * redirect to current page on reload
             */
            if( superdesk.navigation.getStartPathname() != '')
                self.el.find('li > a[href]').each(function()
                {
                    if( $(this).attr('href').replace(/^\/+|\/+$/g, '') == superdesk.navigation.getStartPathname()) 
                        $(this).trigger('click'); 
                });
            
            $('#navbar-logout', self.el) // TODO param.
            .off('click.superdesk')
            .on('click.superdesk', function()
            {
                if(!localStorage.getItem('superdesk.login.session'))
                {
                    AuthApp.require.call();
                    return;
                }
                delete superdesk.login;
                localStorage.removeItem('superdesk.login.name');
                localStorage.removeItem('superdesk.login.id');
                delete $.restAuth.prototype.requestOptions.headers.Authorization;
                $(AuthApp).trigger('logout');
                var gm = self.getMenu(self.render);
            });
        },
        /*!
         * login control
         */
        loginHandler: function(evt)
        {
            if( $(evt.currentTarget).attr('data-logged-in') == 'false' ) AuthApp.require.call();
        }
        
    });
    
    return MenuView;
});